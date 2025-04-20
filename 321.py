from flask import Flask
from flask import request
from flask import redirect
from flask import session
import json
import time
import pymysql
from flask_script import Manager
from flask import render_template#样板容器，可以存网页代码
app=Flask(
    __name__,
    static_folder="static",#静态档案的资料夹名称
    static_url_path="/"#静态档案对应的网址路径
)
manage = Manager(app)
app.config['SECREY_KEY'] = '123456'
@app.route("/<name>")
def welcome(name):
    return "hello s%"%(name)

@app.route("/request")
def request():
    output={
        'basic_url':request.base_url,
        'host_url':request.host_url,
        'accept_mimepath':request.path
    }
@app.route("/setcookie/")
def setcookie():
    resp = make_response("cookie设置成功")
    resp.set_cookie('name','bill',expires=(time.time()+10))
    return resp

@app.route('/getcookie/')
def getcookie():
    name=request.cookies.get('name','不知者无畏')
    return name





if __name__ == '__main__':
    Manager.app()