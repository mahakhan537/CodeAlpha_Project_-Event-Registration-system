import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import os
import bcrypt

# Function to get the database path
def get_db_path():
    db_dir = "C:/Projects/data"  # Change this to your preferred location
    os.makedirs(db_dir, exist_ok=True)  # Ensure the directory exists
    return os.path.join(db_dir, "inventory.db")

DB_PATH = get_db_path()

# Function to initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        quantity INTEGER,
                        price REAL)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password TEXT)''')

    conn.commit()
    conn.close()

# Function to authenticate users
def authenticate(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        hashed_password = user[2]  # Already a byte object
        if bcrypt.checkpw(password.encode(), hashed_password):
            return True
    return False

# Function to add a product to the database
def add_product_to_db(name, quantity, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", (name, quantity, price))
    conn.commit()
    conn.close()

# Function to delete a product from the database
def delete_product_from_db(product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()

# Function to fetch all products
def fetch_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, quantity, price FROM products")

    # Ensure data types are correct and handle None values
    products = [
        (row[0], row[1], row[2] or 0, row[3] or 0.0)
        for row in cursor.fetchall()
    ]
    conn.close()
    return products

# Function to fetch low-stock products
def low_stock_report_from_db(threshold=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, quantity FROM products WHERE quantity < ?", (threshold,))
    low_stock_items = cursor.fetchall()
    conn.close()
    return low_stock_items

# Main application class
class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        
        # Login Frame
        self.login_frame = tk.Frame(self.root)
        self.create_login_frame()

    def create_login_frame(self):
        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0, padx=10, pady=10)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1)

        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0, padx=10, pady=10)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1)

        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, column=0, columnspan=2, pady=10)
        self.login_frame.pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if authenticate(username, password):
            messagebox.showinfo("Success", "Login successful!")
            self.login_frame.destroy()
            self.create_inventory_frame()
        else:
            messagebox.showerror("Error", "Invalid username or password!")

    def create_inventory_frame(self):
        self.inventory_frame = tk.Frame(self.root)
        self.inventory_frame.pack(padx=10, pady=10)

        # Product table
        self.product_table = ttk.Treeview(self.inventory_frame, columns=("ID", "Name", "Quantity", "Price"), show='headings')
        self.product_table.heading("ID", text="ID")
        self.product_table.heading("Name", text="Name")
        self.product_table.heading("Quantity", text="Quantity")
        self.product_table.heading("Price", text="Price")
        self.product_table.pack()

        # Refresh table contents
        self.refresh_table()

        # Buttons
        tk.Button(self.inventory_frame, text="Add Product", command=self.add_product_window).pack(pady=10)
        tk.Button(self.inventory_frame, text="Delete Product", command=self.delete_product).pack(pady=10)
        tk.Button(self.inventory_frame, text="Low Stock Report", command=self.low_stock_report).pack(pady=10)

    def refresh_table(self):
        for row in self.product_table.get_children():
            self.product_table.delete(row)

        for product in fetch_products():
            product_id = product[0]
            product_name = product[1]
            product_quantity = int(product[2])
            product_price = f"{float(product[3]):.2f}"  # Ensure price is formatted correctly
            self.product_table.insert("", "end", values=(product_id, product_name, product_quantity, product_price))

    def add_product_window(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Add Product")

        tk.Label(add_window, text="Name:").grid(row=0, column=0, padx=10, pady=10)
        name_entry = tk.Entry(add_window)
        name_entry.grid(row=0, column=1)

        tk.Label(add_window, text="Quantity:").grid(row=1, column=0, padx=10, pady=10)
        quantity_entry = tk.Entry(add_window)
        quantity_entry.grid(row=1, column=1)

        tk.Label(add_window, text="Price:").grid(row=2, column=0, padx=10, pady=10)
        price_entry = tk.Entry(add_window)
        price_entry.grid(row=2, column=1)

        def save_product():
            name = name_entry.get()
            quantity = quantity_entry.get()
            price = price_entry.get()

            if not name or not quantity.isdigit() or not price.replace(".", "", 1).isdigit():
                messagebox.showerror("Error", "Invalid input!")
                return

            add_product_to_db(name, int(quantity), float(price))
            self.refresh_table()
            add_window.destroy()

        tk.Button(add_window, text="Save", command=save_product).grid(row=3, column=0, columnspan=2, pady=10)

    def delete_product(self):
        selected_item = self.product_table.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a product to delete!")
            return

        product_id = self.product_table.item(selected_item)["values"][0]
        delete_product_from_db(product_id)
        self.refresh_table()

    def low_stock_report(self):
        report_window = tk.Toplevel(self.root)
        report_window.title("Low-Stock Report")

        low_stock_items = low_stock_report_from_db()

        if not low_stock_items:
            tk.Label(report_window, text="No low-stock items found!").pack(padx=10, pady=10)
        else:
            for item in low_stock_items:
                tk.Label(report_window, text=f"ID: {item[0]}, Name: {item[1]}, Quantity: {item[2]}").pack(padx=10, pady=5)

# Run the application
if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
