def generate_explanation(patient, prediction):

    reasons = []

    if patient["age"] >= 60:
        reasons.append("Advanced age is a significant stroke risk factor.")

    if patient["hypertension"] == 1:
        reasons.append("Patient has hypertension.")

    if patient["heart_disease"] == 1:
        reasons.append("Patient has heart disease.")

    if patient["avg_glucose_level"] > 140:
        reasons.append("Elevated glucose level detected.")

    if patient["bmi"] > 30:
        reasons.append("BMI indicates obesity.")

    if patient["smoking_status"] in ["smokes", "formerly smoked"]:
        reasons.append("Smoking history contributes to stroke risk.")

    if len(reasons) == 0:

        if prediction == "Stroke":
            reasons.append(
                "The machine learning model predicts stroke risk based on combined feature patterns learned during training."
            )
        else:
            reasons.append(
                "No major stroke risk factors were detected from the provided information."
            )

    return reasons