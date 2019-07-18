---
layout : post
title : "C的printf参数传递误区"
category : C
duoshuo: true
date : 2014-12-01
tags : [C , printf , 参数传递 ]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

参数传递的机制随实现不同而不同。如下程序：

<pre class="brush: c; ">
	#include&lt;stdio.h&gt;

	int main(void)
	{
		float n1 = 3.0;
		double n2 = 3.0;
		long n3 = 2000000000;
		long n4 = 1234567890;
	
		printf("%ld %ld %ld %ld\n", n1, n2, n3, n4);
		return 0;
	}
</pre>

<!-- more -->

![参数传递](/res/img/blog/2014/12/01/trans_param.png)

```printf("%ld %ld %ld %ld\n", n1, n2, n3, n4)```调用指明计算机将变量n1,n2,n3,n4传递给计算机，计算  
机把它们放置在被称为堆栈(stack)的一块内存区域中实现。计算机根据变量的类型而非转换说明符把这些值放置在堆栈中。

因此，n1在堆栈中占用8个字节(**float被转换成了double**),同样，n2占用8个字节，而n3和n4分别占用4个字  
节，然后控制转移到printf()函数中，该函数从堆栈中读取值，**但是在读取时，按照转换说明符读取**，```%ld```说  
明，printf()函数应该读取4个字节，所以printf()在堆栈中读取前四个字节作为它的第一个值。这就是n1的前半  
部分，它被解释成一个长整数。下一个```%ld```再读取4个字节，是n1的后半部分，被解释成第二个长整数，同样，  
```%ld```的第三个和第四个实例使得n2的前半部分和后半部分被读出，并解释成两个长整数。所以，**虽然n3和n4的说明符**都正确，但是printf()仍然读取了错误的字节。





