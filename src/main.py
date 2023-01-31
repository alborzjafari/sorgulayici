import os
import json
import time
import base64
import xmltodict
from datetime import datetime
import requests
from utils.mssql_connector import MsSqlConnector
from utils.hizli_servis import HizliService


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
    db = MsSqlConnector('newmssql.makrosum.com', 'sa', '3genYildiz.', 'ffatura_main', '1433')
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

    msg = str()
    if app_type == AppType['GELEN_E-FATURA'] or app_type == AppType['GELEN_E-IRSALIYE']:
        if invoice['ProfileId'] == 'TEMELIRSALIYE':
            template = MsgTemplates['IRSALIYE']
            msg = template.format(firma_adi, target_title, date, doc_id, profile_id)
        else:
            template = MsgTemplates['FATURA']
            payable_amount = "{:,.2f}".format(float(invoice['PayableAmount']))
            currency_code = invoice['DocumentCurrencyCode']
            msg = template.format(firma_adi, target_title, date, doc_id, payable_amount,
                                  currency_code, profile_id)
    else:
        template = MsgTemplates['GIDEN_FATURA']
        payable_amount = "{:,.2f}".format(float(invoice['PayableAmount']))
        currency_code = invoice['DocumentCurrencyCode']
        msg = template.format(target_title, firma_adi, date, doc_id, payable_amount,
                              currency_code, profile_id)

    return msg

def get_file_name(invoice):
    date = datetime.fromisoformat(invoice['IssueDate']).strftime('%d-%m-%Y')
    doc_id = invoice['DocumentId']
    target_title = invoice['TargetTitle']
    file_name = "{}-({})-{}".format(doc_id, date, target_title)
    return file_name

def normalize_tel(tel_no):
    if tel_no is None:
        return None
    tel_no = ''.join([i for i in tel_no if i.isdigit()])
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
    print("contact list:", contact_list)
    tels_list = list()
    for contact, value in contact_list.items():
        print("contact:", contact)
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

def send_giden_invoice(hizli_service, app_type, invoice, uuid, message):

    is_account = invoice['IsAccount']
    envelop_stat = invoice['EnvelopeStatus']
    if is_account == True:
        return
    else:
        if envelop_stat != 1300 or envelop_stat != 14000:
            return

    xml_obj = hizli_service.download_media(app_type, uuid, 'XML')
    xml_str = base64.b64decode(xml_obj)
    xml_dic = xmltodict.parse(xml_str)
    contact_list = xml_dic['Invoice']['cac:AccountingCustomerParty']['cac:Party']['cac:Contact']

    if contact_list is None:
        return
    tels = get_tels_from_contacts(contact_list)

    if tels is not None:
        print("XML Telefonları:", tels)
        # TODO delete this list
        tels = "905527932091, 905334993344"
        pdf_obj = hizli_service.download_media(app_type, uuid, 'PDF')
        pdf_name = get_file_name(invoice)
        send_invoice_pdf(message, tels, pdf_obj, pdf_name)
        time.sleep(1)
        send_invoice_text(message, tels)

    hizli_service.mark_accounted(uuid, app_type)

def send_gelen_invoice(hizli_service, app_type, invoice, uuid, message, tels):
    pdf_obj = hizli_service.download_media(app_type, uuid, 'PDF')
    pdf_name = get_file_name(invoice)
    send_invoice_pdf(message, tels, pdf_obj, pdf_name)
    time.sleep(1)
    send_invoice_text(message, tels)
    hizli_service.mark_taken([uuid,], app_type)

def send_invoices(invoices_collection, hbt_user, hbt_password, tels, token,
                  firma_adi):
    hizli_service = HizliService(hbt_user, hbt_password)
    for _, invoices_list in invoices_collection.items():
        if invoices_list is None:
            continue
        for invoice in invoices_list:
            app_type = invoice['AppType']
            message = generate_message(invoice, firma_adi, app_type)
            uuid = invoice['UUID']
            #print("------------------------------\n", invoice)
            if app_type == AppType['GIDEN_E-FATURA'] or \
                    app_type == AppType['GIDEN_E-ARSIV_FATURA']:
                    #app_type == AppType['GIDEN_E-IRSALIYE']:
                        pass
                        #send_giden_invoice(hizli_service, app_type, invoice, uuid, message)
            elif app_type == AppType['GELEN_E-FATURA'] or \
                    app_type == AppType['GELEN_E-IRSALIYE']:
                send_gelen_invoice(hizli_service, app_type, invoice, uuid, message, tels)


if __name__ == '__main__':
    while True:
        users = get_users_list()
        for user in users:
            print("USER:\n", user)
            hbt_user = user['hbt_user']
            hbt_password = user['hbt_password']
            firma_adi = user['title']
            tels = user['mhatsapptels']
            token = user['mhatsapptoken']
            invoices_collection = get_invoices(hbt_user, hbt_password)
            if len(tels) < 12 or len(token) != 36:
                continue
            if invoices_collection is not None:
                 send_invoices(invoices_collection, hbt_user, hbt_password,
                               tels, token, firma_adi)
        time.sleep(1)
