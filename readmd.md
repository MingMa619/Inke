### WormWrapper 使用指南

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

可以使用多种方法添加task，由于需求原因暂时只提供虚拟task添加的接口。

##### 开始运行

在admin程序中输入run，即可激活所有的worm，让它们开始工作。

##### 跟踪结果

在admin程序中输入showinfo (taskname)，即可跟踪运行的结果。

#### 二、移植

worm需要告诉它做什么才能工作，而它只需要你修改dowork函数来告诉它。dowork函数有两个参数，第二个参数是输出结果的列表，格式如下：

[{"timestamp": (timestamp), "data": (data)}, ...]

第一个参数是输入的信息，格式为一个dict，worm应该根据输入的信息进行正确的操作。

添加结果可以使用emitresult函数。

#### 三、注意事项

1. admin的命令并不能马上到达worm，而是过一小段时间才会到达。
2. run和forcestop有一个100秒的最小间隔
3. 并不是每一次emitresult就会马上更新，更新是不定时进行的

#### 四、准备添加的功能

1. 自动运行多个worm
2. 对Task进行更精细的操作