# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, make_response, json
from data import CHEMICAL_DATABASE, OPTIONS
from logic import calculate_inhalation_risk
from datetime import datetime
import pandas as pd
import io

app = Flask(__name__)

# Helper to find chemical ID by CAS number for batch processing
def find_chem_id_by_cas(cas):
    for chem in CHEMICAL_DATABASE:
        if chem['cas'] == cas:
            return chem['id']
    return None

@app.route('/')
def index():
    """Renders the main input form."""
    return render_template('index.html',
                           chemicals=CHEMICAL_DATABASE,
                           options=OPTIONS,
                           now=datetime.now(),
                           form_data={})

@app.route('/calculate', methods=['POST'])
def calculate():
    """Handles single assessment form submission."""
    form_data = request.form.to_dict()
    results = {'inhalation': calculate_inhalation_risk(form_data)}

    return render_template('index.html',
                           results=results,
                           chemicals=CHEMICAL_DATABASE,
                           options=OPTIONS,
                           form_data=form_data,
                           now=datetime.now())

@app.route('/batch_calculate', methods=['POST'])
def batch_calculate():
    """Handles batch CSV file upload and processing."""
    if 'csv_file' not in request.files:
        return "No file part", 400
    file = request.files['csv_file']
    if file.filename == '':
        return "No selected file", 400

    if file and file.filename.endswith('.csv'):
        try:
            # Read CSV with string data type to avoid pandas type inference issues
            df = pd.read_csv(file, dtype=str)
            results = []

            # Add 'form' and 'q2_spray' to required columns
            required_cols = {'cas', 'concentration', 'q1_amount', 'q4_ventilation', 'q5_time', 'title', 'form', 'q2_spray'}
            if not required_cols.issubset(df.columns):
                return f"CSV must contain the following columns: {', '.join(required_cols)}", 400

            for _, row in df.iterrows():
                cas = row['cas']
                chem_id = find_chem_id_by_cas(cas)
                if not chem_id:
                    continue

                # Simulate the form data structure for the calculation logic
                form_data = {
                    'substance_id': str(chem_id),
                    'concentration': row['concentration'],
                    'q1_amount': row['q1_amount'],
                    'q4_ventilation': row['q4_ventilation'],
                    'q5_time': row['q5_time'],
                    'form': row['form'],
                    'q2_spray': row['q2_spray'].lower() # Ensure boolean check is case-insensitive
                }

                result = calculate_inhalation_risk(form_data)
                result['title'] = row['title'] # Add title from CSV to the result
                results.append(result)

            results_json = json.dumps(results)

            return render_template('batch_results.html', results=results, results_json=results_json)

        except Exception as e:
            return f"An error occurred: {e}", 500

    return "Invalid file type", 400

@app.route('/download_results', methods=['POST'])
def download_results():
    """Handles downloading the batch results as a CSV file."""
    results_json = request.form.get('results_json')
    if not results_json:
        return "No data to download", 400

    results = json.loads(results_json)

    output_data = []
    for res in results:
        output_data.append({
            'CAS RN': res['chem']['cas'],
            'Substance Name': res['chem']['name'],
            'Task Title': res['title'],
            'Estimated Exposure (ppm)': res['conc'],
            'Risk Ratio (RCR)': res['rcr'],
            'Risk Level': res['level']['val'],
            'Judgement': res['level']['msg']
        })
    df = pd.DataFrame(output_data)

    output = io.StringIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=risk_assessment_results.csv"
    response.headers["Content-type"] = "text/csv; charset=utf-8-sig"

    return response


if __name__ == '__main__':
    app.run(debug=True, port=5000)
