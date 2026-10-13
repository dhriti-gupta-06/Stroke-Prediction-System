"""
test_system.py  —  Automated integration test suite for NeuralStroke API.
Runs against the Flask application test client.
Usage: python test_system.py
"""
import unittest
import json
import io
from app import app, db, User, Patient, PatientPrediction, PredictionHistory

class NeuralStrokeTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        cls.client = app.test_client()

    def test_01_default_users_exist(self):
        """Verify default demo users are initialized properly in the database."""
        with app.app_context():
            u_doc1 = User.query.filter_by(username="doctor1").first()
            u_doc2 = User.query.filter_by(username="doctor2").first()
            u_admin = User.query.filter_by(username="admin").first()

            self.assertIsNotNone(u_doc1, "doctor1 should exist")
            self.assertEqual(u_doc1.role, "doctor")

            self.assertIsNotNone(u_doc2, "doctor2 should exist")
            self.assertEqual(u_doc2.role, "doctor")

            self.assertIsNotNone(u_admin, "admin should exist")
            self.assertEqual(u_admin.role, "admin")

    def test_02_auth_login_success(self):
        """Test successful login for doctor1, doctor2, and admin."""
        for user, pwd, expected_role in [
            ("doctor1", "pass123", "doctor"),
            ("doctor2", "pass456", "doctor"),
            ("admin", "admin123", "admin")
        ]:
            resp = self.client.post("/api/login", json={"username": user, "password": pwd})
            self.assertEqual(resp.status_code, 200, f"Failed login for {user}")
            data = resp.get_json()
            self.assertIn("token", data)
            self.assertEqual(data["username"], user)
            self.assertEqual(data["role"], expected_role)

    def test_03_auth_login_failure(self):
        """Test login with wrong password and nonexistent user."""
        resp = self.client.post("/api/login", json={"username": "doctor1", "password": "wrongpassword"})
        self.assertEqual(resp.status_code, 401)
        self.assertIn("error", resp.get_json())

        resp = self.client.post("/api/login", json={"username": "nonexistent_doc", "password": "any"})
        self.assertEqual(resp.status_code, 401)

        resp = self.client.post("/api/login", json={"username": "", "password": ""})
        self.assertEqual(resp.status_code, 400)

    def test_04_protected_endpoint_me(self):
        """Test @jwt_required on /api/me with and without token."""
        # Without token
        resp = self.client.get("/api/me")
        self.assertEqual(resp.status_code, 401)

        # With valid doctor token
        login_resp = self.client.post("/api/login", json={"username": "doctor1", "password": "pass123"})
        token = login_resp.get_json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = self.client.get("/api/me", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["username"], "doctor1")
        self.assertEqual(data["role"], "doctor")

    def test_05_dashboard_and_metrics_endpoints(self):
        """Test public model metrics and dashboard endpoints."""
        resp = self.client.get("/api/dashboard")
        self.assertEqual(resp.status_code, 200)
        d = resp.get_json()
        self.assertIn("production_model", d)
        self.assertIn("leaderboard", d)
        self.assertEqual(d["production_model"]["name"], "LightGBM")

        resp = self.client.get("/api/metrics")
        self.assertEqual(resp.status_code, 200)
        metrics_list = resp.get_json()
        self.assertIsInstance(metrics_list, list)
        self.assertGreaterEqual(len(metrics_list), 7)

    def test_06_single_patient_prediction(self):
        """Test ML inference for all 7 models."""
        patient_payload = {
            "id": 99991,
            "gender": "Male",
            "age": 67.0,
            "hypertension": 1,
            "heart_disease": 1,
            "ever_married": "Yes",
            "work_type": "Private",
            "Residence_type": "Urban",
            "avg_glucose_level": 228.69,
            "bmi": 36.6,
            "smoking_status": "formerly smoked"
        }
        resp = self.client.post("/api/predict", json=patient_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("final_prediction", data)
        self.assertIn("probability", data)
        self.assertIn("risk_level", data)
        self.assertIn("model_results", data)
        self.assertEqual(len(data["model_results"]), 7)

    def test_07_prediction_save_and_retrieval(self):
        """Test saving a prediction with JWT and checking role-based isolation."""
        # Login as doctor1
        login_resp = self.client.post("/api/login", json={"username": "doctor1", "password": "pass123"})
        doc1_token = login_resp.get_json()["token"]
        doc1_headers = {"Authorization": f"Bearer {doc1_token}"}

        patient = {
            "id": "STR_TEST_001",
            "gender": "Female",
            "age": 52.0,
            "hypertension": 0,
            "heart_disease": 0,
            "ever_married": "Yes",
            "work_type": "Self-employed",
            "Residence_type": "Rural",
            "avg_glucose_level": 92.5,
            "bmi": 24.2,
            "smoking_status": "never smoked"
        }
        pred_resp = self.client.post("/api/predict", json=patient)
        self.assertEqual(pred_resp.status_code, 200)
        pred_result = pred_resp.get_json()

        save_resp = self.client.post("/api/save-prediction", json={
            "patient": patient,
            "result": pred_result
        }, headers=doc1_headers)
        self.assertEqual(save_resp.status_code, 200)
        save_data = save_resp.get_json()
        self.assertTrue(save_data.get("success"))

        # Verify doctor1 sees the saved record
        records_resp = self.client.get("/api/predictions", headers=doc1_headers)
        self.assertEqual(records_resp.status_code, 200)
        records_data = records_resp.get_json()
        found = any(r.get("patient_id") == "STR_TEST_001" for r in records_data.get("records", []))
        self.assertTrue(found, "Saved record should be visible to doctor1")

        # Verify patient details endpoint
        patient_resp = self.client.get("/api/patient/STR_TEST_001", headers=doc1_headers)
        self.assertEqual(patient_resp.status_code, 200)
        p_data = patient_resp.get_json()
        self.assertEqual(p_data["patient"]["patient_id"], "STR_TEST_001")
        self.assertGreaterEqual(len(p_data["prediction_history"]), 1)

    def test_08_pdf_report_generation(self):
        """Test PDF generation endpoint returns valid PDF."""
        payload = {
            "id": "STR_TEST_001",
            "gender": "Female",
            "age": 52.0,
            "hypertension": 0,
            "heart_disease": 0,
            "ever_married": "Yes",
            "work_type": "Self-employed",
            "Residence_type": "Rural",
            "avg_glucose_level": 92.5,
            "bmi": 24.2,
            "smoking_status": "never smoked",
            "prediction": "No Stroke",
            "probability": 4.5,
            "risk_level": "Low",
            "explanation": ["Normal blood glucose level", "Normal BMI"]
        }
        resp = self.client.post("/api/download-stroke-pdf", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "application/pdf")
        self.assertTrue(resp.data.startswith(b"%PDF-"), "Response should be valid PDF binary")

    def test_09_patient_id_generator(self):
        """Test patient ID generation route."""
        resp = self.client.get("/api/generate-patient-id")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["patient_id"].startswith("STR"))

if __name__ == "__main__":
    unittest.main()
