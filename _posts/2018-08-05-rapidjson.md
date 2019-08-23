---
layout : post
title : "rapidjson使用过程中的小坑"
category : C
duoshuo: true
date : 2017-08-05
tags : [C]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

rapidjson是腾讯的开源json解析框架,用c++实现,全部代码仅用header file实现,容易集成在项目中使用

最近在使用rapidjson过程中,发现封装字符串出现了乱码,但是仔细检查代码,均未发现问题,上网寻找良策,
发现如下相关内容

现象：
\u00000\u0004T_\u0000\u0000E html&gt;&lt;html&gt;
&lt;head&gt;&lt;meta http-equiv=\"Content-Type\" content=\"text/html; 
charset=utf-8\"&gt;

<!-- more -->

---

使用rapidjson时出现以上问题:

1.不是完整的内容，2.多次转义"\"


bid.AddMember("adm", rapidjson::StringRef(html_snippet.c_str(),html_snippet.size()), allocator);


stringRef(html_snippet.c_str())一开始以为可能可能是字符串结束标志问题,
这种方式会调动C的strlen去查找\0判断字符串结束，而指定字符串长度的
size后仍然会有\u00000的乱码出现.

使用另一种方式，未出现此种问题：
Value str_val;
str_val.SetString(html_snippet.c_str(),html_snippet.length(),allocator);
bid.AddMember("adm", str_val, allocator);

等价的方式：
stringRef(html_snippet.c_str()，Value().SetString(html_snippet.c_str(),allocator).Move(),allocator)

回去仔细查看手册对比源码,这两种方式的差异是StringRef是引用转移,也就是把指针指向了真正内容所在的内存区域。
而第二种方式是值copy的方式,会分配内存把字符串复制一份副本,所以问题的根源是html_snippet是临时局部变量,
在document对象序列成json string是html_snippet局部变量已被析构,故转移的方式指向的内存区域是未知的,
导致了\00000的出现。

2.多次转义\是嵌套json 对象导致。

看了上述内容,发现和自己遇到的问题雷同,区别在于封装字符串的过程中发现字符串没有按照定义的内容去封装,反而封装了
该字符串变量最后一次赋的值,试了一下上述方法,奏效。

<pre class="brush: c; ">

rapidjson::Value point_val(rapidjson::kObjectType);
rapidjson::Value str_val;

point_with_suffix = cfgHdl.m_HisDataSvrCfg["avg_10m"];
str_val.SetString(
    point_with_suffix.c_str(),
    point_with_suffix.size(), 
    doc.GetAllocator());
point_val.AddMember(
    "arg", 
    statistic_iter->avg_10m, 
    doc.GetAllocator());

</pre>


