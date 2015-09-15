#!/usr/bin/python
# -*- coding:utf-8 -*-
#

#
__author__ = 'nasiry.teng@gmail.com'

from  tornadoCookieClient import aClient
from tornado import gen
import  time


##############################################################################################
# Code prices from bcloud

BAIDU_URL = 'http://www.baidu.com/'
PASSPORT_BASE = 'https://passport.baidu.com/'
PASSPORT_URL = PASSPORT_BASE + 'v2/api/'
PASSPORT_LOGIN = PASSPORT_BASE + 'v2/api/?login'
REFERER = PASSPORT_BASE + 'v2/?login'
# USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0'
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:31.0) Gecko/20100101 Firefox/31.0 Iceweasel/31.2.0'
PAN_URL = 'http://pan.baidu.com/'
PAN_API_URL = PAN_URL + 'api/'
PAN_REFERER = 'http://pan.baidu.com/disk/home'
SHARE_REFERER = PAN_URL + 'share/manage'

# 一般的服务器名
PCS_URL = 'http://pcs.baidu.com/rest/2.0/pcs/'
# 上传的服务器名
PCS_URL_C = 'http://c.pcs.baidu.com/rest/2.0/pcs/'
PCS_URLS_C = 'https://c.pcs.baidu.com/rest/2.0/pcs/'
# 下载的服务器名
PCS_URL_D = 'http://d.pcs.baidu.com/rest/2.0/pcs/'

## 以下常量是模拟的PC客户端的参数.
CHANNEL_URL = 'https://channel.api.duapp.com/rest/2.0/channel/channel?'
PC_USER_AGENT = 'netdisk;4.5.0.7;PC;PC-Windows;5.1.2600;WindowsBaiduYunGuanJia'
PC_DEVICE_ID = '08002788772E'
PC_DEVICE_NAME = '08002788772E'
PC_DEVICE_TYPE = '2'
PC_CLIENT_TYPE = '8'
PC_APP_ID = '1981342'
PC_DEVUID = 'BDIMXV2%2DO%5FFD60326573E54779892088D1378B27C6%2DC%5F0%2DD%5F42563835636437366130302d6662616539362064%2DM%5F08002788772E%2DV%5F0C94CA83'
PC_VERSION = '4.5.0.7'

## HTTP 请求时的一些常量
CONTENT_FORM = 'application/x-www-form-urlencoded'
CONTENT_FORM_UTF8 = CONTENT_FORM + '; charset=UTF-8'
ACCEPT_HTML = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
ACCEPT_JSON = 'application/json, text/javascript, */*; q=0.8'
##############################################################################################
# END Code prices from bcloud
##############################################################################################



import json
import re
import tornado


class fakeLogin(aClient):
    keys = {}
    tokens = {}
    datas = {}
    @gen.coroutine
    def getLogin(self, username, password):
        #################################################################
        # fill cookie with BAIDUID
        #################################################################
        url = ''.join([
            PASSPORT_URL,
            '?getapi&tpl=mn&apiver=v3',
            '&class=login&logintype=basicLogin',
            '&tt=', self.timestamp()
        ])

        resp = yield self.fetch(url)

        #################################################################
        # fill local with token
        #################################################################
        url = ''.join([
            PASSPORT_URL,
            '?getapi&tpl=pp&apiver=v3',
            '&class=login&logintype=basicLogin',
            '&tt=', self.timestamp(),
        ])

        resp = yield self.fetch(url)
        token = json.loads(resp.body.replace("'", '"'))
        self.tokens["token"] = token['data']['token']

        #################################################################
        # fill local RSA keys
        #################################################################
        url = ''.join([
            PASSPORT_BASE, 'v2/getpublickey',
            '?token=', self.tokens['token'],
            '&tt=', self.timestamp()
        ])
        resp = yield self.fetch(url)
        key = json.loads(resp.body.replace("'", '"'))
        self.keys["pubkey"] = key["pubkey"]
        self.keys["key"] = key["key"]

        #################################################################
        # check if we need codeString and vcodetype
        #################################################################
        url = ''.join([
            PASSPORT_URL,
            '?logincheck',
            '&token=', self.tokens['token'],
            '&tpl=mm&apiver=v3',
            '&username=', self.quoteURL(username),
            '&isphone=false',
            '&tt=', self.timestamp()
        ])
        resp = yield self.fetch(url)
        data = json.loads(resp.body.replace("'", '"'))
        self.datas["codestring"] = data["data"]["codeString"]
        self.datas["vcodetype"] = data["data"]["vcodetype"]


        #################################################################
        # found vcode required
        #################################################################
        if self.datas["vcodetype"] != None and self.datas["vcodetype"] != '':
            print self.datas["vcodetype"]
            url = ''.join([
                PASSPORT_BASE,
                'cgi-bin/genimage?',
                self.datas["codestring"],
            ])
            print "[Acces below URL for VerifyPIC :]"
            print url
            # resp = yield self.fetch(url)
            # vpic = open("vcode.jpg","wb")
            # vpic.write(resp.body)
            # vpic.close()
            verifycode = raw_input().strip()

            # resp = yield self.fetch(url)
        else:
            verifycode = ""


        #################################################################
        # Act login
        #################################################################
        password = self.encodeBaiduPassword(password)
        url = PASSPORT_LOGIN
        data = ''.join([
            'staticpage=https%3A%2F%2Fpassport.baidu.com%2Fstatic%2Fpasspc-account%2Fhtml%2Fv3Jump.html',
            '&charset=UTF-8',
            '&token=', self.tokens['token'],
            '&tpl=pp&subpro=&apiver=v3',
            '&codestring=', self.datas["codestring"],
            '&safeflg=0&u=http%3A%2F%2Fpassport.baidu.com%2F',
            '&isPhone=',
            '&quick_user=0&logintype=basicLogin&logLoginType=pc_loginBasic&idc=',
            '&loginmerge=true',
            '&username=', self.quoteURL(username),
            '&password=', self.quoteURL(password),
            '&verifycode=', verifycode,  # from picture self.datas["vcodetype"],
            '&mem_pass=on',
            '&rsakey=', self.keys["key"],
            '&crypttype=12',
            '&ppui_logintime=', self.get_ppui_logintime(),
            '&callback=parent.bd__pcbs__28g1kg',
            '&tt=', self.timestamp()
        ])
        # print data

        resp = yield self.fetch(url, body=data, method="POST")
        # print resp.headers
        # print self.cookie
        content = resp.body.decode()
        match = re.search('"(err_no[^"]+)"', content)
        if not match:
            print resp.body
            raise gen.Return("unknown error")
        else:
            err_no = tornado.escape.parse_qs_bytes(match.group(1))['err_no']
            err_no = int(err_no[0])

            if err_no == 0:  # done
                raise gen.Return("done")
            elif err_no == 18:  # err_no=18 : no cellphone
                raise gen.Return("done")
            elif err_no == 4:  # err_no=18 : no cellphone
                raise gen.Return("wrong password")
            elif err_no == 6:  # err_no = 6 :verifyCode error
                raise gen.Return("wrong verifyCode")
            elif err_no == 120019:  # err_no=120019 : 验证次数过多 请登录网页界面解锁
                raise gen.Return("login too much time")
            elif err_no == 257:  # err_no = 6 :verifyCode error
                raise gen.Return("need verifyCode")
            elif err_no == 400031:  # err_no=120019 : need SMS verify
                raise gen.Return("need SMS verify")
            else:
                print resp.body
                raise gen.Return("unknown error")

    def saveContext(self):
        import shelve
        cache = shelve.open("contextdb", "c")
        cache["cookie"] = self.cookie
        cache["keys"] = self.keys
        cache["token"] = self.tokens
        cache["data"] = self.datas
        cache.close()

    def loadContext(self):
        import shelve
        cache = shelve.open("contextdb")

        self.cookie = cache["cookie"]
        self.keys = cache["keys"]
        self.tokens = cache["token"]
        self.datas = cache["data"]
        cache.close()


    def quoteURL(self, strToQuote):
        return tornado.escape.url_escape(strToQuote)


    def timestamp(self):
        return str(int(time.time() * 1000))


    def get_ppui_logintime(self):
        import random
        return str(random.randint(30000, 58535))

    def encodeBaiduPassword(self,pwd):
        from  Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        import base64
        rsakey = RSA.importKey(self.keys["pubkey"]) #encrypt with RAS key
        rsakey = PKCS1_v1_5.new(rsakey)
        encpwd = rsakey.encrypt(pwd.encode())

        return base64.encodestring(encpwd).decode().replace('\n', '') #encode into base64