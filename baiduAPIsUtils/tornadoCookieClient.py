#!/usr/bin/python
# -*- coding:utf-8 -*-
#

#
__author__ = 'nasiry.teng@gmail.com'


import tornado.httpclient
import re
import Cookie
import gzip



try:
    import urllib.parse as urlparse  # py3
except ImportError:
    import urlparse   # Python 2.6+

class aClientCookie(Cookie.SmartCookie):
    def outputres(self,domain):
        ret = ""
        for key in self.keys():
            if domain.find(self.get(key)["domain"])>=0:
                ret+= key+"="+self.get(key).value+";"


        ret = ret.replace("\n","").replace("\r","").replace(" ","")
        return ret
            
import mimetypes
class aClient(object):



    def __init__(self,config=None):
        self.ac = tornado.httpclient.AsyncHTTPClient()
        self.cookie = aClientCookie()

    def get_content_type(self,filename):
        return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


    #usegae :        content_type,body = self.encode_multipart_formdata(files)
    #just post the body is fine
    def encode_multipart_formdata(self, files,fields=None,):
            """
                fields is a sequence of (name, value) elements for regular form fields.
                files is a sequence of (name, filename, value) elements for data to be
                uploaded as files.
                Return (content_type, body) ready for httplib.HTTP instance
            """
            BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
            CRLF = '\r\n'
            L = []
            if fields!=None:
                for (key, value) in fields:
                    L.append('--' + BOUNDARY)
                    L.append('Content-Disposition: form-data; name="%s"' % key)
                    L.append('')
                    L.append(value)
            if files!=None:
                for (key, filename, value) in files:
                    filename = filename.encode("utf8")
                    L.append('--' + BOUNDARY)
                    L.append(
                        'Content-Disposition: form-data; name="%s"; filename="%s"' % (
                            key, filename
                        )
                    )
                    L.append('Content-Type: %s' % self.get_content_type(filename))
                    L.append('')
                    L.append(value)
            L.append('--' + BOUNDARY + '--')
            L.append('')
            body = CRLF.join(L)
            content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
            return content_type, body
    # save Cookies
    def procHeaders(self, *args, **kwargs):
        scre = re.compile('^Set-Cookie:(.)')
        for line in args:
            matched = scre.search(line)
            if matched:
                self.cookie.load(line)

    def fetch(self,url,callback=None, raise_error=True, headers=None,**kwargs):



        outheaders = tornado.httputil.HTTPHeaders()
        outheaders["Cookie"] = self.cookie.outputres(urlparse.urlparse(url).hostname)
        outheaders["Accept"] = "*/*"
        outheaders["Accept-Encoding"] =  'deflate' #do not enable gzip here
        outheaders['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.116 Safari/537.36'
        if headers!=None:
            for key in headers:
                outheaders[key] =  headers[key]




        print "rcc:"+url
        return  self.ac.fetch(url,callback=callback,header_callback=self.procHeaders,headers=outheaders,raise_error=raise_error, **kwargs)



