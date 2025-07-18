import csv
from datetime import datetime, timedelta
import io
import math
import os
import random
from PIL import Image  # type: ignore
from flask import (
    Blueprint,
    Response,
    abort,
    current_app,
    make_response,
    render_template,
    request,
    jsonify,
    send_file,
    url_for,
)
from io import BytesIO, StringIO
import pandas as pd
from sqlalchemy import func
from xhtml2pdf import pisa
from flask import current_app as app
from flask_login import login_user, logout_user, login_required, current_user
from appPackage.models import Feedback, User, Prediction
from appPackage import db
from appPackage.user_management.routes import role_required
import uuid
from werkzeug.utils import secure_filename

from tensorflow.keras.models import load_model  # type: ignore
from tensorflow.keras.preprocessing.image import img_to_array, load_img  # type: ignore
import numpy as np
import tensorflow as tf

tf.config.optimizer.set_jit(
    True
)  # Enable XLA (Accelerated Linear Algebra) for faster computation

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


main = Blueprint("main", __name__)

# Load ensemble model
model = load_model("Model/xception_cervical_cancer.keras")
# classes in the model
labels = [
    "Dyskeratotic",
    "Koilocytotic",
    "Metaplastic",
    "Parabasal",
    "Superficial-Intermediate",
]


# home/landing page's route
@main.route("/")
@login_required
def home():
    return render_template("main/index.html")


# dashboard route
@main.route("/dashboard/model-trends")
@login_required
@role_required("admin", "super admin", "doctor")
def dashboard():
    title = "Dashboard"
    # if current_user.is_authenticated and current_user.email == "super_admin01@gmail.com":
    #     current_user.role = "super admin"
    #     db.session.commit()  # Commit the role change to the database
    # if (
    #     current_user.is_authenticated
    #     and current_user.email == "wonganikaunga726@gmail.com"
    # ):
    #     current_user.role = "admin"
    #     try:
    #         db.session.commit()
    #         print(f"{current_user.email}'s role has been updated to admin")
    #     except Exception as e:
    #         print(f"Error updating role for {current_user.email}: {e}")
    users = None
    return render_template("main/dashboard.html")


# prediction route
@main.route("/prediction", methods=["GET", "POST"])
@login_required
@role_required("doctor", "nurse")
def prediction():

    if request.method == "POST":
        image_file = request.files.get("image")
        user_id = current_user.id
        first_name = request.form.get("firstname")
        surname = request.form.get("surname")
        date_of_birth = request.form.get("userDOB")
        dateOfPrediction = request.form.get("predictionDate")

        # Validate required fields
        if not all(
            [user_id, first_name, surname, date_of_birth, dateOfPrediction, image_file]
        ):
            return jsonify({"error": "Missing required fields"}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Invalid user_id"}), 400

        try:
            dob = datetime.strptime(date_of_birth, "%Y-%m-%d")
            today = datetime.today()
            age = (
                today.year
                - dob.year
                - ((today.month, today.day) < (dob.month, dob.day))
            )
        except Exception:
            return jsonify({"error": "Invalid DOB format"}), 400

        try:
            created_at = datetime.strptime(dateOfPrediction, "%Y-%m-%d")
        except Exception:
            return jsonify({"error": "Invalid date format"}), 400

        # Validate image file and saving it to tye file system for later use
        try:
            # Ensure allowed extension
            # ext = os.path.splitext(image_file.filename)[1].lower()
            # allowed_exts = [".jpg", ".jpeg", ".png"]
            # if ext not in allowed_exts:
            #     return jsonify({"error": "Unsupported image format"}), 400

            # Generate a unique and safe filename
            filename = f"{uuid.uuid4().hex}.jpg"
            user_folder = os.path.join(
                current_app.root_path, "static", "uploads", f"user_{user_id}"
            )
            os.makedirs(user_folder, exist_ok=True)
            filepath = os.path.join(user_folder, secure_filename(filename))

            # Open the uploaded image
            image = Image.open(image_file).convert("RGB")  # Converts even PNG to RGB
            image = image.resize((224, 224))  # Resize to model's required dimensions

            # Save the image as JPEG
            image.save(filepath, format="JPEG", quality=85, optimize=True)

        except Exception as e:
            print("Image processing error:", e)
            return jsonify({"error": "Failed to process image"}), 400

        # Prepare image for prediction (only for model input)
        image_for_model = Image.open(filepath).convert("RGB")
        image_for_model = img_to_array(image_for_model) / 255.0
        image_for_model = np.expand_dims(image_for_model, axis=0)

        # Model prediction
        preds = model.predict(image_for_model)
        probs = preds[0]

        # Top-1 and Top-2
        sorted_indices = np.argsort(probs)[::-1]
        top1_idx = sorted_indices[0]
        top2_idx = sorted_indices[1]
        label = labels[top1_idx]
        top1 = float(probs[top1_idx])
        top2 = float(probs[top2_idx])
        # Calculate score gap
        score_gap = float(top1 - top2)

        if top1 >= 0.9999:
            top1 = 0.9996
        if top1 >= 0.9998:
            top1 = 0.9994
        elif 0.9987 <= top1 <= 0.9997:
            top1 = 0.9992
        elif top1 >= 0.9999:
            top1 = 0.9989
        # Entropy (natural log)
        entropy = -np.sum(probs * np.log(probs + 1e-9))

        # Thresholds
        confidence_cap = 0.9989
        min_score_gap = 0.02
        entropy_threshold = 0.05

        # OOD Check
        if (
            top1 >= confidence_cap
            and score_gap >= min_score_gap
            and entropy <= entropy_threshold
        ):
            ood_status = "accepted"
        else:
            ood_status = "rejected"

        # Save to DB
        prediction = Prediction(
            first_name=first_name,
            surname=surname,
            age=age,
            # image_path=os.path.join(f"user_{user_id}", filename),
            image_path=f"user_{user_id}/{filename}",
            predicted_class=label if ood_status == "accepted" else None,
            confidence=top1,
            ood_status=ood_status,
            created_at=created_at,
            user_id=user_id,
        )
        db.session.add(prediction)
        db.session.commit()

        if ood_status == "rejected":
            return (
                jsonify(
                    {
                        "error": "⚠️ Prediction is not reliable.",
                        "ood_status": ood_status,
                        "entropy": float(round(entropy, 4)),
                        "confidence": float(round(top1, 4)),
                        "score_gap": float(round(score_gap, 4)),
                        "recommendation": "Please ensure the image is a clear cervical screening image.",
                    }
                ),
                400,
            )

        return jsonify(
            {
                "result": label,
                "first_name": first_name,
                "surname": surname,
                "age": age,
                "confidence": float(round(top1, 4)),
                "entropy": float(round(entropy, 4)),
                "score_gap": float(round(score_gap, 4)),
                "ood_status": ood_status,
            }
        )

    return render_template("main/predict.html")


# === route responsible for generating reports in the system ===
@main.route("/results")
@login_required
def result_generation():
    # if current_user.role not in ["admin", "super_admin"]:
    #     abort(403)
    # if current_user.is_authenticated and current_user.email == "superadmin@gmail.com":

    #     # Commit the role change to the database
    #     try:
    #         current_user.role = "super admin"
    #         db.session.commit()
    #         print(current_user.email + "'s role has been changed to admin")
    #     except Exception as e:
    #         print("error ", e)
    return render_template("main/results.html")


@main.route("/api/result")
@login_required
def api_report():
    start = request.args.get("start")
    end = request.args.get("end")
    pred_class = request.args.get("class")
    uploaded_by = request.args.get("user")
    page = request.args.get("page", 1, type=int)
    per_page = 5  # Set 5 items per page

    query = Prediction.query.join(User)

    # Filtering only current user's data if they're not admin/super_admin
    if current_user.role not in ["admin", "super admin", "doctor"]:
        query = query.filter(Prediction.user_id == current_user.id)
    else:
        if uploaded_by:
            query = query.filter(User.id == uploaded_by)

    if start:
        query = query.filter(Prediction.created_at >= start)
    if end:
        query = query.filter(Prediction.created_at <= end)
    if pred_class:
        query = query.filter(Prediction.predicted_class == pred_class)

    # Use pagination
    pagination = query.order_by(Prediction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    predictions = pagination.items

    # Only [admin, super admin, doctor] get the list of all users
    users = []
    if current_user.role in ["admin", "super admin", "doctor"]:
        users = User.query.with_entities(User.id, User.f_name, User.surname).all()

    return jsonify(
        {
            "predictions": [
                {
                    "id": p.id,
                    "date": p.created_at.date().isoformat(),
                    "first_name": p.first_name,
                    "surname": p.surname,
                    "patient_name": f"{p.first_name} {p.surname}",  # Full name
                    "predicted_class": p.predicted_class,
                    "true_label": p.true_label,  # Include true label
                    "confidence": p.confidence,
                    "ood_status": p.ood_status,
                    "user_name": f"{p.user.f_name} {p.user.surname}",  # Uploader
                }
                for p in predictions
            ],
            "users": [{"id": u.id, "name": f"{u.f_name} {u.surname}"} for u in users],
            "pagination": {
                "total": pagination.total,
                "pages": pagination.pages,
                "current_page": pagination.page,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        }
    )


# api to produce csv report
@main.route("/export/predictions/csv")
@login_required
def export_csv():
    try:
        # Get filter parameters from request
        start = request.args.get("start")
        end = request.args.get("end")
        pred_class = request.args.get("class")
        uploaded_by = request.args.get("user")

        query = db.session.query(
            Prediction.created_at,
            Prediction.predicted_class,
            Prediction.confidence,
            Prediction.ood_status,
            Prediction.first_name,
            Prediction.surname,
            Prediction.true_label,
        ).join(User)

        # Apply filtering logic
        if current_user.role not in ["admin", "super admin", "doctor"]:
            query = query.filter(Prediction.user_id == current_user.id)
        elif uploaded_by:
            query = query.filter(User.id == uploaded_by)

        # Date filtering
        if start:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            query = query.filter(func.date(Prediction.created_at) >= start_date)
        if end:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            query = query.filter(func.date(Prediction.created_at) <= end_date)

        if pred_class:
            query = query.filter(Prediction.predicted_class == pred_class)

        results = query.order_by(Prediction.created_at.desc()).all()

        # Prepare CSV data
        csv_data = []
        headers = [
            "Date",
            "Patient Name",
            "Predicted Class",
            "True Label",
            "Confidence",
            "OOD Status",
        ]
        csv_data.append(",".join(headers))

        for r in results:
            date_str = r[0].date().isoformat()
            patient_name = f"{r[4]} {r[5]}"  # first_name + surname from Prediction
            confidence = f"{round(r[2]*100, 2)}%" if r[2] is not None else "N/A"
            ood_status = r[3] if r[3] is not None else "N/A"
            predicted_class = r[1]
            true_label = getattr(
                r, "true_label", "N/A"
            )  # Safely access if not included in query

            row = [
                date_str,
                patient_name,
                predicted_class,
                true_label,
                confidence,
                ood_status,
            ]
            csv_data.append(",".join(f'"{x}"' for x in row))

        # Generate filename
        filename_parts = ["predictions"]
        if start:
            filename_parts.append(f"from_{start}")
        if end:
            filename_parts.append(f"to_{end}")
        if pred_class:
            filename_parts.append(f"class_{pred_class}")
        if uploaded_by and current_user.role in ["admin", "super admin", "doctor"]:
            user = User.query.get(uploaded_by)
            if user:
                filename_parts.append(f"user_{user.f_name}_{user.surname}")

        filename = "_".join(filename_parts) + ".csv"

        # Create response
        response = make_response("\n".join(csv_data))
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv"

        return response

    except Exception as e:
        current_app.logger.error(f"Error generating CSV: {str(e)}")
        return "Error generating CSV results", 500


# api to produce pdf report
@main.route("/export/predictions/pdf")
@login_required
def export_pdf():
    try:
        # Get filter parameters from request
        start = request.args.get("start")
        end = request.args.get("end")
        pred_class = request.args.get("class")
        uploaded_by = request.args.get("user")

        query = db.session.query(
            Prediction.created_at,
            Prediction.predicted_class,
            Prediction.confidence,
            Prediction.ood_status,
            Prediction.first_name,
            Prediction.surname,
            Prediction.true_label,
        ).join(User)

        # Apply filtering logic
        if current_user.role not in ["admin", "super admin", "doctor"]:
            query = query.filter(Prediction.user_id == current_user.id)
        elif uploaded_by:
            query = query.filter(User.id == uploaded_by)

        # Date filtering
        if start:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            query = query.filter(func.date(Prediction.created_at) >= start_date)
        if end:
            end_date = datetime.strptime(end, "%Y-%m-%d").date()
            query = query.filter(func.date(Prediction.created_at) <= end_date)

        if pred_class:
            query = query.filter(Prediction.predicted_class == pred_class)

        results = query.order_by(Prediction.created_at.desc()).all()

        # Build HTML
        html = f"""
        <html>
        <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #333; font-size: 18px; }}
            h2 {{ color: #555; font-size: 14px; margin-top: 5px; }}
            .filter-info {{ margin-bottom: 15px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ background-color: #f2f2f2; text-align: left; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
            .footer {{ margin-top: 20px; font-size: 10px; color: #777; }}
        </style>
        </head>
        <body>
        <h1>Prediction Results</h1>
        <div class="filter-info">
        """

        # Add filter information
        filter_parts = []
        if start:
            filter_parts.append(f"From: {start}")
        if end:
            filter_parts.append(f"To: {end}")
        if pred_class:
            filter_parts.append(f"Class: {pred_class}")
        if uploaded_by and current_user.role in ["admin", "super admin", "doctor"]:
            user = User.query.get(uploaded_by)
            if user:
                filter_parts.append(f"User: {user.f_name} {user.surname}")

        if filter_parts:
            html += "<h2>" + " | ".join(filter_parts) + "</h2>"
        else:
            html += "<h2>All Predictions</h2>"

        html += """
        </div>
        <table>
            <tr>
                <th>Date</th>
                <th>Patient</th>
                <th style={{ max-width: 70px; display: block;}}>Predicted Class</th>
                <th>True Label</th>
                <th>Confidence</th>
                <th>OOD Status</th>
            </tr>
        """

        for r in results:
            date_str = r[0].date().isoformat()
            confidence = f"{round(r[2] * 100, 2)}%" if r[2] is not None else "N/A"
            ood_status = r[3] if r[3] is not None else "N/A"
            predicted_class = r[1]
            true_label = r[6] if len(r) > 6 else "N/A"
            patient_name = f"{r[4]} {r[5]}"

            html += f"""
            <tr>
                <td>{date_str}</td>
                <td>{patient_name}</td>
                <td>{predicted_class}</td>
                <td>{true_label}</td>
                <td>{confidence}</td>
                <td>{ood_status}</td>
            </tr>
            """

        html += f"""
        </table>
        <div class="footer">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Records: {len(results)}
        </div>
        </body>
        </html>
        """

        # Generate filename
        filename_parts = ["predictions"]
        if start:
            filename_parts.append(f"from_{start}")
        if end:
            filename_parts.append(f"to_{end}")
        if pred_class:
            filename_parts.append(f"class_{pred_class}")
        if uploaded_by and current_user.role in ["admin", "super admin", "doctor"]:
            user = User.query.get(uploaded_by)
            if user:
                filename_parts.append(f"user_{user.f_name}_{user.surname}")

        filename = "_".join(filename_parts) + ".pdf"

        # Generate PDF
        pdf = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=pdf)

        if pisa_status.err:
            raise Exception("PDF generation error")

        pdf.seek(0)

        response = make_response(pdf.getvalue())
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"

        return response

    except Exception as e:
        current_app.logger.error(f"Error generating PDF: {str(e)}")
        return "Error generating PDF results", 500


# Feedback Route
@main.route("/feedback", methods=["POST"])
@login_required
@role_required("admin", "super admin")
def feedback():
    data = request.get_json()
    if not data or "message" not in data or "user_id" not in data:
        return jsonify({"error": "Missing message or user_id"}), 400

    user = User.query.get(data["user_id"])
    if not user:
        return jsonify({"error": "Invalid user_id"}), 400

    new_feedback = Feedback(message=data["message"], user_id=data["user_id"])
    db.session.add(new_feedback)
    db.session.commit()
    return jsonify({"message": "Feedback submitted successfully"})


# ==== user profile route ====
# @main.route("/profile")
# @login_required
# def user_profile():
#     return render_template("main/profile.html")


# reports route
@main.route("/reports")
@login_required
@role_required("admin", "super admin")
def reports():
    return render_template("main/reports.html")


# summary reports endpoint
@main.route("/api/report/summary")
@login_required
@role_required("admin", "super admin")
def report_summary():

    start_date = request.args.get("start")
    end_date = request.args.get("end")

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    query = Prediction.query
    if start:
        query = query.filter(Prediction.created_at >= start)
    if end:
        query = query.filter(Prediction.created_at <= end)

    total = query.count()
    avg_conf = (
        query.filter(Prediction.confidence != None)
        .filter(Prediction.confidence <= 1.0)  # <- Filter out incorrect values
        .with_entities(func.avg(Prediction.confidence))
        .scalar()
        or 0
    )

    rejected = query.filter_by(ood_status="rejected").count()

    # Class distribution
    class_counts = (
        db.session.query(Prediction.predicted_class, func.count(Prediction.id))
        .filter(Prediction.created_at >= start if start else True)
        .filter(Prediction.created_at <= end if end else True)
        .group_by(Prediction.predicted_class)
        .all()
    )
    class_dist = [{"class": c[0], "count": c[1]} for c in class_counts]

    # Most frequent class
    top_class = max(class_counts, key=lambda x: x[1])[0] if class_counts else "N/A"

    # Most recent upload
    recent = query.order_by(Prediction.created_at.desc()).first()
    last_upload = recent.created_at.strftime("%Y-%m-%d %H:%M") if recent else "N/A"

    return jsonify(
        {
            "total_predictions": total,
            "avg_confidence": round(avg_conf, 4),
            "rejected_count": rejected,
            "class_distribution": class_dist,
            "top_class": top_class,
            "last_upload": last_upload,
        }
    )


# Export summary report as CSV
@main.route("/export/summary_report/csv")
@login_required
@role_required("admin", "super admin")
def export_summary_csv():

    # Extract and parse date range
    start = request.args.get("start")
    end = request.args.get("end")
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d") if start else None
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else None
    except:
        return jsonify({"error": "Invalid dates"}), 400

    query = Prediction.query
    if start_dt:
        query = query.filter(Prediction.created_at >= start_dt)
    if end_dt:
        query = query.filter(Prediction.created_at <= end_dt)

    total = query.count()
    avg_conf = query.with_entities(func.avg(Prediction.confidence)).scalar() or 0
    rejected = query.filter_by(ood_status="rejected").count()

    class_counts = (
        db.session.query(Prediction.predicted_class, func.count(Prediction.id))
        .filter(Prediction.created_at >= start_dt if start_dt else True)
        .filter(Prediction.created_at <= end_dt if end_dt else True)
        .group_by(Prediction.predicted_class)
        .all()
    )
    top_class = max(class_counts, key=lambda x: x[1])[0] if class_counts else "N/A"
    recent = query.order_by(Prediction.created_at.desc()).first()
    last_upload = recent.created_at.strftime("%Y-%m-%d %H:%M") if recent else "N/A"

    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric", "Value"])
    writer.writerow(["Total Predictions", total])
    writer.writerow(["Average Confidence", f"{avg_conf * 100:.2f}%"])
    writer.writerow(["Rejected Predictions", rejected])
    writer.writerow(["Most Frequent Class", top_class])
    writer.writerow(["Most Recent Upload", last_upload])
    writer.writerow(["Class Distribution"])
    for c in class_counts:
        writer.writerow([c[0], c[1]])

    output.seek(0)
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=report_summary.csv"},
    )


# API for exporting PDF report
@main.route("/export/summary_report/pdf")
@login_required
@role_required("admin", "super admin")
def export_summary_pdf():
    from collections import defaultdict
    import matplotlib.pyplot as plt
    import base64

    start = request.args.get("start")
    end = request.args.get("end")
    try:
        start_dt = datetime.strptime(start, "%Y-%m-%d") if start else None
        end_dt = datetime.strptime(end, "%Y-%m-%d") if end else None
    except:
        return jsonify({"error": "Invalid dates"}), 400

    query = Prediction.query
    if start_dt:
        query = query.filter(Prediction.created_at >= start_dt)
    if end_dt:
        query = query.filter(Prediction.created_at <= end_dt)

    total = query.count()
    avg_conf = query.with_entities(func.avg(Prediction.confidence)).scalar() or 0
    rejected = query.filter_by(ood_status="rejected").count()

    class_counts = (
        db.session.query(Prediction.predicted_class, func.count(Prediction.id))
        .filter(Prediction.created_at >= start_dt if start_dt else True)
        .filter(Prediction.created_at <= end_dt if end_dt else True)
        .group_by(Prediction.predicted_class)
        .all()
    )

    top_class = max(class_counts, key=lambda x: x[1])[0] if class_counts else "N/A"
    recent = query.order_by(Prediction.created_at.desc()).first()
    last_upload = recent.created_at.strftime("%Y-%m-%d %H:%M") if recent else "N/A"

    # Daily predictions (trend data)
    date_counts = defaultdict(int)
    for pred in query.all():
        date = pred.created_at.strftime("%Y-%m-%d")
        date_counts[date] += 1

    sorted_dates = sorted(date_counts.items())
    dates, counts = zip(*sorted_dates) if sorted_dates else ([], [])

    # Generate bar chart (trend)
    if dates:
        plt.figure(figsize=(6, 3))
        plt.bar(dates, counts, color="skyblue")
        plt.xticks(rotation=45, ha="right", fontsize=6)
        plt.tight_layout()
        plt.title("Prediction Count per Day")
        plt.ylabel("Count")

        chart_buffer = BytesIO()
        plt.savefig(chart_buffer, format="png")
        chart_buffer.seek(0)
        chart_base64 = base64.b64encode(chart_buffer.read()).decode("utf-8")
        plt.close()

        chart_html = f'<img src="data:image/png;base64,{chart_base64}" width="100%">'
    else:
        chart_html = "<p>No trend data available.</p>"

    # Generate class distribution HTML
    class_dist_html = "<ul>"
    for c in class_counts:
        class_dist_html += f"<li>{c[0]}: {c[1]}</li>"
    class_dist_html += "</ul>"

    # HTML Report Template
    html = f"""
    <html>
    <body>
    <h2 style="text-align: center;">Cervical Cancer Prediction Report Summary</h2>
    <hr>
    <p><strong>Report Time Range:</strong> {start} to {end}</p>
    <h3>1. Total Predictions</h3>
    <p>{total} predictions were made in the selected period. This indicates the level of screening activity and model usage.</p>

    <h3>2. Average Confidence Score</h3>
    <p>{(avg_conf * 100):.2f}% - This reflects how certain the model was on average. Higher confidence suggests stronger model predictions.</p>

    <h3>3. Rejected Predictions</h3>
    <p>{rejected} predictions were flagged as out-of-distribution (OOD) and rejected. These may indicate unfamiliar or poor-quality inputs.</p>

    <h3>4. Most Frequent Predicted Class</h3>
    <p><strong>{top_class}</strong> - This class appeared most often.</p>

    <h3>5. Class Distribution</h3>
    {class_dist_html}

    <h3>6. Most Recent Upload</h3>
    <p>Last recorded prediction upload: {last_upload}</p>

    <h3>7. Prediction Trends Over Time</h3>
    <p>This chart shows how many predictions were made each day, helping track usage patterns or screening campaigns.</p>
    {chart_html}

    <hr>
    <p style="font-size: 12px; color: #888;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </body>
    </html>
    """

    # Generate PDF
    pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf)

    if pisa_status.err:
        return jsonify({"error": "Error generating PDF"}), 500

    pdf.seek(0)
    response = make_response(pdf.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = (
        "attachment; filename=prediction_report_detailed.pdf"
    )
    return response


# Route to get, edit, and delete predictions
# @main.route("/api/prediction/<int:pred_id>", methods=["GET", "PUT", "DELETE"])
# @login_required
# def api_prediction(pred_id):
#     prediction = Prediction.query.get_or_404(pred_id)

#     # Authorization check
#     if (
#         current_user.role not in ["admin", "super admin", "doctor"]
#         and prediction.user_id != current_user.id
#     ):
#         abort(403)

#     if request.method == "GET":
#         return jsonify(
#             {
#                 "id": prediction.id,
#                 "first_name": prediction.first_name,
#                 "surname": prediction.surname,
#                 "age": prediction.age,
#                 "predicted_class": prediction.predicted_class,
#                 "confidence": prediction.confidence,
#                 "ood_status": prediction.ood_status,
#                 "image_path": prediction.image_path,
#                 "created_at": prediction.created_at.isoformat(),
#                 "user_id": prediction.user_id,
#             }
#         )

#     elif request.method == "PUT":
#         data = request.get_json()
#         if "ood_status" in data:
#             prediction.ood_status = data["ood_status"]

#         db.session.commit()
#         return jsonify({"message": "Prediction updated successfully"})

#     elif request.method == "DELETE":
#         db.session.delete(prediction)
#         db.session.commit()
#         return jsonify({"message": "Prediction deleted successfully"})


# GET prediction details for review modal
@main.route("/api/prediction/<int:prediction_id>")
@login_required
@role_required("doctor", "admin", "super admin")
def get_prediction_details(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)

    # Construct full image URL for use in frontend
    image_url = url_for("static", filename=f"uploads/{prediction.image_path}")

    return jsonify(
        {
            "id": prediction.id,
            "first_name": prediction.first_name,
            "surname": prediction.surname,
            "age": prediction.age,
            "predicted_class": prediction.predicted_class,
            "confidence": prediction.confidence,
            "ood_status": prediction.ood_status,
            "true_label": prediction.true_label,
            "image_path": image_url,
            "created_at": prediction.created_at.isoformat(),
            "user_name": f"{prediction.user.f_name} {prediction.user.surname}",
        }
    )


# POST to update a prediction (OOD + true_label)
@main.route("/api/prediction/<int:prediction_id>/update", methods=["POST"])
@login_required
@role_required("doctor", "admin", "super admin")
def update_prediction(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)

    try:
        data = request.get_json()

        if "ood_status" in data:
            prediction.ood_status = data["ood_status"] or None

        if "true_label" in data:
            prediction.true_label = data["true_label"] or None

        db.session.commit()

        return jsonify({"success": True, "message": "Prediction updated successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400


# DELETE a prediction and its image file
@main.route("/api/prediction/<int:prediction_id>/delete", methods=["DELETE"])
@login_required
@role_required("doctor", "admin", "super admin")
def delete_prediction(prediction_id):
    prediction = Prediction.query.get_or_404(prediction_id)

    try:
        # Delete image from disk
        if prediction.image_path:
            image_abs_path = os.path.join(
                current_app.root_path, "static", "uploads", prediction.image_path
            )

            if os.path.exists(image_abs_path):
                os.remove(image_abs_path)

        db.session.delete(prediction)
        db.session.commit()

        return jsonify({"success": True, "message": "Prediction deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400
