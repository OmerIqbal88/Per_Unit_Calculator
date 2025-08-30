import streamlit as st
import math
import pandas as pd
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Transmission Line Per-Unit Calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
def load_css():
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);}
    .result-box {background-color: #e0f7fa; border-left: 7px solid #00bcd4; 
                  color: #004d40; padding: 1.5rem; border-radius: 10px; margin-top: 20px; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- BASE VALUE CALCULATIONS ---
def calculate_base_values(S_base, V_base):
    Z_base = (V_base ** 2) / S_base
    I_base = S_base / (math.sqrt(3) * V_base)
    return Z_base, I_base

# --- PER UNIT CALCULATIONS ---
def to_pu(value, Z_base=None, I_base=None, quantity_type="Impedance"):
    if quantity_type in ["Resistance", "Reactance", "Impedance"]:
        return value / Z_base if Z_base else 0
    elif quantity_type == "Susceptance":
        B_base = 1 / Z_base if Z_base else 0
        return value / B_base if B_base else 0
    elif quantity_type == "Voltage":
        return value / V_base
    elif quantity_type == "Current":
        return value / I_base
    else:
        return 0

def from_pu(pu_value, Z_base=None, I_base=None, quantity_type="Impedance"):
    if quantity_type in ["Resistance", "Reactance", "Impedance"]:
        return pu_value * Z_base if Z_base else 0
    elif quantity_type == "Susceptance":
        B_base = 1 / Z_base if Z_base else 0
        return pu_value * B_base if B_base else 0
    elif quantity_type == "Voltage":
        return pu_value * V_base
    elif quantity_type == "Current":
        return pu_value * I_base
    else:
        return 0

# --- MAIN APP ---
load_css()
st.title("⚡ Transmission Line Per-Unit Calculator (Multi-Line)")

# --- System Base Values ---
st.subheader("System Base Values")
col1, col2 = st.columns(2)
S_base = col1.number_input("Base MVA (S_base)", min_value=0.1, value=100.0, format="%.2f",
                           help="System base power in MVA")
V_base = col2.number_input("Base Voltage (V_base, Line-to-Line kV)", min_value=0.1, value=13.8, format="%.2f",
                           help="System base voltage in kV")

Z_base, I_base = calculate_base_values(S_base, V_base)
with st.expander("Derived Base Values", expanded=True):
    st.metric("Base Impedance Z_base (Ω)", f"{Z_base:.4f}")
    st.metric("Base Current I_base (kA)", f"{I_base:.4f}")

st.markdown("---")
st.subheader("Transmission Lines Input")

# --- Multiple Lines Input ---
num_lines = st.number_input("Number of Lines", min_value=1, max_value=50, value=1, step=1)

sequences = st.multiselect(
    "Select Sequence(s) to Calculate",
    ["Positive", "Negative", "Zero"],
    default=["Positive"],
    help="Choose sequence type for R, X, B, Voltage, and Current calculations"
)

calc_mode = st.radio(
    "Input Mode",
    ["Actual → PU", "PU → Actual"],
    help="Choose if you are entering actual values or PU values"
)

quantities = ["Resistance", "Reactance", "Susceptance", "Voltage", "Current"]
per_km = st.checkbox("Input values as per km?", help="Check if values are given per km; will multiply by line length")
if per_km:
    line_length = st.number_input("Line Length (km)", min_value=0.1, value=10.0, format="%.2f")

# --- Input Section for Multiple Lines ---
results = []
for line_idx in range(1, num_lines + 1):
    st.markdown(f"### Line {line_idx}")
    line_result = {"Line": line_idx}
    for qty in quantities:
        for seq in sequences:
            key = f"{qty}_{seq}_line{line_idx}"
            if calc_mode == "Actual → PU":
                if per_km and qty not in ["Voltage", "Current"]:
                    val = st.number_input(f"{qty} ({seq}) per km (Line {line_idx})", min_value=0.0, value=0.05, format="%.6f", key=key)
                    actual_val = val * line_length
                else:
                    actual_val = st.number_input(f"{qty} ({seq}) total value (Line {line_idx})", min_value=0.0, value=0.5, format="%.6f", key=key)
                pu_val = to_pu(actual_val, Z_base=Z_base, I_base=I_base, quantity_type=qty)
            else:  # PU → Actual
                pu_val = st.number_input(f"{qty} ({seq}) PU value (Line {line_idx})", min_value=0.0, value=0.05, format="%.6f", key=key)
                actual_val = from_pu(pu_val, Z_base=Z_base, I_base=I_base, quantity_type=qty)
            line_result[f"{qty}_{seq}_Actual"] = actual_val
            line_result[f"{qty}_{seq}_PU"] = pu_val
    results.append(line_result)

# --- Display & Export Results ---
if st.button("Calculate & Export"):
    df = pd.DataFrame(results)
    st.subheader("Results Table")
    st.dataframe(df)

    # CSV download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='pu_results_multiline.csv',
        mime='text/csv'
    )

    # Excel download
    towrite = BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    st.download_button(
        label="Download Excel",
        data=towrite,
        file_name='pu_results_multiline.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
