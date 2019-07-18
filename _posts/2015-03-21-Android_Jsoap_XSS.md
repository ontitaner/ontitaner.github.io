---
layout : post
title : "消除不受信任的HTML (来防止XSS攻击)"
category : Android
duoshuo: true
date : 2015-07-24
tags : [Android , Jsoap , XSS ]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

###问题：###

在做网站的时候，经常会提供用户评论的功能,有些不怀好意的用户,会搞一些脚本到评论内容中，而这些脚本可能会
破坏整个页面的行为，更严重的是获取一些机要信息，此时需要清理该HTML，以避免跨站脚本cross-site 
scripting攻击（XSS）。

<!-- more -->

**方法**

使用jsoup HTML Cleaner 方法进行清除，但需要指定一个可配置的 Whitelist。
		
![picture1](/res/img/blog/2015/03/21/pic1.png)

**说明**
		
XSS又叫CSS (Cross Site Script) ，跨站脚本攻击。它指的是恶意攻击者往Web页面里插入恶意html代码，当用户浏览
该页之时，嵌入其中Web里面的html代码会被执行，从而达到恶意攻击用户的特殊目的。XSS属于被动式的攻击，因为其被
动且不好利用，所以许多人常忽略其危害性。所以我们经常只让用户输入纯文本的内容，但这样用户体验就比较差了。一
个更好的解决方法就是使用一个富文本编辑器WYSIWYG如CKEditor 和 TinyMCE。这些可以输出HTML并能够让用户可视化编
辑。虽然他们可以在客户端进行校验，但是这样还不够安全，需要在服务器端进行校验并清除有害的HTML代码，这样才能
确保输入到你网站的HTML是安全的。否则，攻击者能够绕过客户端的Javascript验证，并注入不安全的HMTL直接进入您的
网站。jsoup的whitelist清理器能够在服务器端对用户输入的HTML进行过滤，只输出一些安全的标签和属性。jsoup提供
了一系列的Whitelist基本配置，能够满足大多数要求；但如有必要，也可以进行修改，不过要小心。这个cleaner非常好
用不仅可以避免XSS攻击，还可以限制用户可以输入的标签范围。
