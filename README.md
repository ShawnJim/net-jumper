# vmess 自动化安装脚本

## 先决条件

- 开放服务器80、443、8080端口

## 快速安装
```shell
git clone https://github.com/ShawnJim/net-jumper.git
cd net-jumper
chmod +x install.sh && ./install.sh
```

## 验证通过环境
- Ubuntu 20.04
- CentOS 7.6

## 核心组件
- V2ray Core
- OpenResty
- Acme.sh (证书受签)
- Vnstat (监控)

## 功能模块
- 流量监控
  - 流量超额邮件告警
  - 流量超额自动切断
- GFW防检测
- 自动续签证书
- 管理后台
- 订阅生成
- `cfw` 客户端 Rules 管理

## 最后

本项目仅供学习交流使用，不得用于任何商业用途

有任何疑问请在 Issues 中讨论沟通
