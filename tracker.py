import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# === UPDATED FILE PATH ===
DATA_PATH = "Contracts Traded.xlsx"

st.title("📈 WHL Exports Tracking Dashboard")

# Check if file exists
if not os.path.exists(DATA_PATH):
    st.error(f"File not found at: {DATA_PATH}")
else:
    # Load Excel
    df = pd.read_excel(DATA_PATH, header=1)
    

    # Parse and clean data
    df['PC Date'] = pd.to_datetime(df['PC Date'], errors='coerce')
    df['Container Qty'] = pd.to_numeric(df['Container Qty'], errors='coerce')
    df['SC Qty (MT)'] = pd.to_numeric(df['SC Qty (MT)'], errors='coerce')
    df['Sales Rate/MT (USD)'] = pd.to_numeric(df['Sales Rate/MT (USD)'], errors='coerce')
    df['Purchase Rate/MT (USD)'] = pd.to_numeric(df['Purchase Rate/MT (USD)'], errors='coerce')

    # Drop rows with missing critical values
    df.dropna(subset=['SC#', 'PC Date', 'SC Qty (MT)', 'Sales Rate/MT (USD)', 'Purchase Rate/MT (USD)'], inplace=True)

    # Calculations
    df['Revenue'] = df['SC Qty (MT)'] * df['Sales Rate/MT (USD)']
    df['Cost'] = df['SC Qty (MT)'] * df['Purchase Rate/MT (USD)']
    df['Gross Margin'] = df['Revenue'] - df['Cost']

    # KPIs
    total_contracts = df['SC#'].nunique()
    total_material_sent = df['Container Qty'].sum()
    total_qty_sold = df['SC Qty (MT)'].sum()
    total_revenue = df['Revenue'].sum()
    total_cost = df['Cost'].sum()
    total_margin = df['Gross Margin'].sum()

    # Show KPIs
    st.subheader("🔢 Key Metrics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Contracts", total_contracts)
    col2.metric("Quantity Sent", f"{total_material_sent:,.2f}MT")
    col3.metric("Quantity Sold", f"{total_qty_sold:,.2f}MT")

    col4, col5, col6 = st.columns(3)
    col4.metric("Total Revenue", f"${total_revenue:,.2f}")
    col5.metric("Total Cost", f"${total_cost:,.2f}")
    col6.metric("Gross Margin", f"${total_margin:,.2f}")
    # -------------------------------
# 🔽 Filter by Contract (SC#)
# -------------------------------
unique_contracts = df['SC#'].unique()
selected_contract = st.selectbox("Select a Contract (SC#)", unique_contracts)

# Filter the DataFrame for the selected contract
filtered_df = df[df['SC#'] == selected_contract]

# Recalculate KPIs for selected contract
contract_material_sent = filtered_df['Container Qty'].sum()
contract_qty_sold = filtered_df['SC Qty (MT)'].sum()
contract_revenue = filtered_df['Revenue'].sum()
contract_cost = filtered_df['Cost'].sum()
contract_margin = filtered_df['Gross Margin'].sum()

st.subheader(f"📌 KPIs for Contract: {selected_contract}")
col1, col2, col3 = st.columns(3)
col1.metric("Quantity Sent", f"{contract_material_sent:,.2f}MT")
col2.metric("Quantity Sold", f"{contract_qty_sold:,.2f}MT")
col3.metric("Revenue", f"${contract_revenue:,.2f}")

col4, col5, col6 = st.columns(3)
col4.metric("Cost", f"${contract_cost:,.2f}")
col5.metric("Margin", f"${contract_margin:,.2f}")
col6.metric("Containers", len(filtered_df))

# Monthly trend
df['Month'] = df['PC Date'].dt.to_period('M').astype(str)
trend = df.groupby('Month').agg({
        'Revenue': 'sum',
        'Cost': 'sum',
        'Gross Margin': 'sum'
    }).reset_index()

st.subheader("📊 Monthly Revenue Trend")
fig, ax = plt.subplots()
ax.plot(trend['Month'], trend['Revenue'], marker='o', label='Revenue ($)')
ax.plot(trend['Month'], trend['Cost'], marker='o', label='Cost ($)')
ax.plot(trend['Month'], trend['Gross Margin'], marker='o', label='Margin ($)')
ax.set_ylabel("Amount ($)")
ax.set_title("Revenue, Cost, and Margin Over Time")
plt.xticks(rotation=45)
ax.legend()
st.pyplot(fig)

st.subheader("🗃️ Raw Contract Data")
st.dataframe(df[['SC#', 'PC Date', 'Container Qty', 'SC Qty (MT)', 
                     'Sales Rate/MT (USD)', 'Purchase Rate/MT (USD)', 

                 'Revenue', 'Cost', 'Gross Margin']])

