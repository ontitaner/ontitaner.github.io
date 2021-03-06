---
layout : post
title : "CMMB数字广播信号测试与分析软件归档"
category : 工程项目
duoshuo: true
date : 2015-07-28
tags : [Project]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

首先，在聊这个项目之前，对共同参与协作开发CMMB数字广播信号测试与分析软件项目的团队成员表示敬意，尤其以
**TroyHorse**,**wangmumu806**(姓名不透露了，大家都懂的)为代表，没有他们，仅靠一人之力，是完不成如此庞大的项目的，身为团队中的一员，表示很高兴参与到这个项目中来，虽然很累，期间也有过很多吐槽，但看到这么多成果，累也是值得的！

**在中国电子科技集团第41研究所联调现场。**

![联调现场](/res/img/blog/2015/07/28/spot.png)

<!-- more -->

---		

好了，言归正传，来谈谈这个项目。
下面这张图是我们团队在项目开发过程中，利用版本控制系统针对此项目的一个记录，算作我们辛勤劳动的一个见证吧。
还请大家在看的时候可以耐心点，不强求，毕竟还有一个**read more**，重点不能落下 ^_^ 。
		
![project_work_flow](/res/img/blog/2015/07/28/project_work_flow.png)

**与中国电子科技集团第41研究所联调结果**

通过与**中国电子科技集团公司第41研究所**联调测试，本项目软件成功实现了对IQ时域数据功率分析方面的测试，包括:频谱检测，通道功率，邻道功率比，频谱发射模板等。可以说，这是本项目的一个**关键里程碑**，不仅仅验证了项目研究方法的正确性，为**调制精度测量联调**奠定了基础，更鼓舞了我们团队的士气。

---

**项目概况**

为实现对数字广播电视信号传输质量的测试与分析，本项目利用信号发生器、信号分析仪、测试电缆、计算机等相关设备对信号发生器产生的
原始IQ数据进行获取、分析和输出显示，并与信号分析仪同步进行比较，测试其正确性。如下图所示：

![原理图](/res/img/blog/2015/07/28/IQ_Analyse.png)

---

**整体设计架构**

下面这张图是我在原有基础上稍微细化而得到的，整体软件架构设计**基本上**从**模块化**角度出发，为什么说**基本上**，因为在最初软件开发过程中，缺少与合作方沟通(**其实对方也不清楚，也在探索**)，导致某些软件需求模棱两可，这是造成软件不断修改已有部分的罪魁祸首，也是我最想吐槽的地方，在这里就不说了。And从中可以看出沟通的重要性！！！相信在后期的优化过程中，能把软件性能进一步提升。从宏观上看，软件基本上划分为三个层次:**原始数据读写控制层**、**数据处理层**、**图谱显示层**,再细划分，每个层次又分为若干不同模块。具体见图。

![整体设计架构图](/res/img/blog/2015/07/28/frame_work.png)

**软件模块化遇到的问题(个人见解，此处倒叙)**

为什么会有三个版本？答：**每半年一次中期监理，为了更好的过渡，有了这三个版本。**

* 第三版软件(划时代呀)
	
	第三版软件完全抛弃了之前两版的设计思想，加之对需求分析的进一步明朗，在boss(有两个boss，这是我boss，另一个boss是让时间紧迫起来的那啥，哼，这里无贬低的意思)的建议下，重新设计了一套框架，整体框架**比拟MVC**，将原始数据采集、数据处理层、图谱显示层严格的划分出来，对各个具体子模块从接口定义到功能实现进行了重新规划。
	
	在数据处理显示过程中，对控件进行了重构，加入了**双缓冲技术**，使结果显示列表在**毫秒级**刷新频率下**不闪频，增强了用户体验效果。**整体框架引入了开源项目.dll--DockPanel,用户可以根据个人需求对窗口进行布局定制，可以实现窗口的**悬浮、拖拽、停靠**等功能。
	
	在与中国电子科技集团第41研究所现场联调过程中，现场加入了IQ原始数据网络传输模块，使得软件**第一次在真实环境** 、 **真实测试数据下运行(真正意义上的千万级)**，运行状况良好，甚是欣慰。
	
* 第二版软件
	
	第二版软件在第一版软件的基础上进行“深加工”，由于第一版软件在设计上的各种不合理，在模块划分上没有进行合理规划，导致在开发过程中，**牵一发而动全身，编写过程十分痛苦**，没有对模块之间数据交互的接口进行合理定义，导致**A模块访问B模块的内部数据(B模块中的某些数据强制定义为静态类型)**十分频繁，即**内容耦合**过强，此类耦合对软件是及其有害的。
		
	譬如在**功率测量**数据处理过程中，由于没有对频谱监测、IQ时域数据、邻道功率比等相关模块定义与之匹配的数据处理接口，因此**不得不在数据处理线程中将功率测量所有模块的数据结果一次性算出，即便当下不需要**,可想而知，**多么愚蠢的做法，但是我就做了**，因为没有时间让我多做思考，可恶。在这种情况下，我们试想，原始IQ数据从采集经过数据处理再到图谱显示，冗余的运算让图谱显示效率极低出现界面卡顿甚至崩溃，and then，当然我调试喽，痛苦！
	
	当然，一方面取决于处理数据(第三版软件千万级，当时比这少多了，还未实时)规模的庞大，但是，更要归功于这拙劣的数据处理方案。其次，就是软件相关模块的**封装不严谨**，导致部分模块的实现细节对其他模块透明，**A模块调用了B模块的实现码**，没有严谨的接口去控制模块与模块之间的通信。再其次，就是图谱显示层里面居然参杂了数据处理的部分处理逻辑，模块化从严格意义上来说，已经名存实亡。

* 第一版软件
	
	由于项目中期监理时间的紧迫性在软件设计上根本**没有独立思考**的余地，只知道赶紧编(至于为什么时间紧迫，时间充足的时候干嘛去了，表示我们只是打工者~就不和稀泥了，总之期间吐槽很正常)更不用提软件模块化了，所以，对于第一版，表示现在已经不忍直视了，就不说了。
	
---

**IQ分析原理总结:**

输入的射频信号经过混频器，得到中频信号，经过抗混叠滤波器和步进增益的处理,通过A/D转换器将模拟中频信号转换为数字中频信号，经过数字信号处理，得到IQ数据，并在主机存储，根据需要显示的视图类型，对IQ数据进行不同的处理，得到其频谱图，幅度时间图，IQ时间图等。本地计算机通过网线与主机(信号分析仪)连接，通过编写的**网络传输工具软件(按照SCPI协议)**将原始IQ数据保存在本地计算机，供本机软件进行IQ分析测试，并与实际信号分析仪分析结果进行对比，验证其正确性。

![IQ分析原理图](/res/img/blog/2015/07/28/pic5.png)

---

**IQ数据网络传输工具的实现(略讲)**

该网络传输工具采用TCP面向对象连接，按照**SCPI协议**编写，可以根据用户实际需求向信号发射机发送相关控制命令，同时接收IQ原始数据，供数据处理层进行相关运算。

---

**CMMB数字广播电视信号测试与分析软件**主要有两大方面需求：**功率测量**和**调制精度测量**

* ###功率分析模块预期目标(注:**由于涉及一些保密信息，关键流程略去**)

	![功率测量](/res/img/blog/2015/07/28/power_analyse.png)
	
* ###调制精度测量预期目标(注:**同上**)
		
	![调制精度](/res/img/blog/2015/07/28/demodulation.png)
---

###功率测量方面

* **频谱**

	输入数据: **FFT模块输出的频域信息，采样率Fs及采样点数N(N为用户设置的时间窗口长度确定)**
	
	输出数据: **频谱图的横坐标与纵坐标**
	
	其    中: **Fn=(n-1)*Fs/N (Fs是采样频率，N是采样点数，n表是第n个点)**
	
* **通道功率**

	计算选择的频率范围内的平均功率，一方面可以供通道功率显示模块显示，另一方面可以供ACP模块调用计算邻道功率比。

	![通道功率计算公式](/res/img/blog/2015/07/28/pic11.png)

	**n2,n1:** 信道内像素的数量

	**CHBW:** 信道带宽

	**RBW:** 分辨率带宽

	**Kn:** 分辨带宽校正系数(RBW*kn=功率带宽)

	**A:** 通信方式对应的基带匹配滤波器的修正值，匹配滤波器通常为高斯型，升余弦，或者根升余弦形式。

	信道内的每个像素都必须进行电平的反对数运算以获得线性功率，各个像素的线性功率在信道内求和，然后除以像素的个数(n2-n1)，其和用信道带宽和功率带宽关联加权。

* **邻道功率比**

	![邻道功率比](/res/img/blog/2015/07/28/adjacent.png)
	
	具体计算略去。
	
	输出信号显示如下图
	
	![输出显示](/res/img/blog/2015/07/28/main.png)
	
	相邻信道设置参数如下图
	
	![邻道设置](/res/img/blog/2015/07/28/adjcent_set.png)


* **肩部衰减**

	在实际编写软件过程中，由于在2MHz带宽条件下未指定肩部衰减，故暂时使用占用带宽起始点与结束点，在邻域范围内各取10个点求其平均，起始点与终止点中带肩衰减较大
	的肩带衰减值作为输出。
	
	**带肩:** 数字电视信号经过放大器后在在频道外的互调产物为近似连续频谱，频道外的连续频谱在频道附近会产生“肩部”效应，此为带肩。
	偏离中心频率某一规定值(本项目中，在8MHz带宽条件下，偏离中心频率正负4.2MHz)的带外频率点平均功率相对于中心频率点的变化量，单位为dB。

	**P(f=fs/2±4.2)(8MHz带宽)**
	
* **信噪比**
	
	占用带宽内的信号平均功率与占用带宽外的信号平均功率之比，单位若采用dB，采用减法。
	
	**信噪比估计算法**基于前导符号的OFDM系统信噪比估计方法(此处略去N个字)

* **PDF概率密度函数**
	
	+ 1.根据所得的数据Xi=Ii+Qi，得到Pi=pow(Ii)+pow(Qi),得到N个数据；
	+ 2.根据N个数据，求得P=SUM(Pi) ,分别计算每个数据的概率；
	+ 3.得到N个数据的经验累积分布函数ECDF(**cdfcalc函数**)；
	+ 4.对经验累积分布函数进行平滑滤波(**三点重心法**)；
	+ 5.1-ECDF即得补偿曲线CCDF；
	+ 6.对得到的经验分布函数ECDF进行求导，即得到概率密度函数PDF；
	
* **带外杂散测试与分析**

	+ **杂散发射:** 落在中心频率两侧，必要带宽±250%倍处或以外的发射。
	+ **带外发射:** 落在中心频率两侧，必要带宽±250%倍处以内的无用发射。

* **功率统计互补累积分布函数**

	CCDF功率互补累积分布函数是静态的功率计算，仅能用于时域数据。描述等于或者大于特定功率电平采样点在整个统计期间出现的概率，0db是信号的平均功率。
	
	**Trace A  Mkr  1:				2 dB					12 %**
	
	**表示在信道功率(平均功率)已知的情况下，采样点功率与平均功率之差大于或等于2dB的概率为12%.**
	
	计算过程如下:
	
	![CCDF功率互补累积分布函数](/res/img/blog/2015/07/28/ccdf.png)
	
	输出显示如下:
	
	![CCDF功率互补累积分布函数输出](/res/img/blog/2015/07/28/ccdf_result.png)
	
* **占用带宽**

	系统默认值占用功率99%(可设置)，利用通道功率模块，分别从起始点与终止点开始累积功率，直至功率大于等于(1-占用功率比值)/2×通道总功率，得到的两点即为占用带宽的起点与终点。

* **功率谱估计(项目中目用到的是FFT变换以及AR模型)**

	通过比较几种功率谱估计的算法，周期图法、自相关法以及Welch法，发现前两者产生的功率谱由较多毛刺，而用Welch法产生的功率谱相对比较平滑，因此决定采用Welch法进行功率谱估计。下面对利用Welch法获得功率谱的原理做简单介绍。
	
	**Welch算法**
	
	Welch算法谱估计采取数据分段加窗处理取平均的方法，先分别求出每段的谱估计，然后进行总平均。根据概率统计理论，若将原长度为N的数据分成L段，每段长度取M=N/L，且各段数据互为独立，则估计的方差将只有原来不分段的1/L，达到一致估计的目的。
	
	算法如下式：
	
	![Welch算法公式](/res/img/blog/2015/07/28/pic12.png)
	
	但若L增加M减小，则分辨率下降；相反，若L减小M增加，虽然估计的偏差减小，但估计的方差增大。所以在实际中必须兼顾分辨率与方差的要求适当选取L和M的值。在分段时为了减小因分段数增加给分辨率带来的影响，采取各段数据有一定重叠的方法。

	注：**Welch法一是要选择适当的窗函数w(n)，加窗的优点是无论什么样的窗函数均可使谱估计非负。二是在分段时，可使各段之间有重叠，使方差减小。**
	
---

###调制精度测量

**发射端协议《GYT 220.1-2006 移动多媒体广播 第1部分：广播信道帧结构、信道编码和调制》**

定义了在30MHz-3000MHz频率范围内，移动多媒体广播系统广播信道物理层各功能模块，定义了帧结构、信道编码、调制技术以及传输指示信息。

定义的物理层带宽分为**8MHz**和**2MHz**

* **物理层结构**

	广播信道物理层通过物理层逻辑信道(PLCH)为上层业务提供广播通道，分为**控制逻辑信道(CLCH)**和**业务逻辑信道(SLCH)**
	
	CLCH承载控制信息，SLCH承载业务。CLCH只有**1**个，占用第**0**时隙发送，SLCH可以为**1~39**个，每个SLCH占用整数个时隙。
	
	**物理层结构**
	
	![物理层结构](/res/img/blog/2015/07/28/plch_content.png)
	
	物理层对每个物理层逻辑信道进行单独编码和调制。
	
	CLCH:**RS(240,240)**、**RS(240,240)**、**LDPC:1/2码率**、**星座映射--BPSK**、**扰码初始值:选项0**
	
	SLCH:根据系统需求配置。
	
	**物理层功能图示**
	
	![物理层功能图示](/res/img/blog/2015/07/28/function.png)
	
* **帧结构**

	**Per Frame---1s---40 time slots**
	
	**Per time slot---25ms---一个信标+53个OFDM符号**
	
	**帧结构图示**
	
	![帧结构图示](/res/img/blog/2015/07/28/frame.png)
	
	**一个信标=发射机标识信号(TxID)+2个同步信号**
	
	**信标图示**
	
	![信标图示](/res/img/blog/2015/07/28/xinbiao.png)
	
	**OFDM符号=循环前缀(CP:per CP 51.2us)+OFDM数据体(per 460.8us)**
	
	**OFDM符号图示**
	
	![OFDM符号](/res/img/blog/2015/07/28/ofdm.png)
	
	**发射机标志信号、同步信号和相邻OFDM符号之间，通过保护间隔(GI:per GI 2.4us)相互交叠,相邻符号经过窗函数W(t)加权后，前一个符号尾部GI与后一个符号头部GI相互交叠。**
	
	**保护间隔图示**
	
	![保护间隔](/res/img/blog/2015/07/28/gi.png)
	
	注:**符号交叠时，每时隙两段同步信号之间无保护间隔**
	
	**保护间隔信号选取图示**
	
	![保护间隔信号选取](/res/img/blog/2015/07/28/gi_select.png)
	
* **数据分析**

	一个时隙的由来 **25ms=(409.6us+51.2us) * 53+(2.4us) * 54+(36us+2.4us)+204.8us * 2**
	
	从数据子载波分析
	
	+ 物理层带宽为**2M**
		
		![物理层带宽为2M](/res/img/blog/2015/07/28/analyse_2M.png)
		
	+ 物理层带宽为**8M**
	
		![物理层带宽为8M](/res/img/blog/2015/07/28/analyse_8M.png)
		
	+ 1个OFDM符号**(460.8us)**
	
		![1个OFDM符号](/res/img/blog/2015/07/28/ofdm2.png)
		
	
* **星座映射**

	从左到右依次为**BPSK**、**QPSK**、**16QAM**
	
	![星座映射](/res/img/blog/2015/07/28/bpsk.png)

* **RS编码和字节交织**(此处省略)

* **LDPC编码**(此处省略)

* **比特交织**(此处省略)

此协议为实际发射端协议，而本项目涉及接收端，因此依据此协议，逆向分析**调制精度测量**部分,以上只是简单讲解发射端协议，如果想详细了解，请查阅相关资料。

---

###同步算法总结

* **粗符号定时同步方法**

	+ **获取同步信号初始位置**
	
		![同步信号初始位置计算方法](/res/img/blog/2015/07/28/tongbu.png)
		
		其中
		
		r(n):**接收到的I+jQ数据，j表示虚数，* 表示共轭**
		
		C(n):**表示接收信号和延迟D个采样点的相关函数**
		
		D   :**一个同步信号的采样点数，物理层带宽为2MHz时，D=512，物理层带宽为8MHz时，D=2048**
		
		R(n):**接收到D个信号的平均能量**
		
		式(3)结果:**表示估计的度量函数，用平均能量R(n)归一化C(n)得到的函数。**
		
		注  :**粗符号定时同步所确定的FFT窗口的粗略位置在该度量函数取最大值时n值的附近**
		  
		由于粗符号定时同步只要粗略确定的FFT窗口的位置,可设置一个门限THcoarse。,当估计度量函数的值大于该门限时,即认为该n值就是粗定时同步确定的主径位置。门限值的设定如下式所示
		
		![门限THcoarse](/res/img/blog/2015/07/28/coarse.png)
		
		其中，**a可取0.9**
		
	+ **取OFDM数据**
	
		输入:**粗同步定位到的位置 n**
		
		每个OFDM数据体首地址如下(i表示本时隙中第i个OFDM数据体):
			
		- **物理带宽2MHz**
				
			**Position(i)=n+512 * 2 + 6 * i + 128 * i +1024 * (i-1);**
			
		- **物理带宽8MHz**
				
			**Position(i)=n+2048 * 2 + 6 * i + 512 * i +4096 * (i-1);**
				
		以物理带宽为2MHz考虑
		
		![物理带宽为2MHz](/res/img/blog/2015/07/28/tongbu1.png)
		
		时域OFDM数据体为：**r(Position(i)：（Positon(i)+1023))**
		
		经FFT模块转换为频域信号：**FFT(r(Position(i)：(Positon(i)+1023)))**,FFT模块的**N=1024**。
		
* **细符号定时同步方法**

	粗符号定时同步后将接收到的数据进行**FFT变换**，获得频域数据，由离散导频信息估计出多径信道的时延特性，进行细符号同步精确找到FFT窗口起始位置。
	
	输入数据: **频域OFDM数据体，即粗符号同步输出的OFDM数据体时域信息经过FFT变换得到的频域信息。**
	
	输出数据: **输出数据为同步位置纠正信息，输出至粗符号定时同步模块。**
	
	

---

###项目演示

**IQ幅值波形**

![pic1](/res/img/blog/2015/07/28/pic1.png)
	
**邻道功率比**

![pic2](/res/img/blog/2015/07/28/pic2.png)
	
**占用带宽**

![pic3](/res/img/blog/2015/07/28/pic3.png)

**通道脉冲响应**

![pic4](/res/img/blog/2015/07/28/cmmb5.png)

**频谱不平坦度**

![pic5](/res/img/blog/2015/07/28/cmmb2.png)

**通道频率响应**

![pic6](/res/img/blog/2015/07/28/cmmb3.png)

**幅度误差**

![pic7](/res/img/blog/2015/07/28/cmmb1.png)

**IQ星座图**

![pic8](/res/img/blog/2015/07/28/cmmb4.png)

---
