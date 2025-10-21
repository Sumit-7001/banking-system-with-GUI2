import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
import excel_Day2 
from datetime import datetime
from functools import wraps
from fpdf import FPDF  
from flask import make_response 

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_for_flash_messages'


# --- PDF তৈরির জন্য হেলপার ক্লাস ---
class PDF(FPDF):
    def header(self):
        # লোগো বা ব্যাঙ্কের নাম
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'BRAINWARE BAKWAS BANK', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Transaction Statement', 0, 1, 'C')
        self.ln(10) # লাইন ব্রেক

    def footer(self):
        # পেজ নম্বর
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def print_account_info(self, name, acc_no):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, f'Account Holder: {name}', 0, 1, 'L')
        self.cell(0, 10, f'Account Number: {acc_no}', 0, 1, 'L')
        self.ln(5)

    def print_transaction_table(self, transactions):
        # টেবিল হেডার
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(230, 230, 230) # হালকা ধূসর
        self.cell(50, 10, 'Date', 1, 0, 'C', True)
        self.cell(30, 10, 'Type', 1, 0, 'C', True)
        self.cell(40, 10, 'Amount (INR)', 1, 0, 'C', True)
        self.cell(40, 10, 'New Balance', 1, 1, 'C', True)
        
        # টেবিল ডেটা
        self.set_font('Arial', '', 9)
        # লেনদেনগুলি উল্টে নেওয়া হচ্ছে (পুরনো > নতুন)
        for tx in reversed(transactions):
            self.cell(50, 8, str(tx['date']), 1)
            
            # Deposit/Withdraw অনুযায়ী রঙ
            if tx['type'] == 'Deposit':
                self.set_text_color(0, 100, 0) # সবুজ
                amount_str = f"+ {tx['amount']}"
            else:
                self.set_text_color(220, 50, 50) # লাল
                amount_str = f"- {tx['amount']}"
                
            self.cell(30, 8, str(tx['type']), 1)
            self.cell(40, 8, amount_str, 1, 0, 'R')
            
            self.set_text_color(0, 0, 0) # রঙ রিসেট
            self.cell(40, 8, str(tx['balance']), 1, 1, 'R')
# ------------------------------------

USERS_DB = {
    "sumit": {
        "password": "pass123",
        "full_name": "Sumit Sahoo",
        "image": "s1.jpg"  
    },
    "moumi": { 
        "password": "moumi123", 
        "full_name": "Moumi",
        "image": "moumi.jpeg" 
    },
    "rudra": {
        "password": "rudra123",
        "full_name": "Rudra",
        "image": "jeet.jpg" 
    },
    "user1": {
        "password": "pass1",
        "full_name": "User One",
        "image": None
    },
    "user2": {
        "password": "pass2",
        "full_name": "User Two",
        "image": None
    }
}

# --- লগইন ডেকোরেটর ---
# এই ফাংশনটি চেক করবে ব্যবহারকারী লগইন করেছেন কিনা
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash("Please log in to access this page.", 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- লগইন পেজ ---
# --- লগইন পেজ ---
@app.route('/', methods=['GET', 'POST'])
def login():
    # যদি ব্যবহারকারী ইতিমধ্যে লগইন করে থাকেন, তাকে ড্যাশবোর্ডে পাঠানো হবে
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # USERS_DB থেকে ব্যবহারকারীকে খুঁজুন
        if username in USERS_DB:
            user_data = USERS_DB[username]
            
            # পাসওয়ার্ড চেক করুন
            if user_data['password'] == password:
                # সেশনে ব্যবহারকারীর সব তথ্য সেভ করুন
                session['username'] = username
                session['full_name'] = user_data['full_name']
                session['image_file'] = user_data['image']
                # সেশনে ব্যবহারকারীর সব তথ্য সেভ করুন
                session['username'] = username
                session['full_name'] = user_data['full_name']
                session['image_file'] = user_data['image']
                
                # --- এই নতুন লাইনটি যোগ করুন ---
                session['session_transaction_total'] = 0.0
                # ---------------------------------
                flash(f"Welcome back, {session['full_name']}!", 'success')
                return redirect(url_for('dashboard'))

        # লগইন ব্যর্থ হলে
        flash("Invalid username or password. Please try again.", 'danger')
        return redirect(url_for('login'))
        
    return render_template('login.html')

# --- লগআউট ---
@app.route('/logout')
def logout():
    session.pop('username', None) # সেশন থেকে ব্যবহারকারীর নাম মুছে ফেলা হচ্ছে
    session.pop('session_transaction_total', None)
    flash("You have been logged out successfully.", 'info')
    return redirect(url_for('login'))

# --- ড্যাশবোর্ড / হোম পেজ ---
@app.route('/dashboard')
@login_required # এই পেজটি অ্যাক্সেস করার জন্য লগইন আবশ্যক
def dashboard():
    # লগইন করা অ্যাডমিনের ইউজারনেম দিয়ে তার লগ ফাইল থেকে ডেটা আনবে
    activities = excel_Day2.get_all_recent_activities(session['username'], 5)
    return render_template('index.html', recent_activities=activities)
# --- অ্যাকাউন্ট তৈরি ---
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_account():
    if request.method == 'POST':
        try:
            name = request.form['name']
            acc_no = request.form['acc_no']
            balance = float(request.form['balance'])
            aadhar_no = request.form['aadhar_no']
            mail_id = request.form['mail_id']
            dob = request.form['dob']
            address = request.form['address']
            
            if excel_Day2.create_new_account(acc_no, name, balance, aadhar_no, mail_id, dob, address):
                flash(f"Account created successfully for {name}!", 'success')
            if excel_Day2.create_new_account(acc_no, name, balance, aadhar_no, mail_id, dob, address):
                flash(f"Account created successfully for {name}!", 'success')
                # --- এই নতুন লাইনটি যোগ করুন ---
                excel_Day2.save_admin_transaction(session['username'], "New Account", acc_no, balance)
                # ---------------------------------
            else:
                flash("Account already exists!", 'danger')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('create_account'))
    return render_template('create_account.html')

# --- টাকা জমা (Deposit) ---
@app.route('/deposit', methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        try:
            acc_no = request.form['acc_no']
            amount = float(request.form['amount'])
            file_path = excel_Day2.GetAccount(acc_no)

            if not os.path.exists(file_path):
                flash("Account does not exist!", 'danger')
            else:
                balance = excel_Day2.get_balance(file_path)
                new_balance = balance + amount
                excel_Day2.update_balance(file_path, new_balance)
                excel_Day2.save_transaction(file_path, "Deposit", amount, new_balance)
                session['session_transaction_total'] = session.get('session_transaction_total', 0.0) + amount
                # ---------------------------------
                excel_Day2.save_admin_transaction(session['username'], "Deposit", acc_no, amount)
                flash(f"Deposited {amount} successfully. New Balance: {new_balance}", 'success')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('deposit'))
    return render_template('deposit.html')

# --- টাকা তোলা (Withdraw) ---
@app.route('/withdraw', methods=['GET', 'POST'])
@login_required
def withdraw():
    if request.method == 'POST':
        try:
            acc_no = request.form['acc_no']
            amount = float(request.form['amount'])
            file_path = excel_Day2.GetAccount(acc_no)

            if not os.path.exists(file_path):
                flash("Account does not exist!", 'danger')
            else:
                balance = excel_Day2.get_balance(file_path)
                if amount > balance:
                    flash("Insufficient funds!", 'danger')
                else:
                    new_balance = balance - amount
                    excel_Day2.update_balance(file_path, new_balance)
                    excel_Day2.save_transaction(file_path, "Withdraw", amount, new_balance)
                    session['session_transaction_total'] = session.get('session_transaction_total', 0.0) + amount
                     # ---------------------------------
                    excel_Day2.save_admin_transaction(session['username'], "Withdraw", acc_no, amount)
                    flash(f"Withdrew {amount} successfully. New Balance: {new_balance}", 'success')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        return redirect(url_for('withdraw'))
    return render_template('withdraw.html')

# --- ব্যালেন্স চেক ---
@app.route('/balance', methods=['GET', 'POST'])
@login_required
def check_balance():
    balance = None
    acc_no_checked = None
    if request.method == 'POST':
        try:
            acc_no = request.form['acc_no']
            file_path = excel_Day2.GetAccount(acc_no)
            acc_no_checked = acc_no
            if not os.path.exists(file_path):
                flash("Account does not exist!", 'danger')
            else:
                balance = excel_Day2.get_balance(file_path)
                flash(f"Current balance for {acc_no} is: {balance}", 'success')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
    return render_template('check_balance.html', balance=balance, acc_no=acc_no_checked)

# --- লেনদেন (Transactions) ---
@app.route('/transactions', methods=['GET', 'POST'])
@login_required
def show_transactions():
    transactions = []
    acc_no_checked = None
    if request.method == 'POST':
        try:
            acc_no = request.form['acc_no']
            file_path = excel_Day2.GetAccount(acc_no)
            acc_no_checked = acc_no
            if not os.path.exists(file_path):
                flash("Account does not exist!", 'danger')
            else:
                transactions = excel_Day2.get_last_transactions(file_path, 5)
                if not transactions:
                    flash("No transactions found.", 'info')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
    return render_template('transactions.html', transactions=transactions, acc_no_checked=acc_no_checked)

# --- PDF প্রিন্ট রুট ---
@app.route('/print/<acc_no>')
@login_required
def print_transactions(acc_no):
    try:
        file_path = excel_Day2.GetAccount(acc_no)
        if not os.path.exists(file_path):
            flash("Account not found, cannot generate PDF.", 'danger')
            return redirect(url_for('show_transactions'))

        # এক্সেল থেকে ডেটা আনুন
        details = excel_Day2.get_account_details(file_path)
        transactions = excel_Day2.get_all_transactions(file_path)

        if not transactions:
            flash("No transactions found to print.", 'info')
            return redirect(url_for('show_transactions'))

        # PDF তৈরি করুন
        pdf = PDF()
        pdf.add_page()
        pdf.print_account_info(details['name'], details['acc_no'])
        pdf.print_transaction_table(transactions)
        
        # PDF ফাইলটি ব্রাউজারে দেখানোর জন্য প্রস্তুত করুন
        pdf_bytes = pdf.output(dest='B')
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=transactions_{acc_no}.pdf'
        
        return response

    except Exception as e:
        flash(f"An error occurred while generating PDF: {e}", 'danger')
        return redirect(url_for('show_transactions'))

if __name__ == '__main__':
    app.run(debug=True)