var express=require("express");
var app=express();
app.get("/",function(req,res){
	res.send("Hello World");
});
app.get("/mypath",function(req,res){
    res.send("this is my path");
});

app.listen(3000,function(){
    console.log("伺服器已经启动在 http://localhost:3000/");
});