---
layout : post
title : "virtualbox共享文件夹软连接无法创建解决方案"
category : 不用就忘系列
duoshuo: true
date : 2020-06-05
tags : [不用就忘系列]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

我的开发环境，主机是windows7，虚拟机是ubuntu16，VirtualBox5.2。

今天发现不能再虚拟机中不能创建软连接，ln -s target link

<!-- more -->

---

解决方案

* ln: failed to create symbolic link 'src': Read-only file system

* 在win7中：管理员身份打开cmd，cd 到VirtualBox的安装目录，然后运行下面的命令


<pre class="brush: c; ">

VBoxManage setextradata接下

YOURVMNAME VBoxInternal2/ 接下
SharedFoldersEnableSymlinksCreate/ 接下
YOURSHAREFOLDERNAME 1

YOURVMNAME ：

你虚拟机的名字（virtualbox左侧虚机列表，例如centos7）

YOURSHAREFOLDERNAME ：

共享文件夹的名字，不是地址

</pre>

* 检查设置是否正确

<pre class="brush: c; ">

VBoxManage getextradata YOURVMNAME enumerate

eg：

VBoxManage getextradata centos7 enumerate

结果中有类似，说明设置成功了

Key:

VBoxInternal2/ 接下

SharedFoldersEnableSymlinksCreate/接下

YOURSHAREFOLDERNAME,Value: 1

</pre>

* 如果你不知管理员用户，你可能还是不能创建软连接，还需要第三步在win7 下,
run secpol.msc，打开的是本地安全策略

<pre class="brush: c; ">

本地安全策略-->本地策略-->
用户权限分配-->创建符号链接-->添加用户或者组权限

</pre>

* 虚机用户无法访问共享文件夹，需添加用户

<pre class="brush: c; ">

sudo usermod -a -G vboxsf 你的用户名

eg:

sudo usermod -a -G vboxsf windos

</pre>







