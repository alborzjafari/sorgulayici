import datetime
import pyodbc
import traceback

class mssqlConnect:
    def __init__(self,host,username,password,dbasename,port=1433):
        self.host = host
        self.username = username
        self.password = password
        self.dbasename = dbasename
        self.port = port
        self.connect = None
        self.cursor = None
    def createConnection(self):
        self.connect = pyodbc.connect('Driver={ODBC Driver 17 for SQL Server}; Server=' + '{},{}'.format(self.host,self.port) + ';Database=' + self.dbasename + ';UID=' + self.username + ';PWD=' + self.password + ';')
        self.cursor = self.connect.cursor()
    def disconnect(self):
        self.cursor.close()
        self.connect.close()
    def prepareProcedure(self,procedurename,params):
        procedure = "exec {} ".format(procedurename)
        procedure = procedure + self.cleanParams(params)
        return procedure
    def cleanParams(self,params):
        para = ''
        for i in params:
            para += "'{}',".format(i.replace("'","") if type(i) == str else i)
        return para[:-1]
    def getResult(self,procedure):
        self.cursor.execute(procedure)
        columns = [column[0] for column in self.cursor.description]
        results = list()
        for i in self.cursor.fetchall():
            results.append(dict(zip(columns, i)))
        return results
    def upsertProcedure(self,procedure):
        self.cursor.execute(procedure)
        self.cursor.commit()
        return True
    def selectProcedure(self,procedurename, params):
        procedure = self.prepareProcedure(procedurename,params)
        return self.getResult(procedure)

    def selectProcedure(self, procedurename):
        procedure = self.prepareProcedure(procedurename, '')
        return self.getResult(procedure)

    def upsertProcedureParams(self,procedurename,params):
        procedure = self.prepareProcedure(procedurename,params).replace('\\','')
        result = self.upsertProcedure(procedure)
        return result
    def update(self,tablename,params,where):
        updProcedure = "UPDATE {} SET ".format(tablename)
        for i in params:
            updProcedure += "{} = '{}',".format(i['key'],i['value'].replace("'",""))
        updProcedure = updProcedure[:-1]
        updProcedure += ' {}'.format(where)
        self.cursor.execute(updProcedure)
        self.cursor.commit()
        return True
    def sendInsertQueryComing(self,tablename,firmId,data,jpgLink,pdfLink,xmlLink,klasorId):
        if tablename == 'deaf_geleneirsaliye':
            sorgu = "INSERT INTO {}(firmaid,ettn,faturaNo,faturaTarihi,islemTarihi,gonderenUnvan,vknTckn,senaryoTur,faturaTuru,documentState,yildiz,isArchived,isPrinted,isRead,entegre,pdfId,jpgLink,pdfLink,xmlLink) values ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
                tablename, int(firmId), data['UUID'], data['DocumentId'],
                str(datetime.datetime.fromisoformat(data['IssueDate'].split("T")[0])),
                str(datetime.datetime.fromisoformat(data['CreatedDate'].split("T")[0])), data['TargetTitle'],
                data['TargetIdentifier'], data['ProfileId'],
                data['DocumentTypeCode'],
                data['EnvelopeExp'], 0, 0, 0, 0, 0, klasorId, jpgLink, pdfLink, xmlLink)
        else:
            sorgu = "INSERT INTO {}(firmaid,ettn,faturaNo,faturaTarihi,islemTarihi,gonderenUnvan,vknTckn,kdvTutari,genelToplam,senaryoTur,faturaTuru,documentState,yildiz,isArchived,isPrinted,isRead,entegre,pdfId,jpgLink,pdfLink,xmlLink) values ('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}')".format(
            tablename, int(firmId), data['UUID'], data['DocumentId'],
            str(datetime.datetime.fromisoformat(data['IssueDate'].split("T")[0])),
            str(datetime.datetime.fromisoformat(data['CreatedDate'].split("T")[0])), data['TargetTitle'],
            data['TargetIdentifier'],
            data['TaxTotal'], data['PayableAmount'], data['ProfileId'],
            data['DocumentTypeCode'],
            data['EnvelopeExp'], 0, 0, 0, 0, 0, '', jpgLink, pdfLink, xmlLink)

        self.cursor.execute(sorgu)
        self.cursor.commit()
        # print("bitti")
    def invoiceRowAdd(self,tabloAdi,firmaId,data,xml,r=0):
        self.cursor.execute(
            "SELECT id FROM {} WHERE firmaid = '{}' AND ettn = '{}'".format(tabloAdi, firmaId, data['UUID']))
        faturaId = self.cursor.fetchone()[0]
        if r == 0:
            if data['AppType'] != 4 and data['AppType'] != 5 and data['AppType'] != 8 and data['AppType'] != 9:
                self.kalemIsle({'firmaid': firmaId, 'vknTckn': data['TargetIdentifier'],
                                'faturaNo': data['DocumentId'],
                                'ettn': data['UUID'], 'faturaTarihi': data['IssueDate'].split('T')[0],
                                'islemTarihi': data['CreatedDate'].split('T')[0], 'id': faturaId}, data['AppType'], xml)
            elif data['AppType'] == 4 or data['AppType'] == 5:
                self.kalemIsleIrsaliye({'firmaid': firmaId, 'vknTckn': data['TargetIdentifier'],
                                        'faturaNo': data['DocumentId'],
                                        'ettn': data['UUID'], 'faturaTarihi': data['IssueDate'].split('T')[0],
                                        'islemTarihi': data['CreatedDate'].split('T')[0], 'id': faturaId},
                                       data['AppType'], xml)
        else:
            self.kalemIsleIrsaliyeCevap({'firmaid': firmaId, 'vknTckn': data['TargetIdentifier'],
                                    'faturaNo': data['DocumentId'],
                                    'ettn': data['UUID'], 'faturaTarihi': data['IssueDate'].split('T')[0],
                                    'islemTarihi': data['CreatedDate'].split('T')[0], 'id': faturaId}, data['AppType'],
                                   xml)
        #ToDo irsaliye kalem işlemeleri eklenecek
        # print("satırlar ekledndi")

    def kalemIsle(self,i, ffff,xml):
        sorguGonder = 'INSERT INTO deaf_kalemler (k_firma_id,k_vkn,k_malkodu,k_maladi,k_miktar,k_birim,k_birim_fiyat,k_iskonto,k_kdv_tutari,k_kdv_oran,k_diger_tutar,k_fatura_no,k_ettn,k_satir_no,k_brut,k_vdtt,k_fatura_tarih,k_islem_tarih,k_fatura_id,k_fatura_tipi) VALUES '
        kalemler = xml[[*xml][0]]['cac:InvoiceLine'] if type(xml[[*xml][0]]['cac:InvoiceLine']) == list else [
            xml[[*xml][0]]['cac:InvoiceLine']]
        for urun in kalemler:
            maladi = urun['cac:Item']['cbc:Name'].replace("'", "") if urun['cac:Item']['cbc:Name'] != None else ''
            malkodu = ''
            if 'cac:SellersItemIdentification' in urun['cac:Item'].keys():
                if 'cbc:ID' in urun['cac:Item']['cac:SellersItemIdentification'].keys():
                    malkodu = urun['cac:Item']['cac:SellersItemIdentification']['cbc:ID'] if type(
                        urun['cac:Item']['cac:SellersItemIdentification']['cbc:ID']) == str else ''
                else:
                    malkodu = urun['cac:Item']['cbc:Name'].replace("'", "") if urun['cac:Item']['cbc:Name'] != None else ''
            else:
                # ToDo Bak
                malkodu = urun['cac:Item']['cbc:Name'].replace("'", "") if urun['cac:Item']['cbc:Name'] != None else ''
            birim = urun['cbc:InvoicedQuantity']['@unitCode']
            birimFiyat = float(urun['cac:Price']['cbc:PriceAmount']['#text'])
            miktar = int(float(urun['cbc:InvoicedQuantity']['#text']))
            iskonto = 0
            if 'cac:AllowanceCharge' in urun.keys():
                if type(urun['cac:AllowanceCharge']) == list:
                    for isk in urun['cac:AllowanceCharge']:
                        iskonto += float(isk['cbc:Amount']['#text'])
                else:
                    iskonto = float(urun['cac:AllowanceCharge']['cbc:Amount']['#text'])
            kdv = float(0)
            diger = float(0)
            kdvOran = 0
            if 'cac:TaxTotal' in urun:
                if type(urun['cac:TaxTotal']) == list:
                    for vergi in urun['cac:TaxTotal']:
                        if vergi['cac:TaxCategory']['cac:TaxScheme']['cbc:TaxTypeCode'] == '0015':
                            kdv += float(vergi['cbc:TaxAmount']['#text'])
                            kdvOran = int(vergi['cbc:Percent'])
                        else:
                            diger += float(vergi['cbc:TaxAmount']['#text'])
                else:
                    if type(urun['cac:TaxTotal']['cac:TaxSubtotal']) == list:
                        for vergi in urun['cac:TaxTotal']['cac:TaxSubtotal']:
                            if vergi['cac:TaxCategory']['cac:TaxScheme']['cbc:TaxTypeCode'] == '0015':
                                kdv += int(float(vergi['cbc:TaxAmount']['#text']))
                                kdvOran = int(float(vergi['cbc:Percent']))
                            else:
                                diger += float(vergi['cbc:TaxAmount']['#text'])
                    else:
                        kdv += float(urun['cac:TaxTotal']['cbc:TaxAmount']['#text'])
                        kdvOran = int(float(urun['cac:TaxTotal']['cac:TaxSubtotal']['cbc:Percent']))
            satirno = int(urun['cbc:ID'])
            brut = miktar * birimFiyat
            vdtt = float(urun['cbc:LineExtensionAmount']['#text']) + kdv + diger - iskonto
            sorguGonder += "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}'),".format(
                i['firmaid'], i['vknTckn'], malkodu[0:50], maladi[0:150], miktar, birim, birimFiyat, iskonto, kdv,
                kdvOran,
                diger, i['faturaNo'], i['ettn'], satirno, brut, vdtt, i['faturaTarihi']
                , i['islemTarihi'], i['id'], ffff)
        self.cursor.execute(sorguGonder[:-1])
        self.cursor.commit()

    def kalemIsleIrsaliye(self,i,ffff,xml):
        sorguGonder = 'INSERT INTO deaf_kalemler_irsaliye (k_firma_id,k_vkn,k_malkodu,k_maladi,k_miktar,k_birim,k_fatura_no,k_ettn,k_satir_no,k_fatura_tarih,k_islem_tarih,k_fatura_id,k_fatura_tipi) VALUES '
        if 'DespatchAdvice' in xml.keys():
            kv = xml['DespatchAdvice']
        else:
            kv = xml['q1:DespatchAdvice']
        kalemler = kv['cac:DespatchLine'] if type(kv['cac:DespatchLine']) == list else [
            kv['cac:DespatchLine']]
        for urun in kalemler:
            maladi = urun['cac:Item']['cbc:Name'].replace("'", "")
            malkodu = ''
            if 'cac:SellersItemIdentification' in urun['cac:Item'].keys():
                if 'cbc:ID' in urun['cac:Item']['cac:SellersItemIdentification'].keys():
                    malkodu = urun['cac:Item']['cac:SellersItemIdentification']['cbc:ID'] if type(
                        urun['cac:Item']['cac:SellersItemIdentification']['cbc:ID']) == str else ''
                else:
                    malkodu = urun['cac:Item']['cbc:Name'].replace("'", "")
            birim = urun['cbc:DeliveredQuantity']['@unitCode']
            birimFiyat = 0
            miktar = int(float(urun['cbc:DeliveredQuantity']['#text']))
            satirno = int(urun['cbc:ID'])
            sorguGonder += "('{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}','{}'),".format(
                i['firmaid'], i['vknTckn'], malkodu[0:50], maladi[0:150], miktar, birim, i['faturaNo'], i['ettn'], satirno, i['faturaTarihi']
                , i['islemTarihi'], i['id'], ffff)
        self.cursor.execute(sorguGonder[:-1])
        self.cursor.commit()
    def kalemIsleIrsaliyeCevap(self,i,ffff,xml):
     try:
        kalemler = xml['ReceiptAdvice']['cac:ReceiptLine'] if type(
            xml['ReceiptAdvice']['cac:ReceiptLine']) == list else [
            xml['ReceiptAdvice']['cac:ReceiptLine']]
        for urun in kalemler:
            satirNo = urun['cbc:ID']
            kabulEdilen = urun['cbc:ReceivedQuantity']['#text'] if type(urun['cbc:ReceivedQuantity']) == dict else urun['cbc:ReceivedQuantity']

            if 'cbc:ShortQuantity' in urun.keys():
                eksikMiktar = urun['cbc:ShortQuantity']['#text'] if type(urun['cbc:ShortQuantity']) == dict else urun['cbc:ShortQuantity']
            else:
                eksikMiktar = 0

            if 'cbc:RejectedQuantity' in urun.keys():
                redMiktar = urun['cbc:RejectedQuantity']['#text'] if type(urun['cbc:RejectedQuantity']) == dict else urun['cbc:RejectedQuantity']
            else:
                redMiktar = 0

            if 'cbc:OversupplyQuantity' in urun.keys():
                fazlaMiktar = urun['cbc:OversupplyQuantity']['#text'] if type(urun['cbc:OversupplyQuantity']) == dict else urun['cbc:OversupplyQuantity']
            else:
                fazlaMiktar = 0
            aciklama = urun['cbc:Note'] if 'cbc:Note' in urun.keys() else 0
            sorgu = "UPDATE deaf_kalemler_irsaliye SET k_teslim_adedi = '{}',k_eksik_adedi = '{}',k_fazla_adedi = '{}',k_donus_adedi = '{}',k_donus_aciklama = '{}' " \
                    "WHERE k_fatura_no = '{}' AND k_ettn = '{}' AND k_satir_no = '{}'".format(int(float(kabulEdilen)),int(float(eksikMiktar)),int(float(fazlaMiktar)),int(float(redMiktar)),aciklama,
                                                                                              i['faturaNo'],i['ettn'],int(float(satirNo)))
            self.cursor.execute(sorgu)
            self.cursor.commit()
     except Exception as e:
        print(e)
    
    def execQuery(self,query):
        self.cursor.execute("{}".format(query))
        columns = [column[0] for column in self.cursor.description]
        results = list()
        for i in self.cursor.fetchall():
            results.append(dict(zip(columns, i)))
        return results
    
    def updateQuery(self,query):
        self.cursor.execute("{}".format(query))
        self.cursor.commit()
