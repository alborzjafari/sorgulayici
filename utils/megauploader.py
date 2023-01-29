from mega import Mega
import os
import json
import requests

class megaUploader:
    def __init__(self):
        self.url = 'https://cdn.ffatura.com/'
    def upload(self,file,path):
        folder = self.mega.find(path)
        return self.mega.get_upload_link(self.mega.upload(file,folder[0]))
    def download(self,url,filename):
        return self.mega.download_url(url,self.getDir(),filename)
    def findFolder(self, foldername):
        return self.mega.find(foldername, exclude_deleted=True)
    def getDir(self):
        return os.getcwd() + '/download'
    def getFiles(self):
        return self.mega.get_files()
    def getSpace(self):
        return self.mega.get_storage_space(mega=True)
    def destroyFile(self, fileID):
        self.mega.destroy(fileID)
    def createFolder(self,foldername,destination=None):
        a = requests.post(f'{self.url}create2/', data=json.dumps({'yol': '{}{}'.format(destination,foldername)}))
        return a.json()['result']
    def uploadWithId(self, file, folderid):
        a = requests.post(f'{self.url}upload/', files={'file':open(f'{file}', 'rb')}, data={'yol': f'{folderid}'})
        return a.json()['yol']
    def createFolderNew(self,liste):
        a = requests.post(f'{self.url}create/',data=json.dumps({'yol':liste}))
        return a.json()