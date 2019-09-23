---
layout : post
title : "rapidjson常用操作"
category : C
duoshuo: true
date : 2017-08-05
tags : [C]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

RapidJSON是一个C++的JSON解析器及生成器

* RapidJSON 小而全。它同时支持SAX和DOM风格的API

* RapidJSON 快。它的性能可与 strlen() 相比

* RapidJSON 独立。它不依赖于 BOOST 等外部库。它甚至不依赖于 STL

* RapidJSON 对内存友好。

* RapidJSON 对 Unicode 友好。它支持 UTF-8、UTF-16、UTF-32 (大端序／小端序),
  并内部支持这些编码的检测、校验及转码。

常用的一些操作如下。

<!-- more -->

---


判断合法性及输出
<pre class="brush: c; ">

bool JsonHandle::ValIsDouble(rapidjson::Value & obj_val)
{
	if(!obj_val.IsDouble())
		return false;

	return true;
}

bool JsonHandle::ValIsInt(rapidjson::Value & obj_val)
{
	if(!obj_val.IsInt())
		return false;

	return true;
}

bool JsonHandle::ValIsStr(rapidjson::Value & obj_val)
{
	if(!obj_val.IsString())
		return false;

	return true;
}

string JsonHandle::JsonToStr(const rapidjson::Value & obj_val)
{
	rapidjson::StringBuffer sbBuf;
	rapidjson::Writer&lt;rapidjson::StringBuffer&gt; jWriter(sbBuf);
	obj_val.Accept(jWriter);
	return std::string(sbBuf.GetString());
}

</pre>

常用的封装操作


<pre class="brush: c; ">

{
    "name":"jack",
    "age":18,
    "sub":["a","b"],
    "elp":[ {"a":"A","b":"B"},
            {"c":"C","d":"D"},
          ]
}

//生成json串

std::string build_json_msg(){
 
	rapidjson::Document doc;//生成DOM元素
	doc.SetObject();
    //生成一个分配器
	rapidjson::Document::AllocatorType& 
        allocator = doc.GetAllocator();
 
	//构建键值对
	doc.AddMember("name","jack",allocator);
	doc.AddMember("age",18,allocator);
	//====构建数组元素====["1","2"]
    rapidjson::Value array_sub(rapidjson::kArrayType);
    array_sub.PushBack("a",allocator);
    array_sub.PushBack("b",allocator);
	//================
	doc.AddMember("sub",array_sub,allocator);
	//====构建数组object===[{"1":2,},{}]
    rapidjson::Value array_json(rapidjson::kArrayType);
    rapidjson::Value obj(rapidjson::kObjectType);
    obj.AddMember("a","A",allocator);
    obj.AddMember("b","B",allocator);
    array_json.PushBack(obj,allocator);
 
    rapidjson::Value obj1(rapidjson::kObjectType);
    obj1.AddMember("c","C",allocator);
    obj1.AddMember("d","D",allocator);
    array_json.PushBack(obj1,allocator);
    array_json.PushBack(obj1,allocator);
	doc.AddMember("elp",array_json,allocator);
 
	rapidjson::StringBuffer s;
	rapidjson::Writer&lt;rapidjson::StringBuffer&gt;writer(s);
	doc.Accept(writer);
 
	return std::string(s.GetString());
 
}

//解析json串
{
   "errorCode":0,
   "reason":"OK",
   "result":
   {"userId":10086,"name":"test"},
   
   "numbers":[110,120,119,911]
}


int parseJSON(const char *jsonstr){
	Document d;
	if(d.Parse(jsonstr).HasParseError()){
		printf("parse error!\n");
		return -1;
	}
	if(!d.IsObject()){
		printf("should be an object!\n");
		return -1;
	}
	if(d.HasMember("errorCode")){
		Value &m = d["errorCode"];
		int v = m.GetInt();
		printf("errorCode: %d\n", v);
	}
	printf("show numbers: \n");
	if(d.HasMember("numbers")){
		Value &m = d["numbers"];
		if(m.IsArray()){
			for(int i = 0; i < m.Size(); i++){
				Value &e = m[i];
				int n = e.GetInt();
				printf("%d,", n);
			}
		}
	}
	return 0;
}

</pre>






