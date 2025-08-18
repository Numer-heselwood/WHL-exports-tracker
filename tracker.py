import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

DATA_PATH = "Contracts Traded.xlsx"

st.set_page_config(layout="wide", page_title="WHL Exports Dashboard")

# Load data
if not os.path.exists(DATA_PATH):
    st.error(f"File not found at: {DATA_PATH}")
else:
    df = pd.read_excel(DATA_PATH, header=1)

    # Parse columns
    df["PC Date"] = pd.to_datetime(df.get("PC Date"), errors="coerce")
    df["Container Qty"] = pd.to_numeric(df.get("Container Qty"), errors="coerce")
    df["SC Qty (MT)"] = pd.to_numeric(df.get("SC Qty (MT)"), errors="coerce")
    df["Sales Rate/MT (USD)"] = pd.to_numeric(df.get("Sales Rate/MT (USD)"), errors="coerce")
    df["Purchase Rate/MT (USD)"] = pd.to_numeric(df.get("Purchase Rate/MT (USD)"), errors="coerce")
    df["Gross Margin"] = pd.to_numeric(df.get("Gross Margin"), errors="coerce")

    # Drop rows missing essential info
    required_cols = ["SC#", "PC Date", "SC Qty (MT)", "Sales Rate/MT (USD)", "Purchase Rate/MT (USD)"]
    df.dropna(subset=[c for c in required_cols if c in df.columns], inplace=True)

    # Revenue & Cost
    df["Revenue"] = df["SC Qty (MT)"] * df["Sales Rate/MT (USD)"]
    df["Cost"] = df["SC Qty (MT)"] * df["Purchase Rate/MT (USD)"]

    # Main title
    st.markdown("<h1 style='text-align: center;'>📊 WHL Exports</h1>", unsafe_allow_html=True)

    # Page selection buttons (centered)
    colA, colB, colC = st.columns([1, 3, 1])
    with colB:
        page = st.radio(
            "Navigation", 
            ["Overview", "Order Book"], 
            horizontal=True,
            label_visibility="collapsed"
        )

    if page == "Overview":
        st.subheader("📈 WHL Exports Overview")

        # Status filter
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

        st.subheader("Cost Trend")
        fig, ax = plt.subplots()
        ax.plot(trend["Month"], trend["Cost"], marker= 'o', label= "cost ($)", color= "orange")
        ax.set_ylabel("Amount ($)")
        ax.set_title("Cost Trend")
        plt.xticks(rotation=45)
        ax.legend()
        st.pyplot(fig)

        # Raw data
        st.subheader("🗃️ Raw Contract Data (Filtered)")
        show_cols = [c for c in ["SC#", "PC Date", "Status", "Container Qty", "SC Qty (MT)",
                                  "Sales Rate/MT (USD)", "Purchase Rate/MT (USD)",
                                  "Revenue", "Cost", "Gross Margin"] if c in filtered_df.columns]
        st.dataframe(filtered_df[show_cols])
    
    elif page == "Order Book":
        st.subheader("📚 Order Book")

        # Aggregate purchase data by contract
        purchase_df = df.groupby("SC#").agg({
            "PC Qty (MT)": "sum",  # sum all containers per contract
            "Purchase Rate/MT (USD)": "mean"  # average price per contract
        }).rename(columns={
            "PC Qty (MT)": "Purchase Qty",
            "Purchase Rate/MT (USD)": "Purchase Price"
        })

        # Aggregate sales data by contract
        sales_df = df.groupby("SC#").agg({
            "SC Qty (MT)": "sum",  # sum all containers per contract
            "Sales Rate/MT (USD)": "mean",
            "Gross Margin": "sum",
            "Margin/MT": "mean"
        }).rename(columns={
            "SC Qty (MT)": "Sales Qty",
            "Sales Rate/MT (USD)": "Sales Price"
        })

        # Merge purchase and sales data
        order_book_df = pd.merge(purchase_df, sales_df, left_index=True, right_index=True, how="outer")

        # Status check
        order_book_df["Status Check"] = order_book_df.apply(
            lambda x: "Over Sold" if x["Sales Qty"] > x["Purchase Qty"]
            else ("Over Bought" if x["Purchase Qty"] > x["Sales Qty"] else "Balanced"),
            axis=1
        )

        # Exposure: numeric difference
        order_book_df["Exposure"] = order_book_df["Sales Qty"] - order_book_df["Purchase Qty"]

        # Conditional formatting
        def highlight_status_and_exposure(row):
            colors = []
            for col in row.index:
                if col == "Status Check":
                    if row[col] == "Over Sold":
                        colors.append("background-color: #ffcccc")
                    elif row[col] == "Over Bought":
                        colors.append("background-color: #fff2cc")
                    else:
                        colors.append("")
                elif col == "Exposure":
                    if row[col] > 0:
                        colors.append("background-color: #ffcccc")  # oversold
                    elif row[col] < 0:
                        colors.append("background-color: #fff2cc")  # overbought
                    else:
                        colors.append("")
                else:
                    colors.append("")
            return colors

        # Define column order
        column_order = [
            "SC#",
            "Sales Qty",
            "Purchase Qty",
            "Exposure",
            "Sales Price",
            "Purchase Price",
            "Gross Margin",
            "Margin/MT",
            "Status Check"
            
        ]

        # Reset index and reorder
        order_book_df = order_book_df.reset_index()[column_order]

        # Display nicely formatted table
        st.dataframe(
            order_book_df.style
            .apply(highlight_status_and_exposure, axis=1)
            .format({
                "Purchase Qty": "{:,.2f}",
                "Sales Qty": "{:,.2f}",
                "Purchase Price": "${:,.2f}",
                "Sales Price": "${:,.2f}",
                "Gross Margin": "${:,.2f}",
                "Margin/MT": "${:,.2f}",
                "Exposure": "{:,.2f}"
            })
        )
