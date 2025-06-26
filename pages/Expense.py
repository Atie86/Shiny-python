import streamlit as st

st.title("🧾 Expense Planning Page")

income = 50000
allocations = [0.25, 0.25, 0.25, 0.25]

categories = [
    "Food and Non-Alcoholic Beverages",
    "Alcoholic Beverages, Tobacco, and Narcotics",
    "Clothing and Footwear",
    "Housing, Water, Electricity, Gas and Other Fuels",
    "Furnishings, Household Equipment and Routine Household Maintenance",
    "Health",
    "Transport",
    "Communication",
    "Recreation and Culture",
    "Education",
    "Restaurants and Hotels",
    "Miscellaneous Goods and Services"
]

# Create Quarter Tabs
quarter_tabs = st.tabs(["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"])

for q in range(4):
    with quarter_tabs[q]:
        st.subheader(f"Quarter {q + 1} (Allocated: RM {income * allocations[q]:,.2f})")

        max_budget = income * allocations[q]
        total_expense = 0

        for idx, category in enumerate(categories):
            st.markdown(f"### {category}")

            amount_key = f"q{q}_amount{idx}"

            # Just use the input, no need to assign it manually
            manual_input = st.number_input(
                f"Enter amount for {category} (Quarter {q + 1}):",
                min_value=0.0,
                max_value=max_budget,
                step=100.0,
                key=amount_key
            )

            calculated_percentage = (manual_input / max_budget) * 100 if max_budget != 0 else 0
            total_expense += manual_input

            st.info(f"Allocated: RM {manual_input:,.2f} ({calculated_percentage:.2f}%)")
            st.markdown("---")

        remaining_budget = max_budget - total_expense

        if remaining_budget < 0:
            st.error(f"⚠️ You have overspent by RM {-remaining_budget:,.2f}")
        else:
            st.success(f"Remaining budget: RM {remaining_budget:,.2f}")
