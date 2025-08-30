import streamlit as st
import math

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Per-Unit Calculator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM CSS ---
def load_css():
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #f0f4f8 0%, #d9e2ec 100%);
    }
    .result-box {
        background-color: #e0f7fa;
        border-left: 7px solid #00bcd4;
        color: #004d40;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 20px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- BASE VALUE CALCULATIONS ---
def calculate_base_values(S_base, V_base):
    Z_base = (V_base ** 2) / S_base
    I_base = S_base / (math.sqrt(3) * V_base)
    return Z_base, I_base

# --- PER UNIT CALCULATION ---
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
st.title("⚡ Per-Unit Calculator for Electrical Quantities")

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
st.subheader("Electrical Quantity Input")

quantity_type = st.selectbox(
    "Select Quantity Type",
    ["Resistance", "Reactance", "Susceptance", "Voltage", "Current"],
    help="Choose the type of electrical quantity to convert"
)

sequence_type = st.selectbox(
    "Sequence Type",
    ["Positive", "Negative", "Zero"],
    help="Select the sequence for R, X, B quantities"
)

input_mode = st.radio(
    "Input Mode",
    ["Actual Value", "Per-Unit Value"],
    help="Choose whether you are entering the actual quantity or its per-unit value"
)

per_km = st.checkbox("Input as per km value?", help="Check if the value is given per km and will be multiplied by line length")
if per_km:
    value = st.number_input(f"Enter {quantity_type} per km", min_value=0.0, value=0.05, format="%.6f")
    length = st.number_input("Total Line Length (km)", min_value=0.1, value=10.0, format="%.2f")
    actual_value = value * length
else:
    actual_value = st.number_input(f"Enter {quantity_type} value", min_value=0.0, value=0.5, format="%.6f")

# --- PER UNIT CALCULATION ---
if st.button("Calculate Per-Unit and Actual Values"):
    if input_mode == "Actual Value":
        pu_value = to_pu(actual_value, Z_base=Z_base, I_base=I_base, quantity_type=quantity_type)
        st.markdown(f"<div class='result-box'>**{quantity_type} ({sequence_type} sequence)**<br>"
                    f"Actual Value = {actual_value:.6f} Ω<br>"
                    f"Per-Unit Value = {pu_value:.6f} pu</div>", unsafe_allow_html=True)
    else:
        pu_value = actual_value
        actual_val = from_pu(pu_value, Z_base=Z_base, I_base=I_base, quantity_type=quantity_type)
        st.markdown(f"<div class='result-box'>**{quantity_type} ({sequence_type} sequence)**<br>"
                    f"Per-Unit Value = {pu_value:.6f} pu<br>"
                    f"Actual Value = {actual_val:.6f} Ω</div>", unsafe_allow_html=True)
