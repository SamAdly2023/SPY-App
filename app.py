from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from authlib.integrations.flask_client import OAuth
import osint_modules
import db
import paypalrestsdk
import os

app = Flask(__name__, template_folder='.')
app.secret_key = "super_secret_key_for_dev_only" # Static key to prevent session invalidation on restart
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # Allow OAuth over HTTP for dev

# Configuration
GOOGLE_CLIENT_ID = "241819621736-ph4v79l869g1p5mnhsoiaagei8fn2fef.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"

# Configure PayPal
paypalrestsdk.configure({
  "mode": "sandbox", 
  "client_id": "AarwkYK4lzBjwzF7OCgJeoRBnGAZehBAsNrEyrQZSdzu7yyPH3P7qEm0qtm-VNj_SvYFPpKA9PjZqO2G",
  "client_secret": "EIrQs5idryj4M61B1A2sA2EUAEasToLqgB7GiEAULjEhh6Ncj35X75v6DgpIgieisDuiXkHXqs_1oWyF"
})

# Initialize Database
db.init_db()

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Setup OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.name = user_data['name']
        self.email = user_data['email']
        self.profile_pic = user_data['profile_pic']
        self.credits = user_data['credits']
        self.role = user_data.get('role', 'user')

    @property
    def is_admin(self):
        return self.role == 'admin'

@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user(user_id)
    if user_data:
        return User(user_data)
    return None

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login/google')
def google_login():
    redirect_uri = url_for('google_authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/google/callback')
def google_authorize():
    token = google.authorize_access_token()
    user_info = google.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
    user_id = db.create_or_update_user(user_info)
    user = load_user(user_id)
    login_user(user)
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/history_page')
@login_required
def history_page():
    return render_template('history.html', user=current_user)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
    
    users = db.get_all_users()
    history = db.get_all_history()
    return render_template('admin.html', user=current_user, users=users, history=history)

@app.route('/admin/add_credits', methods=['POST'])
@login_required
def admin_add_credits():
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    
    user_id = request.form.get('user_id')
    amount = int(request.form.get('amount'))
    
    db.update_credits(user_id, amount)
    return jsonify({"success": True})

@app.route('/terms')
def terms():
    return render_template('terms.html', user=current_user if current_user.is_authenticated else None)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', user=current_user if current_user.is_authenticated else None)

@app.route('/create_payment', methods=['POST'])
@login_required
def create_payment():
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": url_for('execute_payment', _external=True),
            "cancel_url": url_for('dashboard', _external=True)
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "100 Credits",
                    "sku": "credits_100",
                    "price": "10.00",
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": "10.00",
                "currency": "USD"
            },
            "description": "Purchase 100 OSINT Credits."
        }]
    })

    if payment.create():
        return jsonify({"paymentID": payment.id})
    else:
        return jsonify({"error": payment.error}), 500

@app.route('/execute_payment', methods=['GET'])
@login_required
def execute_payment():
    payment_id = request.args.get('paymentId')
    payer_id = request.args.get('PayerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        # Add credits to user
        db.update_credits(current_user.id, 100)
        return redirect(url_for('dashboard'))
    else:
        return jsonify({"error": payment.error}), 500

@app.route('/history')
@login_required
def history_api():
    return jsonify(db.get_history(current_user.id))

@app.route('/search', methods=['POST'])
@login_required
def search():
    query = request.form.get('query')
    level = request.form.get('level', 'surface')
    
    # Define costs and depths based on level
    costs = {'surface': 1, 'deep': 3, 'extreme': 5}
    depths = {'surface': 2, 'deep': 6, 'extreme': 10}
    
    cost = costs.get(level, 1)
    depth = depths.get(level, 2)

    if current_user.credits < cost:
        return jsonify({"error": "Insufficient credits"}), 403
    
    if not query:
        return jsonify([])

    results = osint_modules.run_osint_scan(query, depth)
    
    db.add_history(current_user.id, query, len(results))
    db.update_credits(current_user.id, -cost) 
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
