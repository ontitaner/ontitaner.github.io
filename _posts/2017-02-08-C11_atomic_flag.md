---
layout : post
title : "atomic_flag实现自旋互斥锁"
category : C++11
duoshuo: true
date : 2016-02-08
tags : [C++11]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

利用C++11中atomic_flag的clear和test_and_set实现简单自旋互斥锁

<!-- more -->

<pre class="brush: c; ">

#include&lt;iostream&gt;
#include&lt;thread&gt;
#include&lt;atomic&gt;

using namespace std;

class SpinLock
{
private :
	atomic_flag m_flag{ATOMIC_FLAG_INIT};
public:
	void lock_flag();
	void unlock_flag();

	void func(int index);
};

void SpinLock::func(int x)
{
	lock_flag();

	for (int i = 0; i < 10000; ++i);

	cout << "thread " << x <<" complete. "<< endl;

	unlock_flag();
}

void SpinLock::lock_flag()
{
	while (m_flag.test_and_set(memory_order_acquire));

}
void SpinLock::unlock_flag()
{
	m_flag.clear(memory_order_release);
}

int main(int argc, char* argv[])
{
	SpinLock m_lock;

	thread* threads[10];
	
	for (int i = 0; i < 10; ++i)
		threads[i] = new thread(&SpinLock::func , &m_lock,i);

	for (int i = 0; i < 10; ++i)
		threads[i]->join();

	return 0;
}

</pre>


