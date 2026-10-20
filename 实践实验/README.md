# 分布式人工智能平台学习资料库

> 📚 围绕「基于分布式架构的 OpenStack 私有云计算平台」主题，收录从计算机基础到云平台部署的全链路学习资料。

## 📖 项目简介

本仓库是一套面向 **分布式架构与私有云计算平台** 的学习资料合集，内容覆盖：

- 计算机基础入门
- Linux 系统理论
- 各类服务（Apache / MySQL / Docker / K8S / OpenStack）的安装与配置
- 网站发布与 CMS 建站
- 常见运维问题解决方案
- 核心论文：基于分布式架构的 OpenStack 私有云计算平台的设计与实现

## 📂 目录结构

```
BOOK/
├── 服务类/                    # 服务搭建与运维文档（10 个 PDF）
├── 服务类安装包/               # 配套安装包（6 个文件）
├── 理论类/                    # 基础理论文档（2 个 PDF）
├── 问题解决/                  # 常见问题解决方案（2 个 PDF）
├── 计算机起点.pdf              # 计算机基础入门
└── 基于分布式架构的OpenStack私有云计算平台的设计与实现.pdf
```

---

## 📄 文档索引

### 1. 服务类/

| 文档 | 内容说明 | 标签 |
|------|---------|------|
| [Apache安装.pdf](./服务类/Apache安装.pdf) | Apache Web 服务器安装与配置 | `web服务` `apache` |
| [CentOS_7_MySQl搭建.pdf](./服务类/CentOS_7_MySQl搭建.pdf) | CentOS 7 下 MySQL 数据库搭建 | `数据库` `mysql` |
| [CentOS 搭建大米CMS.pdf](./服务类/CentOS%20搭建大米CMS.pdf) | 大米 CMS 建站教程 | `cms` |
| [Docker 容器技术 V1.0.pdf](./服务类/Docker%20容器技术%20V1.0.pdf) | Docker 容器化技术入门与实践 | `容器` `docker` |
| [K8S配置和搭建V2.0.pdf](./服务类/K8S配置和搭建V2.0.pdf) | Kubernetes 集群配置与搭建 | `k8s` `编排` |
| [Openstack-单机搭建(新版).pdf](./服务类/Openstack-单机搭建(新版).pdf) | OpenStack 单机版搭建指南 | `openstack` `私有云` |
| [Openstack终版.pdf](./服务类/Openstack终版.pdf) | OpenStack 完整部署方案（终版） | `openstack` `终版` |
| [发布网站 wordpress_V1.pdf](./服务类/发布网站%20wordpress_V1.pdf) | WordPress 网站发布教程 | `wordpress` `建站` |
| [常见的yum源配置的三种方案.pdf](./服务类/常见的yum源配置的三种方案.pdf) | yum 源配置的三种方案 | `yum` `包管理` |
| [解决pip install速度慢、网络速度较慢总是卡死的办法.pdf](./服务类/解决pip%20install速度慢、网络速度较慢总是卡死的办法.pdf) | pip 安装加速与卡死问题解决 | `pip` `python` |

### 2. 服务类安装包/

| 文件 | 用途 | 关联文档 |
|------|------|---------|
| `lnmp1.5.tar.gz` | LNMP 一键安装包（Linux + Nginx + MySQL + PHP） | — |
| `wordpress-4.7.21-zh_cn.tar.gz` | WordPress 中文版源码 | 发布网站 wordpress_V1.pdf |
| `Discuz_X2.5_SC_UTF8.zip` | Discuz 论坛源码 | — |
| `phpBB-v3.3.7.zip` | phpBB 论坛源码 | — |
| `quick_start.sh` | 快速启动脚本 | — |
| `ezdown` | 下载辅助工具 | — |

### 3. 理论类/

| 文档 | 内容说明 |
|------|---------|
| [Linux 文件系统结构介绍.pdf](./理论类/Linux%20文件系统结构介绍.pdf) | Linux 文件系统层级结构详解 |
| [Python游戏开发白皮书 V1.0.pdf](./理论类/Python游戏开发白皮书%20V1.0.pdf) | Python 游戏开发基础白皮书 |

### 4. 问题解决/

| 文档 | 问题场景 |
|------|---------|
| [03 CentOS 7 忘记root密码修改方案.pdf](./问题解决/03%20CentOS%207%20忘记root密码修改方案.pdf) | CentOS 7 忘记 root 密码的修改方案 |
| [有潜在的安全问题Firefox 检测到潜在的安全威胁.pdf](./问题解决/有潜在的安全问题Firefox%20检测到潜在的安全威胁.pdf) | Firefox 检测到潜在安全威胁的处理办法 |

### 5. 根目录核心文件

| 文件 | 定位 |
|------|------|
| [计算机起点.pdf](./计算机起点.pdf) | 计算机入门基础，仓库的"前置知识" |
| [基于分布式架构的OpenStack私有云计算平台的设计与实现.pdf](./基于分布式架构的OpenStack私有云计算平台的设计与实现.pdf) | **核心论文**，整个资料库的顶层设计文档 |

---

## 🚀 推荐学习路径

按以下顺序学习，可形成从基础到实战的完整知识链：

| 阶段 | 主题 | 对应资料 |
|------|------|---------|
| 🔰 入门 | 计算机基础 | `计算机起点.pdf` |
| 📚 理论 | Linux 文件系统 | `理论类/Linux 文件系统结构介绍.pdf` |
| ⚙️ 基础服务 | Web 与数据库 | `服务类/Apache安装.pdf` → `服务类/CentOS_7_MySQl搭建.pdf` |
| 🐳 容器化 | Docker | `服务类/Docker 容器技术 V1.0.pdf` |
| ☸️ 编排 | Kubernetes | `服务类/K8S配置和搭建V2.0.pdf` |
| ☁️ 私有云 | OpenStack | `服务类/Openstack-单机搭建(新版).pdf` → `服务类/Openstack终版.pdf` |
| 🏗️ 顶层设计 | 论文研读 | `基于分布式架构的OpenStack私有云计算平台的设计与实现.pdf` |

---

## 🔧 仓库管理规范（GitCode 风格）

### 分支管理

```
main                          # 稳定版资料
├── feature/openstack-doc     # OpenStack 文档完善分支
├── feature/k8s-update        # K8S 文档更新分支
└── hotfix/troubleshooting    # 问题解决方案补充分支
```

### Issue 模板建议

| 模板类型 | 用途 |
|---------|------|
| 学习疑问 | 记录学习过程中遇到的问题 |
| 文档纠错 | 指出文档中的错误或过时内容 |
| 安装包更新 | 申请更新安装包版本 |

### CodeOwners 建议

| 路径 | 负责人方向 |
|------|-----------|
| `服务类/Openstack*` | OpenStack 方向 |
| `服务类/K8S*` | K8S 方向 |
| `服务类/Docker*` | Docker 方向 |
| `问题解决/` | 运维方向 |

---

## 📊 仓库统计

| 维度 | 数据 |
|------|------|
| 文件总数 | 22 |
| 目录数 | 5 |
| PDF 文档 | 16 |
| 安装包 | 4 |
| 脚本文件 | 1 |
| 核心主题 | OpenStack、K8S、Docker、Linux 运维 |

---

## 📝 说明

- 本仓库为学习资料库，所有 PDF 文档仅供学习参考
- 安装包请从官方渠道下载最新版本，本仓库提供的版本可能已过期
- 如有问题请提交 Issue
