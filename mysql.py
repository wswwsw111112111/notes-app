import pymysql
import requests
def denglu():
    list={
        'username': "ww",
        'password': "ww"
    }
    db=pymysql.connect(host="47.114.74.235",port=3306,user="root",password="8EC77a119dc8",database="mysql")
    cursor=db.cursor()
    cursor.execute("select password from login where username=%s"%("qq") + "'" + str(list["username"]) + "'")
    result=cursor.fetchone()

    if list["password"] in result:
        print("登录成功")
    else:
        print("密码错误")
if __name__ =="__main__":
    denglu()