# 剪力墙深化设计

## 一、输入信息

pip install dc_rebar@git+ssh://git@github.com/IBLofCQU/dc_rebar.git


PKPM或YJK结构计算数据
暂时以Json作为中间数据文件

- webapi

    以运行server_run.py 脚本的方式启动，默认端口占用8083,需要使用的url 后缀为 /countbeamcolumnhandler
    
- worker
    
    以运行tornado celery 配合的计算子程序,运行方式如下
    
    ```bash

    celery -A tasks worker -l info -P eventlet

    ```

注意：
    
    1.webapi 和worker 采用redis 解耦,此时redis 需要配置。目前redis 配置在本地，暂时无需修改
    2.计算的参数和结果未进行存放,采用队列进行通信回发。此时队列是独立配置的，目前是配置在云服务器端。
    
## 二、客户端插件

- 客户端插件内置的rabbit队列IP ，user，pwd 均写死，当调整rabbitmq 指向时需要重新编译源码。

- 客户端使用的serverip 和后缀，均写死，修改部署的位置,需要客户端插件重新编译。


####  redis 相关路径

D:\Program Files\Redis\redis-cli.exe
flushall

#### revit addin 配置路径

C:\ProgramData\Autodesk\Revit\Addins\2019\Config


#### 其他无关紧要

worker 启动方式

celery -A tasks worker -l info -P eventlet



http://127.0.0.1:8083/

#### 代码模块分类
- DoubleWallDesign----双皮剪力墙结构和深化设计数据
- RebarLayout-----双皮剪力墙钢筋排布模块
- DigitalDesign----双皮剪力墙数字化设计(IFC建立、生成生产数据)
- GenerateDrawing----生成设计图纸
- tmp----dxf模板文件模块

