import json

import pdfgen
from pdf2image import convert_from_path
from lxml import etree
import xmltodict
import base64
import traceback

class fileGenerator:
    @staticmethod
    def writeJPG(fid,bdata,fd):
        with open('{}/upd/{}.jpg'.format(fd,fid),'wb') as file:
            file.write(base64.b64decode(bdata))
        return '{}/upd/{}.jpg'.format(fd,fid)
    @staticmethod
    def writeXML(fid, bdata,fd):
        with open('{}/upd/{}.xml'.format(fd,fid), 'wb') as file:
            file.write(base64.b64decode(bdata))
        return '{}/upd/{}.xml'.format(fd,fid)
    @staticmethod
    def writeHTML(fid, bdata,fd):
        with open('{}/upd/{}.html'.format(fd,fid), 'wb') as file:
            file.write(base64.b64decode(bdata))
        return '{}/upd/{}.html'.format(fd,fid)
    @staticmethod
    def writePDF(fid, bdata,fd):
        with open('{}/upd/{}.pdf'.format(fd,fid), 'wb') as file:
            file.write(base64.b64decode(bdata))
        return '{}/upd/{}.pdf'.format(fd,fid)
    @staticmethod
    def getB64JPG(fid,fd):
        with open('{}/upd/{}.jpg'.format(fd,fid),'rb') as file:
            file2 = base64.b64encode(file.read()).decode()
        return file2
    @staticmethod
    def getXMLValue(file):
        try:
            file = base64.decodestring(file.encode("utf8"))
            file2 = json.loads(json.dumps(xmltodict.parse(file)))
            return file2
        except:
            return None

    @staticmethod
    def getXMLValue2(fid, fd):
        with open('{}/upd/{}.xml'.format(fd, fid), 'r',encoding='UTF-8') as file:
            file2 = json.loads(json.dumps(xmltodict.parse(file.read())))
        return file2


    @staticmethod
    def getXMLOrg(fid, fd):
        with open('{}/upd/{}.xml'.format(fd, fid), 'r',encoding='UTF-8') as file:
            file2 = file.read()
        return file2
        
    @staticmethod
    def jpgToB64(fid,fd):
        try:
            with open('{}/upd/{}.jpg'.format(fd, fid), 'rb') as fil:
                return base64.b64encode(fil.read()).decode()
        except:
            return None
    @staticmethod
    def xmlToPDF(fid,fd,ftipi):
        with open('{}/upd/{}.xml'.format(fd,fid), 'r',encoding='UTF-8') as file:
            xmlDosya = file.read()
        parseAt = xmltodict.parse(xmlDosya)
        baseAt = json.loads(json.dumps(parseAt))
        baseAl = ''
        invEk = [*baseAt][0]
        if type(baseAt[invEk]['cac:AdditionalDocumentReference']) == list:
            for i in baseAt[invEk]['cac:AdditionalDocumentReference']:
                if 'cac:Attachment' in i.keys():
                    if '.xslt' in i['cac:Attachment']['cbc:EmbeddedDocumentBinaryObject']['@filename']:
                        baseAl = i['cac:Attachment']['cbc:EmbeddedDocumentBinaryObject']['#text']
        else:
            baseAl = baseAt[invEk]['cac:AdditionalDocumentReference']['cac:Attachment']['cbc:EmbeddedDocumentBinaryObject'][
                '#text']

        baseGetirXslt = base64.b64decode(baseAl).decode('utf-8')
        dom = etree.fromstring(xmlDosya)
        try:
            xslt = etree.fromstring(baseGetirXslt.encode('utf-8'))
        except:
            xslt = etree.parse('/sorgula/general.xslt')
        transform = etree.XSLT(xslt)
        dokuman = etree.tostring(transform(dom)).decode()
        dokuman = dokuman.replace(
            'about:blank', '')
        options = {
            'scale': 1.0,
            'format': 'A4',
            'margin': {
                'top': '0.75in',
                'right': '0.75in',
                'bottom': '0.75in',
                'left': '0.75in',
            },
            'printBackground': True
        }
        pdfgen.sync.from_string(dokuman, '{}/upd/{}.pdf'.format(fd,fid),options=options)
        return '{}/upd/{}.pdf'.format(fd,fid)
    @staticmethod
    def pdfToJPG(fd,fid):
        images = convert_from_path('{}/upd/{}.pdf'.format(fd,fid))
        images[0].save('{}/upd/{}.jpg'.format(fd,fid), 'JPEG')
        return '{}/upd/{}.jpg'.format(fd,fid)