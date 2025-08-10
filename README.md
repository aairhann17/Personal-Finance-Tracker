# Personal Finance Tracker (Python + Tkinter + Streamlit)

A personal finance tracker built in **Python** with:
- **SQLite** backend for persistent storage
- **Tkinter desktop app** for offline use
- **Streamlit web app** for interactive dashboards

Designed to help you **track income, expenses, and visualize spending** — and to showcase Python, data analysis, and full-stack skills on your resume.

---

## Features

### Shared Backend (`finance_backend.py`)
- SQLite database for storing transactions
- Add, view, summarize, and export transactions
- Reusable for multiple frontends (Tkinter + Streamlit)

### Tkinter Desktop App (`finance_tkinter.py`)
- Form-based transaction entry
- Scrollable transaction table
- Expense breakdown pie chart (Matplotlib)
- Export all data to CSV

### Streamlit Web App (`finance_streamlit.py`)
- Sidebar form to add transactions
- Filter transactions by date, type, and category
- Interactive visualizations:
  - Expense breakdown (Pie Chart)
  - Monthly income vs expense (Bar Chart)
  - Cumulative balance over time (Line Chart)
- CSV download for filtered data
- Deployable to **Streamlit Cloud** or Docker
