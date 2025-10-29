import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt

# =========================
# 🔧 Database Setup
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Create expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# =========================
# 🧍 User Authentication
# =========================
def register_user(username, password):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def login_user(username, password):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
    result = c.fetchone()
    conn.close()
    return result

# =========================
# 💰 Expense Functions
# =========================
def add_expense(user_id, date, category, desc, amount):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (user_id, date, category, description, amount) VALUES (?, ?, ?, ?, ?)",
              (user_id, date, category, desc, amount))
    conn.commit()
    conn.close()

def get_expenses(user_id):
    conn = sqlite3.connect("database.db")
    df = pd.read_sql_query("SELECT date, category, description, amount FROM expenses WHERE user_id = ?",
                           conn, params=(user_id,))
    conn.close()
    return df

# =========================
# 🎨 Streamlit UI
# =========================
st.set_page_config(page_title="💸 Personal Expense Tracker", layout="centered")
init_db()

if "user_id" not in st.session_state:
    st.session_state.user_id = None

st.title("💸 Personal Expense Tracker ")

# =========================
# 🔐 Login / Register Page
# =========================
if st.session_state.user_id is None:
    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Register"])

    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user_id = user[0]
                st.success(f"Welcome back, {username}! 🎉")
                st.rerun()

            else:
                st.error("Invalid username or password!")

    with tab2:
        st.subheader("Create a new account")
        new_user = st.text_input("Choose a username")
        new_pass = st.text_input("Choose a password", type="password")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("✅ Account created! You can now log in.")
            else:
                st.error("❌ Username already exists. Try another.")
else:
    # =========================
    # 🧾 Logged-in Dashboard
    # =========================
    st.sidebar.success("✅ Logged in successfully!")
    if st.sidebar.button("Logout"):
        st.session_state.user_id = None
        st.experimental_rerun()

    st.header("Add New Expense")
    date = st.date_input("Date", datetime.today())
    category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Others"])
    desc = st.text_input("Description")
    amount = st.number_input("Amount (₹)", min_value=0.0, step=0.1)

    if st.button("Add Expense"):
        add_expense(st.session_state.user_id, date, category, desc, amount)
        st.success("✅ Expense added successfully!")

    st.header("📋 Your Expenses")
    df = get_expenses(st.session_state.user_id)
    st.dataframe(df)

    if not df.empty:
        # Convert date
        df["date"] = pd.to_datetime(df["date"])
        category_sum = df.groupby("category")["amount"].sum()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🧾 Total by Category")
            st.bar_chart(category_sum)

        with col2:
            st.subheader("🥧 Expense Distribution")
            fig, ax = plt.subplots()
            ax.pie(category_sum, labels=category_sum.index, autopct="%1.1f%%")
            st.pyplot(fig)

        st.subheader("📅 Monthly Trend")
        monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
        st.line_chart(monthly)
    else:
        st.info("No expenses yet. Add your first entry above! 🧾")
