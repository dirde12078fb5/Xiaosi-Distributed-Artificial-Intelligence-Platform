#!/bin/bash

echo "========================================"
echo "   推送到 Gitcode"
echo "========================================"
echo ""
echo "请先在 Gitcode 创建仓库，然后输入仓库地址"
echo "例如: https://gitcode.com/你的用户名/xiaosi-nas.git"
echo ""
read -p "仓库地址: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "仓库地址不能为空"
    exit 1
fi

echo ""
echo "正在添加到远程仓库..."
git remote add origin "$REPO_URL"
git add .
git commit -m "Initial commit: 小思超级多版本NAS服务 v1.0

- 支持28种语言
- 存储卷/用户/SMB共享管理
- 局域网文件夹推送
- 多网卡IP检测"

echo ""
echo "正在推送到Gitcode..."
git push -u origin master --force

echo ""
echo "完成！"
