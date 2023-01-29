import os
import json
import time
from datetime import datetime
import requests
from utils.mssql_connector import MsSqlConnector
from utils.hizli_servis import HizliService
#from utils.filegenerator import fileGenerator


AppType = {
    "GELEN_E-FATURA": 1,
    "GIDEN_E-FATURA": 2,
    "GIDEN_E-ARSIV_FATURA": 3,
    "GELEN_E-IRSALIYE": 4,
    "GIDEN_E-IRSALIYE": 5
}

MsgTemplates = {
    "IRSALIYE": "Sayın *{}* ,\n\n *{}* firmasından \n *{}* tarihli \n *{}* numaralı \n *{}* gelmiştir. \n",
    "FATURA": "Sayın *{}* ,\n\n *{}* firmasından \n *{}* tarihli \n *{}* numaralı \n *{} {}* tutarında \n *{}* gelmiştir. \n"
}

def send_invoice_text(msg, tels):
    token = "c3a87aad6880401b876a7d1eb07b6b67"
    json_data = {'type': 'text',
                 'message': msg,
                 'numbers': tels,
                 'token':[token]
    }
    print("before send")
    req = requests.post('http://api.mhatsapp.com/api/v3/message/send/',
                        data=json.dumps({'action':json_data}),
                        headers={'Content-type':'application/json'})
    print("after send")

def send_invoice_pdf(msg, tels, pdf_obj, pdf_name):
    """Send invoice in whatsapp
    Args:
        msg: Text message
        tels: Comma separated list of telephone numbers.

    """
    token = "c3a87aad6880401b876a7d1eb07b6b67"
    json_data = {'type': 'document',
                 'filename': "{}.pdf".format(pdf_name),
                 'file': pdf_obj,
                 'message': msg,
                 'numbers': tels,
                 'token':[token]
    }
    print("before send")
    req = requests.post('http://api.mhatsapp.com/api/v3/message/send/',
                        data=json.dumps({'action':json_data}),
                        headers={'Content-type':'application/json'})
    print("after send")

def get_users_list():
    """Get user list from Makrosum DB
    """
    users = list()
    db = MsSqlConnector('dbmain.ffatura.com', 'sa', '3genYildiz.', 'ffatura_main', '1433')
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
        invoices = hizli_service.get_documents(app_type, "ALL")
        invoices_collection[app_type] = invoices
    return invoices_collection

def generate_message(invoice, firma_adi):
    doc_id = invoice['DocumentId']
    profile_id = invoice['ProfileId']
    target_title = invoice['TargetTitle']
    date = datetime.fromisoformat(invoice['IssueDate']).strftime('%d-%m-%Y')

    msg = str()
    if invoice['ProfileId'] == 'TEMELIRSALIYE':
        template = MsgTemplates['IRSALIYE']
        msg = template.format(firma_adi, target_title, date, doc_id, profile_id)
    else:
        template = MsgTemplates['FATURA']
        payable_amount = "{:,.2f}".format(float(invoice['PayableAmount']))
        currency_code = invoice['DocumentCurrencyCode']
        msg = template.format(firma_adi, target_title, date, doc_id, payable_amount,
                              currency_code, profile_id)

    return msg

def get_file_name(invoice):
    date = datetime.fromisoformat(invoice['IssueDate']).strftime('%d-%m-%Y')
    doc_id = invoice['DocumentId']
    target_title = invoice['TargetTitle']
    file_name = "{}-({})-{}".format(doc_id, date, target_title)
    return file_name

def send_invoices(invoices_collection, hbt_user, hbt_password, tels, token,
                  firma_adi):
    hizli_service = HizliService(hbt_user, hbt_password)
    for app_type, invoices_list in invoices_collection.items():
        for invoice in invoices_list:
            print("0")
            message = generate_message(invoice, firma_adi)
            uuid = invoice['UUID']
            app_type = int(invoice['AppType'])
            pdf_obj = hizli_service.download_media(app_type, uuid, 'PDF')
            # TODO delete this list
            tels = "905527932091, 905334993344"

            pdf_name = get_file_name(invoice)

            send_invoice_pdf(message, tels, pdf_obj, pdf_name)
            time.sleep(1)
            send_invoice_text(message, tels)
            hizli_service.mark_taken([uuid,], app_type)
        exit(0)


if __name__ == '__main__':
    users = get_users_list()
    for user in users:
        print(user)
        hbt_user = user['hbt_user']
        hbt_password = user['hbt_password']
        firma_adi = user['title']
        token = user['mhatsapptels']
        tels = user['mhatsapptoken']
        invoices_collection = get_invoices(hbt_user, hbt_password)
        send_invoices(invoices_collection, hbt_user, hbt_password, tels,
                      token, firma_adi)
        exit(0)

