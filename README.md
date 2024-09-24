# stair_web_backend

双皮剪力墙深化设计的后端实现

## 开发环境准备

- python 3.8 环境

```shell
pip install -r requirements.txt
```

- 同步数据库表结构

```shell
python manage.py migrate
```

- 创建超级管理员

```shell
python manage.py createsuperuser
```

**注意**:该账号用于登录django网站,具有最高权限

- 运行web 服务

```shell
python manage.py runserver 127.0.0.1:8000
```
然后[点击访问](http://127.0.0.1:8000/admin)
