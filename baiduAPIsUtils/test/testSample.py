#!/usr/bin/python
# -*- coding:utf-8 -*-
#

#
__author__ = 'nasiry.teng@gmail.com'

import tornado

from tornado import  httpclient
from tornado import gen


from baiduAPIsUtils import tornadoCookieClient
from baiduAPIsUtils import pcs




@gen.coroutine
def runner_deviceLogin():



    bdoauth = pcs.bdpcs_open()

    yield  bdoauth.loginDevice("basic,netdisk")
    #waiting on grant
    raw_input()
    yield bdoauth.grantDevice()
    #yield bdoauth.getQuota()
    yield bdoauth.uploadSuper("1.jpg","/apps/tornado-pcs/1.jpg",isOverWrite=True)


# 仅能写入 /apps/bypy 下的文件
@gen.coroutine
def runnerBypy():
    bdoauth = pcs.bdpcs_open()
    yield bdoauth.loginBypy()
    yield bdoauth.getQuota()
    yield bdoauth. makeDir("/apps/bypy/123")
    yield bdoauth.uploadFile("1.jpg","/apps/bypy/123/",isOverWrite=True)
    yield bdoauth.uploadSuper("1.jpg","/apps/bypy/123/1.jpg",isOverWrite=True)

from baiduAPIsUtils import fakelogin
@gen.coroutine
def runnerfakeLogin():
    fl = fakelogin.fakeLogin()
    #put your password here
    fl.getLogin(username ,password)

io_loop = tornado.ioloop.IOLoop.instance()

#io_loop.add_timeout(0,runner_deviceLogin)
#io_loop.add_timeout(0,runnerBypy)
io_loop.add_timeout(0,runnerfakeLogin)
io_loop.start()