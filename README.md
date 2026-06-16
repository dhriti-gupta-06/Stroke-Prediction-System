# NeuralStroke — Clinical Risk Intelligence Platform

A full-stack stroke prediction platform for clinical risk assessment. The system runs seven trained machine learning models, uses **LightGBM** as the production classifier, and provides a modern React interface for single-patient analysis, batch processing, analytics, and role-based record management.

**Stack:** React 18 · Vite · Tailwind CSS · Flask · SQLAlchemy · SQLite · LightGBM / XGBoost / CatBoost

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Demo Users](#demo-users)
- [Authentication & Roles](#authentication--roles)
- [Application Pages](#application-pages)
- [Database Schema](#database-schema)
- [API Reference](#api-reference)
- [ML Pipeline](#ml-pipeline)
- [Production Build](#production-build)
- [User Management](#user-management)
- [Key Design Decisions](#key-design-decisions)
- [Disclaimer](#disclaimer)

---

## Features

### Prediction
- **Single-patient analysis** — enter health attributes, run all 7 models, view risk gauge, explanations, and per-model results
- **Batch prediction** — upload CSV/Excel, process multiple patients, download results, save to database
- **Patient ID management** — auto-generate IDs, check existing patients, view full prediction history in a modal
- **PDF reports** — download stroke risk reports with patient info, prediction, and risk factors
- **Explainability** — rule-based risk factor attribution (age, hypertension, glucose, BMI, smoking, etc.)

### Analytics & Reporting
- **Model Analytics** — advanced insights from saved predictions: usage frequency, stroke rates, confidence distribution, batch vs individual comparison
- **Prediction Records** — searchable, paginated table of all saved single and batch predictions
- **Model Performance** — bar charts, radar charts, and confusion matrices for all 7 models (from offline training metrics)
- **Dashboard** — production model highlight and ROC-AUC leaderboard
- **CSV export** — download model metrics as CSV

### Security & Access Control
- **JWT authentication** — login required for all app routes
- **Role-based data isolation** — doctors see only their own records and analytics
- **Admin oversight** — admin sees all records and can filter analytics by user
- **Server-side enforcement** — scope filtering on the backend; doctors cannot access other users' data via API manipulation

---

## Project Structure

```
stroke-platform/
├── backend/
│   ├── app.py                  # Flask API (all endpoints, JWT, ML inference)
│   ├── database.py             # SQLAlchemy models (User, Patient, Predictions)
│   ├── migrate.py              # One-time DB migration script
│   ├── seed_users.py           # Seed demo users (doctor1, doctor2, admin)
│   ├── create_users.py         # CLI tool to create/list users
│   ├── requirements.txt
│   ├── models/                 # Trained .pkl model files (not in git)
│   │   ├── lightGBM_model.pkl
│   │   ├── logistic_regression.pkl
│   │   ├── decision_tree.pkl
│   │   ├── random_forest.pkl
│   │   ├── random_forest_smote.pkl
│   │   ├── xgboost.pkl
│   │   ├── catboost.pkl
│   │   ├── scaler.pkl
│   │   ├── bmi_median.pkl
│   │   ├── le_married.pkl
│   │   ├── le_residence.pkl
│   │   ├── feature_columns.pkl
│   │   └── metrics.pkl
│   └── utils/
│       ├── predictor.py        # Feature preprocessing pipeline
│       └── explanation.py      # Risk factor explanations
│
└── frontend/
    ├── index.html
    ├── vite.config.js          # Dev server + /api proxy to Flask
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── package.json
    └── src/
        ├── App.jsx             # Routes + protected layout
        ├── main.jsx
        ├── index.css
        ├── context/
        │   └── AuthContext.jsx # JWT + role state
        ├── services/
        │   └── api.js          # Axios client with JWT interceptor
        ├── utils/
        │   └── helpers.js
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── Topbar.jsx
        │   ├── PageHeader.jsx
        │   ├── PatientModal.jsx
        │   ├── RiskGauge.jsx
        │   └── Spinner.jsx
        └── pages/
            ├── Login.jsx
            ├── Dashboard.jsx
            ├── Predict.jsx
            ├── Batch.jsx
            ├── Analytics.jsx
            ├── ModelPerformance.jsx
            └── About.jsx
```

---

## Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ recommended |
| Node.js | 18+ |
| npm | 9+ |

---

## Setup

### 1. Clone and enter the project

```bash
cd stroke-platform
```

### 2. Copy model files

Place all trained `.pkl` files into `backend/models/`:

```
backend/models/
├── logistic_regression.pkl
├── decision_tree.pkl
├── random_forest.pkl
├── random_forest_smote.pkl
├── xgboost.pkl
├── catboost.pkl
├── lightGBM_model.pkl
├── scaler.pkl
├── bmi_median.pkl
├── le_married.pkl
├── le_residence.pkl
├── feature_columns.pkl
└── metrics.pkl
```

> Model files are required for prediction and dashboard metrics. They are not committed to the repository.

### 3. Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt

# Run database migration (adds auth columns, role field, etc.)
python migrate.py

# Seed demo users
python seed_users.py

# Start Flask API
python app.py
```

Flask runs at **http://localhost:5000**

### 4. Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

React runs at **http://localhost:3000**

The Vite dev server proxies all `/api/*` requests to `http://localhost:5000`.

### 5. Open the app

Navigate to **http://localhost:3000** and sign in with a demo account (see below).

---

## Demo Users

| Username | Password | Role |
|----------|----------|------|
| `doctor1` | `pass123` | Doctor |
| `doctor2` | `pass456` | Doctor |
| `admin` | `admin123` | Admin |

Created by `seed_users.py`. Safe to re-run — skips existing users and updates roles.

---

## Authentication & Roles

### How login works

1. User submits credentials to `POST /api/login`
2. Backend validates with bcrypt and returns `{ token, username, role }`
3. Frontend stores `ns_token`, `ns_username`, and `ns_role` in `localStorage`
4. Axios attaches `Authorization: Bearer <token>` on every API request
5. On `401`, the client clears storage and redirects to `/login`

### Role behavior

| Capability | Doctor (`doctor1`, `doctor2`) | Admin |
|------------|-------------------------------|-------|
| Run predictions | Yes | Yes |
| Save predictions | Yes (tagged with `created_by`) | Yes |
| View prediction records | Own records only | All records |
| Model analytics / insights | Own data only | All data |
| User filter dropdown | Hidden | Visible (All Users / admin / doctor1 / doctor2) |
| Predictions per User table | Hidden | Visible |
| Patient history modal | Own predictions only | Scoped by filter |

### Admin user filter

On the **Model Analytics** page, admin sees a dropdown beside **Prediction Records**:

- **All Users** (default) — global view across all saved predictions
- **admin** / **doctor1** / **doctor2** — filters table, charts, advanced insights, pagination, and search to that user's records

Changing the dropdown refetches all analytics from the backend with `?user=<username>`.

### Security

- Doctors **cannot** bypass scope by passing `?user=other_doctor` — the backend ignores the parameter for non-admin roles
- Read endpoints (`/predictions`, `/advanced-metrics`, `/patient/:id`, etc.) require a valid JWT
- Save endpoints require authentication so every record has a `created_by` value

---

## Application Pages

| Route | Page | Description |
|-------|------|-------------|
| `/login` | Login | JWT sign-in |
| `/` | Dashboard | Production model card, ROC-AUC leaderboard, quick actions |
| `/predict` | Patient Analysis | Single-patient form, 7-model inference, risk gauge, save & PDF |
| `/batch` | Batch Prediction | CSV/Excel upload, batch inference, Excel download, save |
| `/analytics` | Model Analytics | Advanced insights, prediction records table, admin user filter |
| `/model-performance` | Model Performance | Charts and confusion matrices from training metrics |
| `/about` | About | Platform overview, model descriptions, design decisions |

---

## Database Schema

SQLite database: `backend/instance/stroke_predictions.db` (created automatically on first run).

| Table | Purpose |
|-------|---------|
| `users` | Authentication (`username`, `password_hash`, `role`) |
| `patients` | One profile row per unique `patient_id` |
| `patient_predictions` | Individual saved predictions (`created_by` = username) |
| `batch_predictions` | Batch saved predictions (`created_by`, `batch_id`) |
| `prediction_history` | Append-only audit log per assessment |

### `created_by` field

Every saved prediction (single and batch) stores the username of the logged-in user who created it. This field drives all role-based filtering.

### Migration

Run once after pulling updates or on a fresh install:

```bash
cd backend
python migrate.py
```

Adds `users` table, `created_by` columns, `role` column, and `prediction_history` if missing. Does not delete existing data.

---

## API Reference

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/login` | No | Login → `{ token, username, role }` |
| GET | `/api/me` | JWT | Current user profile |

### Dashboard & Model Metrics (static training data)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/dashboard` | No | Production model + leaderboard |
| GET | `/api/metrics` | No | Full metrics for all 7 models |
| GET | `/api/model-performance` | No | Same as `/api/metrics` |
| GET | `/api/download-metrics` | No | Download metrics CSV |

### Prediction (inference — no DB write)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/predict` | No | Single-patient prediction (all 7 models) |
| POST | `/api/batch-predict` | No | Batch prediction from file upload |
| POST | `/api/batch-download` | No | Download batch results as Excel |
| GET | `/api/sample-template` | No | Download sample Excel template |
| POST | `/api/download-stroke-pdf` | No | Generate stroke risk PDF report |

### Save & Records (scoped by role)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/save-prediction` | JWT | Save single prediction to DB |
| POST | `/api/save-batch-predictions` | JWT | Save batch results to DB |
| GET | `/api/predictions` | JWT | Paginated records. Admin: `?user=doctor1` |
| GET | `/api/advanced-metrics` | JWT | Analytics from DB. Admin: `?user=` filter |
| GET | `/api/analytics-metrics` | JWT | Stroke counts + per-model CM metrics |
| GET | `/api/user-stats` | JWT | Per-user prediction counts |

### Patients

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/check-patient` | No | Check if patient ID exists |
| GET | `/api/patient/<id>` | JWT | Patient profile + scoped history |
| GET | `/api/generate-patient-id` | No | Generate next `STR<year><seq>` ID |

### Query parameters for scoped endpoints

| Param | Used by | Description |
|-------|---------|-------------|
| `page` | `/api/predictions` | Page number (default: 1) |
| `per_page` | `/api/predictions` | Records per page (default: 20) |
| `search` | `/api/predictions` | Search patient ID, gender, smoking, username |
| `prediction` | `/api/predictions` | Filter: `Stroke` or `No Stroke` |
| `user` | Scoped endpoints | Admin only: filter by username |

---

## ML Pipeline

### Models

| Model | Role |
|-------|------|
| Logistic Regression | Baseline |
| Decision Tree | Interpretable tree |
| Random Forest | Bagged ensemble |
| Random Forest + SMOTE | Imbalance-handled forest |
| XGBoost | Gradient boosting |
| CatBoost | Categorical boosting |
| **LightGBM** | **Production model** |

### Input features

`id`, `gender`, `age`, `hypertension`, `heart_disease`, `ever_married`, `work_type`, `Residence_type`, `avg_glucose_level`, `bmi`, `smoking_status`

### Classification threshold

**10% probability** — optimized for recall/sensitivity on imbalanced stroke data.

### Risk levels

| Probability | Level |
|-------------|-------|
| &lt; 15% | Low |
| 15–39% | Moderate |
| 40–64% | High |
| ≥ 65% | Critical |

### Inference flow

```
Patient input → preprocess_input() → scaler / encoders → 7 models → LightGBM decision
                                                                    → explanations
                                                                    → JSON response
```

---

## Production Build

```bash
# Build frontend static assets
cd frontend
npm run build
# Output: frontend/dist/
```

To serve the built frontend from Flask in production, copy `frontend/dist/` into a static directory and configure Flask to serve `index.html`. Update `JWT_SECRET_KEY` and restrict CORS before deploying.

### Production checklist

- [ ] Change `JWT_SECRET_KEY` in `backend/app.py`
- [ ] Restrict CORS origins (currently `*` for local dev)
- [ ] Use a production WSGI server (e.g. Gunicorn) instead of `app.run(debug=True)`
- [ ] Back up `stroke_predictions.db` regularly
- [ ] Do not commit `.pkl` model files or database files to version control

---

## User Management

### Seed demo users

```bash
cd backend
python seed_users.py
```

### Create users interactively

```bash
cd backend
python create_users.py
```

### Programmatic user creation

Users are stored in the `users` table with bcrypt-hashed passwords. Set `role` to `'admin'` or `'doctor'` (default: `'doctor'`).

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **10% threshold** | Maximizes recall for clinical safety on imbalanced data |
| **LightGBM as production** | Best recall/speed tradeoff among trained models |
| **SQLite** | Zero-config persistence for development and small deployments |
| **JWT auth** | Stateless API authentication with role-based scoping |
| **`created_by` on every record** | Enables per-doctor data isolation without complex ACL tables |
| **Server-side filtering** | Doctors cannot access other users' data even via direct API calls |
| **Unified records view** | Single + batch predictions merged for analytics and the records table |
| **Static vs live metrics** | Dashboard/Model Performance use offline `metrics.pkl`; Analytics uses live DB data |

---

## Disclaimer

This platform is a **machine learning decision-support tool**. It is **not** a medical diagnosis system. Predictions should be reviewed by qualified healthcare professionals and must not replace clinical judgment.

---

## License

Private / educational use. Add a license file if distributing publicly.
