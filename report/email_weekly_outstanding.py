import xmlrpc.client
from jinja2 import Environment, FileSystemLoader
import pdfkit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta, date

# XML-RPC Connection Parameters
url_odoo = 'http://localhost:8069'
db = 'Odoo'
username = 'odoo@obanana.com'
password = 'Obanana2023'

def fetch_loan_main_records():
    # Connect to Odoo via XML-RPC
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    # Create an object to call Odoo's API methods
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    # Calculate the date range for the next week's weekdays (Monday to Friday)
    today = datetime.today()
    next_week_start = today + timedelta(days=(7 - today.weekday()))
    next_week_end = next_week_start + timedelta(days=4)

    # Search for Loan Main records with dates in the next week's weekdays and stage "New" or "Funded"
    domain = [
        ['loan_date', '>=', next_week_start.strftime('%Y-%m-%d')],
        ['loan_date', '<=', next_week_end.strftime('%Y-%m-%d')],
        '|', ['stage', '=', 'New'], ['stage', '=', 'Funded']
    ]
    loan_main_ids = models.execute_kw(db, uid, password, 'loans.main', 'search', [domain])

    # Read data for each Loan Main record
    loan_main_records = []
    for loan_main_id in loan_main_ids:
        loan_main_record = models.execute_kw(
            db, uid, password, 'loans.main', 'read',
            [loan_main_id],
            {'fields': ['loan_date', 'pn_number', 'pn_count', 'company_name', 'bank_name', 'amount', 'amount_type', 'payment_type', 'loan_type', 'stage']}
        )[0]

        amount = loan_main_record['amount']
        formatted_amount = '{:,.2f}'.format(amount)
        loan_main_record['amount'] = formatted_amount

        # Fetch additional data for related fields (company_name and bank_name)
        company_id = models.execute_kw(
            db, uid, password, 'res.partner', 'read',
            [[loan_main_record['company_name'][0]]],
            {'fields': ['name']}
        )[0]['name']

        bank_id = models.execute_kw(
            db, uid, password, 'res.bank', 'read',
            [[loan_main_record['bank_name'][0]]],
            {'fields': ['name']}
        )[0]['name']

        # Append the fetched data to the loan_main_record dictionary
        loan_main_record['company'] = company_id
        loan_main_record['bank'] = bank_id
        #loan_main_record['type'] = loan_main_record['loan_type'][1]
        loan_main_record['loan_stage'] = loan_main_record['stage'][1]

        loan_main_records.append(loan_main_record)

    # Sort the loan_main_records list by loan_date in descending order
    loan_main_records.sort(key=lambda x: x['loan_date'])

    return loan_main_records

def export_loan_main_to_html():
    # Fetch the loan main records from Odoo and sort them by loan_date
    loan_main_records = fetch_loan_main_records()

    today = datetime.today()
    next_week_start = today + timedelta(days=(7 - today.weekday()))
    next_week_end = next_week_start + timedelta(days=4)

    # Load the HTML template
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('loan_main_template.html')

    # Render the template with the data and date range
    html_output = template.render(loan_main_records=loan_main_records,
                                  start_date=next_week_start.strftime('%Y-%m-%d'),
                                  end_date=next_week_end.strftime('%Y-%m-%d'))

    # Save the HTML output to a file
    with open('loan_main_report.html', 'w') as html_file:
        html_file.write(html_output)

    print('HTML report generated successfully!')

def convert_html_to_pdf():
    # Convert HTML to PDF
    pdf_file = 'loan_main_report.pdf'
    options = {
        'page-size': 'Letter',
        'orientation': 'Landscape'
    }
    pdfkit.from_file('loan_main_report.html', pdf_file, options=options)

    print('PDF report generated successfully!')

# Update the send_email_with_pdf function to use the new HTML file name
def send_email_with_pdf():
    # Replace these with your email and password
    sender_email = 'webdev@obanana.com'
    sender_password = '+sTXz,.YkuBs'

    # Convert HTML to PDF
    pdf_file = 'loan_main_report.pdf'
    #pdfkit.from_file('loan_main_report.html', pdf_file)

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
    msg['Subject'] = 'Weekly Outstanding and Funded Loans Report'

    # Add a message to the email body
    email_body = """
Dear recipient,

Please find the weekly outstanding and funded loans report attached.

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
    export_loan_main_to_html()
    convert_html_to_pdf()
    send_email_with_pdf()
