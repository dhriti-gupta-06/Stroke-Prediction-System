from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
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

from database import db, PatientPrediction, BatchPrediction, Patient, PredictionHistory
db.init_app(app)

with app.app_context():
    db.create_all()

# ─── Load Models ────────────────────────────────────────────────────────────
MODEL_DIR = "models"

lr       = joblib.load(f"{MODEL_DIR}/logistic_regression.pkl")
dt       = joblib.load(f"{MODEL_DIR}/decision_tree.pkl")
rf       = joblib.load(f"{MODEL_DIR}/random_forest.pkl")
rf_smote = joblib.load(f"{MODEL_DIR}/random_forest_smote.pkl")
xgb_m    = joblib.load(f"{MODEL_DIR}/xgboost.pkl")
cat      = joblib.load(f"{MODEL_DIR}/catboost.pkl")
lgb      = joblib.load(f"{MODEL_DIR}/lightGBM_model.pkl")

scaler          = joblib.load(f"{MODEL_DIR}/scaler.pkl")
bmi_median      = joblib.load(f"{MODEL_DIR}/bmi_median.pkl")
le_married      = joblib.load(f"{MODEL_DIR}/le_married.pkl")
le_residence    = joblib.load(f"{MODEL_DIR}/le_residence.pkl")
feature_columns = joblib.load(f"{MODEL_DIR}/feature_columns.pkl")
metrics         = joblib.load(f"{MODEL_DIR}/metrics.pkl")

THRESHOLD = 0.10

MODEL_NAMES = [
    "Logistic Regression", "Decision Tree", "Random Forest",
    "Random Forest + SMOTE", "XGBoost", "CatBoost", "LightGBM"
]

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_risk_level(prob):
    if prob < 15:   return "Low"
    elif prob < 40: return "Moderate"
    elif prob < 65: return "High"
    else:           return "Critical"


def run_all_models(patient):
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


def generate_patient_id():
    """
    Generate next sequential Patient ID in format STR<YEAR><SEQUENCE4>.
    e.g. STR20260001, STR20260002 …
    Thread-safe within a single SQLite process (SQLAlchemy session lock).
    """
    year   = datetime.datetime.utcnow().year
    prefix = f"STR{year}"
    # Find the highest existing sequence for this year
    last = (Patient.query
            .filter(Patient.patient_id.like(f"{prefix}%"))
            .order_by(Patient.patient_id.desc())
            .first())
    if last:
        try:
            seq = int(last.patient_id[len(prefix):]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _upsert_patient_profile(pid, patient_data):
    """Create or update a Patient profile row. Returns the Patient object."""
    existing = Patient.query.filter_by(patient_id=pid).first()
    fields = dict(
        gender            = patient_data.get("gender"),
        age               = float(patient_data.get("age", 0) or 0),
        hypertension      = int(patient_data.get("hypertension", 0) or 0),
        heart_disease     = int(patient_data.get("heart_disease", 0) or 0),
        ever_married      = patient_data.get("ever_married"),
        work_type         = patient_data.get("work_type"),
        residence_type    = patient_data.get("Residence_type") or patient_data.get("residence_type"),
        avg_glucose_level = float(patient_data.get("avg_glucose_level", 0) or 0),
        bmi               = float(patient_data.get("bmi", 0) or 0),
        smoking_status    = patient_data.get("smoking_status"),
    )
    if existing:
        for k, v in fields.items():
            setattr(existing, k, v)
        return existing
    else:
        p = Patient(patient_id=pid, **fields)
        db.session.add(p)
        return p


def _unified_records():
    rows = []
    for r in PatientPrediction.query.all():
        rows.append({
            "source":    "single",
            "final":     r.final_prediction,
            "prob":      r.probability or 0,
            "lr":        r.pred_logistic_regression,
            "dt":        r.pred_decision_tree,
            "rf":        r.pred_random_forest,
            "rfs":       r.pred_random_forest_smote,
            "xgb":       r.pred_xgboost,
            "cat":       r.pred_catboost,
            "lgb":       r.pred_lightgbm,
            "prob_lr":   r.prob_logistic_regression  or 0,
            "prob_dt":   r.prob_decision_tree         or 0,
            "prob_rf":   r.prob_random_forest         or 0,
            "prob_rfs":  r.prob_random_forest_smote   or 0,
            "prob_xgb":  r.prob_xgboost               or 0,
            "prob_cat":  r.prob_catboost               or 0,
            "prob_lgb":  r.prob_lightgbm               or 0,
        })
    for r in BatchPrediction.query.all():
        rows.append({
            "source":    "batch",
            "final":     r.final_prediction,
            "prob":      r.probability or 0,
            "lr":        r.pred_logistic_regression,
            "dt":        r.pred_decision_tree,
            "rf":        r.pred_random_forest,
            "rfs":       r.pred_random_forest_smote,
            "xgb":       r.pred_xgboost,
            "cat":       r.pred_catboost,
            "lgb":       r.pred_lightgbm,
            "prob_lr":   0, "prob_dt":  0, "prob_rf":  0, "prob_rfs": 0,
            "prob_xgb":  0, "prob_cat": 0, "prob_lgb": 0,
        })
    return rows


def _compute_cm_metrics(preds, ground_truth):
    tp = sum(1 for p, g in zip(preds, ground_truth) if p == "Stroke"    and g == "Stroke")
    tn = sum(1 for p, g in zip(preds, ground_truth) if p == "No Stroke" and g == "No Stroke")
    fp = sum(1 for p, g in zip(preds, ground_truth) if p == "Stroke"    and g == "No Stroke")
    fn = sum(1 for p, g in zip(preds, ground_truth) if p == "No Stroke" and g == "Stroke")
    n  = len(preds)
    return (
        round((tp + tn) / n * 100, 2)             if n            else 0,
        round(tp / (tp + fp) * 100, 2)             if (tp + fp)    else 0,
        round(tp / (tp + fn) * 100, 2)             if (tp + fn)    else 0,
        round(2*tp / (2*tp + fp + fn) * 100, 2)    if (2*tp+fp+fn) else 0,
    )


# ─── API: Dashboard ──────────────────────────────────────────────────────────
@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    lgb_m = metrics["LightGBM"]
    leaderboard = []
    for name, m in metrics.items():
        leaderboard.append({
            "model":         name,
            "accuracy":      round(m["accuracy"]  * 100, 2),
            "precision":     round(m["precision"] * 100, 2),
            "recall":        round(m["recall"]    * 100, 2),
            "f1_score":      round(m["f1_score"]  * 100, 2),
            "roc_auc":       round(m["roc_auc"]   * 100, 2),
            "is_production": name == "LightGBM",
        })
    leaderboard.sort(key=lambda x: x["roc_auc"], reverse=True)
    return jsonify({
        "production_model": {
            "name":     "LightGBM",
            "accuracy": round(lgb_m["accuracy"] * 100, 2),
            "recall":   round(lgb_m["recall"]   * 100, 2),
            "roc_auc":  round(lgb_m["roc_auc"]  * 100, 2),
            "f1_score": round(lgb_m["f1_score"] * 100, 2),
        },
        "total_models": len(metrics),
        "leaderboard":  leaderboard,
    })


# ─── API: Model Metrics ──────────────────────────────────────────────────────
@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    result = []
    for name, m in metrics.items():
        result.append({
            "model":            name,
            "accuracy":         round(m["accuracy"]  * 100, 2),
            "precision":        round(m["precision"] * 100, 2),
            "recall":           round(m["recall"]    * 100, 2),
            "f1_score":         round(m["f1_score"]  * 100, 2),
            "roc_auc":          round(m["roc_auc"]   * 100, 2),
            "confusion_matrix": m["confusion_matrix"],
            "is_production":    name == "LightGBM",
        })
    return jsonify(result)


# ─── API: Analytics Metrics from DB ──────────────────────────────────────────
@app.route("/api/analytics-metrics", methods=["GET"])
def analytics_metrics():
    all_records = _unified_records()
    total       = len(all_records)
    empty_models = [{"model": n, "accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0} for n in MODEL_NAMES]
    if total == 0:
        return jsonify({"total": 0, "stroke": 0, "no_stroke": 0, "model_metrics": empty_models})

    stroke_count  = sum(1 for r in all_records if r["final"] == "Stroke")
    ground_truth  = [r["final"] for r in all_records]
    model_key_map = {
        "Logistic Regression":   "lr",  "Decision Tree":         "dt",
        "Random Forest":         "rf",  "Random Forest + SMOTE": "rfs",
        "XGBoost":               "xgb", "CatBoost":              "cat",
        "LightGBM":              "lgb",
    }
    model_metrics = []
    for name, key in model_key_map.items():
        valid = [(r[key], ground_truth[i]) for i, r in enumerate(all_records) if r[key] is not None]
        if not valid:
            model_metrics.append({"model": name, "accuracy": 0, "precision": 0, "recall": 0, "f1_score": 0})
            continue
        preds, gt = zip(*valid)
        acc, prec, rec, f1 = _compute_cm_metrics(list(preds), list(gt))
        model_metrics.append({"model": name, "accuracy": acc, "precision": prec, "recall": rec, "f1_score": f1})

    return jsonify({"total": total, "stroke": stroke_count, "no_stroke": total - stroke_count, "model_metrics": model_metrics})


# ─── API: Advanced Metrics ────────────────────────────────────────────────────
@app.route("/api/advanced-metrics", methods=["GET"])
def advanced_metrics():
    all_records   = _unified_records()
    total         = len(all_records)
    model_key_map = {
        "Logistic Regression":   ("lr",  "prob_lr"),
        "Decision Tree":         ("dt",  "prob_dt"),
        "Random Forest":         ("rf",  "prob_rf"),
        "Random Forest + SMOTE": ("rfs", "prob_rfs"),
        "XGBoost":               ("xgb", "prob_xgb"),
        "CatBoost":              ("cat", "prob_cat"),
        "LightGBM":              ("lgb", "prob_lgb"),
    }

    usage_frequency = []
    for name, (pred_key, _) in model_key_map.items():
        usage_frequency.append({"model": name, "count": sum(1 for r in all_records if r[pred_key] is not None)})

    avg_risk_per_model = []
    for name, (pred_key, prob_key) in model_key_map.items():
        probs = [r[prob_key] for r in all_records if r[pred_key] is not None and r[prob_key] > 0]
        if not probs:
            probs = [r["prob"] for r in all_records if r[pred_key] is not None]
        avg_risk_per_model.append({"model": name, "avg_probability": round(sum(probs)/len(probs), 2) if probs else 0})

    stroke_rate_per_model = []
    for name, (pred_key, _) in model_key_map.items():
        preds = [r[pred_key] for r in all_records if r[pred_key] is not None]
        stroke_rate_per_model.append({"model": name, "stroke_rate": round(sum(1 for p in preds if p == "Stroke")/len(preds)*100, 2) if preds else 0})

    bins, counts = ["0–20%","20–40%","40–60%","60–80%","80–100%"], [0,0,0,0,0]
    for r in all_records:
        p = r["prob"]
        idx = min(int(p // 20), 4)
        counts[idx] += 1
    confidence_distribution = [{"range": b, "count": c} for b, c in zip(bins, counts)]

    severity_breakdown = []
    for name, (pred_key, prob_key) in model_key_map.items():
        valid_probs = [r[prob_key] for r in all_records if r[pred_key] is not None and r[prob_key] > 0]
        if not valid_probs:
            valid_probs = [r["prob"] for r in all_records if r[pred_key] is not None]
        severity_breakdown.append({"model": name,
            "low":    sum(1 for p in valid_probs if p < 40),
            "medium": sum(1 for p in valid_probs if 40 <= p < 70),
            "high":   sum(1 for p in valid_probs if p >= 70)})

    single_records = [r for r in all_records if r["source"] == "single"]
    batch_records  = [r for r in all_records if r["source"] == "batch"]
    _ap = lambda recs: round(sum(r["prob"] for r in recs)/len(recs), 2) if recs else 0
    _sr = lambda recs: round(sum(1 for r in recs if r["final"]=="Stroke")/len(recs)*100, 2) if recs else 0

    return jsonify({
        "total":                    total,
        "usage_frequency":          usage_frequency,
        "avg_risk_per_model":       avg_risk_per_model,
        "stroke_rate_per_model":    stroke_rate_per_model,
        "confidence_distribution":  confidence_distribution,
        "severity_breakdown":       severity_breakdown,
        "batch_vs_single": {
            "single_count":       len(single_records),
            "batch_count":        len(batch_records),
            "single_avg_risk":    _ap(single_records),
            "batch_avg_risk":     _ap(batch_records),
            "single_stroke_rate": _sr(single_records),
            "batch_stroke_rate":  _sr(batch_records),
        },
    })


# ─── API: Individual Predict ─────────────────────────────────────────────────
@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    patient = {
        "id":                int(data["id"]) if data.get("id") else 0,
        "gender":            data["gender"],
        "age":               float(data["age"]),
        "hypertension":      int(data["hypertension"]),
        "heart_disease":     int(data["heart_disease"]),
        "ever_married":      data["ever_married"],
        "work_type":         data["work_type"],
        "Residence_type":    data["Residence_type"],
        "avg_glucose_level": float(data["avg_glucose_level"]),
        "bmi":               float(data["bmi"]) if data.get("bmi") else None,
        "smoking_status":    data["smoking_status"],
    }

    probs, _    = run_all_models(patient)
    lgb_prob    = probs["LightGBM"]
    lgb_pct     = round(lgb_prob * 100, 2)
    final       = "Stroke" if lgb_prob > THRESHOLD else "No Stroke"
    risk        = get_risk_level(lgb_pct)
    explanation = generate_explanation(patient, final)

    model_results = [
        {"model": name, "probability": round(p * 100, 2),
         "prediction": "Stroke" if p > THRESHOLD else "No Stroke",
         "is_production": name == "LightGBM"}
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

    required = ["id","gender","age","hypertension","heart_disease","ever_married",
                "work_type","Residence_type","avg_glucose_level","bmi","smoking_status"]
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
            model_preds = {
                "pred_logistic_regression":  "Stroke" if probs["Logistic Regression"]   > THRESHOLD else "No Stroke",
                "pred_decision_tree":        "Stroke" if probs["Decision Tree"]          > THRESHOLD else "No Stroke",
                "pred_random_forest":        "Stroke" if probs["Random Forest"]          > THRESHOLD else "No Stroke",
                "pred_random_forest_smote":  "Stroke" if probs["Random Forest + SMOTE"] > THRESHOLD else "No Stroke",
                "pred_xgboost":              "Stroke" if probs["XGBoost"]                > THRESHOLD else "No Stroke",
                "pred_catboost":             "Stroke" if probs["CatBoost"]               > THRESHOLD else "No Stroke",
                "pred_lightgbm":             "Stroke" if probs["LightGBM"]               > THRESHOLD else "No Stroke",
            }
        except Exception:
            pred, pct, risk, model_preds = "Error", 0.0, "Unknown", {}
        results.append({**{k: row[k] for k in df_input.columns}, "Prediction": pred,
                         "Probability": pct, "Risk_Category": risk, **model_preds})

    stroke_count    = sum(1 for r in results if r["Prediction"] == "Stroke")
    no_stroke_count = sum(1 for r in results if r["Prediction"] == "No Stroke")
    avg_prob        = round(sum(r["Probability"] for r in results) / len(results), 2) if results else 0
    return jsonify({"total": len(results), "stroke_count": stroke_count,
                    "no_stroke_count": no_stroke_count, "avg_probability": avg_prob, "results": results})


# ─── API: Save Individual Prediction (upsert + history) ──────────────────────
@app.route("/api/save-prediction", methods=["POST"])
def save_prediction():
    try:
        data    = request.get_json()
        patient = data.get("patient", {})
        result  = data.get("result",  {})
        models  = {m["model"]: m for m in result.get("model_results", [])}
        pid     = str(patient.get("id", "")).strip()

        def mp(name, key):
            return models.get(name, {}).get(key)

        # ── Upsert PatientPrediction (existing table, unchanged behaviour) ───
        existing = PatientPrediction.query.filter_by(patient_id=pid).first()
        fields = dict(
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
            timestamp                 = datetime.datetime.utcnow(),
        )
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            record = existing
        else:
            record = PatientPrediction(patient_id=pid, **fields)
            db.session.add(record)

        # ── Also write to Patient + PredictionHistory (new tables) ───────────
        _upsert_patient_profile(pid, patient)
        history = PredictionHistory(
            patient_id        = pid,
            prediction_result = result.get("final_prediction"),
            risk_score        = float(result.get("probability", 0) or 0),
            confidence_score  = result.get("risk_level"),
            model_used        = "LightGBM",
            prediction_source = "single",
        )
        db.session.add(history)

        db.session.commit()
        return jsonify({"success": True, "id": record.id, "patient_id": pid, "updated": existing is not None})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ─── API: Save Batch Predictions (upsert + history) ──────────────────────────
@app.route("/api/save-batch-predictions", methods=["POST"])
def save_batch_predictions():
    try:
        data     = request.get_json()
        results  = data.get("results", [])
        batch_id = str(uuid.uuid4())[:8].upper()
        now      = datetime.datetime.utcnow()

        saved = updated = 0
        for row in results:
            pid = str(row.get("id", "")).strip()
            fields = dict(
                batch_id          = batch_id,
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
                upload_timestamp  = now,
                record_timestamp  = now,
            )
            existing = BatchPrediction.query.filter_by(patient_id=pid).first()
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.session.add(BatchPrediction(patient_id=pid, **fields))
                saved += 1

            # Write to Patient + PredictionHistory
            _upsert_patient_profile(pid, {**row, "Residence_type": row.get("Residence_type") or row.get("residence_type")})
            db.session.add(PredictionHistory(
                patient_id        = pid,
                prediction_result = row.get("Prediction"),
                risk_score        = float(row.get("Probability", 0) or 0),
                confidence_score  = row.get("Risk_Category"),
                model_used        = "LightGBM",
                prediction_source = "batch",
            ))

        db.session.commit()
        return jsonify({"success": True, "batch_id": batch_id, "saved": saved, "updated": updated})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ─── API: Fetch Unified Prediction Records (paginated) ───────────────────────
@app.route("/api/predictions", methods=["GET"])
def get_predictions():
    page        = int(request.args.get("page", 1))
    per_page    = int(request.args.get("per_page", 20))
    search      = request.args.get("search", "").strip()
    filter_pred = request.args.get("prediction", "")

    q_single = PatientPrediction.query
    if search:
        q_single = q_single.filter(db.or_(
            PatientPrediction.patient_id.ilike(f"%{search}%"),
            PatientPrediction.gender.ilike(f"%{search}%"),
            PatientPrediction.smoking_status.ilike(f"%{search}%"),
        ))
    if filter_pred:
        q_single = q_single.filter(PatientPrediction.final_prediction == filter_pred)

    q_batch = BatchPrediction.query
    if search:
        q_batch = q_batch.filter(db.or_(
            BatchPrediction.patient_id.ilike(f"%{search}%"),
            BatchPrediction.gender.ilike(f"%{search}%"),
            BatchPrediction.smoking_status.ilike(f"%{search}%"),
        ))
    if filter_pred:
        q_batch = q_batch.filter(BatchPrediction.final_prediction == filter_pred)

    def single_to_dict(r):
        d = r.to_dict(); d["source"] = "single"; return d
    def batch_to_dict(r):
        d = r.to_dict()
        d["timestamp"] = d.get("record_timestamp") or d.get("upload_timestamp")
        d["source"]    = "batch"; return d

    all_rows = [single_to_dict(r) for r in q_single.all()] + [batch_to_dict(r) for r in q_batch.all()]
    all_rows.sort(key=lambda x: x.get("timestamp") or "", reverse=True)

    total = len(all_rows)
    start = (page - 1) * per_page
    return jsonify({
        "records":  all_rows[start: start + per_page],
        "total":    total, "page": page, "per_page": per_page,
        "pages":    max(1, (total + per_page - 1) // per_page),
    })


# ─── API: NEW — Check existing patient ───────────────────────────────────────
@app.route("/api/check-patient", methods=["POST"])
def check_patient():
    data = request.get_json()
    pid  = str(data.get("patient_id", "")).strip()
    if not pid:
        return jsonify({"exists": False})
    patient = Patient.query.filter_by(patient_id=pid).first()
    if not patient:
        return jsonify({"exists": False})
    return jsonify({"exists": True, "patient": patient.to_dict()})


# ─── API: NEW — Get patient details + full history ───────────────────────────
@app.route("/api/patient/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    patient = Patient.query.filter_by(patient_id=patient_id).first()

    # Also search PatientPrediction and BatchPrediction for the demographic data
    # (covers patients saved before the new Patient table existed)
    if not patient:
        pp = PatientPrediction.query.filter_by(patient_id=patient_id).first()
        bp = BatchPrediction.query.filter_by(patient_id=patient_id).first()
        source_row = pp or bp
        if not source_row:
            return jsonify({"error": "Patient not found"}), 404
        profile = {
            "patient_id":        source_row.patient_id,
            "gender":            source_row.gender,
            "age":               source_row.age,
            "hypertension":      source_row.hypertension,
            "heart_disease":     source_row.heart_disease,
            "ever_married":      source_row.ever_married,
            "work_type":         source_row.work_type,
            "residence_type":    source_row.residence_type,
            "avg_glucose_level": source_row.avg_glucose_level,
            "bmi":               source_row.bmi,
            "smoking_status":    source_row.smoking_status,
            "created_at":        None,
        }
    else:
        profile = patient.to_dict()

    # Gather all predictions from both legacy tables
    single_preds = PatientPrediction.query.filter_by(patient_id=patient_id).all()
    batch_preds  = BatchPrediction.query.filter_by(patient_id=patient_id).all()

    history = []
    for r in single_preds:
        d = r.to_dict()
        history.append({
            "date":       d.get("timestamp"),
            "model":      "LightGBM",
            "risk_score": d.get("probability"),
            "prediction": d.get("final_prediction"),
            "source":     "Single",
        })
    for r in batch_preds:
        d = r.to_dict()
        history.append({
            "date":       d.get("record_timestamp") or d.get("upload_timestamp"),
            "model":      "LightGBM",
            "risk_score": d.get("probability"),
            "prediction": d.get("final_prediction"),
            "source":     "Batch",
        })

    # Also include PredictionHistory entries (new table)
    ph_rows = PredictionHistory.query.filter_by(patient_id=patient_id).order_by(PredictionHistory.created_at.desc()).all()
    for r in ph_rows:
        d = r.to_dict()
        history.append({
            "date":       d.get("created_at"),
            "model":      d.get("model_used"),
            "risk_score": d.get("risk_score"),
            "prediction": d.get("prediction_result"),
            "source":     d.get("prediction_source", "").capitalize(),
        })

    # Deduplicate by (date, prediction) and sort newest first
    seen = set()
    unique_history = []
    for h in history:
        key = (h["date"], h["prediction"], h["risk_score"])
        if key not in seen:
            seen.add(key)
            unique_history.append(h)
    unique_history.sort(key=lambda x: x.get("date") or "", reverse=True)

    return jsonify({"patient": profile, "prediction_history": unique_history})


# ─── API: NEW — Generate patient ID ──────────────────────────────────────────
@app.route("/api/generate-patient-id", methods=["GET"])
def api_generate_patient_id():
    pid = generate_patient_id()
    return jsonify({"patient_id": pid})


# ─── API: Model Performance ──────────────────────────────────────────────────
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
    return send_file(output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name="stroke_predictions.xlsx")


# ─── API: Sample Template ───────────────────────────────────────────────────
@app.route("/api/sample-template", methods=["GET"])
def sample_template():
    sample = pd.DataFrame([{
        "id": 1001, "gender": "Male", "age": 67, "hypertension": 0, "heart_disease": 1,
        "ever_married": "Yes", "work_type": "Private", "Residence_type": "Urban",
        "avg_glucose_level": 228.69, "bmi": 36.6, "smoking_status": "formerly smoked",
    }, {
        "id": 1002, "gender": "Female", "age": 45, "hypertension": 0, "heart_disease": 0,
        "ever_married": "Yes", "work_type": "Self-employed", "Residence_type": "Rural",
        "avg_glucose_level": 87.19, "bmi": 28.4, "smoking_status": "never smoked",
    }])
    output = BytesIO()
    sample.to_excel(output, index=False)
    output.seek(0)
    return send_file(output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True, download_name="sample_template.xlsx")


# ─── API: Download Metrics CSV ──────────────────────────────────────────────
@app.route("/api/download-metrics")
def download_metrics():
    rows = [{"Model": n,
             "Accuracy (%)":  round(m["accuracy"]  * 100, 2),
             "Precision (%)": round(m["precision"] * 100, 2),
             "Recall (%)":    round(m["recall"]    * 100, 2),
             "F1 Score (%)":  round(m["f1_score"]  * 100, 2),
             "ROC-AUC (%)":   round(m["roc_auc"]   * 100, 2)}
            for n, m in metrics.items()]
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

    patient = {k: data.get(k, "") for k in
               ["id","gender","age","hypertension","heart_disease","ever_married",
                "work_type","Residence_type","avg_glucose_level","bmi","smoking_status"]}
    prediction  = data.get("prediction",  "Unknown")
    probability = data.get("probability", 0)
    risk_level  = data.get("risk_level",  "Unknown")
    explanation = data.get("explanation", [])

    # Fetch history for the patient (for PDF history section)
    history_lines = ""
    pid = str(data.get("id", "")).strip()
    if pid:
        ph_rows = PredictionHistory.query.filter_by(patient_id=pid).order_by(PredictionHistory.created_at.desc()).limit(10).all()
        if ph_rows:
            history_lines = "\n\nPrevious Predictions:\n"
            for h in ph_rows:
                d = h.to_dict()
                history_lines += f"  {d['created_at']}  |  {d['prediction_result']}  |  {d['risk_score']}%  |  {d['model_used']}\n"

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
{history_lines}
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
            p.showPage(); y = 750
        p.drawString(40, y, line[:120])
        y -= 15
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf",
                     as_attachment=True, download_name="stroke_risk_report.pdf")


if __name__ == "__main__":
    app.run(debug=True, port=5000)