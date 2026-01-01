from flask import Flask, request, jsonify, render_template
import osint_modules
import db

app = Flask(__name__, template_folder='.')

# Initialize Database
db.init_db()

@app.route('/')
def index():
    return render_template('index.html')

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
