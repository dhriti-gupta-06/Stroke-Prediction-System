# database.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo   

db = SQLAlchemy()


def to_ist(dt):
    if not dt:
        return None
    return (
        dt.replace(tzinfo=ZoneInfo("UTC"))
        .astimezone(ZoneInfo("Asia/Kolkata"))
        .strftime("%Y-%m-%d %H:%M:%S")
    )


class PatientPrediction(db.Model):
    __tablename__ = 'patient_predictions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    age = db.Column(db.Float)
    hypertension = db.Column(db.Integer)
    heart_disease = db.Column(db.Integer)
    ever_married = db.Column(db.String(10))
    work_type = db.Column(db.String(50))
    residence_type = db.Column(db.String(20))
    avg_glucose_level = db.Column(db.Float)
    bmi = db.Column(db.Float)
    smoking_status = db.Column(db.String(30))

    final_prediction = db.Column(db.String(20))
    probability = db.Column(db.Float)
    risk_level = db.Column(db.String(20))

    pred_logistic_regression = db.Column(db.String(20))
    pred_decision_tree = db.Column(db.String(20))
    pred_random_forest = db.Column(db.String(20))
    pred_random_forest_smote = db.Column(db.String(20))
    pred_xgboost = db.Column(db.String(20))
    pred_catboost = db.Column(db.String(20))
    pred_lightgbm = db.Column(db.String(20))

    prob_logistic_regression = db.Column(db.Float)
    prob_decision_tree = db.Column(db.Float)
    prob_random_forest = db.Column(db.Float)
    prob_random_forest_smote = db.Column(db.Float)
    prob_xgboost = db.Column(db.Float)
    prob_catboost = db.Column(db.Float)
    prob_lightgbm = db.Column(db.Float)

    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'gender': self.gender,
            'age': self.age,
            'hypertension': self.hypertension,
            'heart_disease': self.heart_disease,
            'ever_married': self.ever_married,
            'work_type': self.work_type,
            'residence_type': self.residence_type,
            'avg_glucose_level': self.avg_glucose_level,
            'bmi': self.bmi,
            'smoking_status': self.smoking_status,

            'final_prediction': self.final_prediction,
            'probability': self.probability,
            'risk_level': self.risk_level,

            'pred_logistic_regression': self.pred_logistic_regression,
            'pred_decision_tree': self.pred_decision_tree,
            'pred_random_forest': self.pred_random_forest,
            'pred_random_forest_smote': self.pred_random_forest_smote,
            'pred_xgboost': self.pred_xgboost,
            'pred_catboost': self.pred_catboost,
            'pred_lightgbm': self.pred_lightgbm,

            # IST timestamp
            'timestamp': to_ist(self.timestamp)
        }


class BatchPrediction(db.Model):
    __tablename__ = 'batch_predictions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.String(50))
    patient_id = db.Column(db.String(50))
    gender = db.Column(db.String(20))
    age = db.Column(db.Float)
    hypertension = db.Column(db.Integer)
    heart_disease = db.Column(db.Integer)
    ever_married = db.Column(db.String(10))
    work_type = db.Column(db.String(50))
    residence_type = db.Column(db.String(20))
    avg_glucose_level = db.Column(db.Float)
    bmi = db.Column(db.Float)
    smoking_status = db.Column(db.String(30))

    final_prediction = db.Column(db.String(20))
    probability = db.Column(db.Float)
    risk_level = db.Column(db.String(20))

    pred_logistic_regression = db.Column(db.String(20))
    pred_decision_tree = db.Column(db.String(20))
    pred_random_forest = db.Column(db.String(20))
    pred_random_forest_smote = db.Column(db.String(20))
    pred_xgboost = db.Column(db.String(20))
    pred_catboost = db.Column(db.String(20))
    pred_lightgbm = db.Column(db.String(20))

    upload_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    record_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'batch_id': self.batch_id,
            'patient_id': self.patient_id,
            'gender': self.gender,
            'age': self.age,
            'hypertension': self.hypertension,
            'heart_disease': self.heart_disease,
            'ever_married': self.ever_married,
            'work_type': self.work_type,
            'residence_type': self.residence_type,
            'avg_glucose_level': self.avg_glucose_level,
            'bmi': self.bmi,
            'smoking_status': self.smoking_status,

            'final_prediction': self.final_prediction,
            'probability': self.probability,
            'risk_level': self.risk_level,

            'pred_logistic_regression': self.pred_logistic_regression,
            'pred_decision_tree': self.pred_decision_tree,
            'pred_random_forest': self.pred_random_forest,
            'pred_random_forest_smote': self.pred_random_forest_smote,
            'pred_xgboost': self.pred_xgboost,
            'pred_catboost': self.pred_catboost,
            'pred_lightgbm': self.pred_lightgbm,

            #  IST timestamps
            'upload_timestamp': to_ist(self.upload_timestamp),
            'record_timestamp': to_ist(self.record_timestamp),
        }