import datetime
import requests
import json
import time

class hizliServis:
    def __init__(self,user,password):
        self.url = 'https://service.hizliteknoloji.com.tr/HizliApi/RestApi/'
        self.headers = {'username':user,'password':password,'Content-Type':'application/json'}
        print(user,password)

    def get(self, method, params):
        responser = requests.get(self.url+method,headers=self.headers,params=params)
        if responser.status_code != 200:
            return None
        return responser.json()

    def post(self,method,data):
        responser = requests.post(self.url+method,headers=self.headers,data=json.dumps(data))
        if responser.status_code != 200:
            return None
        return responser.json()

    def get_documents(self, app_type):
        bugun = datetime.datetime.now()
        dun = bugun - datetime.timedelta(days=15)
        while True:
            sonuc = self.get('GetDocumentList',
                             {'DateType': 'CreatedDate',
                              'TakenFromEntegrator': 'ALL',
                              'StartDate': dun.strftime('%Y-%m-%d'),
                              'EndDate': bugun.strftime('%Y-%m-%d'),
                              'AppType': app_type,
                              'IsNew': False,
                              'IsExport': False,
                              'IsDraft': False
                              })
            if sonuc == None:
                print("sleeping 15")
                time.sleep(1)
                continue
            else:
                return sonuc['documents']

    def getDocumentReceiver(self):
        bugun = datetime.datetime.now()
        dun = bugun - datetime.timedelta(days=30)
        while True:
            sonuc = self.get('GetDocumentReceiverAllList',
                             {'DateType': 'CreatedDate', 'TakenFromEntegrator': 'Yes',
                              'StartDate': dun.strftime('%Y-%m-%d'),
                              'EndDate': bugun.strftime('%Y-%m-%d')})

            if sonuc == None:
                print("sleeping 15")
                time.sleep(1)
                continue
            else:
                return sonuc['documents']

    def download_media(self, app_type, uuid, file_type):
        while True:
            print("before get")
            sonuc = self.get('GetDocumentFile',
                             {'AppType': int(app_type),
                              'Uuid': uuid,
                              'Tur': file_type,
                              'IsDraft': False})
            print("after get")
            if sonuc == None:
                time.sleep(1)
                print("NONE")
                continue
            else:
                return sonuc['DocumentFile']
                
    def downloadMedia(self,appType,uuid,filetype):
        while True:
            sonuc = self.get('GetDocumentFile',{'AppType': int(appType), 'Uuid': uuid, 'Tur': filetype,
                                                           'IsDraft': False})
            if sonuc == None:
                time.sleep(60)
                continue
            else:
                return sonuc['DocumentFile']
    def markRead(self,GUIDList,appType):
        while True:
            sonuc = self.post('SetTakenFromEntegrator', {'GUIDList': GUIDList, 'AppType': appType})
            if sonuc == None:
                time.sleep(60)
                return True
            else:
                return True
    def getDocListGUID(self,faturaTipi,guidList):
        while True:
            sonuc = self.post('GetDocumentListGUID',{'AppType':faturaTipi,'GUIDList':guidList})
            if sonuc == None:
                time.sleep(60)
                continue
            else:
                return sonuc
