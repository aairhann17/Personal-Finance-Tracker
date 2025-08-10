# import necessary libraries for the Python script
import sqlite3
import csv
from datetime import datetime

# This script implements a simple finance tracker using SQLite for database management and CSV for data export.
class Finance_Tracker:
    # Initialize the database connection and create the transactions table if it doesn't exist
    def __init__(self, db_name='finance.db'):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    # create the table for storing transactions
    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    description TEXT,
                    amount REAL
                )
            ''')
    # add transaction to the database
    def add_transaction(self, date, description, amount):
        with self.conn:
            self.conn.execute('''
                INSERT INTO transactions (date, description, amount)
                VALUES (?, ?, ?)
            ''', (date, description, amount))

    # get transactions from the database
    def get_transactions(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM transactions')
        return cursor.fetchall()

    # export transactions to a CSV file
    def export_to_csv(self, filename='transactions.csv'):
        transactions = self.get_transactions()
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Date', 'Description', 'Amount'])