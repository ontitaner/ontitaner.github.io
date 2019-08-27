---
layout : post
title : "memory order加深理解"
category : C++11
duoshuo: true
date : 2016-03-01
tags : [C++11]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

**Memory Order**

内存顺序描述了计算机 CPU 获取内存的顺序，内存的排序既可能发生在编译器编译期间，也可能发生在 CPU 指令执行期间。

为了尽可能地提高计算机资源利用率和性能，编译器会对代码进行重新排序， CPU 会对指令进行重新排序、延缓执行、各种缓存等等，以达到更好的执行效果。当然，任何排序都不能违背代码本身所表达的意义，并且在单线程情况下，通常不会有任何问题。

但是在多线程环境下，比如无锁（lock-free）数据结构的设计中，指令的乱序执行会造成无法预测的行为。所以我们通常引入内存栅栏（Memory Barrier）这一概念来解决可能存在的并发问题


<!-- more -->

**Memory Barrier**

内存栅栏是一个令 CPU 或编译器在内存操作上限制内存操作顺序的指令，通常意味着在 barrier 之前的指令一定在 barrier 之后的指令之前执行。在 C11/C++11 中，引入了六种不同的 memory order，可以让程序员在并发编程中根据自己需求尽可能降低同步的粒度，以获得更好的程序性能。

这六种 order 分别是：relaxed, acquire, release, consume, acq_rel, seq_cst

**memory_order_relaxed**: 只保证当前操作的原子性，不考虑线程间的同步，其他线程可能读到新值，也可能读到旧值。比如 C++shared_ptr 里的引用计数，我们只关心当前的应用数量，而不关心谁在引用谁在解引用。

**memory_order_release**:（可以理解为 mutex 的 unlock 操作）

1. 对写入施加 release 语义（store），在代码中这条语句前面的所有读写操作都无法被重排到这个操作之后，即 store-store 不能重排为 store-store, load-store 也无法重排为 store-load

2. 当前线程内的所有写操作，对于其他对这个原子变量进行 acquire 的线程可见

3. 当前线程内的与这块内存有关的所有写操作，对于其他对这个原子变量进行 consume 的线程可见

**memory_order_acquire**: （可以理解为 mutex 的 lock 操作）

1. 对读取施加 acquire 语义（load），在代码中这条语句后面所有读写操作都无法重排到这个操作之前，即 load-store 不能重排为 store-load, load-load 也无法重排为 load-load

2. 在这个原子变量上施加 release 语义的操作发生之后，acquire 可以保证读到所有在 release 前发生的写入，举个例子：

<pre class="brush: c; ">

c = 0;

thread 1:
{
  a = 1;
  b.store(2, memory_order_relaxed);
  c.store(3, memory_order_release);
}

thread 2:
{
  while (c.load(memory_order_acquire) != 3)
    ;
  // 以下 assert 永远不会失败
  assert(a == 1 && b == 2);
  assert(b.load(memory_order_relaxed) == 2);
}

</pre>

**memory_order_consume**:

1. 对当前要读取的内存施加 release 语义（store），在代码中这条语句后面所有与这块内存有关的读写操作都无法被重排到这个操作之前

2. 在这个原子变量上施加 release 语义的操作发生之后，consume 可以保证读到所有在 release 前发生的并且与这块内存有关的写入，举个例子：

<pre class="brush: c; ">

a = 0;
c = 0;

thread 1:
{
  a = 1;
  c.store(3, memory_order_release);
}

thread 2:
{
  while (c.load(memory_order_consume) != 3)
    ;
  assert(a == 1); // assert 可能失败也可能不失败
}

</pre>

**memory_order_acq_rel**: 

1. 对读取和写入施加 acquire-release 语义，无法被重排
2. 可以看见其他线程施加 release 语义的所有写入，同时自己的 release 结束后所有写入对其他施加 acquire 语义的线程可见

**memory_order_seq_cst**:（顺序一致性）

1. 如果是读取就是 acquire 语义，如果是写入就是 release 语义，如果是读取+写入就是 acquire-release 语义
2. 同时会对所有使用此 memory order 的原子操作进行同步，所有线程看到的内存操作的顺序都是一样的，就像单个线程在执行所有线程的指令一样通常情况下，默认使用 memory_order_seq_cst，所以你如果不确定怎么这些 memory order，就用这个。



