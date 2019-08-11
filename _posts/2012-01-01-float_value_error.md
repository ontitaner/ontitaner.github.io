---
layout : post
title : "浮点数的舍入误差"
category : C
duoshuo: true
date : 2012-01-01
tags : [C , 浮点数 ]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

如下程序打印输出结果如下：

**4008175468544.000000**

**1.000000**

<!-- more -->

为什么会出现这样的问题？

出现这种奇怪的结果是由于计算机缺乏足够的进行正确运算所需的十进制位数，数字2.0e20为2后面20个0，如果对它加1.0，那么变化的是第21位，如果要正确运算，至少需要存储21位数字，而float数字只有6、7位有效数字，因此前面计算注定是不正确的，而下面使用2.0e4代替2.0e20，则能得到正确的结果，因为改变的是第5位数字，float数字对此足够精确。

<pre class="brush: c; ">

	#include&lt;stdio.h&gt;
	
	int main(void)
	{
		float a, b;

		b = 2.0e20 + 1.0;
		a = b - 2.0e20;
		printf("%f\n",a);
		/////////////////////////
		b = 2.0e4 + 1.0;
		a = b - 2.0e4;
		printf("%f\n", a);
		return 0;
	
	}	
	
</pre>



