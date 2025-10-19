import os
from flask import Flask, render_template, request, redirect, url_for, flash
import excel_Day2  # আপনার মূল এক্সেল লজিক ফাইল
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_for_flash_messages'  # একটি সিক্রেট কী সেট করুন

# --- ড্যাশবোর্ড / হোম পেজ ---
@app.route('/')
def index():
    # আপনার index.html পেজটি রেন্ডার করবে
    return render_template('index.html')

# --- অ্যাকাউন্ট তৈরি ---
@app.route('/create', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        try:
            # ফর্ম থেকে ডেটা সংগ্রহ
            name = request.form['name']
            acc_no = request.form['acc_no']
            balance = float(request.form['balance'])
            aadhar_no = request.form['aadhar_no']
            mail_id = request.form['mail_id']
            dob = request.form['dob']
            address = request.form['address']

            # excel_Day2.py থেকে ফাংশন কল
            if excel_Day2.create_new_account(acc_no, name, balance, aadhar_no, mail_id, dob, address):
                flash(f"Account created successfully for {name}!", 'success')
            else:
                flash("Account already exists!", 'danger')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        
        return redirect(url_for('create_account'))

    return render_template('create_account.html')

# --- টাকা জমা (Deposit) ---
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        try:
            acc_no = request.form['acc_no']
            amount = float(request.form['amount'])
            file_path = excel_Day2.GetAccount(acc_no)

            if not os.path.exists(file_path):
                flash("Account does not exist!", 'danger')
                return redirect(url_for('deposit'))

            balance = excel_Day2.get_balance(file_path)
            new_balance = balance + amount

            excel_Day2.update_balance(file_path, new_balance)
            excel_Day2.save_transaction(file_path, "Deposit", amount, new_balance)
            flash(f"Deposited {amount} successfully. New Balance: {new_balance}", 'success')
        
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')

        return redirect(url_for('deposit'))
    
    return render_template('deposit.html')

# --- টাকা তোলা (Withdraw) ---
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        try:
            acc_no = request.form['acc_no']
            amount = float(request.form['amount'])
            file_path = excel_Day2.GetAccount(acc_no)

            if not os.path.exists(file_path):
                flash("Account does not exist!", 'danger')
                return redirect(url_for('withdraw'))

            balance = excel_Day2.get_balance(file_path)
            
            if amount > balance:
                flash("Insufficient funds!", 'danger')
            else:
                new_balance = balance - amount
                excel_Day2.update_balance(file_path, new_balance)
                excel_Day2.save_transaction(file_path, "Withdraw", amount, new_balance)
                flash(f"Withdrew {amount} successfully. New Balance: {new_balance}", 'success')
        
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        
        return redirect(url_for('withdraw'))

    return render_template('withdraw.html')

# --- ব্যালেন্স চেক ---
@app.route('/balance', methods=['GET', 'POST'])
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

    return render_template('check_balance.html', balance=None, acc_no=None)

# --- লেনদেন (Transactions) ---
@app.route('/transactions', methods=['GET', 'POST'])
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
    
    return render_template('transactions.html', transactions=transactions, acc_no=acc_no_checked)


# অ্যাপটি চালানোর জন্য
if __name__ == '__main__':
    app.run(debug=True)