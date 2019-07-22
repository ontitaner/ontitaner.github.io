---
layout : post
title : "CPython扩展模块生成.pyd"
category : CPython
duoshuo: true
date : 2017-08-04
tags : [CPython]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

**VS编译生成.pyd扩展模块**
使用VS编译生成.pyd扩展模块，供python调用。

注意几点：

* 项目依赖中将python安装路径下include目录包含进去，其中包含Cpython需要使用的头文件，例如Python.h

* 连接器配置项中附加库目录将python安装路径下libs目录包含进去，其中有需要用到的lib文件;“输入”项中将python.lib添加进去

* 输出文件设置为“模块名.pyd”格式;

* 确保编译器最后生成的是realease版本

编译执行后，生成.pyd文件，可放置到python site_package下尝试运行

<!-- more -->

<pre class="brush: c; ">
	#include &lt;Python.h&gt;

	static PyObject* example_mul(PyObject* self, PyObject*args)
	{
		float a, b;
		if(!PyArg_ParseTuple(args, "ff", &a, &b))
		{
			return NULL;
		}
		return Py_BuildValue("f", a*b);
	}

	static PyObject* example_div(PyObject* self, PyObject*args)
	{
		float a, b;
		if(!PyArg_ParseTuple(args, "ff", &a, &b))
		{
			return NULL;
		}
		return Py_BuildValue("f", a/b);  // to deal with b == 0
	}

	static char mul_docs[] = "mul(a, b): return a*b\n";
	static char div_docs[] = "div(a, b): return a/b\n";

	static PyMethodDef example_methods[] =
	{
		{"mul", (PyCFunction)example_mul, METH_VARARGS, mul_docs},
		{"div", (PyCFunction)example_div, METH_VARARGS, div_docs},
		{NULL, NULL, 0, NULL}
	};

	static struct PyModuleDef example_module = {
	PyModuleDef_HEAD_INIT,
	"example",   /* name of module */
	NULL, /* module documentation, may be NULL */
	-1,       /* size of per-interpreter state of the module,
					or -1 if the module keeps state in global variables. */
	example_methods
	};


	PyMODINIT_FUNC
	PyInit_example(void)
	{
		return PyModule_Create(&example_module);
	}
</pre>
