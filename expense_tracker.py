
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
import mysql.connector

# -----------------------------------
# MYSQL CONNECTION
# -----------------------------------

def connect_db():
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="NewPassword@123"
        )

        cursor = db.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS expense_tracker")
        cursor.execute("USE expense_tracker")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                amount FLOAT NOT NULL,
                category VARCHAR(50),
                description VARCHAR(200),
                expense_date DATE
            )
        """)

        db.commit()
        return db

    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", str(error))
        return None


# -----------------------------------
# MAIN APPLICATION
# -----------------------------------

root = tk.Tk()
root.title("Personal Expense Tracker")
root.geometry("950x700")
root.configure(bg="#f2f5fa")

db = connect_db()

if db is None:
    root.destroy()
    raise SystemExit("MySQL connection failed")

cursor = db.cursor()

selected_id = None


# -----------------------------------
# ADD EXPENSE
# -----------------------------------

def add_expense():
    try:
        amount = float(amount_entry.get())
        category = category_entry.get().strip()
        description = description_entry.get().strip()
        expense_date = date_entry.get().strip()

        if amount <= 0 or not category:
            messagebox.showwarning(
                "Warning", "Enter a valid amount and category"
            )
            return

        date.fromisoformat(expense_date)

        query = """
            INSERT INTO expenses
            (amount, category, description, expense_date)
            VALUES (%s, %s, %s, %s)
        """

        cursor.execute(
            query, (amount, category, description, expense_date)
        )
        db.commit()

        messagebox.showinfo("Success", "Expense Added Successfully")

        clear_fields()
        view_expenses()

    except ValueError:
        messagebox.showerror(
            "Error", "Enter a valid amount and date (YYYY-MM-DD)"
        )
    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", str(error))


# -----------------------------------
# VIEW EXPENSES
# -----------------------------------

def view_expenses():
    try:
        for item in expense_table.get_children():
            expense_table.delete(item)

        cursor.execute(
            "SELECT * FROM expenses ORDER BY id DESC"
        )

        rows = cursor.fetchall()

        for row in rows:
            expense_table.insert(
                "", tk.END, values=row
            )

        calculate_total()

    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", str(error))


# -----------------------------------
# SELECT EXPENSE
# -----------------------------------

def select_expense(event):
    global selected_id

    selected = expense_table.selection()

    if not selected:
        return

    values = expense_table.item(
        selected[0], "values"
    )

    selected_id = values[0]

    clear_fields(reset_selection=False)

    amount_entry.insert(0, values[1])
    category_entry.insert(0, values[2])
    description_entry.insert(0, values[3])
    date_entry.insert(0, values[4])


# -----------------------------------
# UPDATE EXPENSE
# -----------------------------------

def update_expense():
    global selected_id

    if selected_id is None:
        messagebox.showwarning(
            "Warning", "Select an expense first"
        )
        return

    try:
        amount = float(amount_entry.get())
        category = category_entry.get().strip()
        description = description_entry.get().strip()
        expense_date = date_entry.get().strip()

        if amount <= 0 or not category:
            messagebox.showwarning(
                "Warning", "Enter a valid amount and category"
            )
            return

        date.fromisoformat(expense_date)

        cursor.execute("""
            UPDATE expenses
            SET amount=%s, category=%s,
                description=%s, expense_date=%s
            WHERE id=%s
        """, (
            amount, category, description,
            expense_date, selected_id
        ))

        db.commit()

        messagebox.showinfo(
            "Success", "Expense Updated"
        )

        clear_fields()
        view_expenses()

    except ValueError:
        messagebox.showerror(
            "Error", "Enter valid amount and date"
        )
    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", str(error))


# -----------------------------------
# DELETE EXPENSE
# -----------------------------------

def delete_expense():
    global selected_id

    if selected_id is None:
        messagebox.showwarning(
            "Warning", "Select an expense first"
        )
        return

    confirm = messagebox.askyesno(
        "Delete", "Delete selected expense?"
    )

    if confirm:
        try:
            cursor.execute(
                "DELETE FROM expenses WHERE id=%s",
                (selected_id,)
            )

            db.commit()
            clear_fields()
            view_expenses()

            messagebox.showinfo(
                "Success", "Expense Deleted"
            )

        except mysql.connector.Error as error:
            messagebox.showerror("Database Error", str(error))


# -----------------------------------
# SEARCH EXPENSE
# -----------------------------------

def search_expense():
    try:
        search_text = search_entry.get().strip()

        cursor.execute("""
            SELECT * FROM expenses
            WHERE category LIKE %s
               OR description LIKE %s
        """, (
            "%" + search_text + "%",
            "%" + search_text + "%"
        ))

        rows = cursor.fetchall()

        for item in expense_table.get_children():
            expense_table.delete(item)

        for row in rows:
            expense_table.insert(
                "", tk.END, values=row
            )

    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", str(error))


# -----------------------------------
# TOTAL EXPENSE
# -----------------------------------

def calculate_total():
    try:
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM expenses"
        )

        total = cursor.fetchone()[0]

        total_label.config(
            text=f"Total Expenses: Rs. {total:.2f}"
        )

    except mysql.connector.Error as error:
        messagebox.showerror("Database Error", str(error))


# -----------------------------------
# MONTHLY BUDGET CALCULATOR
# -----------------------------------

def calculate_budget():
    try:
        budget = float(budget_entry.get())
        daily_food = float(food_entry.get())
        days = int(days_entry.get())
        other = float(other_entry.get())

        if budget < 0 or daily_food < 0 or days <= 0 or other < 0:
            messagebox.showwarning(
                "Warning", "Enter valid positive values"
            )
            return

        monthly_food = daily_food * days
        total_spending = monthly_food + other
        remaining = budget - total_spending

        food_result.config(
            text=f"Monthly Food Expense: Rs. {monthly_food:.2f}"
        )

        spending_result.config(
            text=f"Total Planned Spending: Rs. {total_spending:.2f}"
        )

        remaining_result.config(
            text=f"Remaining Money: Rs. {remaining:.2f}"
        )

        if remaining < 0:
            remaining_result.config(fg="red")
        else:
            remaining_result.config(fg="green")

    except ValueError:
        messagebox.showerror(
            "Error", "Please enter valid numbers"
        )


# -----------------------------------
# CLEAR FIELDS
# -----------------------------------

def clear_fields(reset_selection=True):
    global selected_id

    amount_entry.delete(0, tk.END)
    category_entry.delete(0, tk.END)
    description_entry.delete(0, tk.END)
    date_entry.delete(0, tk.END)

    date_entry.insert(0, date.today().isoformat())

    if reset_selection:
        selected_id = None
        for item in expense_table.selection():
            expense_table.selection_remove(item)


# -----------------------------------
# GUI DESIGN
# -----------------------------------

title = tk.Label(
    root,
    text="PERSONAL EXPENSE TRACKER",
    font=("Arial", 22, "bold"),
    bg="#253b80",
    fg="white",
    pady=15
)
title.pack(fill="x")


# EXPENSE INPUT SECTION

input_frame = tk.LabelFrame(
    root,
    text="Add / Update Expense",
    font=("Arial", 12, "bold"),
    bg="#f2f5fa",
    padx=15,
    pady=10
)
input_frame.pack(fill="x", padx=20, pady=10)

tk.Label(input_frame, text="Amount (Rs.)", bg="#f2f5fa").grid(
    row=0, column=0, padx=5, pady=5
)

amount_entry = tk.Entry(input_frame)
amount_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(input_frame, text="Category", bg="#f2f5fa").grid(
    row=0, column=2, padx=5, pady=5
)

category_entry = tk.Entry(input_frame)
category_entry.grid(row=0, column=3, padx=5, pady=5)

tk.Label(input_frame, text="Description", bg="#f2f5fa").grid(
    row=1, column=0, padx=5, pady=5
)

description_entry = tk.Entry(input_frame)
description_entry.grid(row=1, column=1, padx=5, pady=5)

tk.Label(input_frame, text="Date", bg="#f2f5fa").grid(
    row=1, column=2, padx=5, pady=5
)

date_entry = tk.Entry(input_frame)
date_entry.grid(row=1, column=3, padx=5, pady=5)
date_entry.insert(0, date.today().isoformat())


# BUTTON SECTION

button_frame = tk.Frame(root, bg="#f2f5fa")
button_frame.pack(pady=8)

tk.Button(
    button_frame, text="Add",
    width=12, command=add_expense,
    bg="#28a745", fg="white"
).grid(row=0, column=0, padx=5)

tk.Button(
    button_frame, text="Update",
    width=12, command=update_expense
).grid(row=0, column=1, padx=5)

tk.Button(
    button_frame, text="Delete",
    width=12, command=delete_expense,
    bg="#dc3545", fg="white"
).grid(row=0, column=2, padx=5)

tk.Button(
    button_frame, text="View All",
    width=12, command=view_expenses
).grid(row=0, column=3, padx=5)

tk.Button(
    button_frame, text="Clear",
    width=12, command=clear_fields
).grid(row=0, column=4, padx=5)


# SEARCH SECTION

search_frame = tk.Frame(root, bg="#f2f5fa")
search_frame.pack(pady=5)

tk.Label(
    search_frame, text="Search:",
    bg="#f2f5fa"
).pack(side="left", padx=5)

search_entry = tk.Entry(search_frame, width=35)
search_entry.pack(side="left", padx=5)

tk.Button(
    search_frame,
    text="Search",
    command=search_expense
).pack(side="left", padx=5)


# EXPENSE TABLE

table_frame = tk.Frame(root)
table_frame.pack(fill="both", expand=True, padx=20, pady=8)

columns = (
    "ID", "Amount", "Category",
    "Description", "Date"
)

expense_table = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    height=7
)

for col in columns:
    expense_table.heading(col, text=col)
    expense_table.column(col, width=150)

expense_table.pack(
    side="left", fill="both", expand=True
)

scrollbar = ttk.Scrollbar(
    table_frame,
    orient="vertical",
    command=expense_table.yview
)
scrollbar.pack(side="right", fill="y")

expense_table.configure(
    yscrollcommand=scrollbar.set
)

expense_table.bind(
    "<<TreeviewSelect>>", select_expense
)


# TOTAL LABEL

total_label = tk.Label(
    root,
    text="Total Expenses: Rs. 0",
    font=("Arial", 14, "bold"),
    bg="#f2f5fa",
    fg="#253b80"
)
total_label.pack(pady=5)


# BUDGET PLANNER SECTION

budget_frame = tk.LabelFrame(
    root,
    text="Monthly Budget Planner",
    font=("Arial", 12, "bold"),
    bg="#f2f5fa",
    padx=15,
    pady=10
)
budget_frame.pack(fill="x", padx=20, pady=10)

tk.Label(
    budget_frame, text="Starting Budget",
    bg="#f2f5fa"
).grid(row=0, column=0, padx=5, pady=5)

budget_entry = tk.Entry(budget_frame, width=15)
budget_entry.grid(row=0, column=1)
budget_entry.insert(0, "10000")

tk.Label(
    budget_frame, text="Daily Food",
    bg="#f2f5fa"
).grid(row=0, column=2, padx=5)

food_entry = tk.Entry(budget_frame, width=15)
food_entry.grid(row=0, column=3)
food_entry.insert(0, "80")

tk.Label(
    budget_frame, text="Days",
    bg="#f2f5fa"
).grid(row=1, column=0, padx=5, pady=5)

days_entry = tk.Entry(budget_frame, width=15)
days_entry.grid(row=1, column=1)
days_entry.insert(0, "30")

tk.Label(
    budget_frame, text="Other Expenses",
    bg="#f2f5fa"
).grid(row=1, column=2, padx=5)

other_entry = tk.Entry(budget_frame, width=15)
other_entry.grid(row=1, column=3)
other_entry.insert(0, "0")

tk.Button(
    budget_frame,
    text="Calculate Budget",
    command=calculate_budget,
    bg="#253b80",
    fg="white"
).grid(row=2, column=0, columnspan=4, pady=10)

food_result = tk.Label(
    budget_frame,
    text="Monthly Food Expense: Rs. 0",
    bg="#f2f5fa"
)
food_result.grid(row=3, column=0, columnspan=4)

spending_result = tk.Label(
    budget_frame,
    text="Total Planned Spending: Rs. 0",
    bg="#f2f5fa"
)
spending_result.grid(row=4, column=0, columnspan=4)

remaining_result = tk.Label(
    budget_frame,
    text="Remaining Money: Rs. 0",
    font=("Arial", 12, "bold"),
    bg="#f2f5fa"
)
remaining_result.grid(row=5, column=0, columnspan=4)


# -----------------------------------
# START APPLICATION
# -----------------------------------

def close_app():
    cursor.close()
    db.close()
    root.destroy()


root.protocol("WM_DELETE_WINDOW", close_app)

view_expenses()
calculate_budget()

root.mainloop()
