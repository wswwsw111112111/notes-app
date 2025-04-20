import re
import hashlib
with open('user.txt','r') as f :
     resultlist=f.readlines()
     resultstr=str(resultlist)

username='wswwsw'
h=hashlib.md5()
h.update(b'wswwsw')
print(h.hexdigest())
resultname=re.findall(r'({}) password'.format(username),resultstr)
resultpwd=re.findall(r"{} password:(.+?)'".format(username),resultstr)
resultpwd=str(resultpwd).replace(r'\\n','')
resultpwd=resultpwd.replace("'",'')
print(resultname)
print((resultpwd))