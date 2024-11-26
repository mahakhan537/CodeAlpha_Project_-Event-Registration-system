import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import bcrypt  # type: ignore
import os

def get_db_path():
    db_dir = "C:/Projects/data"  # Or another directory you prefer
    os.makedirs(db_dir, exist_ok=True)  # Ensure the directory exists
    return os.path.join(db_dir, "inventory.db")

# Define DB_PATH at the start of your script
DB_PATH = get_db_path()

def init_db():
    conn = sqlite3.connect(DB_PATH)  # Use the correct DB_PATH
    cursor = conn.cursor()

    # Create users and products tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY,
                        username TEXT UNIQUE,
                        password TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY,
                        name TEXT,
                        quantity INTEGER,
                        price REAL)''')

    # Add a default admin user if no users exist
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        hashed_pw = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ('admin', hashed_pw))

    conn.commit()
    conn.close()

# Authenticate user credentials
def authenticate(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    
    conn.close()
    
    if user and bcrypt.checkpw(password.encode(), user[2]):  # No need to encode user[2] since it's already a bytes object
        return True
    else:
        return False



# Add a product to the database
def add_product(name, quantity, price):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO products (name, quantity, price) VALUES (?, ?, ?)", (name, quantity, price))
    conn.commit()
    conn.close()

# Fetch all products from the database
def fetch_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return products

# Fetch low-stock products
def low_stock_report(threshold=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE quantity < ?", (threshold,))
    low_stock_items = cursor.fetchall()
    conn.close()
    return low_stock_items

# GUI Components
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

        tk.Button(self.inventory_frame, text="Add Product", command=self.add_product_window).grid(row=0, column=0, padx=10, pady=10)
        tk.Button(self.inventory_frame, text="Low-Stock Report", command=self.low_stock_report).grid(row=0, column=1, padx=10, pady=10)

        self.product_table = ttk.Treeview(self.inventory_frame, columns=("ID", "Name", "Quantity", "Price"), show="headings")
        self.product_table.heading("ID", text="ID")
        self.product_table.heading("Name", text="Name")
        self.product_table.heading("Quantity", text="Quantity")
        self.product_table.heading("Price", text="Price")
        self.product_table.grid(row=1, column=0, columnspan=2, padx=10, pady=10)

        self.refresh_table()
        self.inventory_frame.pack()

    def refresh_table(self):
        for row in self.product_table.get_children():
            self.product_table.delete(row)

        for product in fetch_products():
            self.product_table.insert("", "end", values=product)

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

            if not name or not quantity.isdigit() or not price.replace(".", "").isdigit():
                messagebox.showerror("Error", "Invalid input!")
                return

            add_product(name, int(quantity), float(price))
            self.refresh_table()
            add_window.destroy()

        tk.Button(add_window, text="Save", command=save_product).grid(row=3, column=0, columnspan=2, pady=10)

    def low_stock_report(self):
        report_window = tk.Toplevel(self.root)
        report_window.title("Low-Stock Report")

        low_stock_items = low_stock_report()
        if not low_stock_items:
            tk.Label(report_window, text="No low-stock items found!").pack(padx=10, pady=10)
        else:
            for item in low_stock_items:
                tk.Label(report_window, text=f"ID: {item[0]}, Name: {item[1]}, Quantity: {item[2]}").pack(padx=10, pady=5)

# Initialize the database and run the app
if __name__ == "__main__":
    init_db()  # Ensure database is initialized
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()
