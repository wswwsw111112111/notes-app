from flask import Flask
from flask import request
from flask import redirect
from flask import render_template
import json
app=Flask(__name__)#代表目前执行的模组
#建立Application 物件，可以设定静态档案的路径处理

app=Flask(
    __name__,
    static_folder="static",#静态档案的资料夹名称
    static_url_path="/static"#静态档案对应的网址路径
)#所有在static资料夹地下的档案，都对应到网址路径/static/档案名称




#建立路径/getSum对应的处理韩式
#利用要求子串(Query String)提供弹性:/getSum?max=最大数字

@app.route("/getSum")
def getSum(): #1+2+3...+max
    maxNumber=request.args.get("max",100)
    maxNumber=int(maxNumber)
    print("最大字数",maxNumber)
    result=0
    for n in range(1,maxNumber+1):
        result+=n
    return "结果："+str(result)


@app.route("/")#函数装饰器
def home():
    # return redirect("https:www.google.com/")#导向到路径https:www.google.com/



    print("请求方法",request.method)
    print("通讯协定",request.scheme)
    print("主机名称",request.host)
    print("路径",request.path)
    print("完整的网址",request.url)
    print("浏览器和作业系统",request.headers.get("user-agent"))
    print("引荐网址",request.headers.get("referrer"))
    lang=request.headers.get("accept-language")
    if lang.startswith("en"):
        return redirect("/en/")
        # return json.dumps({
        #     "status":"Hello Flask",
        #     "text":"Hello world"})
    else:
        return redirect("/zh/")
        # return json.dumps({
        #     "status":"Hello Flask",
        #     "text":"你好，欢迎光临"},ensure_ascii=False)#不要用ASCII编码处理中文

@app.route("/en/")
def index_english():
    return json.dumps({
            "status":"Hello Flask",
            "text":"Hello world"})


@app.route("/te/")
def te():
    return render_template("index",name="胡子哥")


@app.route("/zh/")
def index_chinese():
        return json.dumps({
            "status":"Hello Flask",
            "text":"你好，欢迎光临"},ensure_ascii=False)#不要用ASCII编码处理中文



@app.route("/test")
def test():
    return "my test"


@app.route("/user/<username>")
def handleUser(username):
    if username=="ww":
        return "你好！"+username
    else:
        return "Hello!"+username
if __name__=="__main__":
    #启动网站伺服器，可以透过port参数指定端口号
    app.run(port=3000)