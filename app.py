from flask import Flask, request, jsonify, render_template
import osint_modules
import db
import paypalrestsdk

app = Flask(__name__, template_folder='.')

# Configure PayPal
paypalrestsdk.configure({
  "mode": "sandbox", # Change to "live" for production
  "client_id": "AarwkYK4lzBjwzF7OCgJeoRBnGAZehBAsNrEyrQZSdzu7yyPH3P7qEm0qtm-VNj_SvYFPpKA9PjZqO2G",
  "client_secret": "EIrQs5idryj4M61B1A2sA2EUAEasToLqgB7GiEAULjEhh6Ncj35X75v6DgpIgieisDuiXkHXqs_1oWyF"
})

# Initialize Database
db.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/create_payment', methods=['POST'])
def create_payment():
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "redirect_urls": {
            "return_url": "http://localhost:5000/payment/execute",
            "cancel_url": "http://localhost:5000/payment/cancel"
        },
        "transactions": [{
            "item_list": {
                "items": [{
                    "name": "OSINT Export",
                    "sku": "export_001",
                    "price": "10.00",
                    "currency": "USD",
                    "quantity": 1
                }]
            },
            "amount": {
                "total": "10.00",
                "currency": "USD"
            },
            "description": "Export OSINT search results."
        }]
    })

    if payment.create():
        return jsonify({"paymentID": payment.id})
    else:
        return jsonify({"error": payment.error}), 500

@app.route('/execute_payment', methods=['POST'])
def execute_payment():
    payment_id = request.json.get('paymentID')
    payer_id = request.json.get('payerID')

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": payment.error}), 500

@app.route('/history')
def history():
    return jsonify(db.get_history())

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    depth = request.form.get('depth', 2)
    
    if not query:
        return jsonify([])

    # Call the function from our new module
    results = osint_modules.run_osint_scan(query, depth)
    
    # Save to history
    db.add_history(query, len(results))
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
