# 推送到 Gitcode 指南

## 准备工作

### 1. 创建 Gitcode 仓库

1. 访问 [Gitcode](https://gitcode.com) 并登录
2. 点击「新建仓库」
3. 填写仓库信息：
   - 仓库名称：`xiaosi-nas`
   - 描述：小思超级多版本NAS服务
   - 公开/私有：选择「公开」
   - 不要勾选「使用README初始化」
4. 点击「创建仓库」

### 2. 获取仓库地址

创建后会显示仓库地址，例如：
```
https://gitcode.com/你的用户名/xiaosi-nas.git
```

---

## 推送代码

在项目目录下执行以下命令：

```bash
# 1. 添加所有文件到暂存区
git add .

# 2. 提交代码
git commit -m "Initial commit: 小思超级多版本NAS服务 v1.0

- 支持28种语言
- 存储卷/用户/SMB共享管理
- 局域网文件夹推送
- 多网卡IP检测"

# 3. 添加远程仓库（替换为你的地址）
git remote add origin https://gitcode.com/你的用户名/xiaosi-nas.git

# 4. 推送到Gitcode
git push -u origin master
```

---

## 一键推送脚本

如果你是首次推送，可以运行项目中的 `push_to_gitcode.sh` 脚本：

```bash
./push_to_gitcode.sh
```

或在 Windows 命令行中：
```cmd
push_to_gitcode.bat
```

---

## 常见问题

### Q: 推送时需要登录？
**答:** 是的，首次推送需要输入Gitcode用户名和密码或令牌。

### Q: 如何生成访问令牌？
1. 进入 Gitcode → 设置 → 访问令牌
2. 创建新令牌，勾选 `repo` 权限
3. 使用令牌代替密码推送

### Q: 推送被拒绝？
```
! [rejected]        master -> master (fetch first)
```
**答:** 远程仓库有更新，先拉取再推送：
```bash
git pull origin master --rebase
git push origin master
```

---

## Gitcode 仓库结构

```
xiaosi-nas/
├── README.md         # 项目说明
├── LICENSE           # MIT许可证
├── .gitignore        # Git忽略规则
├── nas_server.py     # Python主程序
├── start.bat         # Windows启动
├── start.sh          # Linux/macOS启动
├── config.json       # 配置文件
└── push_to_gitcode.sh # 推送脚本
```

---

## 更新代码

以后更新代码后，推送命令：

```bash
git add .
git commit -m "更新说明"
git push origin master
```

---

## 克隆仓库

在其他机器上克隆：

```bash
git clone https://gitcode.com/你的用户名/xiaosi-nas.git
cd xiaosi-nas
python nas_server.py
```

---

## Gitcode 特性

- 🚀 免费且高速的访问
- 📦 中国大陆优化
- 🔒 支持私有仓库
- 📝 支持Markdown文档
- 🌐 中文界面
