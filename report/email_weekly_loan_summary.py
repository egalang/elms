import xmlrpc.client
from jinja2 import Environment, FileSystemLoader
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import datetime

# XML-RPC Connection Parameters
url = 'http://localhost:8069'
db = 'Odoo'
username = 'odoo@obanana.com'
password = 'Obanana2023'

def fetch_loan_summaries():
    # Connect to Odoo via XML-RPC
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    # Create an object to call Odoo's API methods
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Search for Loan Summary records
    summary_ids = models.execute_kw(db, uid, password, 'loans.summary', 'search', [[]])

    # Read data for each Loan Summary record, and fetch additional data for related fields
    summaries = []
    for summary_id in summary_ids:
        summary = models.execute_kw(
            db, uid, password, 'loans.summary', 'read',
            [summary_id],
            {'fields': ['company_id', 'bank_id', 'principal', 'credit_line', 'available_balance', 'type']}
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
        summaries.append(summary)

    # Sort the summaries list by bank name in alphabetical order
    summaries.sort(key=lambda x: x['company'])

    return summaries

def export_loan_summary_to_html():
    # Fetch the loan summaries from Odoo and sort them by bank name
    summaries = fetch_loan_summaries()

    # Load the HTML template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('loan_summary_template.html')

    # Get the current date
    current_date = datetime.date.today()

    # Render the template with the data and current date
    html_output = template.render(summaries=summaries, current_date=current_date)

    # Render the template with the data
    # html_output = template.render(summaries=summaries)

    # Save the HTML output to a file
    with open('loan_summary_report.html', 'w') as html_file:
        html_file.write(html_output)

    print('HTML report generated successfully!')

def convert_html_to_pdf():
    # Convert HTML to PDF
    pdf_file = 'loan_summary_report.pdf'
    pdfkit.from_file('loan_summary_report.html', pdf_file)

    print('PDF report generated successfully!')

def send_email_with_pdf():
    # Replace these with your email and password
    sender_email = 'webdev@obanana.com'
    sender_password = '+sTXz,.YkuBs'

    # Convert HTML to PDF
    pdf_file = 'loan_summary_report.pdf'
    pdfkit.from_file('loan_summary_report.html', pdf_file)

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
    msg['Subject'] = 'Weekly Loan Summary Report'

    # Add a message to the email body
    email_body = """
Dear recipient,

Please find the weekly loan summary report attached.

Thank you.

Best regards,
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

if __name__ == "__main__":
    export_loan_summary_to_html()
    convert_html_to_pdf()
    send_email_with_pdf()
