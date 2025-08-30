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
                  color: #004d40; padding: 1rem; border-radius: 10px; margin-top: 20px; text-align: center;}
    .sequence-header {background-color:#d0ebff; padding:5px; border-radius:5px; margin-top:10px;}
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

# --- UNIT LABELS ---
unit_labels = {
    "Resistance": "Ω",
    "Reactance": "Ω",
    "Susceptance": "S",
    "Voltage": "kV",
    "Current": "kA"
}

# --- HIGHLIGHT PU OUT OF RANGE ---
def highlight_pu(val):
    try:
        if isinstance(val, (int, float)):
            if val < 0.05 or val > 1.2:
                return 'background-color: #ffcccc'  # Light red
    except:
        pass
    return ''

# --- MAIN APP ---
load_css()
st.title("⚡ Transmission Line Per-Unit Calculator (Multi-Line & Sequences)")

# --- System Base Values ---
st.subheader("System Base Values")
col1, col2 = st.columns(2)
S_base = col1.number_input(
    "Base MVA (S_base)", min_value=0.1, value=100.0, format="%.2f",
    help="System base power in MVA.\nUsed to calculate Z_base = V_base^2 / S_base and I_base = S_base / (√3 * V_base)"
)
V_base = col2.number_input(
    "Base Voltage (V_base, Line-to-Line kV)", min_value=0.1, value=13.8, format="%.2f",
    help="System base voltage in kV.\nUsed to calculate Z_base = V_base^2 / S_base and I_base = S_base / (√3 * V_base)"
)

Z_base, I_base = calculate_base_values(S_base, V_base)
with st.expander("Derived Base Values", expanded=True):
    st.metric("Base Impedance Z_base (Ω)", f"{Z_base:.4f} Ω", help="Z_base = V_base^2 / S_base")
    st.metric("Base Current I_base (kA)", f"{I_base:.4f} kA", help="I_base = S_base / (√3 * V_base)")

st.markdown("---")
st.subheader("Transmission Lines Input")

# --- Multiple Lines Input ---
num_lines = st.number_input("Number of Lines", min_value=1, max_value=50, value=1, step=1,
                            help="Enter the number of transmission lines to calculate")

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

per_km = st.checkbox("Input values as per km?", help="Check if values are given per km; will multiply by line length")
if per_km:
    line_length = st.number_input(
        "Line Length (km)", min_value=0.1, value=10.0, format="%.2f",
        help="Enter total line length to scale per km values"
    )

# --- Input Section for Multiple Lines (Compact UI) ---
results = []
for line_idx in range(1, num_lines + 1):
    st.markdown(f"### Line {line_idx}")
    line_result = {"Line": line_idx}

    for seq in sequences:
        st.markdown(f"<div class='sequence-header'>{seq} Sequence</div>", unsafe_allow_html=True)

        # R, X, B in one row
        cols = st.columns(len(["Resistance","Reactance","Susceptance"]))
        for i, qty in enumerate(["Resistance","Reactance","Susceptance"]):
            label_unit = unit_labels[qty]
            key = f"{qty}_{seq}_line{line_idx}"
            tooltip_text = f"{qty} in {label_unit}.\nFor PU calculation: PU = Actual / Z_base (or 1/Z_base for Susceptance)"
            if calc_mode == "Actual → PU":
                if per_km:
                    val = cols[i].number_input(f"{qty} [{label_unit}]", min_value=0.0, value=0.05, format="%.6f", key=key, help=tooltip_text)
                    actual_val = val * line_length
                else:
                    actual_val = cols[i].number_input(f"{qty} [{label_unit}]", min_value=0.0, value=0.5, format="%.6f", key=key, help=tooltip_text)
                pu_val = to_pu(actual_val, Z_base=Z_base, I_base=I_base, quantity_type=qty)
            else:
                pu_val = cols[i].number_input(f"{qty} PU", min_value=0.0, value=0.05, format="%.6f", key=key, help=tooltip_text)
                actual_val = from_pu(pu_val, Z_base=Z_base, I_base=I_base, quantity_type=qty)
            line_result[f"{qty}_{seq}_Actual ({label_unit})"] = actual_val
            line_result[f"{qty}_{seq}_PU (pu)"] = pu_val

        # Voltage and Current in one row
        cols2 = st.columns(2)
        for j, qty in enumerate(["Voltage","Current"]):
            label_unit = unit_labels[qty]
            key2 = f"{qty}_{seq}_line{line_idx}"
            tooltip_text = f"{qty} in {label_unit}.\nPU = Actual / Base ({V_base} kV or I_base kA)"
            if calc_mode == "Actual → PU":
                actual_val = cols2[j].number_input(f"{qty} [{label_unit}]", min_value=0.0, value=V_base if qty=="Voltage" else 0.5, format="%.4f", key=key2, help=tooltip_text)
                pu_val = to_pu(actual_val, Z_base=Z_base, I_base=I_base, quantity_type=qty)
            else:
                pu_val = cols2[j].number_input(f"{qty} PU", min_value=0.0, value=0.05, format="%.6f", key=key2, help=tooltip_text)
                actual_val = from_pu(pu_val, Z_base=Z_base, I_base=I_base, quantity_type=qty)
            line_result[f"{qty}_{seq}_Actual ({label_unit})"] = actual_val
            line_result[f"{qty}_{seq}_PU (pu)"] = pu_val

    results.append(line_result)

# --- Display & Export Results ---
if st.button("Calculate, Highlight & Export"):
    df = pd.DataFrame(results)
    st.subheader("Results Table with PU Highlighting (PU <0.05 or >1.2)")

    pu_cols = [col for col in df.columns if "_PU" in col]
    st.dataframe(df.style.applymap(highlight_pu, subset=pu_cols))

    # --- Summary Metrics ---
    st.subheader("Summary Metrics (Actual & PU Values)")
    summary_data = []
    quantities = ["Resistance","Reactance","Susceptance","Voltage","Current"]
    for qty in quantities:
        for seq in sequences:
            actual_col = f"{qty}_{seq}_Actual ({unit_labels[qty]})"
            pu_col = f"{qty}_{seq}_PU (pu)"
            summary_data.append({
                "Quantity": qty,
                "Sequence": seq,
                f"Max Actual ({unit_labels[qty]})": df[actual_col].max(),
                f"Min Actual ({unit_labels[qty]})": df[actual_col].min(),
                f"Average Actual ({unit_labels[qty]})": df[actual_col].mean(),
                "Max PU (pu)": df[pu_col].max(),
                "Min PU (pu)": df[pu_col].min(),
                "Average PU (pu)": df[pu_col].mean()
            })
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df)

    # --- CSV download ---
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name='pu_results_multiline.csv', mime='text/csv')

    # --- Excel download with summary ---
    towrite = BytesIO()
    with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Line Data")
        summary_df.to_excel(writer, index=False, sheet_name="Summary Metrics")
    towrite.seek(0)
    st.download_button(
        label="Download Excel (with Summary)",
        data=towrite,
        file_name='pu_results_multiline.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
