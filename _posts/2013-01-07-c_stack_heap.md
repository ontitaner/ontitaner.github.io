---
layout : post
title : "C中关于堆栈的总结"
category : C
duoshuo: true
date : 2013-01-07
tags : [C ]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

在计算机领域，堆栈是一个不容忽视的概念，但是很多人甚至是计算机专业的人也没有明确堆栈其实是两种数据结构。堆栈都是一种数据项按序排列的数据结构，只能在一端(称为栈顶(top))对数据项进行插入和删除。

**要点：**堆，顺序随意。栈，后进先出(Last-In/First-Out)。

<!-- more -->

---

**两种“堆栈”的对比**

* **堆(从操作系统角度)**

	一般由程序员分配释放，若程序员不释放，程序结束时可能由操作系统回收，分配方式类似于链表。堆存放在**二级缓存**中，生命周期由虚拟机的垃圾回收算法决定（并不是一旦成为孤儿对象就能被回收）。所以调用这些对象的速度要相对来得低一些

* **栈(从操作系统角度)**

	由编译器自动分配释放，存放函数的参数值，局部变量等。操作方式类似于数据结构中的栈，栈使用的是**一级缓存**， 他们通常都是被调用时处于存储空间中，调用完毕立即释放。
	
>这里的堆实际上指的就是(满足堆性质的)优先队列的一种数据结构，第1个元素有最高的优先权；栈实际上就是满足后进先出的性质的数学或数据结构。

* **堆(从操作系统角度)**
	
	堆可以被看成是一棵树，如：堆排序

* **栈(从操作系统角度)**

	一种后进先出的的数据结构
	
##申请方式

* **栈**

	由系统自动分配。 例如，声明在函数中一个局部变量int b; 系统自动在栈中为b开辟空间。
	
* **堆**

	需要程序员自己申请，并指明大小，在c中使用malloc函数,如p1 = (char *)malloc(10);在C++中用new运算符，如p2 = new char[20];**但是注意p1、p2本身是在栈中的。**
	
##申请后系统的响应

* **栈**

	只要栈的剩余空间大于所申请空间，系统将为程序提供内存，否则将报异常提示栈溢出。
	
* **堆**

	首先应该知道操作系统有一个记录空闲内存地址的链表，当系统收到程序的申请时，会遍历该链表，寻找第一个空间大于所申请空间的堆结点，然后将该结点从空闲结点链表中删除，并将该结点的空间分配给程序，对于大多数系统，会在这块内存空间中的首地址处记录本次分配的大小，这样，代码中的delete语句才能正确的释放本内存空间。由于找到的堆结点的大小不一定正好等于申请的大小，系统会自动的将多余的那部分重新放入空闲链表中。

##申请大小的限制

* **栈**

	在Windows下,栈是**向低地址扩展的数据结构，是一块连续的内存的区域**。这句话的意思是栈顶的地址和栈的最大容量是系统预先规定好的，在WINDOWS下，栈的大小是2M(也有的说是1M，总之是一个编译时就确定的常数)，如果申请的空间超过栈的剩余空间时，将提示overflow。因此，能从栈获得的空间较小。
	
* **堆**

	堆是**向高地址扩展的数据结构，是不连续的内存区域**。这是由于系统是用链表来存储的空闲内存地址的，自然是不连续的，而**链表的遍历方向是由低地址向高地址**。堆的大小受限于计算机系统中有效的虚拟内存。由此可见，**堆获得的空间比较灵活，也比较大**。
**在C Primer Plus(第五版)中，看到这么一段话，**整数常量表达式是由整数常量组成的表达式，sizeof表达式被认为是一个整数常量，而(和C++不一样)一个const的值不是一个整数常量，并且表达式的值必须大于0**

##申请效率的比较

* **栈**

	系统自动分配，速度较快。但程序员是无法控制的。
	
* **堆**

	由new分配的内存，一般速度比较慢，而且容易产生内存碎片,不过用起来最方便。另外，在WINDOWS下，**最好的方式是用VirtualAlloc分配内存，他不是在堆，也不是在栈,而是直接在进程的地址空间中保留一块内存，虽然用起来最不方便。但是速度快，也最灵活。**

##堆和栈中的存储内容

* **栈**
	
	在函数调用时，第一个进栈的是主函数中函数调用后的下一条指令(函数调用语句的下一条可执行语句)的地址，然后是函数的各个参数，在大多数的C编译器中，参数是由右往左入栈的，然后是函数中的局部变量。注意静态变量是不入栈的。当本次函数调用结束后，局部变量先出栈，然后是参数，最后栈顶指针指向最开始存的地址，也就是主函数中的下一条指令，程序由该点继续运行。

* **堆**

	一般是在堆的头部用一个字节存放堆的大小。堆中的具体内容由程序员安排。
	
##存取效率的比较
	
char s1[] = "aaaaaaaaaaaaaaa";char *s2 = "bbbbbbbbbbbbbbbbb";

**aaaaaaaaaaa是在运行时刻赋值的；而bbbbbbbbbbb是在编译时就确定的，但是，在以后的存取中，在栈上的数组比指针所指向的字符串(例如堆)快。**
	
<pre class="brush: c; ">

#include&lt;stdio.h&gt;

	int main()
	{
    char a = 1;
    char c[] = "1234567890";
    char *p ="1234567890";
    a = c[1];
    a = p[1];
    return 0;
	} 

</pre>  
	
对应的汇编代码：
	
<pre class="brush: c; ">

	10: a = c[1];
	00401067 8A 4D F1 mov cl,byte ptr [ebp-0Fh]
	0040106A 88 4D FC mov byte ptr [ebp-4],cl
	11: a = p[1];
	0040106D 8B 55 EC mov edx,dword ptr [ebp-14h]
	00401070 8A 42 01 mov al,byte ptr [edx+1]
	00401073 88 45 FC mov byte ptr [ebp-4],al

</pre>
	
**第一种在读取时直接就把字符串中的元素读到寄存器cl中，而第二种则要先把指针值读到edx中，再根据edx读取字符，显然慢了。**
	
##总结

>堆和栈的区别可以用如下的比喻来看出：
>使用栈就象我们去饭馆里吃饭，只管点菜（发出申请）、付钱、和吃（使用），吃饱了就走，不必理会切菜、洗菜等准备工作和洗碗、刷锅等扫尾工作，他的好处是快捷，但是自由度小。使用堆就象是自己动手做喜欢吃的菜肴，比较麻烦，但是比较符合自己的口味，而且自由度大。
	
