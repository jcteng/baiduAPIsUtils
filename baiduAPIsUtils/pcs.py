#!/usr/bin/python
# -*- coding:utf-8 -*-
#

#
__author__ = 'nasiry.teng@gmail.com'

from oauth import oauthMulti
from tornado import gen

from  tornado.escape import  url_escape
import json


import hashlib
import datetime

class bdpcs_open(oauthMulti):


    bdpcs_cfg={
        "UPLOADTHRESHOLD":1024*1024*4,#upload 4M onetime max ,single file in 4GB
        "SUPERFILE_PREFIX":"onloading_",
        "MAX_SCAN_TASKS":5,#MAX_SCAN_TASK in sametime
    }
    uploadTasksList = {



    }
    @gen.coroutine
    def getQuota(self):
        urlTemplate = "https://pcs.baidu.com/rest/2.0/pcs/quota?method=info&access_token=%s"%self.tokens["access_token"]
        resp = yield  self.fetch(urlTemplate)

        print json.loads(resp.body)
        raise gen.Return(json.loads(resp.body))

    def encode_baidu_formdata(self, datastream,filename):
        #refernece PHP
        # $boundary = md5 ( time () );
        # $postContent .= "--" . $boundary . "\r\n";
        # $postContent .= "Content-Disposition: form-data; name=\"file\"; filename=\"{$fileName}\"\r\n";
        # $postContent .= "Content-Type: application/octet-stream\r\n\r\n";
        # $postContent .= $fileContent . "\r\n";
        # $postContent .= "--" . $boundary . "\r\n";
        filename.encode("utf-8")
        md = hashlib.md5()
        md.update(str(datetime.datetime.utcnow()))
        boundary =md.hexdigest()
        postContent = "--" + boundary + "\r\n";
        postContent += 'Content-Disposition: form-data; name="file";'+'filename="'+filename+'"\r\n'
        postContent +="Content-Type: application/octet-stream\r\n\r\n"

        postContent += datastream

        postContent += "--" + boundary + "\r\n";
        return  postContent,boundary


    #we can only upload the data into the folder we created under apps
    @gen.coroutine
    def uploadFile(self,localPath,targetPath,datastream=None,isOverWrite=False,isCreateSuperFile=False):
        targetPath= url_escape(targetPath)

        if isOverWrite:
            ondup = 'overwrite'
        else:
            ondup ="newcopy"
        import os

        if isCreateSuperFile:
            appendURL = "&type=tmpfile"
        else:
            appendURL =""

        if datastream==None:
            fp = open(localPath,"rb")
            datastream = fp.read()
            fp.close()

        md = hashlib.md5()
        md.update(datastream)
        md5sum =md.hexdigest()


        fname = os.path.basename(localPath)
        urlTemplate = "https://c.pcs.baidu.com/rest/2.0/pcs/file?method=upload&path=%s&access_token=%s&ondup=%s%s"%(targetPath,self.tokens["access_token"],ondup,appendURL)
        body,boundary = self.encode_baidu_formdata(datastream,fname)
        headers = {"Content-Type":'multipart/form-data; boundary=%s'%boundary}
        resp = yield  self.fetch(urlTemplate,method="POST",body =body,headers=headers)
        jsonresp = json.loads(resp.body)
        if md5sum!=jsonresp["md5"]:
            raise IOError("md5 check error","in __file__")

        raise gen.Return(jsonresp)

    @gen.coroutine
    def makeDir(self,targetPath):
        targetPath = url_escape(targetPath)
        urlTemplate = "https://pcs.baidu.com/rest/2.0/pcs/file?method=mkdir&access_token=%s&path=%s"%(self.tokens["access_token"],targetPath)
        body=""
        resp = yield  self.fetch(urlTemplate,method="POST",body =body)
        raise gen.Return(json.loads(resp.body))

    @gen.coroutine
    def getMeta(self,targetPath):
        targetPath = url_escape(targetPath)
        urlTemplate = "https://pcs.baidu.com/rest/2.0/pcs/file?method=meta&access_token=%s&path=%s"%(self.tokens["access_token"],targetPath)
        resp = yield  self.fetch(urlTemplate)
        raise gen.Return(json.loads(resp.body))

    @gen.coroutine
    def uploadSuper(self,localPath,targetPath,isOverWrite=False):
        import os
        targetPath = url_escape(targetPath)
        fname = os.path.basename(localPath)
        #dstDir = targetPath+self.bdpcs_cfg["SUPERFILE_PREFIX"]+fname
        try:
            self.uploadTasksList[localPath] =dict()
            self.uploadTasksList[localPath]["dstDir"] = targetPath
            self.uploadTasksList[localPath] ["blocklist"] = dict()
        except:
            meta = yield self.getMeta(targetPath)
        print self.uploadTasksList
        yield  self.scanFile(localPath)

    @gen.coroutine
    def scanFileTask(self,localPath,i):
        #Async File IO shoud be improved here
        print "this is task[%d]"%i
        import mmap
        import contextlib
        import os

        with open(localPath, 'rb') as f:
            for block in  self.uploadTasksList[localPath] ["blocklist"]:
                blk = self.uploadTasksList[localPath] ["blocklist"][block]
                if blk["state"] == "notouched":
                    import  time
                    tstart = time.time()
                    blk["state"] = "on_task_%d"%i
                    print blk["state"],blk["startaddr"]

                    f.seek(blk["startaddr"])
                    ds= f.read(self.bdpcs_cfg["UPLOADTHRESHOLD"])
                    try:
                    #if True:
                        resp =yield  self.uploadFile(datastream=ds,isCreateSuperFile=True,localPath=localPath,targetPath=(self.uploadTasksList[localPath]["dstDir"]))
                        blk["state"] = "done"
                        blk["md5"] = resp["md5"]
                        print "md5 ok"
                    except :
                    #    print Exception.strerror
                    #else:
                        blk["state"] = "notouched" #make it back
                        print "md5 mismatch"
                    tend = time.time()
                    print "done %d[%d]"%(i,(self.bdpcs_cfg["UPLOADTHRESHOLD"]/1024)/(tend-tstart))
                else:
                    print blk["state"],"SKIP",i
        f.close()

    @gen.coroutine
    def mergeFiles(self,localPath):
          blklist = self.uploadTasksList[localPath] ["blocklist"].keys()
          blklist.sort()
          print blklist
          urlTemplate = "https://pcs.baidu.com/rest/2.0/file?method=createsuperfile&path=%s&access_token=%s"%(self.uploadTasksList[localPath]["dstDir"],self.tokens["access_token"])
          pcs_block_list = dict()
          pcs_block_list["block_list"] = list()
          for blk in blklist:
              pcs_block_list["block_list"].append(self.uploadTasksList[localPath] ["blocklist"][blk]["md5"])

          body = "param="+json.dumps(pcs_block_list)
          print body
          resp = yield  self.fetch(urlTemplate,method="POST",body=body)
          print resp.body
          #print self.uploadTasksList[localPath] ["blocklist"]

    @gen.coroutine
    def scanFile(self,localPath):
    # 0. create split files list
    # 1. do scan file block list as upload tasks
    # 2. upload tasks pick uploadTasksList item to upload
    # 3. Merge all of them into big file

        import os
        fsize = os.path.getsize(localPath)
        index = 0
        for startAddr in range(0,fsize,self.bdpcs_cfg["UPLOADTHRESHOLD"]):
            #print startAddr

            self.uploadTasksList[localPath] ["blocklist"][("block%6d"%index)] = dict()
            self.uploadTasksList[localPath] ["blocklist"][("block%6d"%index)]["state"] ="notouched"
            self.uploadTasksList[localPath] ["blocklist"][("block%6d"%index)]["md5"] =""
            self.uploadTasksList[localPath] ["blocklist"][("block%6d"%index)]["startaddr"] =startAddr
            index +=1
        #print self.uploadTasksList
        #No Async block io usable .So no need to scan in parallelism,  let's do scan and upload in same task
        print self.uploadTasksList[localPath] ["blocklist"]
        while True:

            yield [self.scanFileTask(localPath,i) for i in range(self.bdpcs_cfg["MAX_SCAN_TASKS"])]

            onLoading = False;
            for block in self.uploadTasksList[localPath] ["blocklist"]:
                if self.uploadTasksList[localPath] ["blocklist"][block]["state"] == "done":
                    continue
                else:
                    onLoading = True;
                    break;

            if onLoading==False:
                #all uploaded
                #let do merge them
                yield self.mergeFiles(localPath)
                print "upload finished"
                return

