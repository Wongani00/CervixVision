# Cervical Cancer Prediction Web App

A web-based system that predicts cervical cancer from cervical images using a machine learning model Xception. The system is built with Flask and includes role-based access for health practitioners, and admins.

---

## Features

- **Cervical Image Prediction** using an ML model
- **Role-based Access Control**:
  - **Health Practitioners**: Upload images and view predictions
  - **Admins**: Manage users, verify accounts, view statistics
  - **Super Admin**: Full system control (admins + users)
- **Dashboards** for prediction trends (daily, monthly, gender)
- **Image Upload and Scheduling** of next screenings
- **System Reports** per user or overall (PDF/CSV ready)
- **Model Performance Monitoring**
- **Secure Login/Signup** with strong password enforcement

---

## Tech Stack

- **Backend**: Flask + Flask-SQLAlchemy + Flask-Migrate
- **Frontend**: HTML + CSS + Bootstrap + TailwindCSS + Vanilla JavaScript (AJAX)
- **ML Model**: Xception (Keras/TensorFlow)
- **Database**: SQLite (dev), PostgreSQL (production ready)
- **Deployment Ready**: Render / Railway / Heroku / Any Platform That Supports Python

---

## Getting Started

### Installation

```bash
git clone https://github.com/Wongani00/CervixVision.git
cd CervixVision
python -m venv venv
venv\Scripts\activate  # on Windows:
pip install -r requirements.txt
```
