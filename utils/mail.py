import smtplib
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import traceback


class Mail:
    def __init__(self, host, username, password, port, type):
        self.host = host
        self.username = username
        self.password = password
        self.port = int(port)
        self.type = type

    def checkException(self, e):
        print(str(e))
        print(type(str(e)))
        if 'STARTTLS extension not supported by server' in str(e) or \
                'SSL: WRONG_VERSION' in str(e) or \
                'Connection unexpectedly' in str(e) or \
                '[Errno 60]' in str(e) or 'timed out' in str(e):
            return {'result': 'PORT'}
        elif 'Username' in str(e) or 'Password' in str(e):
            pass
        elif 'Errno 8' in str(e):
            pass
        else:
            pass

    def connect(self):
        if self.type == 'SSL':
            try:
                mailserver = smtplib.SMTP_SSL(self.host, self.port, timeout=20)
                mailserver.ehlo()
                mailserver.login(self.username,self.password)
                mailserver.close()
                return {'result':'success'}

            except Exception as e:
                self.checkException(e)
                pass
        else:
            try:
                mailserver = smtplib.SMTP(self.host, self.port, timeout=20)
                mailserver.ehlo()
                mailserver.starttls()
                mailserver.ehlo()
                mailserver.login(self.username,self.password)
                mailserver.close()
                return {'result': 'success'}
            except Exception as e:
                self.checkException(e)
                pass
    def sendMsg(self, to: list,fatura,location,firmadi,pdflink):
        """
        Bu fonksiyonda bir sıkıntı varsa öncelikle,
        try-catch bloğunu kaldırın, sonra debug edin
        - SAYGILAR [ÖNCEKİ YAZILIMCI - ATAKAN]
        """
        try:
            if self.type == 'SSL':
                server = smtplib.SMTP_SSL(self.host, self.port)
                server.ehlo()
                server.login(self.username, self.password)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.username, self.password)
            message = MIMEMultipart("alternative")
            message["Subject"] = 'FFatura Bilgilendirme'
            message["From"] = self.username
            message["To"] = ','.join(to)
            appTypes = {2:'E-Fatura',3:'E-Arşiv Fatura',5:'E-İrsaliye'}
            with open(location+'/utils/mailtemplate.html','r') as file:
                mesaj = file.read().replace('##musteriadi##',
                                            fatura['TargetTitle']).replace(
                    '##faturatipi##',
                    appTypes[int(fatura['AppType'])]).replace('##firmaadi##', firmadi).replace('##pdflink##', pdflink)
                if int(fatura['AppType']) != 5:
                    mesaj = mesaj.replace('##fiyat##',
                                            '{:,} {}'.format(fatura['PayableAmount'] if int(
                                                fatura['AppType']) != 5 else '', fatura[
                                                                'DocumentCurrencyCode'] if int(
                                                fatura['AppType']) != 5 else ''))
                else:
                    mesaj = mesaj.replace('##fiyat##', '')
            if int(fatura['AppType']) == 5:
                mesaj = mesaj.replace('tutarında','')
            m1 = MIMEText(mesaj, 'html')
            message.attach(m1)
            with open(location+'/utils/logo.png','rb') as file2:
                resim = MIMEImage(file2.read())
            resim.add_header('Content-ID','<image1>')
            message.attach(resim)
            #with open('{}/upd/{}.pdf'.format(location,fatura['DocumentId']), "rb") as attachment:
            with open('{}/upd/{}.pdf'.format(location,fatura['UUID']), "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                    'attachment', filename='{}.pdf'.format(fatura['DocumentId'])
            )
            message.attach(part)
            server.sendmail(from_addr=self.username, to_addrs=to, msg=message.as_string())
            server.close()
        except:
            pass
    def yeni_sendMsg(self, to: list,data,location,firmadi,pdflink,dataXML):
        try:
            dataXML2 = dataXML
            dataXML2['DocumentCurrencyCode'] = dataXML2['Invoice']['cac:InvoiceLine']['cac:Price']['cbc:PriceAmount']['@currencyID']
        except:
            dataXML2 = {}
            dataXML2['DocumentCurrencyCode']='TL'
        fatura = {
        'ProfileId':data['senaryoTur'],
        'DocumentCurrencyCode':dataXML2['DocumentCurrencyCode'],
        'TargetTitle':data['gonderenUnvan'],
        'DocumentId':data['faturaNo'],
        'IssueDate':data['faturaTarihi'],
        'CreatedDate':data['faturaTarihi'],
        'TargetIdentifier':data['vknTckn'],
        }
        """
        Bu fonksiyonda bir sıkıntı varsa öncelikle,
        try-catch bloğunu kaldırın, sonra debug edin
        - SAYGILAR [ÖNCEKİ YAZILIMCI - ATAKAN]
        """
        try:
            if self.type == 'SSL':
                server = smtplib.SMTP_SSL(self.host, self.port)
                server.ehlo()
                server.login(self.username, self.password)
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=20)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.username, self.password)
            message = MIMEMultipart("alternative")
            message["Subject"] = 'FFatura Bilgilendirme'
            message["From"] = self.username
            message["To"] = ','.join(to)
            appTypes = {2:'E-Fatura',3:'E-Arşiv Fatura',5:'E-İrsaliye'}
            with open(location+'/utils/mailtemplate.html','r') as file:
                mesaj = file.read().replace('##musteriadi##',
                                            fatura['TargetTitle']).replace(
                    '##faturatipi##',
                    appTypes[int(fatura['AppType'])]).replace('##firmaadi##', firmadi).replace('##pdflink##', pdflink)
                if int(fatura['AppType']) != 5:
                    data['PayableAmount'] = data['genelToplam']
                    mesaj = mesaj.replace('##fiyat##',
                                            '{:,} {}'.format(fatura['PayableAmount'] if int(
                                                fatura['AppType']) != 5 else '', fatura[
                                                                'DocumentCurrencyCode'] if int(
                                                fatura['AppType']) != 5 else ''))
                else:
                    mesaj = mesaj.replace('##fiyat##', '')
            if int(fatura['AppType']) == 5:
                mesaj = mesaj.replace('tutarında','')
            m1 = MIMEText(mesaj, 'html')
            message.attach(m1)
            with open(location+'/utils/logo.png','rb') as file2:
                resim = MIMEImage(file2.read())
            resim.add_header('Content-ID','<image1>')
            message.attach(resim)
            #with open('{}/upd/{}.pdf'.format(location,fatura['DocumentId']), "rb") as attachment:
            
            with open("./gonderilecekler/{}.pdf".format(fatura['UUID']),'rb') as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                    'attachment', filename='{}.pdf'.format(fatura['DocumentId'])
            )
            message.attach(part)
            server.sendmail(from_addr=self.username, to_addrs=to, msg=message.as_string())
            server.close()
        except:
            pass