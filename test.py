from flask import Flask,url_for
from flask import request
from flask import redirect
from flask import session
import json
# import pymysql
import re
import hashlib
from flask import render_template#样板容器，可以存网页代码

app=Flask(
    __name__,
    static_folder="static",#静态档案的资料夹名称
    static_url_path="/"#静态档案对应的网址路径
)#所有在static资料夹地下的档案，都对应到网址路径/static/档案名称


# @app.route("/page")
# def page():
#     return render_template("page.html")

# @app.route("/",methods=["get"])
# def index():
#     return render_template("index.html")

# @app.route("/hex")
# def hex():
#     return render_template("login.html")
#
@app.route("/show")
def show():
    name=request.args.get("n","")
    return "你好"+name
# @app.route("/hex")
# def hex():



@app.route("/calculate",methods=["post"])
def calculate():
    # maxnumber=request.args.get("max","")
    # 这是get请求方法
    maxnumber=request.form["max"]
    # 这是POST方法
    maxnumber=int(maxnumber)
    result=0
    for n in range(1,maxnumber+1):
        result+=n
    return render_template("result.html",data=result)

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/baidu")
def baidu():
    return render_template("baidu.html")


@app.route("/denglu",methods=["post"])
def denglu():
    user= request.form.get('username')
    pwd=request.form.get('password')
    #数据库查询账号操作
    # db=pymysql.connect(host="47.114.74.235",port=3306,user="root",password="8EC77a119dc8",database="mysql")
    # cursor=db.cursor()
    # cursor.execute("select password from login where username='%s'"%(str(user)))
    # result=cursor.fetchone()
    with open('user.txt', 'r') as f:
        resultlist = f.readlines()
        resultstr = str(resultlist)
        resultstr.replace('\n', '')
    resultname = re.findall(r'({}) password'.format(user), resultstr)
    resultpwd = re.findall(r"{} password:(.+?)'".format(user), resultstr)
    resultpwd = str(resultpwd).replace(r'\\n', '')
    resultpwd = resultpwd.replace("[", '')
    resultpwd = resultpwd.replace("]",'')
    resultpwd = resultpwd.replace("'", '')
    if resultname !=[]:
        if pwd==resultpwd:
            return render_template("index.html")

        else:
            # return "密码错误"
            return redirect(url_for("baidu"))
    else:
        return "用户不存在"


if __name__=="__main__":
    app.run(host="0.0.0.0",port=3000,debug=True)


