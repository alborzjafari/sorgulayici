import os
import json
import datetime
import requests
from utils.mssqlconnector import mssqlConnect
from utils.hizliservis import hizliServis
from utils.filegenerator import fileGenerator


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

def send_mhatsapp(data, belge_tarihi, pdf_obj):
    """
    """
    print("1")
    if data['ProfileId'] == 'TEMELIRSALIYE':
        caption = MsgTemplates["IRSALIYE"].format("firmaAdı",
                                                  data['TargetTitle'], belge_tarihi, data['DocumentId'],
                                                  data['ProfileId'])
    else:
        caption = MsgTemplates["FATURA"].format("firmaAdı",
                                                data['TargetTitle'], belge_tarihi, data['DocumentId'],
                                                "{:,.2f}".format(float(data['PayableAmount'])),
                                                data['DocumentCurrencyCode'],
                                                data['ProfileId'])
    print("2")
    token = "c3a87aad6880401b876a7d1eb07b6b67"
    data2 = {'type': 'document','filename':'{}.pdf'.format(data['DocumentId']),
            'file':pdf_obj,
            'message':caption,
            'numbers': "905527932091",
            #'numbers': "905527932091,905334993344",
            'token':[token]
    }
    print("before send")
    req = requests.post('http://api.mhatsapp.com/api/v3/message/send/',
                        data=json.dumps({'action':data2}),
                        headers={'Content-type':'application/json'})
    print("after send")

def get_users_list():
    """Get user list from Makrosum DB
    """
    users = list()
    db = mssqlConnect('dbmain.ffatura.com', 'sa', '3genYildiz.', 'ffatura_main', '1433')
    db.createConnection()
    users = db.selectProcedure('kullanicilari_getir')

    return users

def get_invoice(hbt_user, hbt_password):
    """Get user's invoice.
    """
    hizli_service = hizliServis(hbt_user, hbt_password)
    for app_type in [AppType["GELEN_E-FATURA"], AppType["GELEN_E-IRSALIYE"]]:
        gelen_belgeler = hizli_service.get_documents(app_type)
        for gelen_belge in gelen_belgeler:
            print("gelen_belge:", gelen_belge)
            date = datetime.datetime.fromisoformat(gelen_belge['IssueDate'])
            belge_tarihi = date.strftime('%d-%m-%Y')
            file_name = "{}-({})-{}".format(gelen_belge["DocumentId"], belge_tarihi, gelen_belge["TargetTitle"])
            app_type_ = int(gelen_belge['AppType'])
            uuid_ = gelen_belge['UUID']
            print("before media download")
            media = hizli_service.download_media(app_type, uuid_,'PDF')
            print("after media download")

            send_mhatsapp(gelen_belge, belge_tarihi, media)

            exit(0)
            fileGenerator.writePDF(file_name, media, os.path.dirname(os.path.realpath(__file__)))
            media = hizli_service.download_media(app_type, uuid_,'XML')
            fileGenerator.writeXML(file_name, media, os.path.dirname(os.path.realpath(__file__)))



if __name__ == '__main__':
    users = get_users_list()
    for user in users:
        hbt_user = user['hbt_user']
        password = user['hbt_password']
        get_invoice(hbt_user, password)
