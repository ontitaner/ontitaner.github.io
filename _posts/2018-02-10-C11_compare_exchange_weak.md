---
layout : post
title : "compare_exchange_weak实现线程安全操作链表"
category : C++11
duoshuo: true
date : 2016-02-10
tags : [C++11]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

compare_exchange_weak

<pre class="brush: c; ">

bool compare_exchange_weak (T& expected, T val,
           memory_order sync = memory_order_seq_cst) volatile noexcept;
bool compare_exchange_weak (T& expected, T val,
           memory_order sync = memory_order_seq_cst) noexcept;
bool compare_exchange_weak (T& expected, T val,
           memory_order success, memory_order failure) volatile noexcept;
bool compare_exchange_weak (T& expected, T val,
           memory_order success, memory_order failure) noexcept;

</pre>

* if true, it replaces the contained value with val (like store).
* if false, it replaces expected with the contained value.


<!-- more -->

<pre class="brush: c; ">

#include&lt;iostream&gt;
#include&lt;thread&gt;
#include&lt;atomic&gt;
#include&lt;vector&gt;

using namespace std;

struct Node
{
	int val;
	Node* pNode;
};

atomic&lt;Node*&gt;nodeList{nullptr};

void append_node(int val)
{
	Node* oldNode = nodeList;

	Node* newNode = new Node{val,oldNode};

	while (!nodeList.compare_exchange_weak(oldNode, newNode))
	{
		newNode->pNode = oldNode;
	}
}

int main(int argc, char * argv)
{
	vector&lt;thread&gt;vecThread;

	for(int i = 0; i < 10; ++i)
	{
		vecThread.push_back(thread(append_node, i));
	}

	for (auto& th : vecThread)
		th.join();

	for (Node* it = nodeList; it != nullptr; it = it->pNode)
		cout << it->val << endl;

	Node* it = nullptr;
	while (nodeList != nullptr)
	{
		it = nodeList;
		nodeList = it->pNode;
		delete it;
	}
}

</pre>


