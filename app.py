from flask import Flask, render_template, request, redirect, url_for, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    """Renders the main upload page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_csv():
    """Handles the CSV file upload and processing."""
    # Placeholder for file handling and processing logic
    return redirect(url_for('index'))

@app.route('/download/template')
def download_template():
    """Serves the template CSV file for download."""
    return send_from_directory('data', 'template.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
