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
    </style>
    """, unsafe_allow_html=True)

# --- UNIT CATEGORIES for Capacitance Converter ---
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

def highlight_pu(val):
    try:
        if isinstance(val, (int, float)):
            if val < 0.05 or val > 1.2:
                return 'background-color: #ffcccc'
            else:
                return 'background-color: #ccffcc'
    except:
        pass
    return ''

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
    st.info("Calculate Resistance, Reactance, Susceptance, Voltage, Current in PU and actual values.")

    col1, col2 = st.columns(2)
    S_base = col1.number_input("Base MVA (S_base)", min_value=0.1, value=100.0, format="%.2f")
    V_base = col2.number_input("Base Voltage (V_base, kV)", min_value=0.1, value=13.8, format="%.2f")
    
    Z_base, I_base = calculate_base_values(S_base, V_base)
    st.metric("Base Impedance Z_base (Ω)", f"{Z_base:.4f}")
    st.metric("Base Current I_base (kA)", f"{I_base:.4f}")
    
    num_lines = st.number_input("Number of Lines", min_value=1, max_value=50, value=1)
    sequences = st.multiselect("Select Sequence(s)", ["Positive", "Negative", "Zero"], default=["Positive"])
    calc_mode = st.radio("Input Mode", ["Actual → PU", "PU → Actual"])
    per_km = st.checkbox("Input values as per km?")
    line_length = st.number_input("Line Length (km)", min_value=0.1, value=10.0) if per_km else 1.0

    results = []
    for line_idx in range(1, num_lines + 1):
        line_result = {"Line": line_idx}
        for seq in sequences:
            for qty in ["Resistance","Reactance","Susceptance","Voltage","Current"]:
                key = f"{qty}_{seq}_line{line_idx}"
                label_unit = unit_labels[qty]
                if calc_mode == "Actual → PU":
                    val = st.number_input(f"{qty} {seq} [{label_unit}] (Line {line_idx})", min_value=0.0,
                                          value=0.5, key=key)
                    actual_val = val * line_length if qty in ["Resistance","Reactance","Susceptance"] and per_km else val
                    pu_val = to_pu(actual_val, Z_base=Z_base, I_base=I_base, V_base=V_base, quantity_type=qty)
                else:
                    pu_val = st.number_input(f"{qty} {seq} PU (Line {line_idx})", min_value=0.0,
                                             value=0.05, key=key)
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
                    "Quantity": qty, "Sequence": seq,
                    f"Max Actual ({unit_labels[qty]})": df[actual_col].max(),
                    f"Min Actual ({unit_labels[qty]})": df[actual_col].min(),
                    f"Average Actual ({unit_labels[qty]})": df[actual_col].mean(),
                    "Max PU (pu)": df[pu_col].max(),
                    "Min PU (pu)": df[pu_col].min(),
                    "Average PU (pu)": df[pu_col].mean()
                })
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name='pu_results.csv', mime='text/csv')
        towrite = BytesIO()
        with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Line Data")
            summary_df.to_excel(writer, index=False, sheet_name="Summary Metrics")
        towrite.seek(0)
        st.download_button("Download Excel", data=towrite, file_name='pu_results.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# --- REACTANCE & SUSCEPTANCE CALCULATOR ---
def render_reactance_susceptance_calculator():
    st.header("⚛️ Reactance & Susceptance Calculators")
    calc_mode = st.radio("Choose Calculation", [
        "Inductive Reactance (from L, f)", "Inductance (from X, f)",
        "Capacitive Reactance (from C, f)", "Capacitance (from Xc, f)",
        "Susceptance (B) from Capacitance", "Capacitance from Susceptance"
    ], horizontal=True)

    if calc_mode == "Inductive Reactance (from L, f)":
        L = st.number_input("Enter Inductance (H)", min_value=0.0, value=0.01, format="%.6f")
        f = st.number_input("Enter Frequency (Hz)", min_value=0.0, value=50.0, format="%.2f")
        Xl = 2 * math.pi * f * L
        st.markdown(f'**Inductive Reactance Xₗ = {Xl:.4f} Ω**')

    elif calc_mode == "Inductance (from X, f)":
        Xl = st.number_input("Enter Inductive Reactance (Ω)", min_value=0.0, value=10.0, format="%.4f")
        f = st.number_input("Enter Frequency (Hz)", min_value=1e-6, value=50.0, format="%.2f")
        L = Xl / (2 * math.pi * f) if f > 0 else 0
        st.markdown(f'**Inductance L = {L:.6f} H**')

    elif calc_mode == "Capacitive Reactance (from C, f)":
        C = st.number_input("Enter Capacitance (F)", min_value=1e-12, value=1e-6, format="%.10f")
        f = st.number_input("Enter Frequency (Hz)", min_value=0.0, value=50.0, format="%.2f")
        Xc = 1 / (2 * math.pi * f * C) if f > 0 and C > 0 else 0
        st.markdown(f'**Capacitive Reactance Xc = {Xc:.4f} Ω**')

    elif calc_mode == "Capacitance (from Xc, f)":
        Xc = st.number_input("Enter Capacitive Reactance (Ω)", min_value=1e-9, value=10.0, format="%.4f")
        f = st.number_input("Enter Frequency (Hz)", min_value=1e-6, value=50.0, format="%.2f")
        C = 1 / (2 * math.pi * f * Xc) if f > 0 and Xc > 0 else 0
        st.markdown(f'**Capacitance C = {C:.8f} F**')

    elif calc_mode == "Susceptance (B) from Capacitance":
        C = st.number_input("Enter Capacitance (F)", min_value=1e-12, value=1e-6, format="%.10f")
        f = st.number_input("Enter Frequency (Hz)", min_value=0.0, value=50.0, format="%.2f")
        B = 2 * math.pi * f * C
        st.markdown(f'**Susceptance B = {B:.8f} S**')

    elif calc_mode == "Capacitance from Susceptance":
        B = st.number_input("Enter Susceptance (S)", min_value=1e-12, value=1e-6, format="%.10f")
        f = st.number_input("Enter Frequency (Hz)", min_value=1e-6, value=50.0, format="%.2f")
        C = B / (2 * math.pi * f) if f > 0 else 0
        st.markdown(f'**Capacitance C = {C:.8f} F**')

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
