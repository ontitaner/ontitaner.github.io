---
layout : post
title : "Android系统架构"
category : Android
duoshuo: true
date : 2015-04-13
tags : [Android]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

Android 手机操作系统是运行在 Linux Kernel 的分层操作系统，一共分为4层，从上到下依次为**应用层、应用框架层、系统运行库层、核心层**，具体分层结构如下图。

![android_system_frame](/res/img/blog/2015/04/13/android_system_frame.png) 

<!-- more -->

* **应用层**(略)

* **应用框架层**

	应用框架层提供API供开发者访问设备硬件、获取位置信息等，不需要关心底层具体的实现机制和硬件实现方式，简化了应用程序开发的框架设计。
	
	主要包括以下组件:
	
	+ **Views(视图)**
	
	+ **Resource(资源管理器)**
		
		提供非代码资源转换和访问，如本地字符串(XML 文件配置)、组件和布局文件
	
	+ **Notification Manager(通知管理器)**
	
		可以在状态栏中显示自定义的提示信息。
	
	+ **Activity Manager(Activity管理器)**
	
		管理Android应用程序界面的生命周期(onCreate--创建、onResume--显示、onpause--暂停、onStop--停止等)，一个手机屏幕界面可以对应一个Activity。
	
* **系统运行库层**
	
	+ **C/C++核心库**
	
		提供必须的C/C++核心库支持对应组件使用，例如(libc、SGL、OpenGL、SQLite、WebKit、SSL)
		
	+ **Dalvik虚拟机运行环境**
	
		运行库包含Android Runtime，核心为Dalvik虚拟机,每个android 应用程序都运行在Dalvik虚拟机上，且每一个应用程序都有独立运行的进程空间：**Dalvik虚拟机**只执行DEX可执行文件。
		
		DEX生成:**java应用程序 --> .class-->通过dx工具将class文件转换成DEX格式**
		
		总结Dalvik虚拟机特性:
		
		- **每个android应用运行在一个Dalvik虚拟机实例，每一个虚拟机实例都是一个独立的进程空间**
		
		- **虚拟机的线程机制、内存分配和管理、Mutex(进程同步)等的实现都依赖底层Linux系统**
		
		- **所有android 应用的线程都对应一个Linux线程，因而虚拟机可以更多的使用Linux系统的线程调度和管理机制**

* **核心层**

	提供核心系统服务，例如文件管理、内存管理、进程管理、网络堆栈、驱动模型，核心层内核同时也作为硬件与硬件之间的抽象层。
	
**系统运行库的HAL层**

* **Windows下的HAL层**
	
	位于操作系统最底层，直接操作物理硬件设备，使用抽象接口来隔离不同硬件的具体实现，为上层的操作系统和设备驱动程序提供一个统一接口，起到
	对硬件的抽象作用。这样在更换硬件时，编写硬件的驱动只要实现符合HAL定义的标准接口即可，而上层应用不会受到影响，不必关心具体实现的什么硬件。
	
* **Linux下的HAL层**

	Linux下的HAL位于操作系统核心层和驱动程序之上，是运行在User Space中的服务程序。目的是为上层应用提供一个统一的查询硬件设备的接口。正因为有了
	HAL接口，可以提前开始应用的开发，不需要关心具体实现的硬件类型；其次，硬件厂商若需要更改硬件设备，只需要按照HAL接口规范和标准提供对应的硬件
	驱动，而不需要改变应用；最后，HAL简化了应用程序查询硬件的逻辑，把这一部分复杂性转移给HAL统一处理。
	
**Android中的HAL运行结构**

+ **Android_src/hardware/libhardware_legacy**:老式HAL结构采用so动态链接库方式；

+ **Android_src/hardware/libhardware**:新式HAL结构，采用stub代理方式调用。
	
	![HAL](/res/img/blog/2015/04/13/hal.png)
	
	左侧通过so动态链接库调用而达到对硬件驱动的访问。在so动态链接库里，实现了对驱动的访问逻辑处理。
	
	**HAL Stub**是Proxy代理概念。Stub虽然以 *.so的形式存在，但HAL将*.so的具体实现隐藏了起来，Stub向HAL提供Operations方法，Runtime通过Stub提供的so获取
	
	它的operations方法，并告知Runtime的callback方法，Runtime和Stub都有对方调用的方法，一个应用的请求通过Runtime调用Stub的operations方法，而Stub响应
	
	operations方法并完成后，在调用Runtime的callback方法进行返回。
	
	上层通过HAL提供的functions调用底部硬件，而底层硬件处理完上层请求或硬件状态发生变化后，HAL层通过Runtime提供的callback接口回调上层应用。