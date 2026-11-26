# RPM 构建说明

当前 Windows 环境没有 rpmbuild / WSL2 / Docker，RPM 需要在一台 Linux 机器上编译。
构建套件位于 `build_linux/`，详细说明见 `build_linux/README.md`。

## 快速构建
```bash
sudo dnf install -y rpm-build     # Fedora / RHEL
bash build_linux/build_rpm.sh
```

生成：
```
release/Linux/xiaosi-ai-platform-5.26.11.29-4.noarch.rpm
release/Linux/xiaosi-ai-platform-5.26.11.29-4.noarch.rpm.sha256
```

## 安装
```bash
sudo dnf install --nogpgcheck ./xiaosi-ai-platform-5.26.11.29-4.noarch.rpm
xiaosi
```

## 注意
- 本包为 noarch 源码包，不包含 Windows 工具合集与 Windows 版 LM Studio。
- Windows 专用功能在 Linux 上不可用或自动降级，请在目标发行版实测。
- 旧文件 `xiaosi-ai-platform-5.26.11.29-3.noarch.rpm` 是之前的 Linux 精简版，
  不会被本套件覆盖；新包为 `-4`。
