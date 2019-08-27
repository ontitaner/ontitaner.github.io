---
layout : post
title : "C++11中的六种memory order"
category : C++11
duoshuo: true
date : 2016-03-01
tags : [C++11]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

转自知乎用户的回答，感觉浅显易懂，不明觉厉，醍醐灌顶


<!-- more -->


1. Relaxed ordering: 在单个线程内，所有原子操作是顺序进行的。按照什么顺序？基本上就是代码顺序（sequenced-before）。这就是唯一的限制了！两个来自不同线程的原子操作是什么顺序？两个字：任意。

2. Release -- acquire: 来自不同线程的两个原子操作顺序不一定？那怎么能限制一下它们的顺序？这就需要两个线程进行一下同步（synchronize-with）。同步什么呢？同步对一个变量的读写操作。线程 A 原子性地把值写入 x (release), 然后线程 B 原子性地读取 x 的值（acquire）. 这样线程 B 保证读取到 x 的最新值。注意 release -- acquire 有个牛逼的副作用：线程 A 中所有发生在 release x 之前的写操作，对在线程 B acquire x 之后的任何读操作都可见！本来 A, B 间读写操作顺序不定。这么一同步，在 x 这个点前后， A, B 线程之间有了个顺序关系，称作 inter-thread happens-before.

3. Release -- consume: 我只想同步一个 x 的读写操作，结果把 release 之前的写操作都顺带同步了？如果我想避免这个额外开销怎么办？用 release -- consume 呗。同步还是一样的同步，这回副作用弱了点：在线程 B acquire x 之后的读操作中，有一些是依赖于 x 的值的读操作。管这些依赖于 x 的读操作叫 赖B读. 同理在线程 A 里面, release x 也有一些它所依赖的其他写操作，这些写操作自然发生在 release x 之前了。管这些写操作叫 赖A写. 现在这个副作用就是，只有 赖B读 能看见 赖A写. （卧槽真累）有人问了，说什么叫数据依赖（carries dependency）？其实这玩意儿巨简单：

S1. c = a + b;
S2. e = c + d;

S2 数据依赖于 S1，因为它需要 c 的值。

4. Sequential consistency: 理解了前面的几个，顺序一致性就最好理解了。Release -- acquire 就同步一个 x，顺序一致就是对所有的变量的所有原子操作都同步。这么一来，我擦，所有的原子操作就跟由一个线程顺序执行似的。

评论里有很多关于x86内存模型的指正，放在这里：

Loads are not reordered with other loads.Stores are not reordered with other stores.Stores are not reordered with older loads.

然后最重要的：

**Loads may be reordered with older stores to different locations**

因为 store-load 可以被重排，所以x86不是顺序一致。但是因为其他三种读写顺序不能被重排，所以x86是 acquire/release 语义。

**aquire语义**：load 之后的读写操作无法被重排至 load 之前。即 load-load, load-store 不能被重排。

**release语义**：store 之前的读写操作无法被重排至 store 之后。即 load-store, store-store 不能被重排。



