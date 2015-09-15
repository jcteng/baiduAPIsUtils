# baiduAPIsUtils
Utils Package for Baidu's access
===============
百度小工具
==========
##oauth：

认证方式                                  说明

*deviceAuth：设备认证方式    +使用时直接将百度OAUTH的key和sert 填到oauth.py里面即可。
*Bypy                        +借用bypy的认证key，实现百度oauth登录。不需要申请百度应用，有百度用户名和密码即可使用。好处是可以使用pcs权限


##pcs:


                                 说明

*pcs openrest实现            +    主要是上传接口，支持分块上传
                             +openrest 的权限只能在/apps/<your application>/下建立和访问文件
                             +如果直接使用bypy认证，可以在此处访问 /apps/bypy


##fakelogin:

模仿web方式的登录，可以用来访问一些oauth权限不够的信息


