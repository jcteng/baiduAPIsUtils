#!/usr/bin/python
# -*- coding:utf-8 -*-
#

#
__author__ = 'nasiry.teng@gmail.com'

import json

from tornado import gen
import json

from  tornadoCookieClient import aClient


class oauthMulti(aClient):
    oauthcfg = {
        "baseURL": "http://openapi.baidu.com/oauth/2.0/",
        "authPage": "authorize",

    }
    # 在这里申请
    # http://developer.baidu.com/console#app/project
    #
    SecretKey = "Put your Key here"
    ClientID = "i830Vq13GUgPFXf5amCfePsc"
    byPyClientID = "q8WE4EpCsau1oS0MplgMKNBn"
    tokens = {}
    datas = {}



    def saveTokens(self):
        import shelve
        cache = shelve.open("tokencontext","c")
        cache["tokens"] =self.tokens
        cache.close()

    def loadToken(self):
        import shelve
        cache = shelve.open("tokencontext")
        try:
            self.tokens = cache["tokens"]
            return True
        except:
            return False

    # share use Bypy's SecretKey from server side
    @gen.coroutine
    def loginBypy(self):
        # TBD
        if self.loadToken()==False:
            urltemplate = " http://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id=%s&redirect_uri=%s&scope=basic,netdisk&display=popup" % (
            self.byPyClientID, 'oob')  # oob is fix by Bypy
            print urltemplate
            print "visit URL above,input/paste your code there"

            auth_code = raw_input().strip()#/bypy-tianze.rhcloud.com
            urltemplate = "https://bypy-tianze.rhcloud.com/auth?code=%s&redirect_uri=%s" % (auth_code, 'oob')  # oob is fix by Bypy
            print urltemplate

            resp = yield self.ac.fetch(urltemplate)
            body = resp.body

            serverJson = json.loads(body)
            self.tokens["access_token"] = serverJson["access_token"]
            self.tokens["refresh_token"] = serverJson["refresh_token"]
            self.tokens["session_key"] = serverJson["session_key"]
            self.tokens["session_secret"] = serverJson["session_secret"]
            self.saveTokens()

        raise gen.Return(True)

    @gen.coroutine
    def loginDevice(self, services):
        urltemplate = "http://openapi.baidu.com/oauth/2.0/device/code?client_id=%s&response_type=device_code&scope=%s" % (
        self.ClientID, services)
        resp = yield self.ac.fetch(urltemplate)
        deviceJson = json.loads(resp.body)
        self.tokens["device_code"] = deviceJson["device_code"]
        print deviceJson
        raise gen.Return(resp.body)


    @gen.coroutine
    def grantDevice(self):
        "before call this ,please confirm user_code with QR code or verification_url from web side"
        urltemplate = "https://openapi.baidu.com/oauth/2.0/token?grant_type=device_token&code=%s&client_id=%s&client_secret=%s" % (
        self.tokens["device_code"], self.ClientID, self.SecretKey)
        resp = yield self.ac.fetch(urltemplate)
        deviceJson = json.loads(resp.body)
        self.tokens["access_token"] = deviceJson["access_token"]
        self.tokens["refresh_token"] = deviceJson["refresh_token"]
        self.tokens["session_key"] = deviceJson["session_key"]
        self.tokens["session_secret"] = deviceJson["session_secret"]
        raise gen.Return(resp.body)
