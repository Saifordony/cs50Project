"""Streamlit frontend for trackMoney."""

from datetime import date

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = "http://127.0.0.1:8000"
CATEGORIES = ["Food", "Transport", "Bills", "Fun", "Other"]

st.set_page_config(page_title="trackMoney", page_icon="💸", layout="wide")


def init_session_state() -> None:
    """Initialize state keys used by the app."""

    defaults = {
        "token": None,
        "username": None,
        "theme": "Light",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_theme() -> None:
    """Simple in-app theme switcher for dark/light appearance."""

    if st.session_state.theme == "Dark":
        st.markdown(
            """
            <style>
                .stApp { background-color: #0E1117; color: #FAFAFA; }
                .stSidebar { background-color: #111827; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def auth_headers() -> dict[str, str]:
    """Return authorization headers for backend requests."""

    if not st.session_state.token:
        return {}
    return {"Authorization": f"Bearer {st.session_state.token}"}


def api_request(method: str, endpoint: str, **kwargs):
    """Call backend API and raise a readable error on failure."""

    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, timeout=20, **kwargs)
    except requests.RequestException as exc:
        raise RuntimeError(f"Could not connect to backend at {API_BASE_URL}") from exc

    if response.status_code >= 400:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except ValueError:
            pass
        raise RuntimeError(f"{response.status_code}: {detail}")

    if response.status_code == 204:
        return None
    return response.json()


def render_auth_view() -> None:
    """Render login/register page."""

    st.title("💸 trackMoney")
    st.caption("A simple personal expense tracker")

    mode = st.radio("Choose Action", ["Login", "Register"], horizontal=True)

    with st.form("auth_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(mode)

    if not submitted:
        return

    if not username or not password:
        st.error("Please fill in all fields.")
        return

    try:
        if mode == "Register":
            api_request("POST", "/register", json={"username": username, "password": password})
            st.success("Registration successful! You can now login.")
        else:
            data = api_request("POST", "/login", json={"username": username, "password": password})
            st.session_state.token = data["access_token"]
            st.session_state.username = username.strip().lower()
            st.success("Login successful")
            st.rerun()
    except Exception as exc:
        st.error(f"Authentication failed: {exc}")


def fetch_expenses(filters: dict | None = None) -> list[dict]:
    """Fetch expense list with optional filters."""

    return api_request("GET", "/expenses", headers=auth_headers(), params=filters or {})


def render_dashboard() -> None:
    """Render summary cards and visualizations."""

    st.subheader("Dashboard")

    expenses = fetch_expenses()
    summary = api_request("GET", "/expenses/summary", headers=auth_headers())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Spending", f"${summary['total_spending']:,.2f}")
    col2.metric("This Month", f"${summary['monthly_total']:,.2f}")
    col3.metric("Average Daily", f"${summary['average_daily_spending']:,.2f}")
    col4.metric("Top Category", summary["highest_spending_category"])

    if not expenses:
        st.info("No expenses yet. Add your first expense from the sidebar.")
        return

    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])

    st.markdown("### Category Totals")
    category_totals_df = pd.DataFrame(
        [{"category": key, "total": value} for key, value in summary["category_totals"].items()]
    )
    st.dataframe(category_totals_df, use_container_width=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("#### Spending by Category (Pie)")
        if category_totals_df.empty:
            st.info("No category data")
        else:
            pie_figure = category_totals_df.set_index("category").plot.pie(
                y="total", autopct="%1.1f%%", legend=False, ylabel="", figsize=(5, 5)
            ).figure
            st.pyplot(pie_figure)

    with chart_col2:
        st.markdown("#### Spending Over Time")
        trend = df.groupby("date", as_index=False)["amount"].sum().sort_values("date")
        st.line_chart(trend, x="date", y="amount", use_container_width=True)

    st.markdown("#### Monthly Spending")
    monthly_df = pd.DataFrame(summary["monthly_breakdown"])
    if monthly_df.empty:
        st.info("No monthly data yet")
    else:
        st.bar_chart(monthly_df, x="month", y="amount", use_container_width=True)


def create_expense_form() -> None:
    """Render create-expense form."""

    st.subheader("Add New Expense")
    with st.form("add_expense_form", clear_on_submit=True):
        title = st.text_input("Title")
        amount = st.number_input("Amount", min_value=0.01, step=0.50)
        category = st.selectbox("Category", CATEGORIES)
        expense_date = st.date_input("Date", value=date.today())
        notes = st.text_area("Notes (optional)")
        submitted = st.form_submit_button("Add Expense")

    if submitted:
        payload = {
            "title": title,
            "amount": amount,
            "category": category,
            "date": expense_date.isoformat(),
            "notes": notes or None,
        }
        try:
            api_request("POST", "/expenses", headers=auth_headers(), json=payload)
            st.success("Expense added successfully.")
        except Exception as exc:
            st.error(f"Could not add expense: {exc}")


def render_expense_table() -> None:
    """Render expense table with edit/delete actions."""

    st.subheader("View / Edit Expenses")

    with st.expander("Filters & Sorting", expanded=True):
        col1, col2, col3, col4, col5 = st.columns(5)
        sort_by = col1.selectbox("Sort by", ["date", "amount"])
        order = col2.selectbox("Order", ["desc", "asc"])
        category = col3.selectbox("Category", ["All"] + CATEGORIES)
        start_date = col4.date_input("Start date", value=None)
        end_date = col5.date_input("End date", value=None)
        search = st.text_input("Search title/notes")

    filters = {"sort_by": sort_by, "order": order}
    if category != "All":
        filters["category"] = category
    if start_date:
        filters["start_date"] = start_date.isoformat()
    if end_date:
        filters["end_date"] = end_date.isoformat()

    expenses = fetch_expenses(filters)
    if not expenses:
        st.info("No matching expenses found.")
        return

    df = pd.DataFrame(expenses)
    if search:
        search_lower = search.lower()
        df = df[
            df["title"].str.lower().str.contains(search_lower)
            | df["notes"].fillna("").str.lower().str.contains(search_lower)
        ]

    if df.empty:
        st.info("No rows after search filter.")
        return

    st.dataframe(df[["id", "title", "amount", "category", "date", "notes"]], use_container_width=True)

    st.download_button(
        "Export CSV",
        data=df.to_csv(index=False),
        file_name="trackmoney_expenses.csv",
        mime="text/csv",
    )

    selected_id = st.selectbox("Select Expense ID to Edit/Delete", df["id"].tolist())
    selected_row = df[df["id"] == selected_id].iloc[0]

    with st.form("edit_expense_form"):
        title = st.text_input("Title", value=selected_row["title"])
        amount = st.number_input("Amount", min_value=0.01, value=float(selected_row["amount"]))
        category_value = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(selected_row["category"]))
        expense_date = st.date_input("Date", value=pd.to_datetime(selected_row["date"]).date())
        notes = st.text_area("Notes", value=selected_row["notes"] if pd.notna(selected_row["notes"]) else "")

        col_update, col_delete = st.columns(2)
        update_clicked = col_update.form_submit_button("Update Expense")
        delete_clicked = col_delete.form_submit_button("Delete Expense")

    if update_clicked:
        try:
            api_request(
                "PUT",
                f"/expenses/{selected_id}",
                headers=auth_headers(),
                json={
                    "title": title,
                    "amount": amount,
                    "category": category_value,
                    "date": expense_date.isoformat(),
                    "notes": notes or None,
                },
            )
            st.success("Expense updated.")
            st.rerun()
        except Exception as exc:
            st.error(f"Update failed: {exc}")

    if delete_clicked:
        try:
            api_request("DELETE", f"/expenses/{selected_id}", headers=auth_headers())
            st.success("Expense deleted.")
            st.rerun()
        except Exception as exc:
            st.error(f"Delete failed: {exc}")


def render_profile() -> None:
    """Render authenticated profile details."""

    st.subheader("Profile")
    try:
        profile = api_request("GET", "/profile", headers=auth_headers())
        st.write(f"**Username:** {profile['username']}")
        st.write(f"**User ID:** {profile['id']}")
        st.write(f"**Joined:** {profile['created_at']}")
    except Exception as exc:
        st.error(f"Could not load profile: {exc}")


def main() -> None:
    """App entrypoint."""

    init_session_state()
    apply_theme()

    if not st.session_state.token:
        render_auth_view()
        return

    st.sidebar.title("trackMoney")
    st.sidebar.write(f"Logged in as **{st.session_state.username}**")
    st.sidebar.radio("Theme", ["Light", "Dark"], key="theme")

    page = st.sidebar.radio("Navigation", ["Dashboard", "Add Expense", "View / Edit Expenses", "Profile"])

    if st.sidebar.button("Logout"):
        st.session_state.token = None
        st.session_state.username = None
        st.success("Logged out")
        st.rerun()

    if page == "Dashboard":
        render_dashboard()
    elif page == "Add Expense":
        create_expense_form()
    elif page == "View / Edit Expenses":
        render_expense_table()
    elif page == "Profile":
        render_profile()


if __name__ == "__main__":
    main()
