import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
from finance_backend import FinanceTracker
from datetime import datetime
import matplotlib.pyplot as plt

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Finance Tracker")
        self.root.geometry("800x500")

        self.tracker = FinanceTracker()

        # Form frame
        form_frame = tk.Frame(root)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0)
        tk.Label(form_frame, text="Category:").grid(row=1, column=0)
        tk.Label(form_frame, text="Type:").grid(row=2, column=0)
        tk.Label(form_frame, text="Amount:").grid(row=3, column=0)
        tk.Label(form_frame, text="Note:").grid(row=4, column=0)

        self.date_entry = tk.Entry(form_frame)
        self.category_entry = tk.Entry(form_frame)
        self.type_var = tk.StringVar(value="expense")
        self.amount_entry = tk.Entry(form_frame)
        self.note_entry = tk.Entry(form_frame)

        self.date_entry.grid(row=0, column=1)
        self.category_entry.grid(row=1, column=1)
        ttk.Combobox(form_frame, textvariable=self.type_var, values=["income", "expense"]).grid(row=2, column=1)
        self.amount_entry.grid(row=3, column=1)
        self.note_entry.grid(row=4, column=1)

        tk.Button(form_frame, text="Add Transaction", command=self.add_transaction).grid(row=5, columnspan=2, pady=5)

        # Transactions table
        self.tree = ttk.Treeview(root, columns=("ID", "Date", "Category", "Type", "Amount", "Note"), show="headings")
        for col in ("ID", "Date", "Category", "Type", "Amount", "Note"):
            self.tree.heading(col, text=col)
        self.tree.pack(expand=True, fill="both")

        # Bottom buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Refresh", command=self.load_transactions).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Show Summary Chart", command=self.show_summary_chart).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Export CSV", command=self.export_csv).grid(row=0, column=2, padx=5)

        self.load_transactions()

    def add_transaction(self):
        date = self.date_entry.get()
        category = self.category_entry.get()
        type_ = self.type_var.get()
        amount = self.amount_entry.get()
        note = self.note_entry.get()

        # Basic validation
        try:
            datetime.strptime(date, "%Y-%m-%d")
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Error", "Invalid date or amount")
            return

        self.tracker.add_transaction(date, category, type_, amount, note)
        messagebox.showinfo("Success", "Transaction added!")
        self.load_transactions()

    def load_transactions(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for transaction in self.tracker.get_all_transactions():
            self.tree.insert("", "end", values=transaction)

    def show_summary_chart(self):
        expenses = self.tracker.get_summary_by_category("expense")
        if not expenses:
            messagebox.showinfo("Info", "No expense data to show.")
            return
        categories, amounts = zip(*expenses)
        plt.figure(figsize=(6, 4))
        plt.pie(amounts, labels=categories, autopct="%1.1f%%")
        plt.title("Expense Breakdown by Category")
        plt.show()

    def export_csv(self):
        filename = self.tracker.export_to_csv()
        messagebox.showinfo("Exported", f"Data exported to {filename}")


if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()
