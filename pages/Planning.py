import streamlit as st

st.title("🗓️ Planning Page")
st.write("Here you can plan your quarterly allocations.")

# Step 1: Input yearly income
income = st.number_input("Enter your total yearly income (RM):", min_value=0.0, step=1000.0)

if income > 0:
    # Step 2: Select allocation mode
    st.subheader("Select your quarterly allocation mode:")
    allocation_mode = st.radio("Allocation mode:", ["Equal (25% per quarter)", "Manual (custom %)"])

    if allocation_mode == "Equal (25% per quarter)":
        allocations = [0.25, 0.25, 0.25, 0.25]

    else:
        st.subheader("Set your custom allocation for each quarter (Total must be 100%)")
        cols = st.columns(4)
        allocations = []
        total = 0

        for i in range(4):
            percent = cols[i].slider(f"Quarter {i+1} (%)", min_value=0, max_value=100, value=25)
            allocations.append(percent / 100)
            total += percent

        if total != 100:
            st.error(f"Total allocation must be 100%. Current total: {total}%")
        else:
            st.success("Your quarterly allocation is valid.")

    # Display the quarterly breakdown
    if allocation_mode == "Equal (25% per quarter)" or total == 100:
        st.subheader("Your Quarterly Allocation (RM)")
        for i, alloc in enumerate(allocations):
            st.write(f"Quarter {i+1}: RM {income * alloc:,.2f} ({alloc * 100:.0f}%)")
