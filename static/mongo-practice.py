#载入pymongo套件
import pymongo
from bson.objectid import ObjectId
#连线到MongoDB云端资料库
#把资料放入云端数据库
client = pymongo.MongoClient("mongodb+srv://root:root123@cluster0.wurvq.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = client.website#选择要操作的数据库
collection=db.members#选择操作users集合
#把资料新增到集合中
# result=collection.insert_one({
#     "name":"蜡笔小新",
#     "gender":"男"
# })
# print(result.inserted_id)
# result=collection.insert_many([{
#     "name":"殷桃小丸子",
#     "email":"john@john.com",
#     "password":"mary"


# },{
#     "name":"修川地藏",
#     "email":"john@john.com",
#     "password":"mary"
# }])

# data=collection.find_one(
#     ObjectId("6129f8d498677d7ad6ed7482")
# )
# print(data)

#一次取得多笔资料s
# cursor=collection.find()
# print(cursor)
# for doc in cursor:
#     print(doc["name"])

#更新集合中的一笔文件资料
result=collection.update_many({
    "email":"john@john.com"
},{
    "$set":{
        "password":"nishibushizhende"
    },
    "$set":{
        "level":3    #给
    },
    "$inc":{
        "level":2
    }
})
print("符合条件的文件数量",result.matched_count)
print("实际更新的文件数量",result.modified_count)
