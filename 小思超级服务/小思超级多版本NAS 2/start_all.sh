#!/bin/bash

echo "========================================"
echo "   小思超级多版本NAS - 第二代"
echo "   支持20种编程语言"
echo "========================================"
echo ""
echo "请选择要启动的语言版本："
echo ""
echo "第一梯队（高性能）："
echo "  1. Python   (端口8080) - 零依赖，开箱即用"
echo "  2. Node.js  (端口8081) - Express框架，前端友好"
echo "  3. Go       (端口8082) - 高性能编译版"
echo "  4. Java     (端口8083) - Spring Boot生态"
echo "  5. Rust     (端口8084) - 内存安全，极致性能"
echo ""
echo "第二梯队（企业级）："
echo "  6. C#       (端口8085) - .NET Core跨平台"
echo "  7. C++      (端口8086) - 原生性能"
echo "  8. Ruby     (端口8087) - Sinatra简洁"
echo "  9. PHP      (端口8088) - 原生PHP内置服务器"
echo "  10. Swift   (端口8089) - Apple生态原生支持"
echo ""
echo "第三梯队（现代语言）："
echo "  11. Kotlin     (端口8090) - JetBrains官方语言"
echo "  12. TypeScript (端口8091) - 类型安全的JavaScript"
echo "  13. Dart       (端口8092) - Flutter生态"
echo "  14. Scala      (端口8093) - JVM函数式编程"
echo "  15. Lua        (端口8094) - 轻量级脚本"
echo ""
echo "第四梯队（小众精品）："
echo "  16. Perl     (端口8095) - 文本处理强大"
echo "  17. Crystal  (端口8096) - Ruby语法C性能"
echo "  18. Nim      (端口8097) - Python语法C性能"
echo "  19. Elixir   (端口8098) - Erlang VM并发"
echo "  20. F#       (端口8099) - .NET函数式编程"
echo ""
echo "  0. 退出"
echo ""

read -p "请输入选项编号 (0-20): " choice

case $choice in
    0) exit ;;
    1) cd python && ./start.sh ;;
    2) cd nodejs && ./start.sh ;;
    3) cd go && ./start.sh ;;
    4) cd java && ./start.sh ;;
    5) cd rust && ./start.sh ;;
    6) cd csharp && ./start.sh ;;
    7) cd cpp && ./start.sh ;;
    8) cd ruby && ./start.sh ;;
    9) cd php && ./start.sh ;;
    10) cd swift && ./start.sh ;;
    11) cd kotlin && ./start.sh ;;
    12) cd typescript && ./start.sh ;;
    13) cd dart && ./start.sh ;;
    14) cd scala && ./start.sh ;;
    15) cd lua && ./start.sh ;;
    16) cd perl && ./start.sh ;;
    17) cd crystal && ./start.sh ;;
    18) cd nim && ./start.sh ;;
    19) cd elixir && ./start.sh ;;
    20) cd fsharp && ./start.sh ;;
    *) echo "选项无效，请重新运行脚本。" ;;
esac