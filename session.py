from flask import Flask
from flask import request
from flask import redirect
from flask import session
from flask import render_template#样板容器，可以存网页代码

app=Flask(
    __name__,
    static_folder="static",#静态档案的资料夹名称
    static_url_path="/"#静态档案对应的网址路径
)#所有在static资料夹地下的档案，都对应到网址路径/static/档案名称
app.secret_key="s15648513s185w851s23"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hello")
def hello():
    name=request.args.get("name","")
    session["username"]=name#session ["栏位名称"]=资料
    return "你好，"+name

@app.route("/talk")
def talk():
    name=session["username"]
    return name+",很高兴见到你"


app.run(port=3000,host='0.0.0.0')