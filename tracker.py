import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

DATA_PATH = "Contracts Traded.xlsx"

st.title("📈 WHL Exports Tracking Dashboard")

# Check if file exists
if not os.path.exists(DATA_PATH):
    st.error(f"File not found at: {DATA_PATH}")
else:
    # Load Excel
    df = pd.read_excel(DATA_PATH, header=1)
    
    # Parse columns
    if "PC Date" in df.columns:
        df["PC Date"] = pd.to_datetime(df["PC Date"], errors="coerce")
    if "Container Qty" in df.columns:
        df["Container Qty"] = pd.to_numeric(df["Container Qty"], errors="coerce")
    if "SC Qty (MT)" in df.columns:
        df["SC Qty (MT)"] = pd.to_numeric(df["SC Qty (MT)"], errors="coerce")
    if "Sales Rate/MT (USD)" in df.columns:
        df["Sales Rate/MT (USD)"] = pd.to_numeric(df["Sales Rate/MT (USD)"], errors="coerce")
    if "Purchase Rate/MT (USD)" in df.columns:
        df["Purchase Rate/MT (USD)"] = pd.to_numeric(df["Purchase Rate/MT (USD)"], errors="coerce")

    # Drop rows with missing essentials
    required_cols = ["SC#", "PC Date", "SC Qty (MT)", "Sales Rate/MT (USD)", "Purchase Rate/MT (USD)"]
    df.dropna(subset=[c for c in required_cols if c in df.columns], inplace=True)

    # Calculate revenue & cost for KPIs
    df["Revenue"] = df["SC Qty (MT)"] * df["Sales Rate/MT (USD)"]
    df["Cost"] = df["SC Qty (MT)"] * df["Purchase Rate/MT (USD)"]

    # Convert Gross Margin to numeric from Excel values
    df["Gross Margin"] = pd.to_numeric(df["Gross Margin"], errors="coerce")

    # =======================
    # Status filter with "All" option
    if "Status" in df.columns:
        statuses = sorted(df["Status"].dropna().astype(str).unique().tolist())
        statuses.insert(0, "All (Completed + Pending)")
        selected_status = st.selectbox("Status", statuses)

        if selected_status == "All (Completed + Pending)":
            status_filtered_df = df.copy()
        else:
            status_filtered_df = df[df["Status"].astype(str) == selected_status].copy()
    else:
        st.warning("No 'Status' column found.")
        status_filtered_df = df.copy()

    # Contract filter
    unique_contracts = status_filtered_df["SC#"].astype(str).unique()
    selected_contract = st.selectbox("Select a Contract (SC#)", unique_contracts)
    filtered_df = status_filtered_df[status_filtered_df["SC#"].astype(str) == str(selected_contract)].copy()

    # =======================
    # KPIs for status filter
    total_contracts = status_filtered_df["SC#"].nunique()
    total_material_sent = status_filtered_df["Container Qty"].sum()
    total_qty_sold = status_filtered_df["SC Qty (MT)"].sum()
    total_revenue = status_filtered_df["Revenue"].sum()
    total_cost = status_filtered_df["Cost"].sum()
    total_margin = status_filtered_df["Gross Margin"].sum()

    st.subheader("🔢 Key Metrics (Filtered by Status)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Contracts", total_contracts)
    col2.metric("Quantity Sent", f"{total_material_sent:,.2f}MT")
    col3.metric("Quantity Sold", f"{total_qty_sold:,.2f}MT")

    col4, col5, col6 = st.columns(3)
    col4.metric("Total Revenue", f"${total_revenue:,.2f}")
    col5.metric("Total Cost", f"${total_cost:,.2f}")
    col6.metric("Gross Margin", f"${total_margin:,.2f}")

    # KPIs for selected contract
    contract_material_sent = filtered_df["Container Qty"].sum()
    contract_qty_sold = filtered_df["SC Qty (MT)"].sum()
    contract_revenue = filtered_df["Revenue"].sum()
    contract_cost = filtered_df["Cost"].sum()
    contract_margin = filtered_df["Gross Margin"].sum()

    st.subheader(f"📌 KPIs for Contract: {selected_contract}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Quantity Sent", f"{contract_material_sent:,.2f}MT")
    col2.metric("Quantity Sold", f"{contract_qty_sold:,.2f}MT")
    col3.metric("Containers", len(filtered_df))

    col4, col5, col6 = st.columns(3)
    col4.metric("Revenue", f"${contract_revenue:,.2f}")
    col5.metric("Cost", f"${contract_cost:,.2f}")
    col6.metric("Margin", f"${contract_margin:,.2f}")

    # Monthly trend
    status_filtered_df["Month"] = status_filtered_df["PC Date"].dt.to_period("M").astype(str)
    trend = status_filtered_df.groupby("Month", as_index=False).agg({
        "Revenue": "sum",
        "Cost": "sum",
        "Gross Margin": "sum"
    })

    st.subheader("📊 Monthly Revenue Trend")
    fig, ax = plt.subplots()
    ax.plot(trend["Month"], trend["Revenue"], marker="o", label="Revenue ($)")
    ax.plot(trend["Month"], trend["Cost"], marker="o", label="Cost ($)")
    ax.plot(trend["Month"], trend["Gross Margin"], marker="o", label="Margin ($)")
    ax.set_ylabel("Amount ($)")
    ax.set_title("Revenue, Cost, and Margin Over Time")
    plt.xticks(rotation=45)
    ax.legend()
    st.pyplot(fig)

    # Show raw data
    st.subheader("🗃️ Raw Contract Data (Filtered)")
    show_cols = [c for c in ["SC#", "PC Date", "Status", "Container Qty", "SC Qty (MT)",
                              "Sales Rate/MT (USD)", "Purchase Rate/MT (USD)",
                              "Revenue", "Cost", "Gross Margin"] if c in filtered_df.columns]
    st.dataframe(filtered_df[show_cols])
