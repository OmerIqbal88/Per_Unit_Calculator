# Import necessary libraries
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px
import os

# --- Page Configuration ---
# Set up the Streamlit page with a title, icon, and wide layout for better data display.
st.set_page_config(
    page_title="Income & Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# --- Constants ---
# Define file paths for data persistence and the currency symbol.
DATA_FILE = 'data.json'
CATEGORIES_FILE = 'categories.json'
PKR_SYMBOL = "PKR"

# --- Data Handling Functions ---

def load_data():
    """
    Load transaction data from the JSON file.
    If the file doesn't exist or is empty, return an empty DataFrame.
    This function also ensures the 'Date' and 'Amount' columns have the correct data types.
    """
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            try:
                data = json.load(f)
                df = pd.DataFrame(data)
            except json.JSONDecodeError:
                # Handle case where the file is empty or malformed
                return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Description', 'Amount'])
    else:
        # Create an empty DataFrame if the file doesn't exist
        return pd.DataFrame(columns=['Date', 'Type', 'Category', 'Description', 'Amount'])
    
    # Ensure data types are correct after loading
    if not df.empty:
        df['Date'] = pd.to_datetime(df['Date'])
        df['Amount'] = pd.to_numeric(df['Amount'])
    return df

def save_data(df):
    """
    Save the transaction DataFrame to the JSON file.
    The date is converted to ISO format for JSON compatibility.
    """
    # Convert DataFrame to a list of dictionaries for JSON serialization
    data = df.to_dict('records')
    # Convert Timestamp objects to string before saving
    for record in data:
        record['Date'] = record['Date'].isoformat()
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_default_categories():
    """Return the default set of income and expense categories."""
    return {
        "Income": ["Revenue", "Investment", "Grants"],
        "Expense": ["Salaries", "Income Tax", "Sales Tax", "Inventory", "Bills", "Marketing", "Rent", "Trainings"]
    }

def load_categories():
    """
    Load custom and default categories from the categories JSON file.
    If the file doesn't exist, it creates it with default categories.
    """
    if os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return get_default_categories()
    else:
        return get_default_categories()

def save_categories(categories):
    """Save the current categories (including custom ones) to the JSON file."""
    with open(CATEGORIES_FILE, 'w') as f:
        json.dump(categories, f, indent=4)

# --- Main Application Logic ---
def main():
    """
    The main function that runs the Streamlit application.
    """
    # --- Load Data and Categories at the start ---
    df = load_data()
    categories = load_categories()

    # --- Sidebar for User Inputs ---
    st.sidebar.header("Add New Transaction")
    
    # Use a form to group inputs and submit them together.
    with st.sidebar.form("transaction_form", clear_on_submit=True):
        transaction_date = st.date_input("Date", datetime.now())
        transaction_type = st.selectbox("Type", ["Income", "Expense"])
        
        # Display categories based on the selected transaction type.
        available_categories = categories[transaction_type]
        transaction_category = st.selectbox("Category", available_categories)
        
        description = st.text_area("Description")
        amount = st.number_input(f"Amount ({PKR_SYMBOL})", min_value=0.01, format="%.2f")
        
        submitted = st.form_submit_button("Add Transaction")
        
        if submitted:
            # Create a new DataFrame for the transaction
            new_transaction = pd.DataFrame([{
                "Date": pd.to_datetime(transaction_date),
                "Type": transaction_type,
                "Category": transaction_category,
                "Description": description,
                "Amount": amount
            }])
            
            # Append the new transaction and save the updated data
            df = pd.concat([df, new_transaction], ignore_index=True)
            save_data(df)
            st.sidebar.success("Transaction added successfully!")

    # --- Sidebar for Managing Custom Categories ---
    st.sidebar.header("Manage Categories")
    with st.sidebar.form("category_form", clear_on_submit=True):
        new_category_type = st.selectbox("Transaction type for new category", ["Income", "Expense"])
        new_category_name = st.text_input("New Category Name")
        add_category_submitted = st.form_submit_button("Add Category")
        
        if add_category_submitted and new_category_name:
            if new_category_name not in categories[new_category_type]:
                categories[new_category_type].append(new_category_name)
                save_categories(categories)
                st.sidebar.success(f"Category '{new_category_name}' added to {new_category_type}!")
            else:
                st.sidebar.warning("Category already exists.")

    # --- Main Dashboard Display ---
    st.title("Organizational Finance Dashboard")
    st.markdown("---")

    # --- Key Performance Indicators (KPIs) ---
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    total_expense = df[df['Type'] == 'Expense']['Amount'].sum()
    net_profit = total_income - total_expense

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Income", f"{PKR_SYMBOL} {total_income:,.2f}")
    col2.metric("Total Expenses", f"{PKR_SYMBOL} {total_expense:,.2f}")
    col3.metric("Net Profit/Loss", f"{PKR_SYMBOL} {net_profit:,.2f}")

    st.markdown("---")

    # --- Visualizations ---
    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Income & Expenses by Category")
            category_summary = df.groupby(['Category', 'Type'])['Amount'].sum().reset_index()
            fig_bar = px.bar(category_summary, 
                             x="Category", 
                             y="Amount", 
                             color="Type",
                             title="Income vs. Expenses Breakdown",
                             labels={"Amount": f"Amount ({PKR_SYMBOL})"},
                             color_discrete_map={"Income": "#2ca02c", "Expense": "#d62728"},
                             barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.subheader("Monthly Financial Trend")
            df_monthly = df.set_index('Date').groupby('Type').resample('M')['Amount'].sum().reset_index()
            fig_line = px.line(df_monthly, 
                               x="Date", 
                               y="Amount", 
                               color='Type', 
                               title="Monthly Income vs. Expenses",
                               labels={"Amount": f"Amount ({PKR_SYMBOL})", "Date": "Month"},
                               color_discrete_map={"Income": "#2ca02c", "Expense": "#d62728"},
                               markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Dashboard is empty. Add transactions using the sidebar to see your financial summary.")

    # --- Interactive Data Table with Editing and Deletion ---
    st.subheader("All Transactions")
    
    if not df.empty:
        # Use st.data_editor for an editable, Excel-like table.
        # It allows adding, deleting, and editing rows directly.
        column_config = {
            "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
            "Amount": st.column_config.NumberColumn("Amount", format=f"{PKR_SYMBOL} %'.2f"),
            "Type": st.column_config.SelectboxColumn("Type", options=["Income", "Expense"], required=True),
            "Category": st.column_config.SelectboxColumn("Category", options=categories["Income"] + categories["Expense"], required=True)
        }
        
        edited_df = st.data_editor(
            df.sort_values(by="Date", ascending=False), # Show newest first
            num_rows="dynamic",
            column_config=column_config,
            use_container_width=True,
            key="data_editor"
        )

        # Detect changes made in the data editor and save them back to the file.
        if not edited_df.equals(df):
            edited_df['Date'] = pd.to_datetime(edited_df['Date'])
            save_data(edited_df)
            st.toast("Changes saved successfully!")
            st.rerun() # Rerun the app to reflect changes in KPIs and charts.
    else:
        st.warning("No transactions recorded yet.")

if __name__ == "__main__":
    main()
