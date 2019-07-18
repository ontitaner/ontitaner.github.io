---
layout : post
title : "Windows8/8.1上使用VHD安装Windows7的双系统"
category : 操作系统
duoshuo: true
date : 2014-11-17
tags : [操作系统 , VHD]
---

网上有很多针对在Windows7/8使用VHD建立Windows8.1的多重开机系统教程，但是现在的情况却正好相反，我搜了一下，在Windows8/8.1下使用VHD安装windows7无外乎两种，一种是挂羊头卖狗肉吸引目光的水贴，另一种就是大胆尝试，却以失败告终，寻找解决方案的提问贴！难道真的不行吗？表示不信，于是我查了一些资料，最终在——挨踢路人甲——上面找到了方案，以下是其转载，最后附上链接。

<!-- more -->

本文简要说明如何在Windows8操作系统下利用VHD搭载Windows7，如图示效果：

![system_pic](/res/img/blog/2014/11/17/pic1.png)

**Windows8/8.1系统利用VHD安装Windows7系统需满足：**

- Windows 8/8.1必须支持VHD(Windows专业版以上均可)

- Windows Bios支持MBR引导格式的硬盘

>好了，具备了上述要求后，我们就开始吧。

##Windows 8/8.1系统安裝VHD的Windows 7操作(以C盘做介绍)

1. 快捷键「win」+「x」,以系统管理员权限进入cmd

2. 使用Diskpart取代原先的「Fdisk」处理磁碟管理，该功能强大，支持脚本运行，在命令行输入「diskpart」，回车，进入diskpart 

	![diskpart1](/res/img/blog/2014/11/17/pic2.png)
	
3. 在diskpart模式下，使用create命令在C盘建立一个20G固定大小VHD,create后的vdisk表示要建立的虚拟硬盘，file后虚拟磁盘的路径
而type可以是expandable（动态扩展）或者fixed（固定容量）。使用固定容量会依照设定直接划分一块区域分配给磁盘映像使用，优点是
存取效能最好，一般采用expandable(动态扩展)方式，此方式能够节省帮助你节省硬盘空间，最后参数maximum是指定容量大小，单位为MB，
例如下面此例：

	create vdisk file="c:\win7.vhd" maximun=20480 type=fixed
	
	![diskpart3](/res/img/blog/2014/11/17/pic3.png)
	
4. 使用select vdisk来选择运作的vhd，接着使用attach vdisk来挂载虚拟硬盘。

	select vdisk file="c:\win7.vhd"
	
	attach vdisk
	
	![diskpart4](/res/img/blog/2014/11/17/pic4.png)
	
5. 使用「Create Partition」对虚拟磁盘进行分割，使用「Format」指令进行格式化，其中FS指格式化的档案格式，LABEL是虚拟磁盘的名称，
quick是快速格式化的意思。

	Create Partition Primary
	
	Format  FS=ntfs LABEL="Win7 VHD" quick
	
	![diskpart5](/res/img/blog/2014/11/17/pic5.png)

6. assign指令是为你的vhd分区命名(例如C:/F:),同时，系统会提示相关信息

	![diskpart6](/res/img/blog/2014/11/17/pic6.png)
	
7. assign指令执行后，检查磁盘分区变化，如图，可以看到

	![diskpart7](/res/img/blog/2014/11/17/pic7.png)
	
8. 之后要确定你windows7的sources来源，因为在windows8/8.1上可以轻松的挂载ISO系统镜像文件，进入windows7系统sources目录，install.wim即为
我们要找的东西。Do you get it?
	
	![diskpart8](/res/img/blog/2014/11/17/pic8.png)
	
9. 在部署Windows7致vhd时，需要清楚你windows7系统的索引值，如果你是在网络上下载的整合多种版本的ISO镜像，需要执行
命令「DISM /get-wiminfo /wimfile:C:\install.wim」来确定要部署的版本索引值，(e是系统镜像盘的根目录,可能与你实际操作不同，请注意。)
下图使用一个多版本的windows7做范例。

	![diskpart9](/res/img/blog/2014/11/17/pic9.png)
	
10. 要将E盘内的install.wim部署到vhd的F盘上，需要使用image.exe工具，此工具是在微软的一套Windows自动化安装套件(Windows AIK)内，具体下载请查
阅网络，部署方式如下：

	imagex.exe /apply e:\sources\install.wim 1 f:\
	
	![diskpart10](/res/img/blog/2014/11/17/pic10.png)
	
11. 如果使用光盘方式来部署，可能需要花费一些时间，将install.wim部署到vhd,最后剩下BCDboot的开机项目设定，利用下述指令来复制一个开机选项，复制
成功后会得到类似{b9b6cb92-4900-11e2-a8af-c520e488c4ad}的ID。

	BCDEDIT /copy {current} /D “Windows 7″
	
	![diskpart11](/res/img/blog/2014/11/17/pic11.png)
	
12. 利用此ID修改启动项目，请务必使用你得到的ID依照如下顺序做修改动作，最后的timeout是调整选项单出现停留的时间。

	BCDEDIT /set {b9b6cb92-4900-11e2-a8af-c520e488c4ad} device vhd=[C:]\win7.vhd
	
	BCDEDIT /set {b9b6cb92-4900-11e2-a8af-c520e488c4ad} osdevice vhd=[C:]\win7.vhd
	
	BCDEDIT /set {b9b6cb92-4900-11e2-a8af-c520e488c4ad} detecthal on
	
	BCDEDIT /timeout 10
	
	![diskpart12](/res/img/blog/2014/11/17/pic12.png)
	
13. 再次进入diskpart模式来中断连接部署的vhd，命令如下：

	diskpart
	
	select vdisk file="c:\win7.vhd"
	
	detach vdisk
	
	exit
	
	![diskpart13](/res/img/blog/2014/11/17/pic13.png)
	
14. 快捷键「win」+「R」开启运行，输入「MSConfig.exe」,确定，选择开机标签页，如图所示：

	![diskpart14](/res/img/blog/2014/11/17/pic14.png)
	
15. 重启计算机，出现如图
	
	![diskpart15](/res/img/blog/2014/11/17/pic15.png)
	
16. 接下来，熟不熟悉，ha！
	
	![diskpart16](/res/img/blog/2014/11/17/pic16.png)
	
17. 再接下来，你懂的哟，新仔相信你可以搞定的。

	![diskpart17](/res/img/blog/2014/11/17/pic17.png)
	
**原文链接**[http://walker-a.com/archives/3003](http://walker-a.com/archives/3003)
	

