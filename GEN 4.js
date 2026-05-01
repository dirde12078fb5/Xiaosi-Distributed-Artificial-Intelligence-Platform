// ====================== 全局状态 ======================
let monitorRunning = false;
let monitorInterval = null;
let downloadAbortController = null;
let downloadStartTime = 0;
let downloadedSize = 0;
let totalSize = 0;
let stopDownloadFlag = false;

// ====================== 标签页切换 ======================
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');
            updateStatus(`切换到 ${tab.innerText} 标签`);
        });
    });
}

// ====================== 状态栏更新 ======================
function updateStatus(text) {
    const bar = document.getElementById('statusBar');
    if (bar) bar.textContent = text;
}

// ====================== 硬件检测 ======================
function initHardwareCheck() {
    const btn = document.getElementById('checkBtn');
    if (!btn) return;
    btn.addEventListener('click', () => {
        const type = document.querySelector('input[name="checkType"]:checked').value;
        const info = document.getElementById('hardwareInfo');
        info.value = "正在进行深度硬件检测，请稍候...\n\n";
        updateStatus("正在进行深度硬件检测...");

        setTimeout(() => {
            let res = "";
            if (type === "gpu") {
                res = `=== GPU 1 详细信息 ===
型号: NVIDIA GeForce RTX 4090
利用率: 25.6%
温度: 42°C
总显存: 24.00 GB
已用显存: 8.50 GB

=== 系统信息 ===
操作系统: Windows 10 64位
总内存: 64.00 GB
可用内存: 48.50 GB
系统启动时间: 1天 5时 30分`;
            } else {
                res = `=== CPU 详细信息 ===
品牌: Intel(R) Core(TM) i9-13900K
物理核心数: 24
逻辑核心数: 32
基础频率: 3.00 GHz
当前频率: 4.50 GHz
缓存大小: L2: 32 MB

=== 系统信息 ===
操作系统: Windows 10 64位
总内存: 64.00 GB
可用内存: 48.50 GB
系统启动时间: 1天 5时 30分`;
            }
            info.value = res;
            updateStatus("硬件检测完成");
        }, 1800);
    });
}

// ====================== 实时监控 ======================
function toggleMonitor() {
    const btn = document.getElementById('monitorBtn');
    if (monitorRunning) {
        clearInterval(monitorInterval);
        monitorRunning = false;
        btn.textContent = "开始监控";
        updateStatus("监控已停止");
        document.getElementById('cpuBar').style.width = "0%";
        document.getElementById('memBar').style.width = "0%";
        document.getElementById('cpuUsage').textContent = "0";
        document.getElementById('memUsage').textContent = "0";
    } else {
        monitorRunning = true;
        btn.textContent = "停止监控";
        updateStatus("正在监控系统资源...");

        monitorInterval = setInterval(() => {
            const cpu = Math.floor(Math.random() * 70) + 10;
            const mem = Math.floor(Math.random() * 40) + 30;

            document.getElementById('cpuBar').style.width = cpu + "%";
            document.getElementById('memBar').style.width = mem + "%";
            document.getElementById('cpuUsage').textContent = cpu;
            document.getElementById('memUsage').textContent = mem;

            setProgressColor('cpuBar', cpu);
            setProgressColor('memBar', mem);
        }, 1000);
    }
}

function setProgressColor(id, percent) {
    const el = document.getElementById(id);
    if (!el) return;
    if (percent < 30) {
        el.style.background = "var(--success)";
    } else if (percent < 70) {
        el.style.background = "var(--warning)";
    } else {
        el.style.background = "var(--error)";
    }
}

// ====================== 下载功能 ======================
function startDownload() {
    const url = document.getElementById('downloadUrl').value.trim();
    if (!url || !url.startsWith('http')) {
        alert("请输入有效的 HTTP/HTTPS 下载链接");
        return;
    }

    const startBtn = document.getElementById('startDownloadBtn');
    const stopBtn = document.getElementById('stopDownloadBtn');
    startBtn.disabled = true;
    stopBtn.disabled = false;
    stopDownloadFlag = false;
    downloadedSize = 0;
    totalSize = 100 * 1024 * 1024;
    downloadStartTime = Date.now();
    updateStatus("开始下载文件...");

    downloadAbortController = new AbortController();
    const signal = downloadAbortController.signal;

    const timer = setInterval(() => {
        if (stopDownloadFlag || signal.aborted) {
            clearInterval(timer);
            startBtn.disabled = false;
            stopBtn.disabled = true;
            updateStatus("下载已停止");
            return;
        }

        const chunk = 1024 * 1024 * (Math.floor(Math.random() * 4) + 1);
        downloadedSize += chunk;
        if (downloadedSize >= totalSize) downloadedSize = totalSize;

        const pct = (downloadedSize / totalSize) * 100;
        document.getElementById('downloadProgress').style.width = pct + "%";
        updateSpeed(pct);

        const bar = document.getElementById('downloadProgress');
        if (pct < 30) bar.style.background = "var(--error)";
        else if (pct < 70) bar.style.background = "var(--warning)";
        else bar.style.background = "var(--success)";

        if (downloadedSize >= totalSize) {
            clearInterval(timer);
            alert("文件下载完成！\n保存路径：浏览器默认下载文件夹");
            startBtn.disabled = false;
            stopBtn.disabled = true;
            updateStatus("下载完成");
        }
    }, 400);
}

function stopDownload() {
    stopDownloadFlag = true;
    if (downloadAbortController) downloadAbortController.abort();
    document.getElementById('speedLabel').textContent = "正在停止下载...";
}

function updateSpeed(progress) {
    const elapsed = (Date.now() - downloadStartTime) / 1000;
    if (elapsed <= 0) return;
    const speed = (downloadedSize / elapsed) / 1024;
    document.getElementById('speedLabel').textContent =
        `速度: ${speed.toFixed(2)} KB/s (${progress.toFixed(1)}%)`;
}

// ====================== 路径与设置 ======================
function choosePath() {
    document.getElementById('savePath').value = "C:\\Users\\当前用户\\Downloads";
}
function chooseSettingsPath() {
    document.getElementById('settingsDownloadPath').value = "C:\\Users\\当前用户\\Downloads";
}
function saveSettings() {
    const path = document.getElementById('settingsDownloadPath').value;
    if (!path) { alert("请输入下载路径"); return; }
    localStorage.setItem('downloadPath', path);
    alert("设置已保存");
    updateStatus("保存设置成功");
}

// ====================== 功能按钮（模拟） ======================
function openOfficial() { alert("打开官方主页"); updateStatus("打开官方主页"); }
function openCloud() { alert("打开技术书籍"); updateStatus("打开技术书籍"); }
function openNxshell() { alert("启动 Nxshell"); updateStatus("启动 Nxshell"); }
function openRc() { alert("打开软仓"); updateStatus("打开软仓"); }
function fastDownload() { alert("打开快速下载"); updateStatus("打开快速下载"); }
function showGpuInfo() { alert("显示 GPU 信息"); updateStatus("显示 GPU 信息"); }
function checkUpdate() { alert("检查更新"); updateStatus("检查更新"); }
function openMC() { alert("打开 MC 面板"); updateStatus("打开 MC 面板"); }
function pingTest() { alert("PING 测速完成"); updateStatus("PING 测速"); }
function openTuba() { alert("打开图吧工具箱"); updateStatus("打开图吧工具箱"); }
function networkSpeed() { alert("网络加速已启动"); updateStatus("网络加速"); }
function printTool() { alert("打开打印工具"); updateStatus("打开打印工具"); }
function dataTransfer() { alert("打开数据传输"); updateStatus("打开数据传输"); }
function openTermius() { alert("启动 Termius"); updateStatus("启动 Termius"); }
function searchTool() { alert("打开万磁搜索"); updateStatus("打开万磁搜索"); }
function openLMStudio() { alert("启动 LM Studio"); updateStatus("启动 LM Studio"); }
function openGMSSH() { alert("启动 GMSSH"); updateStatus("启动 GMSSH"); }
function systemClean() { alert("系统清理完成"); updateStatus("系统清理"); }
function benchmark() { alert("性能测试完成"); updateStatus("性能测试"); }
function videoDownload() { alert("打开视频下载"); updateStatus("视频下载"); }
function windowsSSH() { alert("启动 Windows SSH"); updateStatus("Windows SSH"); }
function fanQian() { alert("启动 ViewTurbo"); updateStatus("ViewTurbo"); }
function networkTool() { alert("打开网络工具"); updateStatus("自动化网络工具"); }
function bilibiliDownload() { alert("B站下载工具"); updateStatus("B站视频下载"); }
function systemDownload() { alert("系统直连下载"); updateStatus("系统下载"); }
function gameFrame() { alert("游戏多帧生成"); updateStatus("游戏多帧生成"); }
function openVMware() { alert("启动 VMware"); updateStatus("VMware"); }
function yuanBao() { alert("启动元宝工具"); updateStatus("元宝"); }
function networkTest() { alert("多向连通测试"); updateStatus("连通测试"); }
function ipScanner() { alert("IP 扫描工具"); updateStatus("IP Scanner"); }
function aiSendme() { alert("AItSendme"); updateStatus("AItSendme"); }
function bdwpUnlimit() { alert("百度网盘解锁"); updateStatus("网盘解锁"); }

function showAbout() {
    alert(`小思分布式人工智能™ 多功能平台 11 Ultra X3D
版本：2026 Ultra X3D
开发者：shazongxian`);
    updateStatus("显示关于信息");
}

// ====================== 页面初始化 ======================
window.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initHardwareCheck();

    // 加载保存的路径
    const path = localStorage.getItem('downloadPath');
    if (path) document.getElementById('settingsDownloadPath').value = path;

    updateStatus("就绪");
});

// 页面关闭清理
window.addEventListener('beforeunload', () => {
    if (monitorInterval) clearInterval(monitorInterval);
    if (downloadAbortController) downloadAbortController.abort();
});