import streamlit as st
import pandas as pd

st.title("💰 Balance Calculation Page")

# Example: Quarterly Allocations (Aij)
income = 50000
allocations = [0.25, 0.25, 0.25, 0.25]
quarterly_budgets = [income * alloc for alloc in allocations]

st.info(f"Quarterly Budgets: {[f'RM {budget:,.2f}' for budget in quarterly_budgets]}")

uploaded_file = st.file_uploader("Upload CSV with Expenses", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("📄 Uploaded Data")
    st.write(df)

    if "Individu" not in df.columns:
        st.error("The CSV must contain a column named 'Individu'.")
    else:
        individu = df.iloc[0]["Individu"]

        # Assume all other columns are categories
        category_columns = df.columns[1:]

        st.subheader(f"💼 Balance Calculation for {individu}")
        total_expenses_per_quarter = []
