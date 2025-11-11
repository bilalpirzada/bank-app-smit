from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'  # Required for sessions

# In-memory storage (lost when server restarts)
accounts = []

# Helper Functions
def find_account(account_number):
    """Find account by account number"""
    for account in accounts:
        if account["number"] == account_number:
            return account
    return None

def validate_pin(pin):
    """Validate 4-digit PIN"""
    return pin.isdigit() and len(pin) == 4

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'account_number' not in session:
            flash('Please login first!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        pin = request.form.get('pin', '').strip()
        initial_deposit = request.form.get('initial_deposit', '0')
        
        # Validation
        if not name:
            flash('Name cannot be empty!', 'error')
            return render_template('create_account.html')
        
        if not validate_pin(pin):
            flash('PIN must be exactly 4 digits!', 'error')
            return render_template('create_account.html')
        
        try:
            amount = float(initial_deposit)
            if amount < 0:
                flash('Initial deposit cannot be negative!', 'error')
                return render_template('create_account.html')
        except ValueError:
            flash('Invalid amount!', 'error')
            return render_template('create_account.html')
        
        # Create account
        account_number = len(accounts) + 1
        new_account = {
            "number": account_number,
            "name": name,
            "pin": pin,
            "balance": amount
        }
        accounts.append(new_account)
        
        flash(f'Account created successfully! Your account number is: {account_number}', 'success')
        return redirect(url_for('login'))
    
    return render_template('create_account.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            account_number = int(request.form.get('account_number', 0))
        except ValueError:
            flash('Invalid account number!', 'error')
            return render_template('login.html')
        
        pin = request.form.get('pin', '').strip()
        
        account = find_account(account_number)
        
        if account is None:
            flash('Account not found!', 'error')
            return render_template('login.html')
        
        if account['pin'] != pin:
            flash('Incorrect PIN!', 'error')
            return render_template('login.html')
        
        # Login successful
        session['account_number'] = account_number
        flash(f'Welcome back, {account["name"]}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    account = find_account(session['account_number'])
    return render_template('dashboard.html', account=account)

@app.route('/deposit', methods=['POST'])
@login_required
def deposit():
    account = find_account(session['account_number'])
    
    try:
        amount = float(request.form.get('amount', 0))
        if amount <= 0:
            flash('Amount must be positive!', 'error')
        else:
            account['balance'] += amount
            flash(f'Successfully deposited PKR {amount:.2f}', 'success')
    except ValueError:
        flash('Invalid amount!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw():
    account = find_account(session['account_number'])
    
    try:
        amount = float(request.form.get('amount', 0))
        if amount <= 0:
            flash('Amount must be positive!', 'error')
        elif amount > account['balance']:
            flash(f'Not enough balance! Current balance: PKR {account["balance"]:.2f}', 'error')
        else:
            account['balance'] -= amount
            flash(f'Successfully withdrawn PKR {amount:.2f}', 'success')
    except ValueError:
        flash('Invalid amount!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/transfer', methods=['POST'])
@login_required
def transfer():
    sender = find_account(session['account_number'])
    
    try:
        receiver_number = int(request.form.get('receiver_account', 0))
        amount = float(request.form.get('amount', 0))
        
        if receiver_number == sender['number']:
            flash('Cannot transfer to your own account!', 'error')
        elif amount <= 0:
            flash('Amount must be positive!', 'error')
        else:
            receiver = find_account(receiver_number)
            if receiver is None:
                flash('Receiver account not found!', 'error')
            elif amount > sender['balance']:
                flash(f'Not enough balance! Current balance: PKR {sender["balance"]:.2f}', 'error')
            else:
                sender['balance'] -= amount
                receiver['balance'] += amount
                flash(f'Successfully transferred PKR {amount:.2f} to {receiver["name"]}', 'success')
    except ValueError:
        flash('Invalid input!', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('account_number', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)