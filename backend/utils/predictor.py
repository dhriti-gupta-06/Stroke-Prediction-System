import pandas as pd


def preprocess_input(
    patient,
    bmi_median,
    le_married,
    le_residence,
    feature_columns
):
    # Convert single input dict → DataFrame
    df = pd.DataFrame([patient])

    # -----------------------------
    # 1. Handle missing BMI safely
    # -----------------------------
    df["bmi"] = df["bmi"].fillna(bmi_median)

    # -----------------------------
    # 2. Safe Label Encoding (ever_married)
    # -----------------------------
    df["ever_married"] = df["ever_married"].apply(
        lambda x: x if x in le_married.classes_ else le_married.classes_[0]
    )
    df["ever_married"] = le_married.transform(df["ever_married"])

    # -----------------------------
    # 3. Safe Label Encoding (Residence_type)
    # -----------------------------
    df["Residence_type"] = df["Residence_type"].apply(
        lambda x: x if x in le_residence.classes_ else le_residence.classes_[0]
    )
    df["Residence_type"] = le_residence.transform(df["Residence_type"])

    # -----------------------------
    # 4. One-hot encoding for categorical features
    # -----------------------------
    df = pd.get_dummies(
        df,
        columns=[
            "gender",
            "work_type",
            "smoking_status"
        ]
    )

    # -----------------------------
    # 5. Align with training columns
    # -----------------------------
    df = df.reindex(columns=feature_columns, fill_value=0)

    return df