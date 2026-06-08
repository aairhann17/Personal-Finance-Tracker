import sqlite3
from datetime import date

import pandas as pd
import streamlit as st


DB_PATH = "finance.db"
ZERO_CURRENCY = "$0.00"


def get_connection():
	return sqlite3.connect(DB_PATH)


def ensure_schema():
	conn = get_connection()
	cur = conn.cursor()

	cur.execute(
		"""
		CREATE TABLE IF NOT EXISTS transactions (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			date TEXT NOT NULL,
			category TEXT,
			type TEXT,
			amount REAL NOT NULL,
			note TEXT
		)
		"""
	)

	cur.execute("PRAGMA table_info(transactions)")
	existing_cols = {row[1] for row in cur.fetchall()}

	if "category" not in existing_cols:
		cur.execute("ALTER TABLE transactions ADD COLUMN category TEXT")
	if "type" not in existing_cols:
		cur.execute("ALTER TABLE transactions ADD COLUMN type TEXT")
	if "note" not in existing_cols:
		cur.execute("ALTER TABLE transactions ADD COLUMN note TEXT")

	# If a legacy schema had description, map missing notes from it.
	if "description" in existing_cols:
		cur.execute(
			"""
			UPDATE transactions
			SET note = COALESCE(note, description)
			WHERE description IS NOT NULL
			"""
		)

	# Infer type for legacy rows if missing.
	cur.execute(
		"""
		UPDATE transactions
		SET type = CASE WHEN amount >= 0 THEN 'income' ELSE 'expense' END
		WHERE type IS NULL OR type = ''
		"""
	)

	conn.commit()
	conn.close()


def add_transaction(txn_date, category, txn_type, amount, note):
	signed_amount = amount if txn_type == "income" else -abs(amount)
	conn = get_connection()
	conn.execute(
		"""
		INSERT INTO transactions (date, category, type, amount, note)
		VALUES (?, ?, ?, ?, ?)
		""",
		(txn_date, category, txn_type, signed_amount, note),
	)
	conn.commit()
	conn.close()


def load_transactions():
	conn = get_connection()
	df = pd.read_sql_query(
		"""
		SELECT id, date, category, type, amount, note
		FROM transactions
		ORDER BY date DESC, id DESC
		""",
		conn,
	)
	conn.close()

	if df.empty:
		return df

	df["date"] = pd.to_datetime(df["date"], errors="coerce")
	df["category"] = df["category"].fillna("Uncategorized")
	df["type"] = df["type"].fillna(df["amount"].apply(lambda x: "income" if x >= 0 else "expense"))
	df["note"] = df["note"].fillna("")
	return df


def apply_filters(df):
	if df.empty:
		return df

	min_date = df["date"].min().date()
	max_date = df["date"].max().date()

	st.sidebar.subheader("Filters")
	start_date = st.sidebar.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
	end_date = st.sidebar.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)

	if start_date > end_date:
		st.sidebar.error("Start date must be before end date.")
		return df.iloc[0:0]

	types = sorted(df["type"].dropna().unique().tolist())
	selected_types = st.sidebar.multiselect("Type", options=types, default=types)

	categories = sorted(df["category"].dropna().unique().tolist())
	selected_categories = st.sidebar.multiselect("Category", options=categories, default=categories)

	mask = (
		(df["date"].dt.date >= start_date)
		& (df["date"].dt.date <= end_date)
		& (df["type"].isin(selected_types if selected_types else types))
		& (df["category"].isin(selected_categories if selected_categories else categories))
	)
	return df.loc[mask].copy()


def render_metrics(df):
	if df.empty:
		c1, c2, c3 = st.columns(3)
		c1.metric("Total income", ZERO_CURRENCY)
		c2.metric("Total expenses", ZERO_CURRENCY)
		c3.metric("Net balance", ZERO_CURRENCY)
		return

	income_total = df.loc[df["amount"] > 0, "amount"].sum()
	expense_total = abs(df.loc[df["amount"] < 0, "amount"].sum())
	net_balance = income_total - expense_total

	c1, c2, c3 = st.columns(3)
	c1.metric("Total income", f"${income_total:,.2f}")
	c2.metric("Total expenses", f"${expense_total:,.2f}")
	c3.metric("Net balance", f"${net_balance:,.2f}")


def render_charts(df):
	st.subheader("Visualizations")

	if df.empty:
		st.info("No data available for the selected filters.")
		return

	expense_df = df[df["amount"] < 0].copy()
	if not expense_df.empty:
		pie_data = (
			expense_df.groupby("category", as_index=False)["amount"]
			.sum()
			.assign(amount=lambda x: x["amount"].abs())
			.rename(columns={"amount": "expense"})
		)
		st.write("Expense breakdown by category")
		st.vega_lite_chart(
			pie_data,
			{
				"mark": {"type": "arc", "innerRadius": 50},
				"encoding": {
					"theta": {"field": "expense", "type": "quantitative"},
					"color": {"field": "category", "type": "nominal"},
					"tooltip": [
						{"field": "category", "type": "nominal"},
						{"field": "expense", "type": "quantitative", "format": ",.2f"},
					],
				},
			},
			use_container_width=True,
		)
	else:
		st.info("No expense rows available for pie chart.")

	month_df = df.copy()
	month_df["month"] = month_df["date"].dt.to_period("M").dt.to_timestamp()
	month_df["income"] = month_df["amount"].clip(lower=0)
	month_df["expense"] = month_df["amount"].clip(upper=0).abs()
	monthly = month_df.groupby("month", as_index=False)[["income", "expense"]].sum()
	st.write("Monthly income vs expense")
	st.bar_chart(monthly.set_index("month"))

	running = df.sort_values("date").copy()
	running["balance"] = running["amount"].cumsum()
	st.write("Cumulative balance over time")
	st.line_chart(running.set_index("date")["balance"])


def main():
	st.set_page_config(page_title="Personal Finance Tracker", page_icon="💸", layout="wide")
	st.title("Personal Finance Tracker")
	st.caption("Track income and expenses with interactive insights.")

	ensure_schema()

	with st.sidebar:
		st.header("Add Transaction")
		with st.form("add_transaction_form", clear_on_submit=True):
			txn_date = st.date_input("Date", value=date.today())
			category = st.text_input("Category", placeholder="Food, Salary, Transport...").strip()
			txn_type = st.selectbox("Type", options=["income", "expense"], index=1)
			amount = st.number_input("Amount", min_value=0.0, step=0.01, format="%.2f")
			note = st.text_input("Note", placeholder="Optional note").strip()
			submit = st.form_submit_button("Add")

		if submit:
			if not category:
				st.error("Category is required.")
			elif amount <= 0:
				st.error("Amount must be greater than 0.")
			else:
				add_transaction(str(txn_date), category, txn_type, amount, note)
				st.success("Transaction added.")

	all_data = load_transactions()
	filtered_data = apply_filters(all_data)

	render_metrics(filtered_data)

	st.subheader("Transactions")
	if filtered_data.empty:
		st.info("No transactions found for selected filters.")
	else:
		display_df = filtered_data.copy()
		display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
		display_df["amount"] = display_df["amount"].map(lambda v: f"{v:,.2f}")
		st.dataframe(display_df, use_container_width=True, hide_index=True)

		csv_data = filtered_data.copy()
		csv_data["date"] = csv_data["date"].dt.strftime("%Y-%m-%d")
		st.download_button(
			label="Download filtered CSV",
			data=csv_data.to_csv(index=False),
			file_name="filtered_transactions.csv",
			mime="text/csv",
		)

	render_charts(filtered_data)


if __name__ == "__main__":
	main()
