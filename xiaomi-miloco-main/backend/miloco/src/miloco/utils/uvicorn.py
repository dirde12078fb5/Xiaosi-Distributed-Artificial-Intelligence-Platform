import logging

from miloco.config import get_settings
from miloco.utils.logger import setup_warning_filters

logger = logging.getLogger(name=__name__)

# 跟踪已 warn 过的 deprecation 字段值(field_name, value),module-level 一次性。
# 防 hot reload / 测试反复调 get_uvicorn_config 时 warn 洪水(住户日志被刷屏)。
_WARNED_DEPRECATIONS: set[tuple[str, str]] = set()


def get_uvicorn_log_config(
    enable_console_logging: bool | None = None,
):
    """Build a single-handler dictConfig for logging.

    The only handler is a StreamHandler on sys.stderr. In daemon mode
    bootstrap() dup2s stderr to the per-boot log file, so this one handler
    suffices for both dev (terminal) and daemon (file) scenarios — a single
    writer to the target fd. The flag here stays for compatibility; setting
    it False disables Python logger output entirely (rarely useful).
    """
    server = get_settings().server
    log_level = str(server.log_level).upper()
    console_logging = (
        server.enable_console_logging
        if enable_console_logging is None
        else enable_console_logging
    )

    handlers = {}
    handler_list: list[str] = []
    if console_logging:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": log_level,
        }
        handler_list.append("console")

    setup_warning_filters()

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            # ColoredFormatter:给 WARNING/ERROR 的 levelname+message 上色(灰底黄/红),
            # 便于 tail -f 时定位 omni 超时等错误。色码会进日志文件,grep 仍可匹配文本。
            "default": {
                "()": "miloco.utils.logger.ColoredFormatter",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": handlers,
        "root": {"level": log_level, "handlers": handler_list},
        "loggers": {
            "uvicorn": {
                "level": log_level,
                "handlers": handler_list,
                "propagate": False,
            },
            "uvicorn.access": {
                "level": log_level,
                "handlers": handler_list,
                "propagate": False,
            },
            "uvicorn.error": {
                "level": log_level,
                "handlers": handler_list,
                "propagate": False,
            },
            # miot 摄像头 P2P 库的连接 / 重连日志(``cs2_client_connect``、``MISS``、
            # ``PPCS_Connect errorcode``、``try start camera`` 等)用 INFO 输出且
            # 单个不可达 cam 每 ~30 秒重试一次,几小时能堆几千行,把真正的 backend
            # 日志淹没。降到 WARNING 屏蔽常态重连噪音;真正的连接异常 SDK 会用
            # WARNING/ERROR 出,仍可见。运维侧若需追这层细节,启动设 LOG_LEVEL=DEBUG
            # 即可恢复。
            "miot.camera": {
                "level": "WARNING",
                "handlers": handler_list,
                "propagate": False,
            },
        },
    }


def get_uvicorn_config():
    """Get and initialize uvicorn config.

    永远 HTTP 模式——本机 / 局域网访问加密无意义；跨网访问应通过反向代理
    （nginx / cloudflare-tunnel）+ 真证书。原 self-signed cert 自动生成 +
    https 启动逻辑已废弃（住户角度只看到一个 http://host:1810 入口，零证书
    警告，install.sh 单端口）。
    """
    server = get_settings().server
    # 旧 config 可能仍带 tls_certfile / tls_keyfile 字段;它们已废弃,
    # 不再注入给 uvicorn。配过的运维需要知道字段静默失效,给一行 warn 提醒。
    # 用 _WARNED_DEPRECATIONS module-level set 跟踪已 warn 过的字段值,防止
    # hot reload / 测试反复调 get_uvicorn_config 时 warn 刷屏。
    dep_key = ("tls_certfile_keyfile", f"{server.tls_certfile}|{server.tls_keyfile}")
    if (
        server.tls_certfile or server.tls_keyfile
    ) and dep_key not in _WARNED_DEPRECATIONS:
        _WARNED_DEPRECATIONS.add(dep_key)
        logger.warning(
            "server.tls_certfile / tls_keyfile 已废弃,backend 永远以 HTTP 启动;"
            "跨网加密请改用 nginx / cloudflare-tunnel + 真证书在反代层终结 TLS。"
            "当前配置静默忽略;v0.1.0 起将彻底从 schema 删除。"
        )
    # log_config=None 让 uvicorn 跳过 dictConfig，沿用 bootstrap() 已配好的 logging
    # 注:**禁止**在这里加 workers 字段。miloco 后端是单实例 daemon(感知引擎 / 监控
    # 守护 / 配置缓存假设单进程),fork 多 worker 会撞 db lock + double-bind。
    # main.py::start_server 末尾 `if workers != 1: raise NotImplementedError` 是
    # future-proof 守护 — 现在 uv_config 不含 workers 守护是 no-op,**未来有人在这
    # 里加 workers=N 字段时**会立即 raise 把改动挡回去。横向扩展走反代层(nginx
    # 多上游 / haproxy)而非 uvicorn workers。
    return {
        "host": server.host,
        "port": server.port,
        "log_level": server.log_level,
        "log_config": None,
    }
