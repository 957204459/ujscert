# 江苏大学网络安全漏洞响应平台

## 运行

### 环境准备

1. 安装 docker 和 [docker-compose](https://docs.docker.com/compose/)
1. 安装 git, 克隆仓库
1. `docker-composer up· 运行

## 开发环境

开发配置文件为 `docker-compose.yml`。部署前复制 `production-example.yml` 为 `docker-compose-production.yml`, 按需求修改配置。

使用 `docker-compose up` 可直接运行测试环境。
使用 `docker-compose --file=docker-compose-production.yml` 可指定配置文件, 实现生产环境变量的切换。

## 目录结构

* `docker/data` docker 的数据持久化
* `docker/nginx` `docker/postgres` `docker/web` 分别对应 nginx, 数据库, Python web 的 Dockerfile
* `docker/web/ca` 存储 CA 私钥和证书, 服务器端私钥和证书
* `web` Django 项目源码
* `web/assets` 运行 Django collectstatic 之后的目的目录
* `node_modules` 使用 npm 安装的前端依赖项
* `templates` Django 模板
* `ujscert` 业务逻辑实现

## 生产环境

可参考 `production-example.yml`, 根据需要自行修改 docker-compose-production.yml 的配置。
docker-compose-production.yml 中实例名和对应的服务如下

* `web_prod` 生产环境的 Python web
* `nginx` nginx, 做静态文件服务和应用反向代理
* `db_prod` 生产环境数据库

## TODO

* 礼品兑换
* 漏洞响应时间线
* 用户手册
* 社区和站内信