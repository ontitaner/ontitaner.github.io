---
layout : post
title : "线程局部存储(thread_local)"
category : C++11
duoshuo: true
date : 2016-01-03
tags : [C++11]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

线程局部存储在其它语言中都是以库的形式提供的(库函数或类)。但在C++11中以关键字的形式，
做为一种存储类型出现，由此可见C++11对线程局部存储的重视。

C++11中有如下几种存储类型:

* **auto**
    + 声明变量时： 根据初始化表达式自动推断变量类型
    + 声明函数作为函数返回值的占位符

* **static**
    + static变量只初始化一次
    + static修饰函数内的“局部”变量时，表明它不需要在进入或离开函数时创建或销毁。且仅在函数内可见
    + static修饰全局变量时，表明该变量仅在当前(声明它的)文件内可见
    + static修饰类的成员变量时，则该变量被该类的所有实例共享

* **register**
    + 寄存器变量。该变量存储在CPU寄存器中，而不是RAM(栈或堆)中。该变量的最大尺寸等于寄存器的大小。由于是存储于寄存器中，因此不能对该变量进行取地址操作

* **extern**
    + 引用一个全局变量。当在一个文件中定义了一个全局变量时，就可以在其它文件中使用extern来声明并引用该变量

* **mutable**
    + 仅适用于类成员变量。以mutable修饰的成员变量可以在const成员函数中修改
    
* **thread_local**
    + 线程周期


<!-- more -->

<pre class="brush: c; ">

#include&lt;iostream&gt;
#include&lt;thread&gt;

class A {
public:
  A() {
    std::cout << std::this_thread::get_id()
              << " " << __FUNCTION__
              << "(" << (void *)this << ")"
              << std::endl;
  }

  ~A() {
    std::cout << std::this_thread::get_id()
              << " " << __FUNCTION__
              << "(" << (void *)this << ")"
              << std::endl;
  }

  // 线程中，第一次使用前初始化
  void doSth() {
  }
};

thread_local A a;

int main() {
  a.doSth();
  std::thread t([]() {
    std::cout << "Thread: "
              << std::this_thread::get_id()
              << " entered" << std::endl;
    a.doSth();
  });

  t.join();

  return 0;
}

//执行结果
g++ -std=c++11 -o debug/tls.out 
    ./thread_local.cpp
./debug/tls.out
A(0xc00720)
Thread: 02 entered
A(0xc02ee0)
~A(0xc02ee0)
~A(0xc00720)

变量a在main线程和t线程中分别保留了一份副本，以下时序图表明了两份副本的生命周期。

</pre>
