import traceback
from flask import Blueprint, jsonify, request
from datetime import date, datetime, timedelta
from sqlalchemy import func, extract, case
from appPackage.models import Prediction
from appPackage import db
from flask_login import login_required
from appPackage.user_management.routes import role_required

api = Blueprint("api", __name__)

# List of all the cell classes (predicted_class values)
CELL_CLASSES = [
    "Dyskeratotic",
    "Koilocytotic",
    "Metaplastic",
    "Parabasal",
    "Superficial-Intermediate",
]

CLASS_COLORS = {
    "Dyskeratotic": "#e74c3c",
    "Koilocytotic": "#f39c12",
    "Metaplastic": "#2980b9",
    "Parabasal": "#1abc9c",
    "Superficial-Intermediate": "#27ae60",
}


@api.route("/api/daily-predictions")
@login_required
@role_required("admin", "super admin", "doctor")
def daily_predictions():
    try:
        days = int(request.args.get("days", 7))
        if days <= 0 or days > 365:
            return jsonify({"error": "Days must be between 1-365"}), 400

        # Get date range
        today = datetime.now().date()
        start_date = today - timedelta(days=days - 1)

        # Query database - exclude NULL predicted_class
        results = (
            db.session.query(
                func.date(Prediction.created_at).label("date"),
                Prediction.predicted_class,
                func.count().label("count"),
            )
            .filter(
                Prediction.created_at
                >= datetime.combine(start_date, datetime.min.time()),
                Prediction.created_at <= datetime.combine(today, datetime.max.time()),
                Prediction.predicted_class.isnot(None),  # Exclude NULL classes
            )
            .group_by(func.date(Prediction.created_at), Prediction.predicted_class)
            .all()
        )

        # Generate date sequence
        date_sequence = [start_date + timedelta(days=i) for i in range(days)]
        weekday_labels = [date.strftime("%a") for date in date_sequence]

        # Build lookup dictionary with proper null handling
        results_dict = {}
        for result in results:
            try:
                # Handle date (string or date object)
                result_date = (
                    result.date
                    if isinstance(result.date, date)
                    else datetime.strptime(str(result.date), "%Y-%m-%d").date()
                )
                # Handle class name (ensure not None and strip whitespace)
                class_name = (
                    str(result.predicted_class).strip().lower()
                    if result.predicted_class
                    else "unknown"
                )
                key = (result_date, class_name)
                results_dict[key] = result.count
            except Exception as e:
                print(f"Error processing record: {e}")
                continue

        # Build datasets
        datasets = []
        for class_name in CELL_CLASSES:
            # Find matching class name (case-insensitive)
            matched_class = next(
                (
                    rc
                    for rc in {
                        str(r.predicted_class).strip()
                        for r in results
                        if r.predicted_class
                    }
                    if rc.lower() == class_name.lower()
                ),
                class_name,
            )

            class_data = {
                "label": class_name,
                "data": [
                    results_dict.get((d, matched_class.lower()), 0)
                    for d in date_sequence
                ],
                "backgroundColor": f"{CLASS_COLORS[class_name]}33",
                "borderColor": CLASS_COLORS[class_name],
                "borderWidth": 1,
            }
            datasets.append(class_data)

        return jsonify(
            {
                "labels": weekday_labels,
                "datasets": datasets,
                "meta": {
                    "query_start": start_date.isoformat(),
                    "query_end": today.isoformat(),
                    "total_days": days,
                    "records_found": len(results),
                    "classes_found": len(
                        {
                            str(r.predicted_class).strip()
                            for r in results
                            if r.predicted_class
                        }
                    ),
                },
            }
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "error": "Failed to fetch daily predictions",
                    "details": str(e),
                    "trace": traceback.format_exc() if __debug__ else None,
                }
            ),
            500,
        )


@api.route("/api/monthly-predictions")
@login_required
@role_required("admin", "super admin", "doctor")
def monthly_predictions():
    months = int(request.args.get("months", 12))

    results = (
        db.session.query(
            extract("month", Prediction.created_at).label("month"),
            Prediction.predicted_class,
            func.count().label("count"),
        )
        .group_by(extract("month", Prediction.created_at), Prediction.predicted_class)
        .order_by(extract("month", Prediction.created_at))
        .all()
    )

    month_names = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    current_month = datetime.now().month
    month_indices = [(current_month - i - 1) % 12 + 1 for i in range(months)]
    month_indices.reverse()

    datasets = []
    for cell_class in CELL_CLASSES:
        class_data = {"label": cell_class, "data": []}
        for month in month_indices:
            count = next(
                (
                    r.count
                    for r in results
                    if r.month == month and r.predicted_class == cell_class
                ),
                0,
            )
            class_data["data"].append(count)
        datasets.append(class_data)

    return jsonify(
        {"labels": [month_names[i - 1] for i in month_indices], "datasets": datasets}
    )


@api.route("/api/age-distribution")
@login_required
@role_required("admin", "super admin", "doctor")
def age_distribution():
    filter_class = request.args.get("class", "all")

    age_bins = [
        (21, 30, "21-30"),
        (31, 40, "31-40"),
        (41, 50, "41-50"),
        (51, 60, "51-60"),
        (61, 200, "61+"),
    ]

    query = db.session.query()

    for low, high, label in age_bins:
        query = query.add_columns(
            func.sum(case((Prediction.age.between(low, high), 1), else_=0)).label(label)
        )

    if filter_class != "all":
        query = query.filter(Prediction.predicted_class == filter_class)

    result = query.one()

    return jsonify(
        {
            "labels": [label for _, _, label in age_bins],
            "values": [getattr(result, label) for _, _, label in age_bins],
        }
    )


@api.route("/api/class-stats")
@login_required
@role_required("admin", "super admin", "doctor")
def class_stats():
    class_counts = db.session.query(
        Prediction.predicted_class, func.count().label("count")
    ).filter(Prediction.predicted_class != None)
    class_counts = class_counts.group_by(Prediction.predicted_class).all()

    counts = {cell_class: 0 for cell_class in CELL_CLASSES}

    for row in class_counts:
        if row.predicted_class in counts:
            counts[row.predicted_class] = row.count

    total = sum(counts.values())

    return jsonify(
        {
            "total": total,
            "counts": counts,
            "percentages": {
                k: round((v / total) * 100, 1) if total > 0 else 0
                for k, v in counts.items()
            },
        }
    )
