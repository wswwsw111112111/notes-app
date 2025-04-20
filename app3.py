from flask import Flask, render_template,request,Response,session,url_for
import config
# from config_class import *
from datetime import timedelta
app = Flask(__name__)
#是使用config.py文件定义配置
app.config.from_object(config)
#是使用
# app.config.from_object(DebugConfig)

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)#设置session保存时间



@app.route('/')

def index():
    return render_template('table_lianliankan.html')
@app.route('/login.do',methods=['POST','GET'])
def login():
    print(url_for('login'))#通过函数名找函数对应的地址
    userName = request.form.get('userName')#表单提交的数据用form
    #链接提交的数据用arg
    userPwd = request.form.get('userPwd')
    if userName=='zhangsan' and userPwd=='123456':
        session['user']='zhangsan'

        return render_template('table_lianliankan.html')
        pass
    elif userName != None and (userName != 'zhangsan' or userPwd != ' 123456'):
        return render_template('login.html',message='用户名或密码错误')

    return render_template('login.html')

    pass
@app.route('/logout.do',methods=['POST,GET'])
def logout():
    pass



if __name__ == '__main__':
    app.run(host="0.0.0.0",port=3000,debug=True)

