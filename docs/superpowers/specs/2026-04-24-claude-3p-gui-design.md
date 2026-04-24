# Claude Desktop 第三方网关配置 GUI (Windows .exe) 设计文档

**日期**: 2026-04-24
**参考脚本**: `/Users/apple/Desktop/claude-3p-setup.ps1`
**产出**: Windows 可执行文件 `Claude3pSetup.exe`

---

## 1. 背景与目标

在 PS1 脚本 (`claude-3p-setup.ps1`) 已有的交互式 CLI 之上,用 Python + tkinter 做一个图形化包装,降低使用门槛。核心变更是**移除自定义 URL 能力**,仅硬编码支持 3 个网关:

- `https://pikachu.claudecode.love`
- `https://dk.claudecode.love`
- `http://154.12.51.83`

其他所有行为(拉模型 → 选模型 → 写 `%APPDATA%\Claude-3p\configLibrary\*.json` → 更新 `_meta.json` → 可选重启 Claude Desktop)与 PS1 脚本保持一致。

## 2. 技术栈

| 方面 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.10+ | tkinter 跨版本稳定,有 urllib 标准库无需 `requests` |
| GUI | tkinter (标准库) | 无额外依赖,打包体积小 (~10MB) |
| HTTP | `urllib.request` | 标准库,PyInstaller 打包更简单 |
| 并发 | `threading` + `queue.Queue` | 防止拉模型阻塞 GUI 主线程 |
| 打包 | PyInstaller `--onefile --windowed` | 单 exe 产物,无 console 窗口 |
| 构建平台 | **必须在 Windows 上打包** | PyInstaller 不支持交叉编译 |

## 3. 架构

单文件 Python 应用,逻辑分三层:

```
claude_3p_gui.py
├── GATEWAYS (常量)                  # 3 个硬编码 URL
│
├── class ConfigManager              # 纯数据层,无 GUI 依赖
│   ├── ensure_claude_dir()          # 检查 %APPDATA%\Claude-3p 存在
│   ├── ensure_meta()                # 创建/读取 _meta.json
│   ├── backup_library()             # 写入前备份 configLibrary → configLibrary.bak-{ts}
│   ├── write_profile(name, url, key, models) -> profile_id
│   └── restart_claude() -> bool     # 杀进程 + 启动
│
├── class ModelFetcher               # 纯网络层,无 GUI 依赖
│   └── fetch(base_url, api_key) -> list[str] | raise
│       # 依次尝试 {base}/v1/models 和 {base}/models
│       # 带三种 header: Authorization/x-api-key/anthropic-version
│       # 超时 15s
│
└── class App(tk.Tk)                 # GUI 层,调用上述两个类
    ├── _build_ui()                  # 构建控件
    ├── _on_fetch_click()            # 启动后台线程
    ├── _poll_fetch_queue()          # after(100ms) 轮询结果
    ├── _on_write_click()
    └── _log(msg)                    # 底部日志区输出
```

**边界设计**: `ConfigManager` 和 `ModelFetcher` 不引用 tkinter,未来换 GUI 框架只需替换 App 类。

## 4. 界面

固定窗口尺寸 560×520,不可缩放(避免布局适配复杂度)。

```
┌─ Claude Desktop 第三方网关配置 ─────────────────────┐
│                                                      │
│  网关 URL:                                          │
│  ( ) https://pikachu.claudecode.love                │
│  (•) https://dk.claudecode.love                     │
│  ( ) http://154.12.51.83                            │
│                                                      │
│  API Key:  [sk-xxxxxxxxxxxxxxxxxxxx        ] [👁]   │
│                                                      │
│  [ 拉取模型列表 ]    状态: 已获取 12 个模型         │
│                                                      │
│  可用模型:                    [全选]  [全清]        │
│  ┌────────────────────────────────────────────┐    │
│  │ ☑ claude-opus-4-7                          │    │
│  │ ☑ claude-sonnet-4-6                        │    │
│  │ ☐ claude-haiku-4-5                         │    │
│  │ ...                                        │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  档案名: [Default                ]                  │
│  ☑ 写入后重启 Claude Desktop                        │
│                                                      │
│              [ 写入配置 ]    [ 退出 ]               │
│                                                      │
│  日志: 已备份旧配置到 configLibrary.bak-20260424... │
└──────────────────────────────────────────────────────┘
```

**控件细节**:

- 网关 URL: `ttk.Radiobutton` 三选一,默认选第一个 `pikachu.claudecode.love`
- API Key: `ttk.Entry(show='•')`,旁边的 👁 按钮切换 `show` 属性
- 拉取模型按钮: 点击后文字变 "拉取中...",禁用状态直到线程返回
- 模型列表: `tk.Listbox` 单选模式不够,用 `tk.Checkbutton` + 滚动框架实现多选勾选。每行一个 BooleanVar。
- 全选/全清: 遍历所有 BooleanVar 设 True/False
- 档案名: `ttk.Entry`,默认 "Default"
- 重启勾选: `ttk.Checkbutton`,默认勾选
- 写入配置: 点击前校验(key 非空、至少选中一个模型、档案名非空)
- 日志区: `tk.Text` 只读,可滚动,最近信息在底部
- 字体: Windows 下用 `Microsoft YaHei UI` 10pt,避免中文字符渲染问题

## 5. 数据流

### 5.1 拉模型流程

1. 用户点 "拉取模型列表"
2. GUI 主线程: 禁用按钮 + 状态栏显示 "拉取中..."
3. 启动 `threading.Thread(target=ModelFetcher.fetch, args=(url, key))`
4. 结果 put 到 `queue.Queue`
5. GUI 主线程通过 `self.after(100, self._poll_fetch_queue)` 轮询
6. 成功: 渲染模型列表(默认全勾),状态栏 "已获取 N 个模型"
7. 失败: 状态栏红字显示错误摘要 + 模型列表区替换为一个单行 Entry + "应用手动模型" 按钮,用户输入逗号分隔的模型名(例: `claude-opus-4-7,claude-sonnet-4-6`),点应用后按同样的勾选形态渲染。这是兜底,不弹模态窗,避免打断节奏。

### 5.2 写配置流程

1. 用户点 "写入配置"
2. 前置校验:
   - API Key 非空
   - 至少勾选一个模型
   - 档案名非空
   - `%APPDATA%\Claude-3p` 存在(不存在 → 弹窗"请先装 Claude Desktop 并启动一次")
3. 调用 `ConfigManager.backup_library()` 备份
4. 调用 `ConfigManager.write_profile(name, url, key, models)`:
   - 读 `_meta.json`
   - 若已有同名档案,复用 profile_id(和 PS1 一致)
   - 否则 `uuid.uuid4()` 生成新 id
   - 写 `configLibrary\{profile_id}.json`:
     ```json
     {
       "inferenceProvider": "gateway",
       "inferenceGatewayBaseUrl": "https://.../",
       "inferenceGatewayApiKey": "sk-...",
       "inferenceModels": ["claude-opus-4-7", ...]
     }
     ```
   - 更新 `_meta.json.appliedId` 和 entries
5. 若勾选重启: `ConfigManager.restart_claude()`
   - `taskkill /F /IM Claude.exe`(Python: `subprocess.run([...], check=False)`)
   - 查找 `%LOCALAPPDATA%\Claude\*.exe` 再找 `%PROGRAMFILES%\Claude\*.exe`
   - `subprocess.Popen([exe_path])`
   - 找不到: 日志区提示手动启动,不视为错误
6. 日志区追加: "配置已写入: {path}"、"档案 'Default' 已设为激活"、"已重启 Claude Desktop" (或 "未找到 Claude.exe")

### 5.3 URL 规范化

用户选的 URL 可能不带尾 `/`,写入前统一规范化:

```python
def normalize_base_url(url: str) -> str:
    url = url.rstrip('/')
    if url.endswith('/v1'):
        url = url[:-3]
    return url + '/'
```

3 个硬编码的 URL 都已是干净形式,此函数主要是为了和 PS1 行为一致。

## 6. 错误处理

| 场景 | 处理 |
|---|---|
| Key 为空,点拉取 | 按钮保持禁用 + 状态栏提示 "请先输入 API Key" |
| 拉模型超时 (15s) | 状态栏红字 "网络超时" + 切换到手动输入兜底 |
| HTTP 401/403 | 状态栏红字 "鉴权失败,请检查 API Key" + 切换到手动输入兜底 |
| HTTP 5xx | 状态栏红字 "服务端错误 {status_code}" + 切换到手动输入兜底 |
| 响应 JSON 解析失败 | 状态栏红字 "响应格式异常" + 切换到手动输入兜底 |
| `%APPDATA%\Claude-3p` 不存在 | 启动时弹窗 "未找到 Claude Desktop 配置目录,请先安装并启动一次" + 禁用写入按钮 |
| 写入文件权限失败 | 弹窗 "写入失败: {e}",不继续重启 |
| 重启找不到 Claude.exe | 日志区 warn,不弹窗 |
| 已有同名档案 | 复用 id(和 PS1 一致),不询问不警告 |

## 7. 打包流程

### 7.1 源码结构

```
Claude3pSetupWin/
├── claude_3p_gui.py          # 主程序(本文档的实现)
├── build.bat                 # Windows 构建脚本
├── requirements-build.txt    # 仅构建期依赖(pyinstaller)
├── README.md                 # 用户使用说明
└── docs/superpowers/specs/
    └── 2026-04-24-claude-3p-gui-design.md
```

运行时无任何第三方依赖,`requirements-build.txt` 仅包含:

```
pyinstaller>=6.0
```

### 7.2 build.bat

```batch
@echo off
python -m pip install -r requirements-build.txt
pyinstaller --onefile --windowed --name Claude3pSetup claude_3p_gui.py
echo.
echo Built: dist\Claude3pSetup.exe
pause
```

### 7.3 跨平台说明

**PyInstaller 不支持交叉编译**。在 macOS 上运行 PyInstaller 只能产出 macOS 二进制文件,无法直接打出 `.exe`。

三种可选路径:

1. **用户侧 Windows 构建 (推荐,README 写明)**: 用户在 Windows 机器上装 Python,克隆项目,双击 `build.bat`
2. **GitHub Actions**: 写一个 workflow 在 windows-latest runner 上构建 + 上传 artifact
3. **Wine + PyInstaller**: macOS 用 Homebrew 装 wine,装 Windows Python,用 wine 驱动 PyInstaller。不推荐(脆弱)

本次交付默认走路径 1 + 可选路径 2。

## 8. 测试策略

**无自动化单元测试**。理由: 纯 GUI 工具,核心价值是 UI 交互,单元测试对 GUI 的覆盖成本高收益低。

**手动验收清单** (Windows 上执行,已装 Claude Desktop 并启动过一次):

- [ ] 启动 `Claude3pSetup.exe` 无报错,窗口居中
- [ ] 3 个 URL radio 按钮可见且可切换,默认选第一个
- [ ] Key 输入框 show 为 `•`,眼睛按钮切换后变明文
- [ ] 未输入 Key 时 "拉取模型列表" 按钮禁用
- [ ] 错误 Key 拉模型 → 弹窗"鉴权失败"
- [ ] 关闭网络/用无法连通的 URL → 超时弹窗
- [ ] 正确 Key 拉模型 → 列表渲染,默认全勾
- [ ] 全选/全清按钮生效
- [ ] 清空档案名点写入 → 提示"档案名非空"
- [ ] 写入 → `%APPDATA%\Claude-3p\configLibrary\{guid}.json` 存在且字段正确
- [ ] `_meta.json.appliedId` 指向刚写入的 id
- [ ] 同名档案二次写入 → id 复用,不新增
- [ ] 勾选重启 → Claude Desktop 被杀并重启
- [ ] `configLibrary.bak-{时间戳}` 备份目录被创建

## 9. 范围

### 做
- tkinter GUI(560×520 固定窗口)
- 3 个硬编码 URL 三选一
- API Key 输入 + 显隐切换
- 拉取模型(后台线程,15s 超时)
- 勾选列表 + 全选/全清
- 手动输入模型 fallback
- 写入 `%APPDATA%\Claude-3p\configLibrary\*.json` 和 `_meta.json`
- 写入前备份
- 可选重启 Claude Desktop
- PyInstaller 单 exe 打包
- `build.bat` 一键构建
- 中文 UI(和 PS1 风格一致)

### 不做
- 自定义 URL 输入(用户明确要求)
- 命令行参数(`-List` 等)
- 档案删除/重命名 UI(复用 PS1 的自动复用同名档案逻辑)
- macOS/Linux GUI 版本(本次只交付 Windows)
- 自动更新、日志文件、崩溃上报
- 登录/多用户
- 配置导入导出
- 自动化测试(GUI 单元测试成本高收益低)

## 10. 开放问题

无。所有关键决策在本文档中已确定。
