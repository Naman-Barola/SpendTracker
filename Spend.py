import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

st.set_page_config(page_title="SpendTracker", layout="centered", page_icon="💸")

# --- TRUE BLACK THEME ---
st.markdown("""
    <style>
        .stApp {
            background-color: #000000;
            color: #FFFFFF;
        }
        section[data-testid="stSidebar"] {
            background-color: #0a0a0a;
            color: #FFFFFF;
        }
        h1, h2, h3, h4, h5, h6, p, label, span, div, input, textarea {
            color: #FFFFFF !important;
        }
        div[data-baseweb="input"] > div {
            background-color: #111111 !important;
            color: #FFFFFF !important;
            border: 1px solid #444444;
        }
        input, textarea {
            background-color: #111111 !important;
            color: #FFFFFF !important;
        }
        .stButton>button {
            background-color: #111111;
            color: #00ccff;
            border-radius: 10px;
            border: 1px solid #00ccff;
            transition: 0.2s;
        }
        .stButton>button:hover {
            background-color: #00ccff;
            color: #000000;
        }
        div[data-testid="stMetricValue"] {
            color: #00FF88 !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #FFFFFF !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "data" not in st.session_state:
    st.session_state.data = {}

# --- PAGE SELECTOR ---
page = st.sidebar.radio("📂 Navigation", ["Enter Data", "View History", "Prediction"])

# --- MONTH HANDLING ---
all_months = sorted(set(st.session_state.data.keys()) | {datetime.now().strftime("%Y-%m")})
selected_month = st.selectbox("Select Month (YYYY-MM)", options=all_months)

# Allow manual entry of new months
new_month = st.text_input("Add New Month (format: YYYY-MM)", "")
if new_month:
    try:
        datetime.strptime(new_month, "%Y-%m")
        if new_month not in st.session_state.data:
            st.session_state.data[new_month] = {"income": 0.0, "expenses": {}}
            st.success(f"Added new month: {new_month}")
            selected_month = new_month
    except ValueError:
        st.error("Invalid format. Use YYYY-MM (e.g., 2025-10).")

# --- ENTER DATA PAGE ---
if page == "Enter Data":
    st.title("SpendTracker")
    st.subheader("Track your income, expenses, and savings — stylish dark edition.")

    month_data = st.session_state.data.get(selected_month, {"income": 0.0, "expenses": {}})

    income = st.number_input("Monthly Income",
                             value=float(month_data.get("income", 0.0)),
                             step=100.0, min_value=0.0)

    st.write("### Add or Edit Expenses")
    categories = ["Food", "Rent", "Utilities", "Transport", "Entertainment", "Shopping", "Other"]

    expenses = {}
    for category in categories:
        expenses[category] = st.number_input(f"{category} Expense",
                                             value=float(month_data.get("expenses", {}).get(category, 0.0)),
                                             step=10.0, min_value=0.0, key=f"{selected_month}_{category}")

    if st.button("Save Data"):
        st.session_state.data[selected_month] = {"income": income, "expenses": expenses}
        st.success(f"Data saved for {selected_month}!")

    total_expenses = sum(expenses.values())
    savings = income - total_expenses
    savings_rate = (savings / income * 100) if income > 0 else 0

    st.metric("Total Expenses", f"${total_expenses:,.2f}")
    st.metric("Savings", f"${savings:,.2f}")
    st.metric("Savings Rate", f"{savings_rate:.2f}%")

# --- VIEW HISTORY PAGE ---
elif page == "View History":
    st.title("Expense History & Trends")

    if not st.session_state.data:
        st.warning("No data yet. Add at least one month in 'Enter Data'.")
    else:
        df = pd.DataFrame([
            {
                "Month": m,
                "Income": v["income"],
                "Expenses": sum(v["expenses"].values()),
                "Savings": v["income"] - sum(v["expenses"].values())
            }
            for m, v in st.session_state.data.items()
        ])

        df["Savings Rate (%)"] = (df["Savings"] / df["Income"] * 100).round(2)
        st.dataframe(df.set_index("Month"))

        st.write("### Income vs Expenses Trend")
        plt.figure(figsize=(7, 4))
        plt.style.use("dark_background")
        plt.plot(df["Month"], df["Income"], label="Income", marker="o", color="#00FF88")
        plt.plot(df["Month"], df["Expenses"], label="Expenses", marker="o", color="#FF5555")
        plt.plot(df["Month"], df["Savings"], label="Savings", marker="o", color="#00CCFF")
        plt.legend()
        plt.grid(True, alpha=0.3)
        st.pyplot(plt)

# --- PREDICTION PAGE ---
elif page == "Prediction":
    st.title("Next Month’s Expenditure Prediction")

    if not st.session_state.data:
        st.warning("Add at least 2 months of data for predictions.")
    else:
        df = pd.DataFrame([
            {
                "Month": m,
                "Income": v["income"],
                "Expenses": sum(v["expenses"].values()),
            }
            for m, v in st.session_state.data.items()
        ])
        df = df.sort_values("Month")

        if len(df) < 2:
            st.warning("Add one more month to generate predictions.")
        else:
            x = np.arange(len(df))
            y = df["Expenses"].values
            coeffs = np.polyfit(x, y, 1)
            predicted_expenses = np.polyval(coeffs, len(df))

            avg_income = df["Income"].mean()
            suggested_savings = avg_income - predicted_expenses

            st.metric("Predicted Next Month Expenses", f"${predicted_expenses:,.2f}")
            st.metric("Expected Savings", f"${suggested_savings:,.2f}")

            last_expenses = list(st.session_state.data.values())[-1]["expenses"]
            sorted_expenses = sorted(last_expenses.items(), key=lambda x: x[1], reverse=True)

            st.write("### 💡 Areas to Cut Back:")
            for cat, amount in sorted_expenses[:3]:
                st.write(f"- **{cat}**: You spent ${amount:,.2f}. Try reducing by 10–15%.")

            st.info("Prediction based on linear regression from your last few months.")
