import xmlrpc.client
from jinja2 import Environment, FileSystemLoader
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import datetime
import argparse

# XML-RPC Connection Parameters
url = 'http://172.22.0.3:8069'
db = 'lms.pivi.com.ph'
username = 'jobaseniero@gmail.com'
password = 'P@$$w0rd!'
#companies = ['PMI']

loan_class_names = {
    'long_term': 'Long Term',
    'short_term': 'Short Term',
    'back_back': 'Back to Back'
}


def fetch_loan_summaries(company):
    # Connect to Odoo via XML-RPC
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    # Create an object to call Odoo's API methods
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    domain = [
        ['company_id', '=', company]
    ]

    # Search for Loan Summary records
    summary_ids = models.execute_kw(db, uid, password, 'loans.summary', 'search', [domain])

    # Read data for each Loan Summary record, and fetch additional data for related fields
    summaries = []
    for summary_id in summary_ids:
        summary = models.execute_kw(
            db, uid, password, 'loans.summary', 'read',
            [summary_id],
            {'fields': ['company_id', 'bank_id', 'principal', 'credit_line', 'available_balance', 'type', 'loan_class']}
        )[0]

        principal = summary['principal']
        formatted_principal = '{:,.2f}'.format(principal)
        summary['principal'] = formatted_principal

        credit_line = summary['credit_line']
        formatted_credit_line = '{:,.2f}'.format(credit_line)
        summary['credit_line'] = formatted_credit_line

        available_balance = summary['available_balance']
        formatted_available_balance = '{:,.2f}'.format(available_balance)
        summary['available_balance'] = formatted_available_balance

        # Fetch additional data for related fields (company_id and bank_id)
        company_name = models.execute_kw(
            db, uid, password, 'res.partner', 'read',
            [[summary['company_id'][0]]],
            {'fields': ['name']}
        )[0]['name']

        bank_name = models.execute_kw(
            db, uid, password, 'res.bank', 'read',
            [[summary['bank_id'][0]]],
            {'fields': ['name']}
        )[0]['name']

        # Append the fetched data along with the bank name to the summaries list
        summary['company'] = company_name
        summary['bank'] = bank_name
        summary['loan_type'] = summary['type'][1]
        summary['loan_class'] = loan_class_names.get(summary['loan_class'], '')

        summaries.append(summary)

    # Sort the summaries list by bank name in alphabetical order
    summaries.sort(key=lambda x: x['company'])

    return summaries

def export_loan_summary_to_html(totals, company):
    summaries = fetch_loan_summaries([company])
    subtotals = compute_subtotals(summaries)  # Calculate subtotals

    # Load the HTML template and render it with the data
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('loan_summary_template.html')
    current_date = datetime.date.today()
    html_output = template.render(
        summaries=summaries,
        current_date=current_date,
        totals=totals,
        subtotals=subtotals  # Pass the subtotals dictionary to the template
    )

    # Save the HTML output to a file
    with open('loan_summary_report.html', 'w') as html_file:
        html_file.write(html_output)

    print('HTML report generated successfully!')



def compute_totals(summaries):
    totals = {'Grand Total': {'credit_line': 0, 'principal': 0, 'available_balance': 0}}

    for summary in summaries:
        company = summary['company']

        # Initialize subtotals for the company if not already present
        if company not in totals:
            totals[company] = {'credit_line': 0, 'principal': 0, 'available_balance': 0}

        # Update subtotals for the company and grand total
        for field in ['credit_line', 'principal', 'available_balance']:
            value = float(summary[field].replace(',', ''))
            totals[company][field] += value
            totals['Grand Total'][field] += value

    return totals

def compute_subtotals(summaries):
    subtotals = {}

    for summary in summaries:
        company = summary['company']
        loan_class = summary['loan_class']

        if company not in subtotals:
            subtotals[company] = {}

        if loan_class not in subtotals[company]:
            subtotals[company][loan_class] = {'credit_line': 0, 'principal': 0, 'available_balance': 0}

        for field in ['credit_line', 'principal', 'available_balance']:
            value = float(summary[field].replace(',', ''))
            subtotals[company][loan_class][field] += value

    return subtotals


def convert_html_to_pdf():
    # Convert HTML to PDF
    pdf_file = 'loan_summary_report.pdf'
    options = {
        'page-size': 'Letter',
        'orientation': 'Landscape'
    }
    pdfkit.from_file('loan_summary_report.html', pdf_file, options=options)

    print('PDF report generated successfully!')

def send_email_with_pdf(company):
    # Replace these with your email and password
    sender_email = 'webdev@obanana.com'
    sender_password = '+sTXz,.YkuBs'

    # Convert HTML to PDF
    pdf_file = 'loan_summary_report.pdf'
    #pdfkit.from_file('loan_summary_report.html', pdf_file)

    # Fetch head_emails from Odoo using XML-RPC
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Fetch email addresses from the head_emails custom model
    head_emails_ids = models.execute_kw(db, uid, password, 'head.emails', 'search', [[]])
    head_emails_records = models.execute_kw(
        db, uid, password, 'head.emails', 'read',
        [head_emails_ids],
        {'fields': ['name']}
    )

    # Create a list of email addresses from the fetched records
    receiver_emails = [record['name'] for record in head_emails_records]

    # Compose the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ', '.join(receiver_emails)
    msg['Subject'] = 'Weekly Loan Summary Report - ' + company

    # Add a message to the email body
    email_body = """
Dear Sir/Ma'am,

Please find attached Weekly Loan Summary Report attached.


Thank and best regards,
Obanana Business Solutions
    """
    body_part = MIMEText(email_body)
    msg.attach(body_part)

    # Add the PDF file as an attachment
    with open(pdf_file, 'rb') as file:
        part = MIMEApplication(file.read())
        part.add_header('Content-Disposition', 'attachment', filename=pdf_file)
        msg.attach(part)

    # Send the email via SMTP
    with smtplib.SMTP('mail.obanana.com', 26) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_emails, msg.as_string())

    print('Email sent successfully!')

def main(company):
    summaries = fetch_loan_summaries([company])  # Pass the company directly as a list
    totals = compute_totals(summaries)
    export_loan_summary_to_html(totals, company) 
    convert_html_to_pdf()
    send_email_with_pdf(company)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate and send loan summary reports.')
    parser.add_argument('company', metavar='COMPANY', type=str, help='the company name for the report')

    args = parser.parse_args()
    main(args.company)
