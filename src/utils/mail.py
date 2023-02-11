import smtplib
from email.header import Header
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


def check_email(string):
    if string is None:
        return False
    if ' ' in string:
        return False
    if "@" not in string:
         return False
    name, domain = string.split('@', 1)
    if '.' not in domain[1:]:
        return False
    return True

def send_mail(sender_address, sender_title, sender_pass, receiver_address, msg_text, subject,
              attachments, smtp_host_port):
    """Send mail using parameters.

    Args:
        sender_address: Sender address and SMTP username.
        sender_pass: SMTP password of sender.
        receiver_address: Email address of receiver.
        msg_text: Text of Email.
        subject: Subject of Email.
        attachments: Dictionary of attachments for attaching.
                     {<attachment_name>: <base64_attachment_data, ...}
        smtp_host_port: Combination of "<host>:<port>".
    Return:
        bool: True for success False for failure.
    """

    message = MIMEMultipart()

    from_title = Header(sender_title, 'utf-8')
    from_title.append(f'<{sender_address}>', 'ascii')
    message['From'] = from_title
    message['To'] = receiver_address
    message['Subject'] = subject

    print("FROM:{}\n TO:{}".format(message['From'], message['To']))

    message.attach(MIMEText(msg_text, 'html'))

    for attachment_name, attachment_data in attachments.items():
        payload = MIMEBase('application', 'octate-stream')
        payload.add_header('Content-Transfer-Encoding', 'base64')
        payload.set_payload(attachment_data)
        payload.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', attachment_name))
        message.attach(payload)

    session = smtplib.SMTP_SSL(smtp_host_port, timeout=10)
    session.login(sender_address, sender_pass)
    text = message.as_string()
    session.sendmail(sender_address, receiver_address, text)
    session.quit()
