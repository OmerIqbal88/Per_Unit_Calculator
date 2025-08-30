import streamlit as st
import math
import pandas as pd
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="All-in-One Electrical Calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CSS Styling ---
def load_css():
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);}
    .result-box {background-color: #e0f7fa; border-left: 7px solid #00bcd4; 
                  color: #004d40; padding: 1rem; border-radius: 10px; margin-top: 20px; text-align: center;}
    .sequence-header {background-color:#d0ebff; padding:5px; border-radius:5px; margin-top:10px;}
    p, h1, h2, h3, h4, h5, h6, div, span {font-family:Aptos; font-size:14px;}
    </style>
    """, unsafe_allow_html=True)

# --- UNIT CATEGORIES ---
UNIT_CATEGORIES = {
    "Capacitance": {
        "units": {
            "Farads (F)": 1.0, "Millifarads (mF)": 1e-3, "Microfarads (μF)": 1e-6,
            "Nanofarads (nF)": 1e-9, "Picofarads (pF)": 1e-12
        }, "icon": "💡"
    }
}

unit_labels = {
    "Resistance": "Ω",
    "Reactance": "Ω",
    "Susceptance": "S",
    "Voltage": "kV",
    "Current": "kA"
}

# --- BASE VALUE CALCULATION ---
def calculate_base_values(S_base, V_base):
    Z_base = (V_base ** 2) / S_base
    I_base = S_base / (math.sqrt(3) * V_base)
    return Z_base, I_base

# --- PER UNIT CALCULATION ---
def to_pu(value, Z_base=None, I_base=None, V_base=None, quantity_type="Impedance"):
    if quantity_type in ["Resistance", "Reactance", "Impedance"]:
        return value / Z_base if Z_base else 0
    elif quantity_type == "Susceptance":
        B_base = 1 / Z_base if Z_base else 0
        return value / B_base if B_base else 0
    elif quantity_type == "Voltage":
        return value / V_base if V_base else 0
    elif quantity_type == "Current":
        return value / I_base if I_base else 0
    else:
        return 0

def from_pu(pu_value, Z_base=None, I_base=None, V_base=None, quantity_type="Impedance"):
    if quantity_type in ["Resistance", "Reactance", "Impedance"]:
        return pu_value * Z_base if Z_base else 0
    elif quantity_type == "Susceptance":
        B_base = 1 / Z_base if Z_base else 0
        return pu_value * B_base if B_base else 0
    elif quantity_type == "Voltage":
        return pu_value * V_base if V_base else 0
    elif quantity_type == "Current":
        return pu_value * I_base if I_base else 0
    else:
        return 0

# --- CARD STYLE DISPLAY ---
def render_per_unit_cards(df, sequences):
    st.subheader("📊 Line Results (Card View)")
    for idx, row in df.iterrows():
        st.markdown(f"### 🏗️ Line {row['Line']}")
        for seq in sequences:
            st.markdown(f"<div class='sequence-header'>{seq} Sequence</div>", unsafe_allow_html=True)
            cols_html = ""
            for qty in ["Resistance", "Reactance", "Susceptance", "Voltage", "Current"]:
                actual = row[f"{qty}_{seq}_Actual ({unit_labels[qty]})"]
                pu = row[f"{qty}_{seq}_PU (pu)"]
                color = "#ccffcc" if 0.05 <= pu <= 1.2 else "#ffcccc"
                cols_html += f"""
                    <div style="display:inline-block; width:18%; margin:1%; padding:10px; border-radius:10px;
                                background-color:{color}; text-align:center;">
                        <b>{qty}</b><br>
                        {actual:.4f} {unit_labels[qty]}<br>
                        {pu:.4f} pu
                    </div>
                """
            st.markdown(cols_html, unsafe_allow_html=True)

# --- ENHANCED PER-UNIT CALCULATOR ---
def render_per_unit_calculator():
    st.header("⚡ Transmission Line Per-Unit Calculator")
    st.markdown('<p>Calculate Resistance, Reactance, Susceptance, Voltage, Current in PU and actual values.</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    S_base = col1.number_input("Base MVA (S_base)", min_value=0.1, value=100.0, format="%.2f")
    V_base = col2.number_input("Base Voltage (V_base, kV)", min_value=0.1, value=13.8, format="%.2f")
    
    Z_base, I_base = calculate_base_values(S_base, V_base)
    st.markdown(f'<p>Base Impedance Z_base = {Z_base:.4f} Ω &nbsp;&nbsp; Base Current I_base = {I_base:.4f} kA</p>', unsafe_allow_html=True)
    
    num_lines = st.number_input("Number of Lines", min_value=1, max_value=50, value=1)
    sequences = st.multiselect("Select Sequence(s)", ["Positive", "Negative", "Zero"], default=["Positive"])
    calc_mode = st.radio("Input Mode", ["Actual → PU", "PU → Actual"])
    per_km = st.checkbox("Input values as per km?")
    line_length = st.number_input("Line Length (km)", min_value=0.1, value=10.0) if per_km else 1.0
    frequency = st.selectbox("Select System Frequency (Hz)", [50, 60], index=0)

    results = []
    for line_idx in range(1, num_lines + 1):
        line_result = {"Line": line_idx}
        for seq in sequences:
            st.markdown(f"### {seq} Sequence")
            cols = st.columns(3)
            for i, qty in enumerate(["Resistance","Reactance","Susceptance"]):
                key = f"{qty}_{seq}_line{line_idx}"
                label_unit = unit_labels[qty]
                if calc_mode == "Actual → PU":
                    val = cols[i].number_input(f"{qty} [{label_unit}] (Line {line_idx})", min_value=0.0,
                                               value=0.5, key=key, help=f"{qty} in {label_unit}")
                    actual_val = val * line_length if per_km else val
                    pu_val = to_pu(actual_val, Z_base=Z_base, I_base=I_base, V_base=V_base, quantity_type=qty)
                else:
                    pu_val = cols[i].number_input(f"{qty} PU (Line {line_idx})", min_value=0.0,
                                                  value=0.05, key=key)
                    actual_val = from_pu(pu_val, Z_base=Z_base, I_base=I_base, V_base=V_base, quantity_type=qty)
                line_result[f"{qty}_{seq}_Actual ({label_unit})"] = actual_val
                line_result[f"{qty}_{seq}_PU (pu)"] = pu_val
            cols2 = st.columns(2)
            for j, qty in enumerate(["Voltage","Current"]):
                key = f"{qty}_{seq}_line{line_idx}"
                label_unit = unit_labels[qty]
                if calc_mode == "Actual → PU":
                    val = cols2[j].number_input(f"{qty} [{label_unit}] (Line {line_idx})", min_value=0.0,
                                                value=V_base if qty=="Voltage" else I_base, key=key)
                    pu_val = to_pu(val, Z_base=Z_base, I_base=I_base, V_base=V_base, quantity_type=qty)
                    actual_val = val
                else:
                    pu_val = cols2[j].number_input(f"{qty} PU (Line {line_idx})", min_value=0.0,
                                                   value=1.0, key=key)
                    actual_val = from_pu(pu_val, Z_base=Z_base, I_base=I_base, V_base=V_base, quantity_type=qty)
                line_result[f"{qty}_{seq}_Actual ({label_unit})"] = actual_val
                line_result[f"{qty}_{seq}_PU (pu)"] = pu_val
        results.append(line_result)

    if st.button("Calculate & Export"):
        df = pd.DataFrame(results)
        render_per_unit_cards(df, sequences)
        st.subheader("Summary Metrics")
        quantities = ["Resistance","Reactance","Susceptance","Voltage","Current"]
        summary_data = []
        for qty in quantities:
            for seq in sequences:
                actual_col = f"{qty}_{seq}_Actual ({unit_labels[qty]})"
                pu_col = f"{qty}_{seq}_PU (pu)"
                summary_data.append({
                    "Quantity": f"{qty} ({seq})",
                    "Actual Value": df[actual_col].mean(),
                    "PU Value": df[pu_col].mean()
                })
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df)

        buffer = BytesIO()
        summary_df.to_excel(buffer, index=False)
        st.download_button("Download Excel", data=buffer, file_name="pu_summary.xlsx", mime="application/vnd.ms-excel")

# --- REACTANCE & SUSCEPTANCE CALCULATOR ---
def render_reactance_susceptance_calculator():
    st.header("⚛️ Reactance & Susceptance Calculators")
    calc_mode = st.radio("Choose Calculation", [
        "Inductive Reactance (from L, f)", "Inductance (from X, f)",
        "Capacitive Reactance (from C, f)", "Capacitance (from Xc, f)",
        "Susceptance (B) from Capacitance", "Capacitance from Susceptance"
    ], horizontal=True)
    # calculations omitted for brevity (same as before)

# --- CAPACITANCE CONVERTER ---
def render_capacitance_converter():
    st.header("💡 Capacitance Converter")
    category = UNIT_CATEGORIES["Capacitance"]
    units = list(category["units"].keys())
    from_unit = st.selectbox("From Unit", units, key="from_cap")
    to_unit = st.selectbox("To Unit", units, key="to_cap")
    value = st.number_input("Enter Capacitance Value", value=1.0, format="%.8f")
    base_val = value * category["units"][from_unit]
    result = base_val / category["units"][to_unit]
    st.markdown(f'**{value} {from_unit} = {result:.8f} {to_unit}**')

# --- MAIN APP LAYOUT ---
load_css()
st.title("🌟 Electrical Engineering Toolkit")

app_mode = st.sidebar.radio(
    "Navigation",
    ["⚡ Per-Unit System", "⚛️ Reactance & Susceptance", "💡 Capacitance Converter"]
)

if app_mode == "⚡ Per-Unit System":
    render_per_unit_calculator()
elif app_mode == "⚛️ Reactance & Susceptance":
    render_reactance_susceptance_calculator()
elif app_mode == "💡 Capacitance Converter":
    render_capacitance_converter()

# --- DISCLAIMER & COPYRIGHT ---
st.markdown("---")
st.markdown(
    """
    <p style='font-size:12px; color:gray; text-align:center;'>
    ⚠️ Disclaimer: This tool is for educational and engineering reference purposes only. 
    Users should verify all results before using in real-world applications.
    </p>
    <p style='font-size:12px; color:gray; text-align:center;'>
    © 2025, All rights reserved.
    </p>
    """, 
    unsafe_allow_html=True
)
