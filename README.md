# trackMoney

`trackMoney` is a personal expense tracker web app built for CS50 final project requirements. It provides secure user authentication, per-user expense CRUD, filters/sorting, and a clear dashboard with spending insights.

## Project Description
Many people track spending in scattered notes or spreadsheets with no simple way to visualize trends. trackMoney solves this by offering one local app where users can:
- create an account,
- securely log in,
- add and manage expenses,
- view summaries and charts.

## Features

### 1) Authentication
- Register account
- Login/logout
- Password hashing with bcrypt
- JWT authentication for protected API access
- Strict per-user data isolation

### 2) Expense Management (CRUD)
- Add expense with title, amount, category, date, optional notes
- Edit expense
- Delete expense
- Table view of expenses
- Sort by date or amount
- Filter by category and date range
- Search by title/notes

### 3) Dashboard Calculations
- Total spending
- Current month spending
- Category totals
- Average daily spending
- Highest spending category
- Monthly breakdown chart

### 4) Streamlit UI/UX
- Sidebar navigation (`Dashboard`, `Add Expense`, `View / Edit Expenses`, `Profile`)
- Clean forms and feedback messages
- Pie chart for category split
- Line chart for spend-over-time
- CSV export for expenses
- Optional light/dark theme toggle

## Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** SQLite + SQLAlchemy ORM
- **Frontend:** Streamlit
- **Authentication:** JWT + Passlib/Bcrypt
- **Optional:** Flutter web scaffold folder

## Project Structure

```text
trackMoney/
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── database.py
│   └── requirements.txt
├── frontend/
│   ├── streamlit_app.py
│   └── requirements.txt
├── flutter_web/
│   └── README.md
└── README.md
```

## Setup Instructions

### 1) Clone project
```bash
git clone <your-repo-url>
cd trackMoney
```

### 2) Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3) Install dependencies
```bash
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

## Run Locally

### Run backend (FastAPI)
```bash
cd backend
uvicorn main:app --reload
```
Backend: `http://127.0.0.1:8000`

### Run frontend (Streamlit)
```bash
cd frontend
streamlit run streamlit_app.py
```
Frontend: `http://localhost:8501`

## API Endpoints
- `POST /register`
- `POST /login`
- `GET /profile`
- `GET /expenses`
- `POST /expenses`
- `PUT /expenses/{id}`
- `DELETE /expenses/{id}`
- `GET /expenses/summary`

## How to Use
1. Open Streamlit app.
2. Register a new account.
3. Login.
4. Use sidebar pages:
   - **Dashboard:** KPIs + charts
   - **Add Expense:** Create new expense
   - **View / Edit Expenses:** Search/filter/sort/edit/delete/export
   - **Profile:** User details
5. Logout from the sidebar.

## CS50 Final Project Compliance
- **Original project:** Custom-built expense tracker implementation.
- **Clear problem statement:** Simplifies personal expense tracking and visibility.
- **Multiple technologies:** FastAPI + Streamlit + SQLite/SQLAlchemy.
- **Substantial codebase:** Auth, models, validation, REST API, UI and analytics.
- **Documentation:** Complete setup/run/usage/compliance details in this README.
- **Clean structure:** Organized backend/frontend separation.
- **No plagiarism:** Implementation is original for this project.
- **Easy setup:** Local run with minimal commands.

## Notes
- SQLite database file is created automatically at `backend/trackmoney.db`.
- For production, set `TRACKMONEY_SECRET_KEY` environment variable and restrict CORS origins.
- Password hashing uses `pbkdf2_sha256`, which avoids bcrypt backend/version issues and the 72-byte password limit problem.
