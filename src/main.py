import re
import json
import time
import base64
import requests
import xmltodict
from datetime import datetime

from utils.mail import send_mail, check_email
from utils.hizli_servis import HizliService
from utils.mssql_connector import MsSqlConnector

from html_msg_generator.generate_html_msg import generate_html_msg


SMTP_HOST_PORT = "mail.makrosum.net:465"
SENDER_MAIL = "no-reply@ffatura.com"
SENDER_PASS = "^Q3X^zZkNUw2iU}!,8Wh"

AppType = {
    'GELEN_E-FATURA': 1,
    'GIDEN_E-FATURA': 2,
    'GIDEN_E-ARSIV_FATURA': 3,
    'GELEN_E-IRSALIYE': 4,
    'GIDEN_E-IRSALIYE': 5
}

MsgTemplates = {
    'IRSALIYE': "Sayın *{}* ,\n\n *{}* firmasından \n *{}* tarihli \n *{}* numaralı \n *{}* gelmiştir.\n\n" +
                "```NOT: Bu mesaj, ffatura.com sistemi tarafından otomatik olarak oluşturulmuştur.```",
    'FATURA': "Sayın *{}* ,\n\n *{}* firmasından \n *{}* tarihli \n *{}* numaralı \n *{} {}* tutarında \n *{}* gelmiştir.\n\n" +
              "```NOT: Bu mesaj, ffatura.com sistemi tarafından otomatik olarak oluşturulmuştur.```",
    'GIDEN_FATURA': "Sayın *{}* ,\n\n *{}* firmasından \n *{}* tarihli \n *{}* numaralı \n *{} {}* tutarında \n *{}* gelmiştir.\n\n" +
                    "```NOT: Bu mesaj, ffatura.com sistemi tarafından otomatik olarak oluşturulmuştur.```"
}

def send_invoice_text(msg, tels, token):
    json_data = {'type': 'text',
                 'message': msg,
                 'numbers': tels,
                 'token':[token]
    }
    req = requests.post('http://api.mhatsapp.com/api/v3/message/send/',
                        data=json.dumps({'action':json_data}),
                        headers={'Content-type':'application/json'})
    print("wp sent, " + tels)

def send_invoice_pdf(msg, tels, pdf_obj, pdf_name, token):
    """Send invoice in whatsapp
    Args:
        msg: Text message
        tels: Comma separated list of telephone numbers.

    """
    json_data = {'type': 'document',
                 'filename': "{}.pdf".format(pdf_name),
                 'file': pdf_obj,
                 'message': msg,
                 'numbers': tels,
                 'token':[token]
    }
    req = requests.post('http://api.mhatsapp.com/api/v3/message/send/',
                        data=json.dumps({'action':json_data}),
                        headers={'Content-type':'application/json'})
    print("wp pdf sent, " + tels)

def get_users_list():
    """Get user list from Makrosum DB
    """
    users = list()
    db = MsSqlConnector('newmssql.makrosum.com', 'sa', '3genYildiz.',
                        'ffatura_main', '1433')
    db.createConnection()
    users = db.selectProcedure('kullanicilari_getir')

    return users

def get_invoices(hbt_user, hbt_password):
    """Get invoices collection for one user.
    Args:
        hbt_user: username
        hbt_password: password
    Returns:
        Dictionary of invoices collection. {"app_type": [invoices list],...}
    """
    invoices_collection = dict()
    hizli_service = HizliService(hbt_user, hbt_password)
    for app_type_name, app_type in AppType.items():
        invoices = hizli_service.get_documents(app_type)
        invoices_collection[app_type] = invoices

    return invoices_collection

def generate_message(invoice, firma_adi, app_type):
    doc_id = invoice['DocumentId']
    profile_id = invoice['ProfileId']
    target_title = invoice['TargetTitle']
    date = datetime.fromisoformat(invoice['IssueDate']).strftime('%d-%m-%Y')

    whatsapp_msg = str()
    mail_msg = str()
    payable_amount = "{:,.2f}".format(float(invoice['PayableAmount']))
    currency_code = invoice['DocumentCurrencyCode']
    if app_type == AppType['GELEN_E-FATURA'] or app_type == AppType['GELEN_E-IRSALIYE']:
        if invoice['ProfileId'] == 'TEMELIRSALIYE':
            template = MsgTemplates['IRSALIYE']
            whatsapp_msg = template.format(firma_adi, target_title, date,
                                           doc_id, profile_id)
            mail_msg = generate_html_msg(firma_adi, target_title, date, doc_id,
                                         payable_amount + " " + currency_code,
                                         profile_id)
        else:
            template = MsgTemplates['FATURA']
            whatsapp_msg = template.format(firma_adi, target_title, date,
                                           doc_id, payable_amount,
                                           currency_code, profile_id)
            mail_msg = generate_html_msg(firma_adi, target_title, date, doc_id,
                                         payable_amount + " " + currency_code,
                                         profile_id)
    else:
        template = MsgTemplates['GIDEN_FATURA']
        whatsapp_msg = template.format(target_title, firma_adi, date, doc_id,
                                       payable_amount, currency_code,
                                       profile_id)
        mail_msg = generate_html_msg(target_title, firma_adi, date, doc_id,
                                     payable_amount + " " + currency_code,
                                     profile_id)

    return whatsapp_msg, mail_msg

def get_file_name(invoice):
    date = datetime.fromisoformat(invoice['IssueDate']).strftime('%d-%m-%Y')
    doc_id = invoice['DocumentId']
    target_title = invoice['TargetTitle']
    file_name = "{}-({})-{}".format(doc_id, date, target_title)
    return file_name

def get_mail_subject(invoice):
    # 187 for »
    return "ffatura bilgilendirme " + chr(187) + " " + get_file_name(invoice)

def normalize_tel(tel_no):
    if tel_no is None:
        return None
    tel_no = ''.join([i for i in tel_no if i.isdigit()])
    if len(tel_no) == 0:
        print("Tel no len is zero... returning")
        return None
    elif len(tel_no) == 12:
        return tel_no

    int_tel_no = int(tel_no)
    tel_no = "90" + str(int_tel_no)
    print("TE:", tel_no)
    if len(tel_no) == 12:
        return tel_no
    else:
        return None

def get_tels_from_contacts(contact_list):
    tels = str()
    sep = ""
    tels_list = list()
    for contact, value in contact_list.items():
        if contact == "cbc:Telephone" and value is not None:
            normalized_tel = normalize_tel(value)
            if normalized_tel is not None:
                tels_list.append(normalized_tel)

    if len(tels_list) == 0:
        return None

    for tel in tels_list:
        tels += sep + tel
        sep = ','

    return tels

def validate_email_address(email_address):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
    if(re.fullmatch(regex, email_address)):
        return True
    return False

def get_emails_from_contacts(contact_list):
    for contact, value in contact_list.items():
        print("contact:", contact)
        if contact == "cbc:ElectronicMail" and value is not None:
            if validate_email_address(value) is True:
                return value
    return None

def send_giden_invoice(hizli_service, app_type, invoice, uuid, token,
                       firma_adi, msg_triggers):
    if msg_triggers['email_giden'] is False and \
            msg_triggers['whatsapp_giden'] is False:
        return

    is_account = invoice['IsAccount']
    envelop_stat = invoice['EnvelopeStatus']
    if is_account == True:
        return
    else:
        if envelop_stat != 1300 and envelop_stat != 14000:
            return

    xml_obj = hizli_service.download_media(app_type, uuid, 'XML')
    xml_str = base64.b64decode(xml_obj)
    xml_dic = xmltodict.parse(xml_str)

    contact_list = None
    try:
        if 'DespatchAdvice' in xml_dic.keys():
            contact_list = xml_dic['DespatchAdvice']['cac:DeliveryCustomerParty']['cac:Party']['cac:Contact']
        elif 'Invoice' in xml_dic.keys():
            contact_list = xml_dic['Invoice']['cac:AccountingCustomerParty']['cac:Party']['cac:Contact']
    except:
        pass

    if contact_list is None:
        print("contact list is None, marking as accounted and returning")
    else:
        file_name = get_file_name(invoice)
        pdf_obj = hizli_service.download_media(app_type, uuid, 'PDF')
        tels = get_tels_from_contacts(contact_list)
        email_address = get_emails_from_contacts(contact_list)
        whatsapp_msg, mail_msg = generate_message(invoice, firma_adi, app_type)
        if check_email(email_address) is True and msg_triggers['email_giden'] is True:
            attachments = {file_name + ".pdf": pdf_obj,
                           file_name + ".xml": xml_obj}
            subject = get_mail_subject(invoice)
            sender_title = f"{firma_adi}"
            send_mail(SENDER_MAIL, sender_title, SENDER_PASS, email_address,
                      mail_msg, subject, attachments, SMTP_HOST_PORT)
        if tels is not None and msg_triggers['whatsapp_giden'] is True:
            send_invoice_pdf(whatsapp_msg, tels, pdf_obj, file_name, token)
            time.sleep(1)
            send_invoice_text(whatsapp_msg, tels, token)

    hizli_service.mark_accounted(uuid, app_type)

def send_gelen_invoice(hizli_service, app_type, invoice, uuid, whatsapp_msg,
                       mail_msg, tels, token, user_mail, msg_triggers):
    if msg_triggers['whatsapp_gelen'] is False and \
            msg_triggers['email_gelen'] is False:
        return

    file_name = get_file_name(invoice)
    subject = get_mail_subject(invoice)
    pdf_obj = hizli_service.download_media(app_type, uuid, 'PDF')

    xml_obj = hizli_service.download_media(app_type, uuid, 'XML')
    xml_str = base64.b64decode(xml_obj)
    xml_dic = xmltodict.parse(xml_str)

    sender_title = str()
    try:
        if 'DespatchAdvice' in xml_dic.keys():
            sender_title = xml_dic['DespatchAdvice']['cac:DespatchSupplierParty']['cac:Party']['cac:PartyName']['cbc:Name']
        elif 'Invoice' in xml_dic.keys():
            sender_title = xml_dic['Invoice']['cac:AccountingSupplierParty']['cac:Party']['cac:PartyName']['cbc:Name']
    except:
        pass

    whatsapp_msg, mail_msg = str(), str()
    mail_gonder = msg_triggers['email_gelen']
    wspp_gonder = msg_triggers['whatsapp_gelen']

    if mail_gonder is True or wspp_gonder is True:
        whatsapp_msg, mail_msg = generate_message(invoice, firma_adi, app_type)

        if check_email(user_mail) is True and mail_gonder is True:
            attachments = {file_name + ".pdf": pdf_obj,
                           file_name + ".xml": xml_obj}
            send_mail(SENDER_MAIL, sender_title, SENDER_PASS, user_mail,
                      mail_msg, subject, attachments, SMTP_HOST_PORT)

        if wspp_gonder is True:
            send_invoice_pdf(whatsapp_msg, tels, pdf_obj, file_name, token)
            time.sleep(1)
            send_invoice_text(whatsapp_msg, tels, token)

    hizli_service.mark_taken([uuid,], app_type)

def send_invoices(invoices_collection, hbt_user, hbt_password, tels, token,
                  firma_adi, user_mail, msg_triggers):
    hizli_service = HizliService(hbt_user, hbt_password)
    for _, invoices_list in invoices_collection.items():
        if invoices_list is None:
            print("invoice is empty")
            continue
        for invoice in invoices_list:
            app_type = invoice['AppType']
            uuid = invoice['UUID']

            if app_type == AppType['GIDEN_E-FATURA'] or \
                    app_type == AppType['GIDEN_E-ARSIV_FATURA'] or \
                    app_type == AppType['GIDEN_E-IRSALIYE']:
                        send_giden_invoice(hizli_service, app_type, invoice,
                                           uuid, token, firma_adi, msg_triggers)
            elif app_type == AppType['GELEN_E-FATURA'] or \
                    app_type == AppType['GELEN_E-IRSALIYE']:
                send_gelen_invoice(hizli_service, app_type, invoice, uuid,
                                   tels, token, user_mail, msg_triggers)


if __name__ == '__main__':
    while True:
        users = get_users_list()
        for user in users:
            print("\nUSER: ", user)
            hbt_user = user['hbt_user']
            hbt_password = user['hbt_password']
            firma_adi = user['title']
            tels = user['mhatsapptels']
            token = user['mhatsapptoken']
            user_mail = user['mailadress']
            print("Getting invoices")
            invoices_collection = get_invoices(hbt_user, hbt_password)
            msg_triggers = {
                    'email_gelen': user['email_gelen'],
                    'email_giden': user['email_giden'],
                    'whatsapp_gelen': user['whatsapp_gelen'],
                    'whatsapp_giden': user['whatsapp_giden']
            }

            if len(tels) < 12 or len(token) != 36:
                continue
            print("Sending invoices")
            if invoices_collection is not None:
                 send_invoices(invoices_collection, hbt_user, hbt_password,
                               tels, token, firma_adi, user_mail, msg_triggers)
            print("-------------------------------------------", flush=True)
        time.sleep(1)

