import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import mysql.connector
import bcrypt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime, timedelta
import calendar
from fpdf import FPDF
from PIL import Image, ImageTk
import logging
from mysql.connector import Error

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='finance_tracker.log'
)


class FinanceTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Finance Tracker")
        self.root.geometry("1200x800")

        # Initialize database connection
        self.db = None
        self.cursor = None
        self.connect_to_database()
        self.initialize_database()

        # Global variables
        self.current_user = None
        self.current_username = None

        # Categories
        self.EXPENSE_CATEGORIES = ["Travel", "Dining Out", "Shopping", "Entertainment",
                                   "Transportation", "Education", "Utilities", "Health"]
        self.INCOME_CATEGORIES = ["Rental", "Stock Income", "Social Security Benefit",
                                  "Wage", "Tips and Bonus", "Other Income"]

        # Color Scheme
        self.PRIMARY_COLOR = "#4e73df"
        self.SECONDARY_COLOR = "#1cc88a"
        self.DANGER_COLOR = "#e74a3b"
        self.WARNING_COLOR = "#f6c23e"
        self.DARK_COLOR = "#5a5c69"
        self.LIGHT_COLOR = "#f8f9fc"
        self.WHITE_COLOR = "#ffffff"

        # Fonts
        self.HEADER_FONT = ("Segoe UI", 16, "bold")
        self.LABEL_FONT = ("Segoe UI", 10)
        self.BUTTON_FONT = ("Segoe UI", 10, "bold")

        # Initialize UI
        self.setup_ui()
        self.login_screen()

    def setup_ui(self):
        """Initialize UI styles and settings"""
        try:
            self.root.iconbitmap('finance_icon.ico')
        except:
            pass

        style = ttk.Style()
        style.theme_use('clam')

        style.configure('TButton', font=self.BUTTON_FONT)
        style.configure('TCombobox', font=self.LABEL_FONT)
        style.configure('TEntry', font=self.LABEL_FONT)

    def connect_to_database(self):
        """Establish database connection"""
        try:
            self.db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="finance_tracker"
            )
            self.cursor = self.db.cursor()
            logging.info("Successfully connected to database")
        except Error as e:
            logging.error(f"Database connection failed: {e}")
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            self.root.destroy()

    def initialize_database(self):
        """Create required tables if they don't exist"""
        try:
            # Create users table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create transactions table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    type ENUM('Income', 'Expense') NOT NULL,
                    date DATE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create budgets table if not exists
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE (user_id, category)
                )
            """)

            self.db.commit()
            logging.info("Database tables initialized successfully")
        except Error as e:
            logging.error(f"Database initialization failed: {e}")
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

    # Helper Functions
    def hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def format_currency(self, amount):
        return f"${float(amount):,.2f}"

    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return amount
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number!")
            return None

    def validate_date(self, date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Error", "Invalid date format! Please use YYYY-MM-DD")
            return None

    # Login/Signup Screens
    def login_screen(self):
        """Display login screen"""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.PRIMARY_COLOR)

        # Main container with shadow effect
        main_frame = tk.Frame(self.root, bg=self.PRIMARY_COLOR)
        main_frame.pack(pady=50, padx=50, fill=tk.BOTH, expand=True)

        # Card with white background
        card = tk.Frame(main_frame, bg=self.WHITE_COLOR, bd=0, highlightthickness=0,
                        relief=tk.RAISED, padx=20, pady=20)
        card.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        card.grid_columnconfigure(0, weight=1)

        # Header
        header_frame = tk.Frame(card, bg=self.WHITE_COLOR)
        header_frame.grid(row=0, column=0, pady=(0, 20))

        tk.Label(header_frame, text="Finance Tracker", font=("Segoe UI", 18, "bold"),
                 bg=self.WHITE_COLOR, fg=self.DARK_COLOR).pack()

        # Form fields
        form_frame = tk.Frame(card, bg=self.WHITE_COLOR)
        form_frame.grid(row=1, column=0, sticky="nsew")

        tk.Label(form_frame, text="Username:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.entry_username = tk.Entry(form_frame, font=self.LABEL_FONT, bd=1, relief=tk.SOLID,
                                       highlightbackground="#cccccc", highlightthickness=1)
        self.entry_username.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        tk.Label(form_frame, text="Password:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=2, column=0, sticky="w", padx=10, pady=(10, 0))
        self.entry_password = tk.Entry(form_frame, font=self.LABEL_FONT, show="*", bd=1, relief=tk.SOLID,
                                       highlightbackground="#cccccc", highlightthickness=1)
        self.entry_password.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 20))

        # Buttons
        btn_frame = tk.Frame(card, bg=self.WHITE_COLOR)
        btn_frame.grid(row=2, column=0, pady=(10, 0))

        login_btn = tk.Button(btn_frame, text="Login", command=self.login,
                              bg=self.PRIMARY_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT,
                              bd=0, padx=25, pady=8, activebackground="#3a5fcd")
        login_btn.pack(side=tk.LEFT, padx=5)

        signup_btn = tk.Button(btn_frame, text="Sign Up", command=self.signup_screen,
                               bg=self.SECONDARY_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT,
                               bd=0, padx=25, pady=8, activebackground="#17a673")
        signup_btn.pack(side=tk.LEFT, padx=5)

        # Make the form responsive
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(0, weight=1)

        # Bind Enter key to login
        self.entry_password.bind('<Return>', lambda event: self.login())

    def signup_screen(self):
        """Display signup screen"""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.PRIMARY_COLOR)

        main_frame = tk.Frame(self.root, bg=self.PRIMARY_COLOR)
        main_frame.pack(pady=50, padx=50, fill=tk.BOTH, expand=True)

        card = tk.Frame(main_frame, bg=self.WHITE_COLOR, bd=0, highlightthickness=0,
                        relief=tk.RAISED, padx=20, pady=20)
        card.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        card.grid_columnconfigure(0, weight=1)

        header_frame = tk.Frame(card, bg=self.WHITE_COLOR)
        header_frame.grid(row=0, column=0, pady=(0, 20))

        tk.Label(header_frame, text="Create Account", font=("Segoe UI", 18, "bold"),
                 bg=self.WHITE_COLOR, fg=self.DARK_COLOR).pack()

        form_frame = tk.Frame(card, bg=self.WHITE_COLOR)
        form_frame.grid(row=1, column=0, sticky="nsew")

        tk.Label(form_frame, text="Username:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 0))
        self.entry_username = tk.Entry(form_frame, font=self.LABEL_FONT, bd=1, relief=tk.SOLID)
        self.entry_username.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))

        tk.Label(form_frame, text="Password:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=2, column=0, sticky="w", padx=10, pady=(10, 0))
        self.entry_password = tk.Entry(form_frame, font=self.LABEL_FONT, show="*", bd=1, relief=tk.SOLID)
        self.entry_password.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))

        tk.Label(form_frame, text="Confirm Password:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=4, column=0, sticky="w", padx=10, pady=(10, 0))
        self.entry_confirm_password = tk.Entry(form_frame, font=self.LABEL_FONT, show="*", bd=1, relief=tk.SOLID)
        self.entry_confirm_password.grid(row=5, column=0, sticky="ew", padx=10, pady=(0, 20))

        btn_frame = tk.Frame(card, bg=self.WHITE_COLOR)
        btn_frame.grid(row=2, column=0, pady=(10, 0))

        signup_btn = tk.Button(btn_frame, text="Sign Up", command=self.signup,
                               bg=self.SECONDARY_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT,
                               bd=0, padx=25, pady=8)
        signup_btn.pack(side=tk.LEFT, padx=5)

        back_btn = tk.Button(btn_frame, text="Back to Login", command=self.login_screen,
                             bg=self.DARK_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT,
                             bd=0, padx=25, pady=8)
        back_btn.pack(side=tk.LEFT, padx=5)

        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        form_frame.grid_columnconfigure(0, weight=1)

        # Bind Enter key to signup
        self.entry_confirm_password.bind('<Return>', lambda event: self.signup())

    def login(self):
        """Handle user login"""
        username = self.entry_username.get()
        password = self.entry_password.get()

        if not username or not password:
            messagebox.showerror("Error", "Username and password are required!")
            return

        try:
            self.cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            user = self.cursor.fetchone()

            if user and self.check_password(password, user[1]):
                self.current_user = user[0]
                self.current_username = username
                messagebox.showinfo("Success", "Login successful!")
                self.main_app()
            else:
                messagebox.showerror("Error", "Invalid username or password!")
        except Error as err:
            logging.error(f"Login failed: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    def signup(self):
        """Handle user signup"""
        username = self.entry_username.get()
        password = self.entry_password.get()
        confirm_password = self.entry_confirm_password.get()

        if not username or not password or not confirm_password:
            messagebox.showerror("Error", "All fields are required!")
            return

        if password != confirm_password:
            messagebox.showerror("Error", "Passwords do not match!")
            return

        if len(password) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long!")
            return

        try:
            self.cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = self.cursor.fetchone()

            if existing_user:
                messagebox.showerror("Error", "Username already exists!")
                return

            hashed_password = self.hash_password(password)
            self.cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                                (username, hashed_password))

            # Set default budgets for new user
            user_id = self.cursor.lastrowid
            for category in self.EXPENSE_CATEGORIES:
                self.cursor.execute(
                    "INSERT INTO budgets (user_id, category, amount) VALUES (%s, %s, %s)",
                    (user_id, category, 0)  # Default budget of 0
                )
            self.db.commit()

            messagebox.showinfo("Success", "Account created successfully!")
            self.login_screen()
        except Error as err:
            logging.error(f"Signup failed: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    # Main Application
    def main_app(self):
        """Main application screen"""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.configure(bg=self.LIGHT_COLOR)

        main_container = tk.Frame(self.root, bg=self.LIGHT_COLOR)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(main_container, bg=self.DARK_COLOR, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(sidebar, text="Finance Tracker", bg=self.DARK_COLOR, fg=self.WHITE_COLOR,
                 font=self.HEADER_FONT, pady=20).pack(fill=tk.X)

        nav_buttons = [
            ("Dashboard", self.show_dashboard),
            ("Transactions", self.show_transactions),
            ("Reports", self.show_reports),
            ("Budgets", self.show_budgets)
        ]

        for text, command in nav_buttons:
            btn = tk.Button(sidebar, text=text, command=command,
                            bg=self.DARK_COLOR, fg=self.WHITE_COLOR, bd=0,
                            font=self.BUTTON_FONT, anchor="w", padx=20)
            btn.pack(fill=tk.X, pady=5)

        user_frame = tk.Frame(sidebar, bg=self.DARK_COLOR)
        user_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        tk.Label(user_frame, text=f"Welcome, {self.current_username}",
                 bg=self.DARK_COLOR, fg=self.WHITE_COLOR, font=self.LABEL_FONT).pack(pady=5)
        tk.Button(user_frame, text="Logout", command=self.login_screen,
                  bg=self.DANGER_COLOR, fg=self.WHITE_COLOR, bd=0,
                  font=self.BUTTON_FONT).pack(pady=5)

        self.content_area = tk.Frame(main_container, bg=self.LIGHT_COLOR)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.show_dashboard()

    def clear_content_area(self):
        """Clear the content area"""
        for widget in self.content_area.winfo_children():
            widget.destroy()

    # Dashboard Functions
    def show_dashboard(self):
        """Display dashboard screen"""
        self.clear_content_area()

        tk.Label(self.content_area, text="Dashboard", font=self.HEADER_FONT,
                 bg=self.LIGHT_COLOR).pack(pady=20)

        summary_frame = tk.Frame(self.content_area, bg=self.LIGHT_COLOR)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)

        # Income Card
        income_card = tk.Frame(summary_frame, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        income_card.grid(row=0, column=0, padx=10, sticky="ew")
        header = tk.Frame(income_card, bg=self.PRIMARY_COLOR)
        header.pack(fill=tk.X)
        tk.Label(header, text="Income", font=("Segoe UI", 10, "bold"),
                 bg=self.PRIMARY_COLOR, fg=self.WHITE_COLOR).pack(pady=5)
        content = tk.Frame(income_card, bg=self.WHITE_COLOR)
        content.pack(fill=tk.BOTH, expand=True)
        self.income_label = tk.Label(content, text="$0.00", font=("Segoe UI", 24, "bold"),
                                     bg=self.WHITE_COLOR, fg=self.PRIMARY_COLOR)
        self.income_label.pack(pady=10)

        # Expense Card
        expense_card = tk.Frame(summary_frame, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        expense_card.grid(row=0, column=1, padx=10, sticky="ew")
        header = tk.Frame(expense_card, bg=self.DANGER_COLOR)
        header.pack(fill=tk.X)
        tk.Label(header, text="Expenses", font=("Segoe UI", 10, "bold"),
                 bg=self.DANGER_COLOR, fg=self.WHITE_COLOR).pack(pady=5)
        content = tk.Frame(expense_card, bg=self.WHITE_COLOR)
        content.pack(fill=tk.BOTH, expand=True)
        self.expense_label = tk.Label(content, text="$0.00", font=("Segoe UI", 24, "bold"),
                                      bg=self.WHITE_COLOR, fg=self.DANGER_COLOR)
        self.expense_label.pack(pady=10)

        # Balance Card
        balance_card = tk.Frame(summary_frame, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        balance_card.grid(row=0, column=2, padx=10, sticky="ew")
        header = tk.Frame(balance_card, bg=self.SECONDARY_COLOR)
        header.pack(fill=tk.X)
        tk.Label(header, text="Balance", font=("Segoe UI", 10, "bold"),
                 bg=self.SECONDARY_COLOR, fg=self.WHITE_COLOR).pack(pady=5)
        content = tk.Frame(balance_card, bg=self.WHITE_COLOR)
        content.pack(fill=tk.BOTH, expand=True)
        self.balance_label = tk.Label(content, text="$0.00", font=("Segoe UI", 24, "bold"),
                                      bg=self.WHITE_COLOR, fg=self.SECONDARY_COLOR)
        self.balance_label.pack(pady=10)

        # Budget Card
        budget_card = tk.Frame(summary_frame, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        budget_card.grid(row=0, column=3, padx=10, sticky="ew")
        header = tk.Frame(budget_card, bg=self.WARNING_COLOR)
        header.pack(fill=tk.X)
        tk.Label(header, text="Remaining Budget", font=("Segoe UI", 10, "bold"),
                 bg=self.WARNING_COLOR, fg=self.WHITE_COLOR).pack(pady=5)
        content = tk.Frame(budget_card, bg=self.WHITE_COLOR)
        content.pack(fill=tk.BOTH, expand=True)
        budget_top = tk.Frame(content, bg=self.WHITE_COLOR)
        budget_top.pack(fill=tk.X, pady=(10, 0))
        self.budget_label = tk.Label(budget_top, text="$0.00 / $5,000.00",
                                     font=("Segoe UI", 14), bg=self.WHITE_COLOR)
        self.budget_label.pack()
        self.budget_progress = ttk.Progressbar(content, orient="horizontal",
                                               length=100, mode="determinate")
        self.budget_progress.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Charts and Recent Transactions
        bottom_frame = tk.Frame(self.content_area, bg=self.LIGHT_COLOR)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Expense Chart
        chart_container = tk.Frame(bottom_frame, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        chart_container.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Label(chart_container, text="Monthly Finance", font=("Segoe UI", 12, "bold"),
                 bg=self.WHITE_COLOR).pack(pady=10)
        self.chart_frame = tk.Frame(chart_container, bg=self.LIGHT_COLOR)
        self.chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Recent Transactions
        trans_container = tk.Frame(bottom_frame, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        trans_container.grid(row=0, column=1, sticky="nsew")
        tk.Label(trans_container, text="Recent Transactions", font=("Segoe UI", 12, "bold"),
                 bg=self.WHITE_COLOR).pack(pady=10)

        trans_inner = tk.Frame(trans_container, bg=self.WHITE_COLOR)
        trans_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.recent_transactions_list = ttk.Treeview(
            trans_inner,
            columns=("ID", "Amount", "Category", "Type", "Date", "Description"),
            show="headings",
            height=5
        )

        self.recent_transactions_list.heading("ID", text="ID")
        self.recent_transactions_list.heading("Amount", text="Amount")
        self.recent_transactions_list.heading("Category", text="Category")
        self.recent_transactions_list.heading("Type", text="Type")
        self.recent_transactions_list.heading("Date", text="Date")
        self.recent_transactions_list.heading("Description", text="Description")

        self.recent_transactions_list.column("ID", width=30, anchor="center")
        self.recent_transactions_list.column("Amount", width=80, anchor="e")
        self.recent_transactions_list.column("Category", width=100, anchor="w")
        self.recent_transactions_list.column("Type", width=80, anchor="center")
        self.recent_transactions_list.column("Date", width=80, anchor="center")
        self.recent_transactions_list.column("Description", width=150, anchor="w")

        scrollbar = ttk.Scrollbar(trans_inner, orient="vertical",
                                  command=self.recent_transactions_list.yview)
        self.recent_transactions_list.configure(yscrollcommand=scrollbar.set)

        self.recent_transactions_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_frame.grid_columnconfigure(0, weight=3)
        bottom_frame.grid_columnconfigure(1, weight=2)
        bottom_frame.grid_rowconfigure(0, weight=1)

        self.recent_transactions_list.tag_configure('income', foreground='green')
        self.recent_transactions_list.tag_configure('expense', foreground='red')

        self.update_dashboard()

    def update_dashboard(self):
        """Update all dashboard widgets"""
        if not self.current_user:
            return

        self.update_summary_cards()
        self.update_expense_chart()
        self.update_recent_transactions()

    def update_summary_cards(self):
        """Update summary cards with latest data"""
        try:
            # Check if widgets still exist
            if not hasattr(self, 'income_label') or not self.income_label.winfo_exists():
                return

            # Total Income
            self.cursor.execute(
                """SELECT COALESCE(SUM(amount), 0) 
                FROM transactions 
                WHERE user_id = %s AND type = 'Income' AND MONTH(date) = MONTH(CURDATE())""",
                (self.current_user,))
            total_income = self.cursor.fetchone()[0]
            self.income_label.config(text=self.format_currency(total_income))

            # Total Expenses
            self.cursor.execute(
                """SELECT COALESCE(SUM(amount), 0) 
                FROM transactions 
                WHERE user_id = %s AND type = 'Expense' AND MONTH(date) = MONTH(CURDATE())""",
                (self.current_user,))
            total_expense = self.cursor.fetchone()[0]
            self.expense_label.config(text=self.format_currency(total_expense))

            # Balance
            balance = total_income - total_expense
            self.balance_label.config(text=self.format_currency(balance))
            self.balance_label.config(fg=self.SECONDARY_COLOR if balance >= 0 else self.DANGER_COLOR)

            # Monthly Budget Progress
            self.cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM budgets WHERE user_id = %s",
                (self.current_user,))
            budget = self.cursor.fetchone()[0] or 2500  # Default budget if not set

            remaining_budget = max(0, budget - total_expense)
            self.budget_label.config(
                text=f"{self.format_currency(remaining_budget)} / {self.format_currency(budget)}")
            self.budget_progress['value'] = (total_expense / budget) * 100 if budget > 0 else 0

        except Error as err:
            logging.error(f"Failed to update summary cards: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")
        except tk.TclError as e:
            logging.error(f"Widget error in update_summary_cards: {e}")

    def update_expense_chart(self):
        """Update expense chart with latest data"""
        try:
            self.cursor.execute(
                """SELECT category, SUM(amount) 
                FROM transactions 
                WHERE user_id = %s AND type = 'Expense' AND MONTH(date) = MONTH(CURDATE()) 
                GROUP BY category""",
                (self.current_user,))
            data = self.cursor.fetchall()

            if not data:
                for widget in self.chart_frame.winfo_children():
                    widget.destroy()
                tk.Label(self.chart_frame, text="No expense data available",
                         bg=self.LIGHT_COLOR).pack(expand=True)
                return

            categories = [row[0] for row in data]
            amounts = [row[1] for row in data]

            fig = plt.Figure(figsize=(5, 3), dpi=80, facecolor=self.LIGHT_COLOR)
            ax = fig.add_subplot(111)
            bars = ax.bar(categories, amounts, color=self.PRIMARY_COLOR)

            ax.set_title('Monthly Finance by Category', fontsize=10)
            ax.set_facecolor(self.LIGHT_COLOR)
            fig.patch.set_facecolor(self.LIGHT_COLOR)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f'${height:,.0f}',
                        ha='center', va='bottom', fontsize=8)

            for widget in self.chart_frame.winfo_children():
                widget.destroy()

            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        except Error as err:
            logging.error(f"Failed to update expense chart: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    def update_recent_transactions(self):
        """Update recent transactions list"""
        try:
            for row in self.recent_transactions_list.get_children():
                self.recent_transactions_list.delete(row)

            self.cursor.execute("""
                SELECT id, amount, category, type, date, description 
                FROM transactions 
                WHERE user_id = %s 
                ORDER BY date DESC LIMIT 5
            """, (self.current_user,))

            for row in self.cursor.fetchall():
                trans_id, amount, category, trans_type, date, description = row
                formatted_amount = self.format_currency(amount)

                # Handle both date strings and datetime objects
                if isinstance(date, str):
                    date_obj = datetime.strptime(date.split()[0], "%Y-%m-%d")
                else:  # datetime.date object
                    date_obj = date
                formatted_date = date_obj.strftime("%b %d")

                self.recent_transactions_list.insert("", "end", values=(
                    trans_id,
                    formatted_amount,
                    category,
                    trans_type,
                    formatted_date,
                    description
                ), tags=('income' if trans_type == 'Income' else 'expense'))

        except Error as err:
            logging.error(f"Failed to update recent transactions: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    # Transaction Functions
    def show_transactions(self):
        """Display transactions management screen"""
        self.clear_content_area()

        tk.Label(self.content_area, text="Transaction Management",
                 font=self.HEADER_FONT, bg=self.LIGHT_COLOR).pack(pady=20)

        form_frame = tk.Frame(self.content_area, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        form_frame.pack(fill=tk.X, padx=20, pady=10)

        tk.Label(form_frame, text="Add New Transaction", font=("Segoe UI", 12, "bold"),
                 bg=self.WHITE_COLOR).pack(pady=10)

        form_inner = tk.Frame(form_frame, bg=self.WHITE_COLOR)
        form_inner.pack(fill=tk.X, padx=10, pady=10)

        # Row 1
        tk.Label(form_inner, text="Amount:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_amount = tk.Entry(form_inner, font=self.LABEL_FONT, bd=1, relief=tk.SOLID)
        self.entry_amount.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        tk.Label(form_inner, text="Date (YYYY-MM-DD):", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=0, column=2, sticky="e", padx=5, pady=5)
        self.entry_date = tk.Entry(form_inner, font=self.LABEL_FONT, bd=1, relief=tk.SOLID)
        self.entry_date.grid(row=0, column=3, sticky="w", padx=5, pady=5)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Row 2
        tk.Label(form_inner, text="Category:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=1, column=0, sticky="e", padx=5, pady=5)
        self.category_var = tk.StringVar()
        category_dropdown = ttk.Combobox(form_inner, textvariable=self.category_var,
                                         values=self.EXPENSE_CATEGORIES + self.INCOME_CATEGORIES,
                                         font=self.LABEL_FONT)
        category_dropdown.grid(row=1, column=1, sticky="w", padx=5, pady=5)

        tk.Label(form_inner, text="Type:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=1, column=2, sticky="e", padx=5, pady=5)
        self.transaction_type_var = tk.StringVar()
        self.transaction_type_var.set("Expense")
        type_dropdown = ttk.Combobox(form_inner, textvariable=self.transaction_type_var,
                                     values=["Expense", "Income"],
                                     font=self.LABEL_FONT)
        type_dropdown.grid(row=1, column=3, sticky="w", padx=5, pady=5)

        # Update categories based on transaction type
        def update_categories(*args):
            if self.transaction_type_var.get() == "Income":
                category_dropdown['values'] = self.INCOME_CATEGORIES
            else:
                category_dropdown['values'] = self.EXPENSE_CATEGORIES
            self.category_var.set('')

        self.transaction_type_var.trace('w', update_categories)

        # Row 3
        tk.Label(form_inner, text="Description:", font=self.LABEL_FONT, bg=self.WHITE_COLOR).grid(
            row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_description = tk.Entry(form_inner, font=self.LABEL_FONT, bd=1, relief=tk.SOLID)
        self.entry_description.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5)

        btn_frame = tk.Frame(form_inner, bg=self.WHITE_COLOR)
        btn_frame.grid(row=3, column=0, columnspan=4, pady=10)

        tk.Button(btn_frame, text="Add Transaction", command=self.add_transaction,
                  bg=self.PRIMARY_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT, bd=0).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear Form", command=self.clear_form,
                  bg=self.DARK_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT, bd=0).pack(side=tk.LEFT, padx=5)

        # Transactions list
        list_frame = tk.Frame(self.content_area, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        tk.Label(list_frame, text="All Transactions", font=("Segoe UI", 12, "bold"),
                 bg=self.WHITE_COLOR).pack(pady=10)

        list_inner = tk.Frame(list_frame, bg=self.WHITE_COLOR)
        list_inner.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.transaction_list = ttk.Treeview(
            list_inner,
            columns=("ID", "Amount", "Category", "Type", "Date", "Description"),
            show="headings",
            height=15
        )

        self.transaction_list.heading("ID", text="ID")
        self.transaction_list.heading("Amount", text="Amount")
        self.transaction_list.heading("Category", text="Category")
        self.transaction_list.heading("Type", text="Type")
        self.transaction_list.heading("Date", text="Date")
        self.transaction_list.heading("Description", text="Description")

        self.transaction_list.column("ID", width=40, anchor="center")
        self.transaction_list.column("Amount", width=100, anchor="e")
        self.transaction_list.column("Category", width=120, anchor="w")
        self.transaction_list.column("Type", width=80, anchor="center")
        self.transaction_list.column("Date", width=100, anchor="center")
        self.transaction_list.column("Description", width=200, anchor="w")

        y_scroll = ttk.Scrollbar(list_inner, orient="vertical",
                                 command=self.transaction_list.yview)
        x_scroll = ttk.Scrollbar(list_inner, orient="horizontal",
                                 command=self.transaction_list.xview)
        self.transaction_list.configure(yscrollcommand=y_scroll.set,
                                        xscrollcommand=x_scroll.set)

        self.transaction_list.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        list_inner.grid_rowconfigure(0, weight=1)
        list_inner.grid_columnconfigure(0, weight=1)

        self.transaction_list.tag_configure('income', foreground='green')
        self.transaction_list.tag_configure('expense', foreground='red')
        self.transaction_list.tag_configure('income_total', foreground='dark green',
                                            font=('Segoe UI', 10, 'bold'))
        self.transaction_list.tag_configure('expense_total', foreground='dark red',
                                            font=('Segoe UI', 10, 'bold'))
        self.transaction_list.tag_configure('balance_total', foreground='blue',
                                            font=('Segoe UI', 10, 'bold'))

        self.view_transactions()

        btn_frame = tk.Frame(list_frame, bg=self.WHITE_COLOR)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="Delete Selected", command=self.delete_transaction,
                  bg=self.DANGER_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT, bd=0).pack(side=tk.LEFT, padx=5)

        tk.Button(btn_frame, text="Export to PDF", command=self.generate_pdf,
                  bg=self.PRIMARY_COLOR, fg=self.WHITE_COLOR, font=self.BUTTON_FONT, bd=0).pack(side=tk.LEFT, padx=5)

    def clear_form(self):
        """Clear the transaction form"""
        self.entry_amount.delete(0, tk.END)
        self.category_var.set('')
        self.transaction_type_var.set('Expense')
        self.entry_date.delete(0, tk.END)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_description.delete(0, tk.END)

    def add_transaction(self):
        """Add a new transaction"""
        # Validate amount
        amount = self.validate_amount(self.entry_amount.get())
        if amount is None:
            return

        category = self.category_var.get()
        transaction_type = self.transaction_type_var.get()
        date = self.validate_date(self.entry_date.get())
        if date is None:
            return

        description = self.entry_description.get()

        if not category or not transaction_type:
            messagebox.showerror("Error", "Category and Type are required!")
            return

        try:
            self.cursor.execute(
                """INSERT INTO transactions 
                (user_id, amount, category, type, date, description) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (self.current_user, amount, category, transaction_type, date, description)
            )
            self.db.commit()
            messagebox.showinfo("Success", "Transaction added successfully!")
            self.clear_form()
            self.view_transactions()
            self.update_dashboard()
        except Error as err:
            logging.error(f"Failed to add transaction: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    def delete_transaction(self):
        """Delete selected transaction"""
        selected_item = self.transaction_list.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a transaction to delete!")
            return

        transaction_id = self.transaction_list.item(selected_item)['values'][0]
        try:
            self.cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
            self.db.commit()
            messagebox.showinfo("Success", "Transaction deleted successfully!")
            self.view_transactions()
            self.update_dashboard()
        except Error as err:
            logging.error(f"Failed to delete transaction: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    def view_transactions(self):
        """View all transactions"""
        if not self.current_user:
            messagebox.showerror("Error", "No user logged in!")
            return

        for row in self.transaction_list.get_children():
            self.transaction_list.delete(row)

        try:
            self.cursor.execute("""
                SELECT id, amount, category, type, date, description 
                FROM transactions 
                WHERE user_id = %s 
                ORDER BY date DESC
            """, (self.current_user,))

            transactions = self.cursor.fetchall()
            total_income = 0
            total_expense = 0

            for row in transactions:
                trans_id, amount, category, trans_type, date, description = row
                formatted_amount = self.format_currency(amount)

                # Handle both date strings and datetime objects
                if isinstance(date, str):
                    date_obj = datetime.strptime(date.split()[0], "%Y-%m-%d")
                else:  # datetime.date object
                    date_obj = date
                formatted_date = date_obj.strftime("%Y-%m-%d")

                if trans_type == "Expense":
                    total_expense += amount
                else:
                    total_income += amount

                self.transaction_list.insert("", "end", values=(
                    trans_id,
                    formatted_amount,
                    category,
                    trans_type,
                    formatted_date,
                    description
                ), tags=('income' if trans_type == 'Income' else 'expense'))

            # Add total rows
            self.transaction_list.insert("", "end", values=(
                "", "", "", "INCOME:", self.format_currency(total_income), ""
            ), tags=('income_total'))

            self.transaction_list.insert("", "end", values=(
                "", "", "", "EXPENSE:", self.format_currency(total_expense), ""
            ), tags=('expense_total'))

            self.transaction_list.insert("", "end", values=(
                "", "", "", "BALANCE:", self.format_currency(total_income - total_expense), ""
            ), tags=('balance_total'))

        except Error as err:
            logging.error(f"Failed to view transactions: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    # Report Functions
    def show_reports(self):
        """Display reports screen"""
        self.clear_content_area()

        tk.Label(self.content_area, text="Financial Reports",
                 font=self.HEADER_FONT, bg=self.LIGHT_COLOR).pack(pady=20)

        reports_frame = tk.Frame(self.content_area, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        reports_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(reports_frame, text="Generate Reports", font=("Segoe UI", 12, "bold"),
                 bg=self.WHITE_COLOR).pack(pady=10)

        reports_inner = tk.Frame(reports_frame, bg=self.WHITE_COLOR)
        reports_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Monthly report section
        monthly_frame = tk.Frame(reports_inner, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        monthly_frame.pack(fill=tk.X, pady=10)

        tk.Label(monthly_frame, text="Monthly Finance Report",
                 font=("Segoe UI", 10, "bold"), bg=self.WHITE_COLOR).pack(pady=10)

        month_controls = tk.Frame(monthly_frame, bg=self.WHITE_COLOR)
        month_controls.pack(pady=10)

        tk.Label(month_controls, text="Select Month:",
                 font=self.LABEL_FONT, bg=self.WHITE_COLOR).pack(side=tk.LEFT, padx=5)
        self.month_var = tk.IntVar()
        self.month_var.set(datetime.now().month)
        month_dropdown = ttk.Combobox(month_controls, textvariable=self.month_var,
                                      values=[(i, calendar.month_name[i]) for i in range(1, 13)],
                                      font=self.LABEL_FONT)
        month_dropdown.pack(side=tk.LEFT, padx=5)

        tk.Button(monthly_frame, text="Generate Monthly Report",
                  command=self.generate_monthly_statement,
                  bg=self.PRIMARY_COLOR, fg=self.WHITE_COLOR,
                  font=self.BUTTON_FONT, bd=0).pack(pady=10)

        # Year-to-date report section
        ytd_frame = tk.Frame(reports_inner, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        ytd_frame.pack(fill=tk.X, pady=10)

        tk.Label(ytd_frame, text="Year-to-Date Finance Report",
                 font=("Segoe UI", 10, "bold"), bg=self.WHITE_COLOR).pack(pady=10)

        tk.Button(ytd_frame, text="Generate YTD Report",
                  command=self.generate_ytd_statement,
                  bg=self.SECONDARY_COLOR, fg=self.WHITE_COLOR,
                  font=self.BUTTON_FONT, bd=0).pack(pady=10)

    def generate_monthly_statement(self):
        """Generate monthly statement report"""
        month = self.month_var.get()
        if not 1 <= month <= 12:
            messagebox.showerror("Error", "Month must be between 1 and 12")
            return

        try:
            self.cursor.execute(
                """SELECT category, SUM(amount) 
                FROM transactions 
                WHERE user_id = %s AND MONTH(date) = %s AND type = 'Expense' 
                GROUP BY category""",
                (self.current_user, month))
            data = self.cursor.fetchall()

            if not data:
                messagebox.showinfo("No Data",
                                    f"No expense transactions found for {calendar.month_name[month]}")
                return

            categories = [row[0] for row in data]
            amounts = [row[1] for row in data]

            fig = plt.figure(figsize=(10, 6))
            ax = fig.add_subplot(111)
            bars = ax.bar(categories, amounts, color=self.PRIMARY_COLOR)

            ax.set_title(f"Monthly Finance Statement for {calendar.month_name[month]}",
                         fontsize=14)
            ax.set_ylabel("Amount Spent", fontsize=12)
            ax.set_facecolor(self.LIGHT_COLOR)
            fig.patch.set_facecolor(self.LIGHT_COLOR)
            plt.xticks(rotation=45, ha="right")

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2, height,
                        f"${height:,.2f}",
                        ha='center', va='bottom',
                        fontsize=10, color='black')

            plt.tight_layout()
            plt.show()

        except Error as err:
            logging.error(f"Failed to generate monthly statement: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    def generate_ytd_statement(self):
        """Generate year-to-date statement"""
        try:
            self.cursor.execute(
                """SELECT category, SUM(amount) 
                FROM transactions 
                WHERE user_id = %s AND YEAR(date) = YEAR(CURDATE()) AND type = 'Expense' 
                GROUP BY category""",
                (self.current_user,))
            data = self.cursor.fetchall()

            if not data:
                messagebox.showinfo("No Data",
                                    "No expense transactions found for the current year!")
                return

            categories = [row[0] for row in data]
            amounts = [row[1] for row in data]
            total_amount = sum(amounts)

            fig = plt.figure(figsize=(8, 6))
            ax = fig.add_subplot(111)

            colors = [self.PRIMARY_COLOR, self.SECONDARY_COLOR, self.WARNING_COLOR,
                      self.DANGER_COLOR, self.DARK_COLOR]
            wedges, texts, autotexts = ax.pie(
                amounts,
                labels=[f"{cat}\n${amt:,.0f}" for cat, amt in zip(categories, amounts)],
                autopct=lambda p: f"{p:.1f}%",
                startangle=140,
                colors=colors[:len(amounts)],
                textprops={'fontsize': 8}
            )

            ax.set_title(f"Year-to-Date Finance Statement\nTotal: ${total_amount:,.2f}",
                         fontsize=12)
            fig.patch.set_facecolor(self.LIGHT_COLOR)

            plt.show()

        except Error as err:
            logging.error(f"Failed to generate YTD statement: {err}")
            messagebox.showerror("Database Error", f"An error occurred: {err}")

    # Budget Functions
    def show_budgets(self):
        """Display budget management screen"""
        self.clear_content_area()

        tk.Label(self.content_area, text="Budget Management",
                 font=self.HEADER_FONT, bg=self.LIGHT_COLOR).pack(pady=20)

        budget_frame = tk.Frame(self.content_area, bg=self.WHITE_COLOR, bd=1, relief=tk.SOLID)
        budget_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        tk.Label(budget_frame, text="Set Monthly Budgets",
                 font=("Segoe UI", 12, "bold"), bg=self.WHITE_COLOR).pack(pady=10)

        budget_inner = tk.Frame(budget_frame, bg=self.WHITE_COLOR)
        budget_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Load existing budgets
        try:
            self.cursor.execute(
                "SELECT category, amount FROM budgets WHERE user_id = %s",
                (self.current_user,))
            budgets = {row[0]: row[1] for row in self.cursor.fetchall()}
        except Error as err:
            logging.error(f"Failed to load budgets: {err}")
            messagebox.showerror("Database Error", f"Failed to load budgets: {err}")
            return

        self.budget_vars = {}

        # Create budget entries for each expense category
        for i, category in enumerate(self.EXPENSE_CATEGORIES):
            row_frame = tk.Frame(budget_inner, bg=self.WHITE_COLOR)
            row_frame.grid(row=i, column=0, sticky="ew", pady=5)

            tk.Label(row_frame, text=category, font=self.LABEL_FONT,
                     bg=self.WHITE_COLOR, width=20, anchor="w").pack(side=tk.LEFT, padx=5)

            var = tk.StringVar(value=str(budgets.get(category, 0)))
            self.budget_vars[category] = var

            entry = tk.Entry(row_frame, textvariable=var, font=self.LABEL_FONT,
                             bd=1, relief=tk.SOLID, width=15)
            entry.pack(side=tk.LEFT, padx=5)

            tk.Label(row_frame, text="$", font=self.LABEL_FONT,
                     bg=self.WHITE_COLOR).pack(side=tk.LEFT)

        # Save button
        btn_frame = tk.Frame(budget_inner, bg=self.WHITE_COLOR)
        btn_frame.grid(row=len(self.EXPENSE_CATEGORIES), column=0, pady=20)

        tk.Button(btn_frame, text="Save Budgets", command=self.save_budgets,
                  bg=self.PRIMARY_COLOR, fg=self.WHITE_COLOR,
                  font=self.BUTTON_FONT, bd=0).pack()

    def save_budgets(self):
        """Save budget amounts"""
        try:
            for category, var in self.budget_vars.items():
                amount = self.validate_amount(var.get())
                if amount is None:
                    return

                self.cursor.execute(
                    """INSERT INTO budgets (user_id, category, amount) 
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE amount = %s""",
                    (self.current_user, category, amount, amount)
                )

            self.db.commit()
            messagebox.showinfo("Success", "Budgets saved successfully!")
            self.update_dashboard()
        except Error as err:
            logging.error(f"Failed to save budgets: {err}")
            messagebox.showerror("Database Error", f"Failed to save budgets: {err}")

    # PDF Generation
    def generate_pdf(self):
        """Generate PDF report of transactions"""
        try:
            # Get transactions data
            self.cursor.execute("""
                SELECT date, amount, category, type, description 
                FROM transactions 
                WHERE user_id = %s 
                ORDER BY date DESC
            """, (self.current_user,))
            transactions = self.cursor.fetchall()

            if not transactions:
                messagebox.showinfo("No Data", "No transactions found to export!")
                return

            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title="Save PDF As"
            )

            if not file_path:
                return  # User cancelled

            # Create PDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)

            # Title
            pdf.cell(0, 10, f"Financial Report for {self.current_username}", 0, 1, 'C')
            pdf.ln(10)

            # Summary
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Transaction Summary", 0, 1)
            pdf.set_font("Arial", '', 10)

            # Get summary data
            self.cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = %s AND type = 'Income'",
                (self.current_user,))
            total_income = self.cursor.fetchone()[0]

            self.cursor.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE user_id = %s AND type = 'Expense'",
                (self.current_user,))
            total_expense = self.cursor.fetchone()[0]

            balance = total_income - total_expense

            pdf.cell(0, 6, f"Total Income: {self.format_currency(total_income)}", 0, 1)
            pdf.cell(0, 6, f"Total Expenses: {self.format_currency(total_expense)}", 0, 1)
            pdf.cell(0, 6, f"Balance: {self.format_currency(balance)}", 0, 1)
            pdf.ln(10)

            # Transactions table
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "Transaction Details", 0, 1)
            pdf.set_font("Arial", 'B', 10)

            # Table header
            pdf.cell(30, 6, "Date", 1)
            pdf.cell(25, 6, "Amount", 1)
            pdf.cell(30, 6, "Category", 1)
            pdf.cell(25, 6, "Type", 1)
            pdf.cell(80, 6, "Description", 1)
            pdf.ln()

            # Table rows
            pdf.set_font("Arial", '', 8)
            for row in transactions:
                date, amount, category, trans_type, description = row

                # Handle date formatting
                if isinstance(date, str):
                    date_str = date.split()[0]
                else:
                    date_str = date.strftime("%Y-%m-%d")

                pdf.cell(30, 6, date_str, 1)
                pdf.cell(25, 6, self.format_currency(amount), 1)
                pdf.cell(30, 6, category, 1)
                pdf.cell(25, 6, trans_type, 1)
                pdf.cell(80, 6, description or "", 1)
                pdf.ln()

            # Save PDF
            pdf.output(file_path)
            messagebox.showinfo("Success", f"PDF report saved successfully at:\n{file_path}")

        except Exception as e:
            logging.error(f"Failed to generate PDF: {e}")
            messagebox.showerror("Error", f"Failed to generate PDF: {str(e)}")


# Main application entry point
if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceTracker(root)
    root.mainloop()