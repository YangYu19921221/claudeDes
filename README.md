# Claude3pSetup (Windows GUI)

一个图形化配置工具,用于把 Claude Desktop (Windows, 已开启 Developer Mode) 指向以下三个固定的第三方网关之一:

- `https://pikachu.claudecode.love`
- `https://dk.claudecode.love`
- `http://154.12.51.83`

功能对标项目根目录的 `claude-3p-setup.ps1`,但 URL 仅限上述三个(不支持自定义)。

## 使用 (已打包好的 exe)

1. 双击 `Claude3pSetup.exe`
2. 选择网关 URL
3. 输入 API Key (sk-...)
4. 点 "拉取模型列表"
5. 勾选要启用的模型
6. 填档案名 (默认 Default),决定是否勾选 "写入后重启 Claude Desktop"
7. 点 "写入配置"

配置写入 `%APPDATA%\Claude-3p\configLibrary\{profileId}.json`,并更新 `_meta.json.appliedId`。

## 自行构建 (Windows)

需要 Python 3.10+ 和 pip。

```bat
git clone <this-repo>
cd Claude3pSetupWin
build.bat
```

构建产物: `dist\Claude3pSetup.exe`。

## 开发 (任意平台)

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests/ -v
python claude_3p_gui.py   # 运行 GUI (macOS/Linux 可调试,但写入路径仅 Windows 可用)
```

## 在 GitHub Actions 上自动打包 (无需 Windows 机器)

项目自带 `.github/workflows/build-windows.yml`,推到 GitHub 后会自动:

1. 在 `windows-latest` runner 上跑单元测试
2. 用 PyInstaller 打出 `Claude3pSetup.exe`
3. 把 exe 作为 artifact 上传(Actions 页面可下载)
4. 打 tag (例如 `git tag v1.0.0 && git push --tags`) 时,自动创建 GitHub Release 并附上 exe

### 快速上手

```bash
cd Claude3pSetupWin
git remote add origin https://github.com/<你>/<你的仓库>.git
git push -u origin main
```

然后在仓库的 Actions tab 就能看到构建进度,构建完成后下载 artifact 得到 `.exe`。

要永久发布版本: `git tag v1.0.0 && git push --tags` → 自动生成 Release。

## 交叉构建说明

PyInstaller 不支持交叉编译: 在 macOS/Linux 上运行 PyInstaller 只能产出对应平台的二进制。生成 `.exe` 有两条路:
- 在 Windows 上双击 `build.bat` (最快)
- 推到 GitHub,让 GitHub Actions 自动打包 (无需 Windows 机器)
