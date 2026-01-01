from flask import Flask, request, jsonify, render_template
import osint_modules

app = Flask(__name__, template_folder='.')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form.get('query')
    depth = request.form.get('depth', 2)
    
    if not query:
        return jsonify([])

    # Call the function from our new module
    results = osint_modules.run_osint_scan(query, depth)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
