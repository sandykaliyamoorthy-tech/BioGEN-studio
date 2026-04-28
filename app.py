import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Biogen Studio – Biomarker Insight Studio",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SIDEBAR ---
st.sidebar.title("🧬 Biogen Studio")
st.sidebar.markdown("AI‑powered biomarker‑insight studio for cardiac‑risk stratification.")

mode = st.sidebar.radio(
    "Mode",
    ["Clinician Mode", "Risk Snapshot", "Patient Mode"],
    index=0
)

st.sidebar.divider()

# --- HELPER: LOAD DATA ---
@st.cache_data
def load_sample_data():
    # Try to load real CSV
    try:
        df = pd.read_csv("data/biomarkers.csv")
        st.success("✅ Loaded real biomarker data from biomarkers.csv")
    except FileNotFoundError:
        np.random.seed(42)
        n = 50
        df = pd.DataFrame({
            "Visit": np.random.choice(["Baseline", "24h", "48h", "72h"], n),
            "Age": np.random.randint(40, 85, n),
            "Sex": np.random.choice(["Male", "Female"], n),
            "Troponin (ng/L)": np.random.lognormal(3, 0.8, n),
            "BNP (pg/mL)": np.random.lognormal(1.5, 0.7, n),
            "CRP (mg/L)": np.random.lognormal(1.2, 0.5, n),
            "Creatinine (µmol/L)": np.random.lognormal(3.2, 0.4, n),
            "Risk_Score": np.random.uniform(0, 1, n)
        })
        st.info("Using sample biomarker data (no data/biomarkers.csv found).")
    return df


# --- MAIN TITLE ---
st.title("🧬 Biogen Studio – AI‑powered biomarker‑insight studio")

if "Clinician" in mode:
    st.markdown("### Clinician Mode – Biomarker dashboard & pattern discovery")

    # --- DATA LOADER + UPLOAD ---
    df = load_sample_data()

    uploaded_file = st.file_uploader("Upload biomarker CSV (optional)", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        st.success("✅ Data loaded from uploaded CSV")

    # --- FILTERS ---
    st.sidebar.subheader("Filters")
    ages = st.sidebar.slider("Age range", int(df["Age"].min()), int(df["Age"].max()), (40, 80))
    df = df[(df["Age"] >= ages[0]) & (df["Age"] <= ages[1])]

    visit_list = st.sidebar.multiselect(
        "Visit",
        df["Visit"].unique(),
        default=df["Visit"].unique()
    )
    df = df[df["Visit"].isin(visit_list)]

    high_risk_thresh = st.sidebar.slider("High‑risk threshold (Risk_Score)", 0.0, 1.0, 0.7)
    df["Is_High_Risk"] = df["Risk_Score"] > high_risk_thresh

    # --- KPIs ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Patients", len(df))
    kpi2.metric("Avg Troponin (ng/L)", f"{df['Troponin (ng/L)'].median():,.1f}")
    kpi3.metric("Avg BNP (pg/mL)", f"{df['BNP (pg/mL)'].median():,.1f}")
    kpi4.metric("High‑risk", f"{df['Is_High_Risk'].sum()} ({df['Is_High_Risk'].mean():.1%})")

    # --- PLOTS ---
    st.markdown("## Biomarker Trends")

    c1, c2 = st.columns(2)

    with c1:
        fig1 = px.scatter(
            df,
            x="BNP (pg/mL)",
            y="Troponin (ng/L)",
            color="Risk_Score",
            hover_data=["Age", "Sex", "Visit"],
            title="Troponin vs BNP with Risk Score"
        )
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fig2 = px.box(
            df,
            x="Visit",
            y="CRP (mg/L)",
            color="Is_High_Risk",
            title="CRP by Visit and Risk"
        )
        st.plotly_chart(fig2, use_container_width=True)

    # --- PATTERN‑DISCOVERY ---
    st.markdown("## Pattern‑Discovery (AI‑Style)")

    threshold = st.slider("High‑risk threshold (Risk_Score)", 0.0, 1.0, 0.7)
    high_risk = df[df["Risk_Score"] > threshold]
    st.write(f"High‑risk patterns ({len(high_risk)} patients):")
    st.dataframe(high_risk.head(8))

    st.markdown("### Suggested patterns (simulated AI):")
    st.markdown("- **Pattern 1**: High early Troponin + BNP → 80% high‑risk")
    st.markdown("- **Pattern 2**: Rising CRP over 48h → 65% high‑risk")
    st.markdown("- **Pattern 3**: Older age + high Creatinine → 70% high‑risk")


# --- RISK SNAPSHOT ---
elif mode == "Risk Snapshot":
    st.markdown("### Patient‑level Risk Snapshot")

    col1, col2, col3 = st.columns(3)
    age = col1.number_input("Age", 18, 100, 60)
    sex = col2.selectbox("Sex", ["Male", "Female"])
    troponin = col3.number_input("Troponin (ng/L)", 0.0, 10000.0, 100.0)
    bnp = st.number_input("BNP (pg/mL)", 0.0, 5000.0, 200.0)
    crp = st.number_input("CRP (mg/L)", 0.0, 300.0, 10.0)
    creatinine = st.number_input("Creatinine (µmol/L)", 20.0, 200.0, 80.0)

    # --- FAKE RISK MODEL ---
    risk_score = (
        0.3 * (troponin / 1000) +
        0.2 * (bnp / 1000) +
        0.1 * (crp / 50) +
        0.1 * (creatinine / 100) +
        0.05 * (age / 80)
    )
    risk_score = min(risk_score, 1.0)
    risk_label = "High Risk" if risk_score > 0.7 else "Medium Risk" if risk_score > 0.4 else "Low Risk"

    # --- DISPLAY RISK ---
    st.markdown("### Predicted Risk")
    st.metric("Risk Score", f"{risk_score:.2f}")
    st.markdown(f"**{risk_label}**")

    # --- RISK VISUAL ---
    risk_gauge = px.bar(
        pd.DataFrame({"value": [risk_score]}),
        y="value",
        range_y=[0, 1],
        text="value",
        title="Patient Risk Score",
        labels={"value": "Risk Score"},
    )
    st.plotly_chart(risk_gauge, use_container_width=True)


# --- PATIENT MODE ---
elif mode == "Patient Mode":
    st.markdown("### Patient Mode – Educated, Empowered, Informed")

    st.markdown("""
    **Welcome!** This view helps you understand your heart‑health biomarkers and your risk profile in simple language.
    """)
    st.markdown("#### What are these numbers?")
    st.markdown("""
    - **Troponin**: Protein released when heart muscle is stressed.  
    - **BNP**: Hormone indicating heart strain and fluid overload.  
    - **CRP**: Inflammation marker.  
    - **Creatinine**: Kidney‑function marker.
    """)

    st.markdown("#### How is my risk calculated?")
    st.markdown("""
    - We combine your age, sex, and lab values into a **Risk Score** from 0–1.  
    - Higher score = higher chance of needing closer follow‑up or treatment.
    """)

    st.markdown("#### What should I do next?")
    st.markdown("""
    - **Low Risk**: Continue routine check‑ups and a healthy lifestyle.  
    - **Medium Risk**: Discuss with your doctor about risk‑reduction steps.  
    - **High Risk**: Seek prompt clinical review for possible acute management.
    """)

    st.markdown("ℹ️ This is a **simulation tool** for education and insight‑generation, not a clinical decision‑system.")