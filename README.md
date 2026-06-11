
# NeuralStroke — Clinical Risk Intelligence Platform

A production-quality stroke prediction SaaS built with React + Vite + Flask.
A machine learning-powered web application that predicts stroke risk using patient health attributes, built with Flask, LightGBM, and a modern frontend interface.

---

## Project Structure

```
stroke-platform/
├── backend/
│   ├── app.py                  # Flask API (all endpoints)
│   ├── requirements.txt
│   ├── models/                 # joblib model files go here
│   └── utils/
│       ├── predictor.py
│       └── explanation.py
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    ├── package.json
    └── src/
        ├── App.jsx
        ├── main.jsx
        ├── index.css
        ├── services/api.js
        ├── utils/helpers.js
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── Topbar.jsx
        │   ├── PageHeader.jsx
        │   ├── RiskGauge.jsx
        │   └── Spinner.jsx
        └── pages/
            ├── Dashboard.jsx
            ├── Predict.jsx
            ├── Batch.jsx
            ├── Analytics.jsx
            └── About.jsx
```

---

## Setup

### 1. Copy your model files

Place all `.pkl` model files into `backend/models/`:

```
models/
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

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
# Flask runs on http://localhost:5000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# React runs on http://localhost:3000
```

The Vite dev server proxies `/api/*` → `http://localhost:5000`.

---

## API Reference

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | /api/dashboard        | Dashboard stats + leaderboard        |
| GET    | /api/metrics          | Full model metrics for all 7 models  |
| POST   | /api/predict          | Manual single-patient prediction     |
| POST   | /api/batch-predict    | Batch prediction (file upload)       |
| POST   | /api/batch-download   | Download batch results as Excel      |
| GET    | /api/sample-template  | Download sample Excel template       |

---

## Production Build

```bash
# Build frontend
cd frontend && npm run build

# Serve static files from Flask (optional)
# Copy frontend/dist → backend/static
# Update Flask to serve index.html from static
```

---

## Key Design Decisions

- **10% threshold**: Maximizes recall/sensitivity for clinical safety
- **LightGBM**: Selected as production model for highest recall (69.4%) on imbalanced data
- **CORS**: Enabled on Flask for local dev; disable/restrict in production
- **No auth**: Add JWT/session auth before deploying to production
