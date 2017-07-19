### WormWrapper V2.0 使用指南

By ttbachyinsda

------

#### 一、简介

WormWrapper 是一个简易的并行计算模块，通过在一台或多台计算机上运行多个worm来实现并行计算，并通过admin程序进行管理功能。本模块需要：

1. 一个mongoDB数据库
2. 一台或多台计算机

只需要如下步骤即可运行WormWrapper：

##### 配置依赖

请使用python 3.5运行本项目，并且安装pymongo模块（可通过pip安装）。推荐使用Anaconda的对应版本。

##### 配置MongoDB数据库

可以使用阿里云或者其他云提供的MongoDB服务，也可以自己手动搭建。搭建方法请见MongoDB官方网站。配置完成后，需要获取MongoDB的连接字符串，并将其填入wormwrapper_worm.py和wormwrapper_admin.py的dburi属性内。

##### 运行准备

在一台或多台计算机上运行多个wormwrapper_worm.py的实例，一台计算机可以运行多个实例使性能发挥到最大。运行后，worm会处于就绪状态。

##### 添加Task

首先写好代码，保存为一个.py文件，然后通过wormwrapper_admin的wormwrapper_user_add_task接口传入task的名字，信息和代码的位置，worm会根据info执行给定代码的内容。

##### 开始运行

在admin程序中输入run，即可激活所有的worm，让它们开始工作。

##### 跟踪结果

在admin程序中输入showinfo (taskname)，即可跟踪运行的结果。

##### 其他操作

可以停止一个task(stoptask)，恢复一个task并使其准备执行(resumetask)，清除一个task的输出信息(cleartask)，删除一个task(deletetask)。

#### 二、移植

worm需要告诉它做什么才能工作，而它现在不需要你修改dowork函数来告诉它，因为你可以直接把代码告诉worm。代码格式如下：

```python
import wormwrapper_interface as wi
from time import sleep
import random
def run(info, resultlist):
    while True:
        wi.emitresult("dowork " + str(info["num"]), resultlist)
        sleep(random.randint(1, 10))
```

只需要完成run过程的编写，根据info传进来的数据，通过wi.emitresult进行输出即可。resultlist这个变量可以忽略。

然后添加task的时候，只需要给出代码的路径，worm就能自动执行你需要执行的那一份代码。

#### 三、注意事项

1. admin的命令并不能马上到达worm，而是过一小段时间才会到达。
2. run和forcestop有一个100秒的最小间隔
3. 并不是每一次emitresult就会马上更新，更新是不定时进行的

#### 四、准备添加的功能

1. 自动运行多个worm
2. 对Task进行更精细的操作