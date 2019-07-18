---
layout : post
title : "智能消防疏散管理系统归档"
category : 工程项目
duoshuo: true
date : 2015-07-27
tags : [Project]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

**智能消防疏散管理系统**简单来说，主要包括如下功能:

* **对下位机通过总线上传的数据进行管理和图形化显示**

* **根据用户的操作通过总线向下位机发送相应的数据**

* **对数据库进行管理，及对图形进行编辑等操作**

软件过程中，有密码保护功能，根据用户权限开放不同功能(两级权限，**用户权限**和**工程调试权限**)

软件具体功能包括:消音、复位、手动应急、状态指示灯、相关信息浏览、预案编辑、系统图层编辑、应急预案编辑等。

**软件部分界面图示**

<div>  
  <img src='/res/img/blog/2015/07/27/firesystem1.png' width="220px"/>
  <img src='/res/img/blog/2015/07/27/firesystem2.png' width="220px"/>
  <img src='/res/img/blog/2015/07/27/firesystem3.png' width="220px"/>
  <img src='/res/img/blog/2015/07/27/firesystem4.png' width="220px"/>
</div>

<!-- more -->

关于**周立功USBCAN**测试工具

**测试原理**

测试平台由上位机软件**ZLGCANTest**和**CAN多主测试网络**组成。当被测试 CAN 产品正确配置后上位机软件 ZLGCANTest 能够同时连接不同的 CAN 产品，包括不同的PCI插卡各种转接卡等并对 CAN产品进行控制，包括数据的收发和错误的处理等。

**CAN多主测试网络**是一个基于PeliCAN的多主网络。网络中每一个节点均支持自发自收，连续发送CAN报文、高速发送CAN报文和接收CAN报文并显示接收帧数,还能配置每一个节点的验收代码滤波器验收屏蔽滤波器以及总线波特率设置。

这样，在测试中，只要将测试产品接入到这个测试网络，并连接上测试软件**ZLGCANTest**，就能进行全面的CAN特性测试。

本项目中CAN设备型号选择**USB-CAN-2E-U**,在配置相关参数(**波特率、设备索引号**)信息后，初始化CAN成功后，看能否**启动CAN**，并且数据是否能够**正常收发**。测试网络如图:

![CAN测试](/res/img/blog/2015/07/27/usbcan.png)

---

**关于设备ID定义**

定义所有设备ID方式:**AA-BB-CC(AA-集中电源号,BB-配电柜号，CC-灯具号)**，其中，**AA(0,10],BB(0,8],CC(0,256]**

* **集中电源表示方法:** AA=集中电源号，BB=0,CC=0；

* **配电柜表示方法:** AA=集中电源号，BB=配电柜号,CC=0；

* **灯具表示方法:** AA=集中电源号，BB=配电柜号,CC=灯具号；

* **集中控制器主机表示方法:** AA=0，BB=0,CC=2，即0-0-2；

* **集中控制器备机表示方法:** AA=0，BB=0,CC=1，即0-0-1；

智能消防疏散管理系统CAN通讯ID格式图示:

![CAN通讯ID](/res/img/blog/2015/07/27/id.png)


