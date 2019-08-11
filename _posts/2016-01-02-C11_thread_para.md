---
layout : post
title : "线程传参"
category : C++11
duoshuo: true
date : 2016-01-02
tags : [C++11]
SyntaxHihglighter: true
shTheme: shThemeMidnight # shThemeDefault  shThemeDjango  shThemeEclipse  shThemeEmacs  shThemeFadeToGrey  shThemeMidnight  shThemeRDark
---

C++11线程库线程传递参数

分别按照值传递、引用传递、成员函数指针及对象指针为线程传递值，
比较他们运行对原对象的影响。

顺道复习一下定义类时的成员函数的使用。

<!-- more -->

<pre class="brush: c; ">

#include&lt;iostream&gt;
#include<iostream>
#include<thread>

using namespace std;

class Object1
{
public:
    Object1();
    Object1(int a, const char* ch);
    Object1(const Object1& obj);
    Object1& operator = (const Object1& obj);
    ~Object1();

public:
    int getInt();
    void setInt(int);
    char * getCharStr();
    void setCharStr(const char*);
private:
    int num = 0;
    char * ch = nullptr;
};

Object1::Object1()
{

}

Object1::Object1(int a, const char * ch)
{
    num = a;
    if (nullptr != ch)
    {
        int len = strlen(ch);
        this->ch = new char[len + 1];
        memcpy(this->ch, ch, len+1);
    }
    else
    {
        this->ch = nullptr;
    }
}

Object1::Object1(const Object1& obj)
{
    this->num = obj.num;

    if (obj.ch != nullptr)
    {
        int len = strlen(obj.ch);
        this->ch = new char[len + 1];
        memcpy(this->ch, obj.ch, len+1);
    }
    else
    {
        this->ch = nullptr;
    }
}

Object1& Object1::operator=(const Object1& obj)
{
    if (this != &obj)
    {
        delete[] this->ch;
        this->num = obj.num;
        if (nullptr != obj.ch)
        {
            int len = strlen(obj.ch);
            this->ch = new char[len + 1];
            memcpy(this->ch, obj.ch, len+1);
        }
        else
        {
            this->ch = nullptr;
        }
    }
    return *this;
    
}

Object1::~Object1()
{
    if (ch != nullptr)
    {
        delete[] ch;
        ch = nullptr;

    }
}

int Object1::getInt()
{
    return num;
}
void Object1::setInt(int a)
{
    this->num = a;
}
void Object1::setCharStr(const char*ch)
{
    if (nullptr != ch)
    {
        delete[] this->ch;
        int len = strlen(ch);
        this->ch = new char[len + 1];
        memcpy(this->ch, ch, len + 1);

    }
}
char* Object1::getCharStr()
{
    return ch;
}

void func1(int para1,int param2, Object1& obj)
{
    const char* ch = "nihao hello world.";
    cout <<"Change before:"<<obj.getInt() ;
    cout<< "\t" << obj.getCharStr() << endl;

    obj.setInt(para1);
    obj.setCharStr(ch);

    cout << "Change after:" << obj.getInt();
    cout<< "\t" << obj.getCharStr() << endl;

}

void func2(int para1, int param2, Object1 obj)
{
    const char* ch = "nihao hello world.";
    cout <<"Change before:"<<obj.getInt() ;
    cout<< "\t" << obj.getCharStr() << endl;

    obj.setInt(para1);
    obj.setCharStr(ch);

    cout << "Change after:" << obj.getInt();
    cout<< "\t" << obj.getCharStr() << endl;

}

int main(int argc, char * argv[])
{
    const char * ch = "hello world" ;

    Object1 obj1(0, ch);

    {
        //块作用域对象析构
        Object1 obj2(obj1);
        cout << obj2.getInt() << "\t";
        cout<< obj2.getCharStr() << endl;
        
        Object1 obj3 = obj2;
        cout << obj3.getInt() << "\t";
        cout << obj3.getCharStr() << endl;
    }
    cout << obj1.getInt() << "\t";
    cout << obj1.getCharStr() << endl;

    //按照引用和值值传递
    int param1 = 10, param2 = 20;
    thread t1(func1, param1,param2, ref(obj1));
    if (t1.joinable())
        t1.join();

    thread t2(func2, param1, param2, obj1);
    if (t2.joinable())
        t2.join();
    //验证原对象影响
    cout << obj1.getInt() << "\t"; 
    cout << obj1.getCharStr() << endl;
    
    //使用成员函数指针和合适的对象指针及参数进行传值
    const char* ch2 = "C++11 thread.";
    thread t3(&Object1::setCharStr, &obj1, ch2);

    if (t3.joinable())
        t3.join();

    //验证线程执行后对原对象的影响
    cout << obj1.getInt() << "\t"; 
    cout << obj1.getCharStr() << endl;

    return 0;

}
</pre>
