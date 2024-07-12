from flask import Flask, render_template, request
from google.cloud import bigquery

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('/index.html')

@app.route('/transactions')
def transactions():
    client = bigquery.Client()
    query = """
    SELECT * FROM `df-pipeline-project-19062024.banking_fraud.transactions_tbl`
    LIMIT 100
    """
    results = client.query(query)
    transactions = [dict(row) for row in results]
    return render_template('transactions.html', transactions=transactions)

@app.route('/frauds')
def frauds():
    client = bigquery.Client()
    query = """
    SELECT * FROM `df-pipeline-project-19062024.banking_fraud.transactions_tbl`
    WHERE fraud_flag = TRUE
    LIMIT 100
    """
    results = client.query(query)
    frauds = [dict(row) for row in results]
    return render_template('frauds.html', frauds=frauds)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
