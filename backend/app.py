from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import Response
import datetime
import uuid

import joblib
import pandas as pd
import numpy as np
from io import BytesIO
import os

from utils.predictor import preprocess_input
from utils.explanation import generate_explanation

app = Flask(__name__)
CORS(app)

# ─── Database ────────────────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stroke_predictions.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from database import db, PatientPrediction, BatchPrediction
db.init_app(app)

with app.app_context():
    db.create_all()

# ─── Load Models ────────────────────────────────────────────────────────────
MODEL_DIR = "models"

lr        = joblib.load(f"{MODEL_DIR}/logistic_regression.pkl")
dt        = joblib.load(f"{MODEL_DIR}/decision_tree.pkl")
rf        = joblib.load(f"{MODEL_DIR}/random_forest.pkl")
rf_smote  = joblib.load(f"{MODEL_DIR}/random_forest_smote.pkl")
xgb_m     = joblib.load(f"{MODEL_DIR}/xgboost.pkl")
cat       = joblib.load(f"{MODEL_DIR}/catboost.pkl")
lgb       = joblib.load(f"{MODEL_DIR}/lightGBM_model.pkl")

scaler          = joblib.load(f"{MODEL_DIR}/scaler.pkl")
bmi_median      = joblib.load(f"{MODEL_DIR}/bmi_median.pkl")
le_married      = joblib.load(f"{MODEL_DIR}/le_married.pkl")
le_residence    = joblib.load(f"{MODEL_DIR}/le_residence.pkl")
feature_columns = joblib.load(f"{MODEL_DIR}/feature_columns.pkl")
metrics         = joblib.load(f"{MODEL_DIR}/metrics.pkl")

THRESHOLD = 0.10

def get_risk_level(prob):
    if prob < 15:   return "Low"
    elif prob < 40: return "Moderate"
    elif prob < 65: return "High"
    else:           return "Critical"

def run_all_models(patient):
    """Run all 7 models on a preprocessed patient dict. Returns probs dict."""
    df = preprocess_input(patient, bmi_median, le_married, le_residence, feature_columns)
    df_scaled = scaler.transform(df)
    return {
        "Logistic Regression":   float(lr.predict_proba(df_scaled)[:, 1][0]),
        "Decision Tree":         float(dt.predict_proba(df)[:, 1][0]),
        "Random Forest":         float(rf.predict_proba(df)[:, 1][0]),
        "Random Forest + SMOTE": float(rf_smote.predict_proba(df)[:, 1][0]),
        "XGBoost":               float(xgb_m.predict_proba(df)[:, 1][0]),
        "CatBoost":              float(cat.predict_proba(df)[:, 1][0]),
        "LightGBM":              float(lgb.predict_proba(df)[:, 1][0]),
    }, df

def build_stroke_report(patient, probability, prediction, risk_level):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_id = str(uuid.uuid4())[:8]
    metrics_table = ""
    for model, m in metrics.items():
        metrics_table += f"""
{model}
Accuracy: {round(m['accuracy']*100,2)}%
Precision: {round(m['precision']*100,2)}%
Recall: {round(m['recall']*100,2)}%
F1 Score: {round(m['f1_score']*100,2)}%
ROC-AUC: {round(m['roc_auc']*100,2)}%
"""
    return f"""
STROKE RISK ASSESSMENT REPORT

1. Report Information
Report Time: {timestamp}
Report ID: {report_id}
Model Used: LightGBM (Production)
System: Stroke Risk Prediction System

---

2. Patient Input Details
Gender: {patient['gender']}
Age: {patient['age']}
Hypertension: {patient['hypertension']}
Heart Disease: {patient['heart_disease']}
Marital Status: {patient['ever_married']}
Work Type: {patient['work_type']}
Residence: {patient['Residence_type']}
Glucose: {patient['avg_glucose_level']}
BMI: {patient['bmi']}
Smoking: {patient['smoking_status']}

---

3. Prediction Outcome
Result: {prediction}
Risk Probability: {probability}%
Confidence Level: {risk_level}

This is a predictive result, not a medical diagnosis.

---

4. Key Risk Factors
Derived from input features.

---

5. Recommendations
- Maintain healthy lifestyle
- Monitor BP and sugar
- Exercise daily
- Avoid smoking

---

6. Model Information
Best Model: LightGBM

Models Evaluated:
Logistic Regression, Decision Tree, Random Forest,
Random Forest + SMOTE, XGBoost, CatBoost, LightGBM

Performance Metrics:
{metrics_table}

---

7. Disclaimer
This report is generated using machine learning and is not medical advice.
"""

# ─── API: Dashboard ──────────────────────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    lgb_m = metrics["LightGBM"]
    leaderboard = []
    for name, m in metrics.items():
        leaderboard.append({
            "model": name,
            "accuracy":  round(m["accuracy"]  * 100, 2),
            "precision": round(m["precision"] * 100, 2),
            "recall":    round(m["recall"]    * 100, 2),
            "f1_score":  round(m["f1_score"]  * 100, 2),
            "roc_auc":   round(m["roc_auc"]   * 100, 2),
            "is_production": name == "LightGBM"
        })
    leaderboard.sort(key=lambda x: x["roc_auc"], reverse=True)
    return jsonify({
        "production_model": {
            "name": "LightGBM",
            "accuracy": round(lgb_m["accuracy"] * 100, 2),
            "recall":   round(lgb_m["recall"]   * 100, 2),
            "roc_auc":  round(lgb_m["roc_auc"]  * 100, 2),
            "f1_score": round(lgb_m["f1_score"] * 100, 2),
        },
        "total_models": len(metrics),
        "leaderboard": leaderboard
    })

# ─── API: Model Metrics (static from training) ───────────────────────────────
@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    result = []
    for name, m in metrics.items():
        result.append({
            "model":      name,
            "accuracy":   round(m["accuracy"]  * 100, 2),
            "precision":  round(m["precision"] * 100, 2),
            "recall":     round(m["recall"]    * 100, 2),
            "f1_score":   round(m["f1_score"]  * 100, 2),
            "roc_auc":    round(m["roc_auc"]   * 100, 2),
            "confusion_matrix": m["confusion_matrix"],
            "is_production": name == "LightGBM"
        })
    return jsonify(result)

# ─── API: Analytics Metrics from DB ─────────────────────────────────────────
@app.route("/api/analytics-metrics", methods=["GET"])
def analytics_metrics():
    """
    Compute per-model accuracy/precision/recall/F1 from saved prediction records.
    Uses LightGBM final_prediction as ground truth proxy (since we have no
    actual clinical labels), and compares each model's stored prediction against it.
    Returns both DB-derived metrics AND total counts for the distribution chart.
    """
    records = PatientPrediction.query.all()
    batch   = BatchPrediction.query.all()

    all_records = []
    for r in records:
        all_records.append({
            'final': r.final_prediction,
            'lr':    r.pred_logistic_regression,
            'dt':    r.pred_decision_tree,
            'rf':    r.pred_random_forest,
            'rfs':   r.pred_random_forest_smote,
            'xgb':   r.pred_xgboost,
            'cat':   r.pred_catboost,
            'lgb':   r.pred_lightgbm,
        })
    for r in batch:
        all_records.append({
            'final': r.final_prediction,
            'lr':    r.pred_logistic_regression,
            'dt':    r.pred_decision_tree,
            'rf':    r.pred_random_forest,
            'rfs':   r.pred_random_forest_smote,
            'xgb':   r.pred_xgboost,
            'cat':   r.pred_catboost,
            'lgb':   r.pred_lightgbm,
        })

    total = len(all_records)

    if total == 0:
        # Return zeros — frontend will show empty state
        model_names = [
            "Logistic Regression", "Decision Tree", "Random Forest",
            "Random Forest + SMOTE", "XGBoost", "CatBoost", "LightGBM"
        ]
        return jsonify({
            "total": 0,
            "stroke": 0,
            "no_stroke": 0,
            "model_metrics": [
                {"model": n, "accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0}
                for n in model_names
            ]
        })

    stroke_count    = sum(1 for r in all_records if r['final'] == 'Stroke')
    no_stroke_count = total - stroke_count

    def compute_metrics(preds, ground_truth):
        """Compute accuracy, precision, recall, F1 against ground truth list."""
        tp = sum(1 for p, g in zip(preds, ground_truth) if p == 'Stroke'    and g == 'Stroke')
        tn = sum(1 for p, g in zip(preds, ground_truth) if p == 'No Stroke' and g == 'No Stroke')
        fp = sum(1 for p, g in zip(preds, ground_truth) if p == 'Stroke'    and g == 'No Stroke')
        fn = sum(1 for p, g in zip(preds, ground_truth) if p == 'No Stroke' and g == 'Stroke')

        n = len(preds)
        accuracy  = round((tp + tn) / n * 100, 2)          if n            else 0
        precision = round(tp / (tp + fp) * 100, 2)          if (tp + fp)    else 0
        recall    = round(tp / (tp + fn) * 100, 2)          if (tp + fn)    else 0
        f1        = round(2 * tp / (2*tp + fp + fn) * 100, 2) if (2*tp+fp+fn) else 0
        return accuracy, precision, recall, f1

    ground_truth = [r['final'] for r in all_records]

    model_keys = {
        "Logistic Regression":   'lr',
        "Decision Tree":         'dt',
        "Random Forest":         'rf',
        "Random Forest + SMOTE": 'rfs',
        "XGBoost":               'xgb',
        "CatBoost":              'cat',
        "LightGBM":              'lgb',
    }

    model_metrics = []
    for name, key in model_keys.items():
        preds = [r[key] for r in all_records if r[key] is not None]
        gt_filtered = [ground_truth[i] for i, r in enumerate(all_records) if r[key] is not None]
        if not preds:
            model_metrics.append({"model": name, "accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0})
            continue
        acc, prec, rec, f1 = compute_metrics(preds, gt_filtered)
        model_metrics.append({
            "model": name,
            "accuracy":  acc,
            "precision": prec,
            "recall":    rec,
            "f1_score":  f1,
        })

    return jsonify({
        "total":        total,
        "stroke":       stroke_count,
        "no_stroke":    no_stroke_count,
        "model_metrics": model_metrics,
    })

# ─── API: Individual Predict ─────────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    patient = {
        "id":                int(data["id"]),
        "gender":            data["gender"],
        "age":               float(data["age"]),
        "hypertension":      int(data["hypertension"]),
        "heart_disease":     int(data["heart_disease"]),
        "ever_married":      data["ever_married"],
        "work_type":         data["work_type"],
        "Residence_type":    data["Residence_type"],
        "avg_glucose_level": float(data["avg_glucose_level"]),
        "bmi":               float(data["bmi"]) if data.get("bmi") else None,
        "smoking_status":    data["smoking_status"]
    }

    probs, _ = run_all_models(patient)

    lgb_prob = probs["LightGBM"]
    lgb_pct  = round(lgb_prob * 100, 2)
    final    = "Stroke" if lgb_prob > THRESHOLD else "No Stroke"
    risk     = get_risk_level(lgb_pct)
    explanation = generate_explanation(patient, final)

    model_results = [
        {
            "model":         name,
            "probability":   round(p * 100, 2),
            "prediction":    "Stroke" if p > THRESHOLD else "No Stroke",
            "is_production": name == "LightGBM"
        }
        for name, p in probs.items()
    ]

    return jsonify({
        "patient_id":       patient["id"],
        "final_prediction": final,
        "probability":      lgb_pct,
        "risk_level":       risk,
        "explanation":      explanation,
        "model_results":    model_results,
    })

# ─── API: Batch Predict ──────────────────────────────────────────────────────
@app.route("/api/batch-predict", methods=["POST"])
def batch_predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file  = request.files["file"]
    fname = file.filename.lower()

    try:
        if fname.endswith(".csv"):
            df_input = pd.read_csv(file)
        elif fname.endswith((".xlsx", ".xls")):
            df_input = pd.read_excel(file)
        else:
            return jsonify({"error": "Only CSV or Excel files are supported"}), 400
    except Exception as e:
        return jsonify({"error": f"Could not read file: {str(e)}"}), 400

    required = ["id","gender","age","hypertension","heart_disease",
                "ever_married","work_type","Residence_type",
                "avg_glucose_level","bmi","smoking_status"]
    missing = [c for c in required if c not in df_input.columns]
    if missing:
        return jsonify({"error": f"Missing columns: {', '.join(missing)}"}), 400

    results = []
    for _, row in df_input.iterrows():
        patient = {
            "id":                int(row["id"]) if not pd.isna(row["id"]) else 0,
            "gender":            str(row["gender"]),
            "age":               float(row["age"]),
            "hypertension":      int(row["hypertension"]),
            "heart_disease":     int(row["heart_disease"]),
            "ever_married":      str(row["ever_married"]),
            "work_type":         str(row["work_type"]),
            "Residence_type":    str(row["Residence_type"]),
            "avg_glucose_level": float(row["avg_glucose_level"]),
            "bmi":               float(row["bmi"]) if not pd.isna(row.get("bmi", float("nan"))) else None,
            "smoking_status":    str(row["smoking_status"]),
        }
        try:
            probs, _ = run_all_models(patient)
            lgb_prob = probs["LightGBM"]
            pct      = round(lgb_prob * 100, 2)
            pred     = "Stroke" if lgb_prob > THRESHOLD else "No Stroke"
            risk     = get_risk_level(pct)

            # Per-model predictions for saving
            model_preds = {
                "pred_logistic_regression":  "Stroke" if probs["Logistic Regression"]   > THRESHOLD else "No Stroke",
                "pred_decision_tree":        "Stroke" if probs["Decision Tree"]          > THRESHOLD else "No Stroke",
                "pred_random_forest":        "Stroke" if probs["Random Forest"]          > THRESHOLD else "No Stroke",
                "pred_random_forest_smote":  "Stroke" if probs["Random Forest + SMOTE"] > THRESHOLD else "No Stroke",
                "pred_xgboost":              "Stroke" if probs["XGBoost"]                > THRESHOLD else "No Stroke",
                "pred_catboost":             "Stroke" if probs["CatBoost"]               > THRESHOLD else "No Stroke",
                "pred_lightgbm":             "Stroke" if probs["LightGBM"]               > THRESHOLD else "No Stroke",
            }
        except Exception as ex:
            pred, pct, risk = "Error", 0.0, "Unknown"
            model_preds = {}

        results.append({
            **{k: row[k] for k in df_input.columns},
            "Prediction":    pred,
            "Probability":   pct,
            "Risk_Category": risk,
            **model_preds          # ← included so Save Batch Data can persist them
        })

    stroke_count    = sum(1 for r in results if r["Prediction"] == "Stroke")
    no_stroke_count = sum(1 for r in results if r["Prediction"] == "No Stroke")
    avg_prob        = round(sum(r["Probability"] for r in results) / len(results), 2) if results else 0

    return jsonify({
        "total":           len(results),
        "stroke_count":    stroke_count,
        "no_stroke_count": no_stroke_count,
        "avg_probability": avg_prob,
        "results":         results
    })

# ─── API: Save Individual Prediction ────────────────────────────────────────
@app.route("/api/save-prediction", methods=["POST"])
def save_prediction():
    try:
        data    = request.get_json()
        patient = data.get("patient", {})
        result  = data.get("result",  {})
        models  = {m["model"]: m for m in result.get("model_results", [])}

        def mp(name, key):
            return models.get(name, {}).get(key)

        record = PatientPrediction(
            patient_id        = str(patient.get("id", "")),
            gender            = patient.get("gender"),
            age               = float(patient.get("age", 0) or 0),
            hypertension      = int(patient.get("hypertension", 0) or 0),
            heart_disease     = int(patient.get("heart_disease", 0) or 0),
            ever_married      = patient.get("ever_married"),
            work_type         = patient.get("work_type"),
            residence_type    = patient.get("Residence_type"),
            avg_glucose_level = float(patient.get("avg_glucose_level", 0) or 0),
            bmi               = float(patient.get("bmi", 0) or 0),
            smoking_status    = patient.get("smoking_status"),
            final_prediction  = result.get("final_prediction"),
            probability       = float(result.get("probability", 0) or 0),
            risk_level        = result.get("risk_level"),
            pred_logistic_regression  = mp("Logistic Regression",   "prediction"),
            pred_decision_tree        = mp("Decision Tree",          "prediction"),
            pred_random_forest        = mp("Random Forest",          "prediction"),
            pred_random_forest_smote  = mp("Random Forest + SMOTE", "prediction"),
            pred_xgboost              = mp("XGBoost",                "prediction"),
            pred_catboost             = mp("CatBoost",               "prediction"),
            pred_lightgbm             = mp("LightGBM",               "prediction"),
            prob_logistic_regression  = mp("Logistic Regression",   "probability"),
            prob_decision_tree        = mp("Decision Tree",          "probability"),
            prob_random_forest        = mp("Random Forest",          "probability"),
            prob_random_forest_smote  = mp("Random Forest + SMOTE", "probability"),
            prob_xgboost              = mp("XGBoost",                "probability"),
            prob_catboost             = mp("CatBoost",               "probability"),
            prob_lightgbm             = mp("LightGBM",               "probability"),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"success": True, "id": record.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ─── API: Save Batch Predictions ────────────────────────────────────────────
@app.route("/api/save-batch-predictions", methods=["POST"])
def save_batch_predictions():
    try:
        data     = request.get_json()
        results  = data.get("results", [])
        batch_id = str(uuid.uuid4())[:8].upper()

        for row in results:
            record = BatchPrediction(
                batch_id          = batch_id,
                patient_id        = str(row.get("id", "")),
                gender            = row.get("gender"),
                age               = float(row.get("age", 0) or 0),
                hypertension      = int(row.get("hypertension", 0) or 0),
                heart_disease     = int(row.get("heart_disease", 0) or 0),
                ever_married      = row.get("ever_married"),
                work_type         = row.get("work_type"),
                residence_type    = row.get("Residence_type") or row.get("residence_type"),
                avg_glucose_level = float(row.get("avg_glucose_level", 0) or 0),
                bmi               = float(row.get("bmi", 0) or 0),
                smoking_status    = row.get("smoking_status"),
                final_prediction  = row.get("Prediction"),
                probability       = float(row.get("Probability", 0) or 0),
                risk_level        = row.get("Risk_Category"),
                pred_logistic_regression  = row.get("pred_logistic_regression"),
                pred_decision_tree        = row.get("pred_decision_tree"),
                pred_random_forest        = row.get("pred_random_forest"),
                pred_random_forest_smote  = row.get("pred_random_forest_smote"),
                pred_xgboost              = row.get("pred_xgboost"),
                pred_catboost             = row.get("pred_catboost"),
                pred_lightgbm             = row.get("pred_lightgbm"),
            )
            db.session.add(record)

        db.session.commit()
        return jsonify({"success": True, "batch_id": batch_id, "saved": len(results)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ─── API: Fetch Prediction Records (paginated) ───────────────────────────────
@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    search   = request.args.get("search", "").strip()
    filter_pred = request.args.get("prediction", "")

    query = PatientPrediction.query
    if search:
        query = query.filter(
            db.or_(
                PatientPrediction.patient_id.ilike(f"%{search}%"),
                PatientPrediction.gender.ilike(f"%{search}%"),
                PatientPrediction.smoking_status.ilike(f"%{search}%"),
            )
        )
    if filter_pred:
        query = query.filter(PatientPrediction.final_prediction == filter_pred)

    total   = query.count()
    records = query.order_by(PatientPrediction.timestamp.desc()) \
                   .offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "records":  [r.to_dict() for r in records],
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    (total + per_page - 1) // per_page,
    })

# ─── API: Model Performance (same as metrics) ────────────────────────────────
@app.route("/api/model-performance", methods=["GET"])
def model_performance():
    return get_metrics()

# ─── API: Download Batch Results ────────────────────────────────────────────
@app.route("/api/batch-download", methods=["POST"])
def batch_download():
    data    = request.get_json()
    results = data.get("results", [])
    if not results:
        return jsonify({"error": "No results to download"}), 400
    df = pd.DataFrame(results)
    output = BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="stroke_predictions.xlsx"
    )

# ─── API: Sample Template ───────────────────────────────────────────────────
@app.route("/api/sample-template", methods=["GET"])
def sample_template():
    sample = pd.DataFrame([{
        "id": 1001, "gender": "Male", "age": 67, "hypertension": 0,
        "heart_disease": 1, "ever_married": "Yes", "work_type": "Private",
        "Residence_type": "Urban", "avg_glucose_level": 228.69,
        "bmi": 36.6, "smoking_status": "formerly smoked"
    }, {
        "id": 1002, "gender": "Female", "age": 45, "hypertension": 0,
        "heart_disease": 0, "ever_married": "Yes", "work_type": "Self-employed",
        "Residence_type": "Rural", "avg_glucose_level": 87.19,
        "bmi": 28.4, "smoking_status": "never smoked"
    }])
    output = BytesIO()
    sample.to_excel(output, index=False)
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="sample_template.xlsx"
    )

# ─── API: Download Metrics CSV ──────────────────────────────────────────────
@app.route("/api/download-metrics")
def download_metrics():
    rows = []
    for model_name, m in metrics.items():
        rows.append({
            "Model":          model_name,
            "Accuracy (%)":   round(m["accuracy"]  * 100, 2),
            "Precision (%)":  round(m["precision"] * 100, 2),
            "Recall (%)":     round(m["recall"]    * 100, 2),
            "F1 Score (%)":   round(m["f1_score"]  * 100, 2),
            "ROC-AUC (%)":    round(m["roc_auc"]   * 100, 2),
        })
    df = pd.DataFrame(rows)
    filename = "model_analytics.csv"
    df.to_csv(filename, index=False)
    return send_file(filename, as_attachment=True)

# ─── API: Download Stroke PDF ────────────────────────────────────────────────
@app.route("/api/download-stroke-pdf", methods=["POST"])
def download_stroke_pdf():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data received"}), 400

    patient = {
        "id":                data.get("id", ""),
        "gender":            data.get("gender", ""),
        "age":               data.get("age", ""),
        "hypertension":      data.get("hypertension", ""),
        "heart_disease":     data.get("heart_disease", ""),
        "ever_married":      data.get("ever_married", ""),
        "work_type":         data.get("work_type", ""),
        "Residence_type":    data.get("Residence_type", ""),
        "avg_glucose_level": data.get("avg_glucose_level", ""),
        "bmi":               data.get("bmi", ""),
        "smoking_status":    data.get("smoking_status", ""),
    }
    prediction  = data.get("prediction",  "Unknown")
    probability = data.get("probability", 0)
    risk_level  = data.get("risk_level",  "Unknown")
    explanation = data.get("explanation", [])

    report_text = f"""
STROKE RISK REPORT

-------------------------------------------------
PATIENT INFORMATION
-------------------------------------------------
ID: {patient['id']}
Gender: {patient['gender']}
Age: {patient['age']}
Hypertension: {patient['hypertension']}
Heart Disease: {patient['heart_disease']}
Ever Married: {patient['ever_married']}
Work Type: {patient['work_type']}
Residence Type: {patient['Residence_type']}
Avg Glucose Level: {patient['avg_glucose_level']}
BMI: {patient['bmi']}
Smoking Status: {patient['smoking_status']}

-------------------------------------------------
PREDICTION RESULT
-------------------------------------------------
Final Prediction: {prediction}
Probability: {probability}%
Risk Level: {risk_level}

-------------------------------------------------
KEY RISK FACTORS
-------------------------------------------------
{chr(10).join(explanation) if explanation else "No explanation available"}

-------------------------------------------------
DISCLAIMER
-------------------------------------------------
This report is generated using a machine learning model.
It is NOT a medical diagnosis.
"""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    y = 750
    for line in report_text.split("\n"):
        if y < 50:
            p.showPage()
            y = 750
        p.drawString(40, y, line[:120])
        y -= 15
    p.save()
    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="stroke_risk_report.pdf"
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)