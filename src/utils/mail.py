import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

SMTP_HOST_PORT = "mail.makrosum.net:465"

def send_mail(sender_address, sender_pass, receiver_address, msg_text, subject,
              file_name, file_data, smtp_host_port=SMTP_HOST_PORT):
    """Send mail using parameters.

    Args:
        sender_address: Sender address and SMTP username.
        sender_pass: SMTP password of sender.
        receiver_address: Email address of receiver.
        msg_text: Text of Email.
        subject: Subject of Email.
        file_name: File name of attachment.
        file_data: File data with base64 encoding.
        smtp_host_port: Combination of "<host>:<port>".
    Return:
        bool: True for success False for failure.
    """

    message = MIMEMultipart()
    message['From'] = sender_address
    message['To'] = receiver_address
    message['Subject'] = subject

    message.attach(MIMEText(msg_text, 'html'))
    payload = MIMEBase('application', 'octate-stream')
    payload.set_payload(file_data)
    payload.add_header('Content-Transfer-Encoding', 'base64')
    message.attach(payload)
    payload.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', file_name))

    session = smtplib.SMTP_SSL(smtp_host_port, timeout=10)
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
