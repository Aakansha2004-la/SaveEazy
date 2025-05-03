import streamlit as st
import pandas as pd
import requests
import altair as alt
from datetime import datetime

API_URL = "https://saveeazy.onrender.com"

st.set_page_config(page_title="SaveEazy", page_icon="💰", layout="wide")
st.title("SaveEazy")
st.markdown("Track your finances, set budgets, and analyze your spending patterns.")

# Sidebar navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Transactions", "Budget", "Analysis"])

# --------------------- API Helpers ---------------------
def get_transactions():
    try:
        response = requests.get(f"{API_URL}/transactions")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching transactions: {e}")
        return []

def add_transaction(transaction_data):
    try:
        response = requests.post(f"{API_URL}/transactions", json=transaction_data)
        response.raise_for_status()
        return response.status_code == 201
    except requests.exceptions.RequestException as e:
        st.error(f"Error adding transaction: {e}")
        return False

def delete_transaction(transaction_id):
    try:
        response = requests.delete(f"{API_URL}/transactions/{transaction_id}")
        response.raise_for_status()
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        st.error(f"Error deleting transaction: {e}")
        return False

def get_budget():
    try:
        response = requests.get(f"{API_URL}/budget")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching budget: {e}")
        return []

def update_budget(budget_data):
    try:
        response = requests.post(f"{API_URL}/budget", json=budget_data)
        response.raise_for_status()
        return response.status_code == 201
    except requests.exceptions.RequestException as e:
        st.error(f"Error updating budget: {e}")
        return False

def get_categories():
    try:
        response = requests.get(f"{API_URL}/categories")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching categories: {e}")
        return []

def get_budget_summary():
    try:
        response = requests.get(f"{API_URL}/analysis/budget_summary")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching budget summary: {e}")
        return {}

def get_spending_patterns():
    try:
        response = requests.get(f"{API_URL}/analysis/spending_patterns")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching spending patterns: {e}")
        return {}

# --------------------- Transactions Page ---------------------
if page == "Transactions":
    st.header("All Transactions")
    transactions = get_transactions()
    if transactions:
        df = pd.DataFrame(transactions)
        df['date'] = pd.to_datetime(df['date'])

        with st.expander("🔍 Filter Transactions"):
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date", value=df['date'].min().date())
            with col2:
                end_date = st.date_input("End Date", value=df['date'].max().date())
            category_filter = st.multiselect("Category", options=df['category'].unique(), default=list(df['category'].unique()))

            df = df[(df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)]
            df = df[df['category'].isin(category_filter)]

        df_display = df.sort_values("date", ascending=False).copy()
        df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
        df_display['amount'] = df_display['amount'].apply(lambda x: f"₹{x:,.0f}")

        st.markdown("###  Transactions List (with Delete Option)")
        for _, row in df_display.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
            col1.write(row['date'])
            col2.write(row['category'])
            col3.write(row['amount'])
            col4.write(row['description'])
            if col5.button("🗑️", key=f"del_txn_{row['id']}"):
                if delete_transaction(row['id']):
                    st.success("Transaction deleted.")
                    st.rerun()

    else:
        st.info("No transactions found.")

    st.markdown("---")
    st.subheader("➕ Add New Transaction")
    with st.form("add_transaction_form"):
        categories = get_categories()
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("Date", value=datetime.today())
            amount = st.number_input("Amount (INR)", min_value=0)
        with col2:
            category = st.selectbox("Category", categories if categories else ["Uncategorized"])
            description = st.text_input("Description")
        submitted = st.form_submit_button("Add Transaction")
        if submitted:
            new_transaction = {
                "date": date.isoformat(),
                "amount": amount,
                "category": category,
                "description": description
            }
            if add_transaction(new_transaction):
                st.success("Transaction added!")
                st.rerun()
            else:
                st.error("Failed to add transaction.")

# --------------------- Dashboard Page ---------------------
elif page == "Dashboard":
    st.header("Finance Dashboard")
    try:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Monthly Budget Summary")
            budget_summary = get_budget_summary()
            if budget_summary and 'categories' in budget_summary:
                summary_data = {
                    'Category': [],
                    'Budget (INR)': [],
                    'Spent (INR)': [],
                    'Remaining (INR)': [],
                    '% Used': []
                }
                for cat in budget_summary['categories']:
                    summary_data['Category'].append(cat['category'])
                    summary_data['Budget (INR)'].append(f"₹{cat['budget']:,}")
                    summary_data['Spent (INR)'].append(f"₹{cat['spent']:,}")
                    summary_data['Remaining (INR)'].append(f"₹{cat['remaining']:,}")
                    summary_data['% Used'].append(f"{cat['percent_used']:.1f}%")
                df_summary = pd.DataFrame(summary_data)
                st.dataframe(df_summary, use_container_width=True)

                st.metric("Total Budget (INR)", f"₹{budget_summary['total_budget']:,}")
                st.metric("Total Spent (INR)", f"₹{budget_summary['total_spent']:,}")
                col_rem, col_pct = st.columns(2)
                with col_rem:
                    st.metric("Remaining (INR)", f"₹{budget_summary['total_remaining']:,}")
                with col_pct:
                    st.metric("Budget Used (%)", f"{budget_summary['overall_percent_used']:.1f}%")
            else:
                st.info("No budget data available. Set up your budget in the Budget tab.")

        with col2:
            st.subheader("Recent Transactions")
            transactions = get_transactions()
            if transactions:
                df_transactions = pd.DataFrame(transactions)
                df_transactions['date'] = pd.to_datetime(df_transactions['date'])
                df_transactions = df_transactions.sort_values('date', ascending=False).head(10)
                df_display = df_transactions[['id', 'date', 'category', 'amount', 'description']].copy()
                df_display['date'] = df_display['date'].dt.strftime('%Y-%m-%d')
                df_display['amount'] = df_display['amount'].apply(lambda x: f"₹{x:,.0f}")

                for _, row in df_display.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 3, 1])
                    col1.write(row['date'])
                    col2.write(row['category'])
                    col3.write(row['amount'])
                    col4.write(row['description'])
                    if col5.button("🗑️", key=f"dash_del_txn_{row['id']}"):

                        if delete_transaction(row['id']):
                            st.success("Transaction deleted from dashboard.")
                            st.rerun()
            else:
                st.info("No recent transactions available.")
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# --------------------- Budget Page ---------------------
elif page == "Budget":
    st.header("Set Monthly Budget by Category")
    categories = get_categories()
    budget_data = []
    for category in categories:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"Category: {category}")
        with col2:
            amount = st.number_input(f"{category} (INR)", min_value=100, step=100, key=category)
            rounded_amount = round(amount / 100) * 100
            budget_data.append({"category": category, "budget": rounded_amount})
    if st.button("Submit Budget"):
        if update_budget({"budgets": budget_data}):
            st.success("Budget updated successfully!")
        else:
            st.error("Failed to update budget.")

# --------------------- Analysis Page ---------------------
elif page == "Analysis":
    st.header("Spending Analysis")
    spending_data = get_spending_patterns()

    if spending_data:
        if 'by_date' in spending_data:
            df_date = pd.DataFrame(spending_data['by_date'])

            if 'spending' in df_date.columns:
                df_date['spending'] = df_date['spending'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)

            df_date['spending'] = pd.to_numeric(df_date['spending'], errors='coerce')
            df_date = df_date.dropna(subset=['spending'])

            if not df_date.empty and df_date['spending'].sum() > 0:
                st.subheader("Spending Over Time")
                df_date['date'] = pd.to_datetime(df_date['month'])
                chart = alt.Chart(df_date).mark_line(point=True).encode(
                    x='date:T',
                    y=alt.Y('spending:Q', title='Amount Spent (₹)'),
                    tooltip=['date:T', 'spending:Q']
                ).properties(width=700, height=400)
                st.altair_chart(chart, use_container_width=True)
            else:
                st.warning("Not enough data to display spending over time.")

        if 'by_category' in spending_data:
            df_cat = pd.DataFrame(spending_data['by_category'])

            if 'total' in df_cat.columns:
                df_cat['total'] = df_cat['total'].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
                df_cat['total'] = pd.to_numeric(df_cat['total'], errors='coerce')
                df_cat = df_cat.dropna(subset=['total'])

            if not df_cat.empty and df_cat['total'].sum() > 0:
                st.subheader("Spending by Category")
                pie = alt.Chart(df_cat).mark_arc().encode(
                    theta=alt.Theta(field="total", type="quantitative"),
                    color=alt.Color(field="category", type="nominal"),
                    tooltip=["category", "total"]
                ).properties(width=500, height=400)
                st.altair_chart(pie, use_container_width=True)
            else:
                st.warning("Not enough category data to display pie chart.")
    else:
        st.info("No spending data available yet.")

# --------------------- Footer ---------------------
st.sidebar.markdown("---")
st.sidebar.info("This is a personal finance analyzer built with Flask + Streamlit.")














