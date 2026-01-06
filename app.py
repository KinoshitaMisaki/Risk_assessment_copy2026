import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'

@app.route('/')
def index():
    """Renders the main upload page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_csv():
    """Handles the CSV file upload and processing."""
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        df = pd.read_csv(filepath)

        # For now, just pass the raw data to the results page
        data = df.to_dict(orient='records')
        columns = df.columns.tolist()

        return render_template('result.html', data=data, columns=columns)

@app.route('/download/template')
def download_template():
    """Serves the template CSV file for download."""
    return send_from_directory('data', 'template.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
