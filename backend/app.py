from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

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

# ─── Load Models ────────────────────────────────────────────────────────────

MODEL_DIR = "models"

lr        = joblib.load(f"{MODEL_DIR}/logistic_regression.pkl")
dt        = joblib.load(f"{MODEL_DIR}/decision_tree.pkl")
rf        = joblib.load(f"{MODEL_DIR}/random_forest.pkl")
rf_smote  = joblib.load(f"{MODEL_DIR}/random_forest_smote.pkl")
xgb       = joblib.load(f"{MODEL_DIR}/xgboost.pkl")
cat       = joblib.load(f"{MODEL_DIR}/catboost.pkl")
lgb       = joblib.load(f"{MODEL_DIR}/lightGBM_model.pkl")

scaler          = joblib.load(f"{MODEL_DIR}/scaler.pkl")
bmi_median      = joblib.load(f"{MODEL_DIR}/bmi_median.pkl")
le_married      = joblib.load(f"{MODEL_DIR}/le_married.pkl")
le_residence    = joblib.load(f"{MODEL_DIR}/le_residence.pkl")
feature_columns = joblib.load(f"{MODEL_DIR}/feature_columns.pkl")
metrics         = joblib.load(f"{MODEL_DIR}/metrics.pkl")

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


THRESHOLD = 0.10

def get_risk_level(prob):
    if prob < 15:
        return "Low"
    elif prob < 40:
        return "Moderate"
    elif prob < 65:
        return "High"
    else:
        return "Critical"

# ─── API: Dashboard Stats ────────────────────────────────────────────────────

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    lgb_m = metrics["LightGBM"]
    leaderboard = []
    for name, m in metrics.items():
        leaderboard.append({
            "model": name,
            "accuracy": round(m["accuracy"] * 100, 2),
            "precision": round(m["precision"] * 100, 2),
            "recall": round(m["recall"] * 100, 2),
            "f1_score": round(m["f1_score"] * 100, 2),
            "roc_auc": round(m["roc_auc"] * 100, 2),
            "is_production": name == "LightGBM"
        })
    leaderboard.sort(key=lambda x: x["roc_auc"], reverse=True)

    return jsonify({
        "production_model": {
            "name": "LightGBM",
            "accuracy": round(lgb_m["accuracy"] * 100, 2),
            "recall": round(lgb_m["recall"] * 100, 2),
            "roc_auc": round(lgb_m["roc_auc"] * 100, 2),
            "f1_score": round(lgb_m["f1_score"] * 100, 2),
        },
        "total_models": len(metrics),
        "leaderboard": leaderboard
    })

# ─── API: Model Metrics ──────────────────────────────────────────────────────

@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    result = []
    for name, m in metrics.items():
        result.append({
            "model": name,
            "accuracy":  round(m["accuracy"]  * 100, 2),
            "precision": round(m["precision"] * 100, 2),
            "recall":    round(m["recall"]    * 100, 2),
            "f1_score":  round(m["f1_score"]  * 100, 2),
            "roc_auc":   round(m["roc_auc"]   * 100, 2),
            "confusion_matrix": m["confusion_matrix"],
            "is_production": name == "LightGBM"
        })
    return jsonify(result)

# ─── API: Manual Predict ────────────────────────────────────────────────────

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

    df = preprocess_input(patient, bmi_median, le_married, le_residence, feature_columns)
    df_scaled = scaler.transform(df)

    probs = {
        "Logistic Regression":   float(lr.predict_proba(df_scaled)[:, 1][0]),
        "Decision Tree":         float(dt.predict_proba(df)[:, 1][0]),
        "Random Forest":         float(rf.predict_proba(df)[:, 1][0]),
        "Random Forest + SMOTE": float(rf_smote.predict_proba(df)[:, 1][0]),
        "XGBoost":               float(xgb.predict_proba(df)[:, 1][0]),
        "CatBoost":              float(cat.predict_proba(df)[:, 1][0]),
        "LightGBM":              float(lgb.predict_proba(df)[:, 1][0]),
    }

    lgb_prob = probs["LightGBM"]
    lgb_pct  = round(lgb_prob * 100, 2)
    final    = "Stroke" if lgb_prob > THRESHOLD else "No Stroke"
    risk     = get_risk_level(lgb_pct)
    explanation = generate_explanation(patient, final)

    model_results = [
        {
            "model":      name,
            "probability": round(p * 100, 2),
            "prediction": "Stroke" if p > THRESHOLD else "No Stroke",
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

    file = request.files["file"]
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
            proc = preprocess_input(patient, bmi_median, le_married, le_residence, feature_columns)
            prob = float(lgb.predict_proba(proc)[:, 1][0])
            pct  = round(prob * 100, 2)
            pred = "Stroke" if prob > THRESHOLD else "No Stroke"
            risk = get_risk_level(pct)
        except Exception as ex:
            pred, pct, risk = "Error", 0.0, "Unknown"

        results.append({
            **{k: row[k] for k in df_input.columns},
            "Prediction":   pred,
            "Probability":  pct,
            "Risk_Category": risk
        })

    stroke_count    = sum(1 for r in results if r["Prediction"] == "Stroke")
    no_stroke_count = sum(1 for r in results if r["Prediction"] == "No Stroke")
    avg_prob        = round(sum(r["Probability"] for r in results) / len(results), 2) if results else 0

    return jsonify({
        "total":          len(results),
        "stroke_count":   stroke_count,
        "no_stroke_count": no_stroke_count,
        "avg_probability": avg_prob,
        "results":        results
    })

# ─── API: Download Batch Results ────────────────────────────────────────────

@app.route("/api/batch-download", methods=["POST"])
def batch_download():
    data = request.get_json()
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

@app.route("/api/download-metrics")
def download_metrics():

    import pandas as pd

    rows = []

    for model_name, m in metrics.items():

        rows.append({
            "Model": model_name,
            "Accuracy (%)": round(m["accuracy"] * 100, 2),
            "Precision (%)": round(m["precision"] * 100, 2),
            "Recall (%)": round(m["recall"] * 100, 2),
            "F1 Score (%)": round(m["f1_score"] * 100, 2),
            "ROC-AUC (%)": round(m["roc_auc"] * 100, 2)
        })

    df = pd.DataFrame(rows)

    filename = "model_analytics.csv"

    df.to_csv(filename, index=False)

    return send_file(
        filename,
        as_attachment=True
    )

@app.route("/api/download-stroke-pdf", methods=["POST"])
def download_stroke_pdf():

    data = request.get_json()

    if not data:
        return jsonify({"error": "No input data received"}), 400

    # ─── Patient data (from frontend form) ─────────────────────────────
    patient = {
        "id": data.get("id", ""),
        "gender": data.get("gender", ""),
        "age": data.get("age", ""),
        "hypertension": data.get("hypertension", ""),
        "heart_disease": data.get("heart_disease", ""),
        "ever_married": data.get("ever_married", ""),
        "work_type": data.get("work_type", ""),
        "Residence_type": data.get("Residence_type", ""),
        "avg_glucose_level": data.get("avg_glucose_level", ""),
        "bmi": data.get("bmi", ""),
        "smoking_status": data.get("smoking_status", "")
    }

    # ─── Prediction results (from frontend) ────────────────────────────
    prediction = data.get("prediction", "Unknown")
    probability = data.get("probability", 0)
    risk_level = data.get("risk_level", "Unknown")
    explanation = data.get("explanation", [])

    # ─── Report text ───────────────────────────────────────────────────
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

    # ─── PDF generation ────────────────────────────────────────────────
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
