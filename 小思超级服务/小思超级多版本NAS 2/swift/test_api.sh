#!/bin/bash

echo "🧪 测试小思NAS服务API"
echo "========================"

BASE_URL="http://localhost:8089"

echo "1. 测试主页"
curl -s "$BASE_URL/" | head -20
echo ""
echo ""

echo "2. 测试获取存储卷列表"
curl -s "$BASE_URL/api/storage/volumes"
echo ""
echo ""

echo "3. 测试创建存储卷"
curl -s -X POST "$BASE_URL/api/storage/volumes" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_volume","path":"./nas_data/test","quota_gb":100}'
echo ""
echo ""

echo "4. 测试获取用户列表"
curl -s "$BASE_URL/api/users"
echo ""
echo ""

echo "5. 测试创建用户"
curl -s -X POST "$BASE_URL/api/users" \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"test123","role":"user"}'
echo ""
echo ""

echo "6. 测试获取SMB共享列表"
curl -s "$BASE_URL/api/smb/shares"
echo ""
echo ""

echo "7. 测试创建SMB共享"
curl -s -X POST "$BASE_URL/api/smb/shares" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_share","path":"./nas_data/share","readonly":false,"users":["test_user"]}'
echo ""
echo ""

echo "8. 测试获取本机IP"
curl -s "$BASE_URL/api/ip/local"
echo ""
echo ""

echo "9. 测试获取推送目标列表"
curl -s "$BASE_URL/api/push/targets"
echo ""
echo ""

echo "10. 测试获取翻译（中文）"
curl -s "$BASE_URL/api/i18n/?lang=zh_CN"
echo ""
echo ""

echo "11. 测试获取翻译（英文）"
curl -s "$BASE_URL/api/i18n/?lang=en_US"
echo ""
echo ""

echo "✅ 所有测试完成"