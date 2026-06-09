# AVG Builder V0.1a

AVG Builder V0.1a 是一个本地 HTTP 工具，用于只读扫描本地 Ren'Py 项目结构、资源列表与 Git 状态。它面向工具项目 `AVGBuilder`，不会修改被扫描的外部项目文件，也不会执行自动 commit、push、导出或热区编辑。

## 功能范围

- FastAPI 后端 + 原生 HTML/CSS/JS 前端。
- 首页：`http://127.0.0.1:8000`。
- 输入 Ren'Py 项目根路径，例如：`D:\GitHub\DemoAVG`。
- 点击扫描后调用 `POST /api/project/open`。
- 项目结构检查：
  - `game/`
  - `game/script.rpy`
  - `game/gui.rpy`
  - `game/options.rpy`
  - `.gitignore`
- 资源分类扫描：
  - `backgrounds`
  - `characters`
  - `ui`
  - `audio`
- Git 状态读取：
  - 是否 Git 仓库
  - 当前分支
  - 工作区是否 clean
  - `git status --short`
  - 最新 commit

## 项目结构

```text
AVGBuilder/
├─ backend/
│  ├─ app.py
│  ├─ project_scanner.py
│  ├─ asset_scanner.py
│  ├─ git_status.py
│  └─ models.py
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  └─ style.css
├─ data/
├─ scripts/
│  ├─ start_dev.ps1
│  ├─ check_all.ps1
│  ├─ status_all.ps1
│  └─ push_safe.ps1
├─ README.md
├─ requirements.txt
└─ .gitignore
```

## 安装与启动

建议使用 Python 3.10+。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

启动后访问：

```text
http://127.0.0.1:8000
```

## 本地开发脚本（PowerShell）

以下脚本都只在 `AVGBuilder` 仓库内工作，不会修改 `DemoAVG`。如果 PowerShell 执行策略阻止脚本运行，可先在当前终端使用：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 1. 启动本地服务

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1
```

默认行为：

- 在 AVGBuilder 内创建/复用 `.venv`。
- 安装 `requirements.txt`。
- 启动 `uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload`。
- 打开 `http://127.0.0.1:8000` 访问首页。

可选参数：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1 -Port 8001
powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1 -SkipInstall
powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1 -NoReload
```

### 2. 检查前后端

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_all.ps1
```

检查内容：

- `python -m compileall backend`
- `node --check frontend/app.js`
- `git diff --check`

如果想使用本仓库 `.venv` 中的 Python：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_all.ps1 -UseVenv
```

### 3. 查看 AVGBuilder 与 DemoAVG 状态

```powershell
powershell -ExecutionPolicy Bypass -File scripts/status_all.ps1
```

默认会检查：

- 当前 `AVGBuilder` 仓库。
- 与 `AVGBuilder` 同级目录下的 `DemoAVG` 仓库（只读 `git status` / branch / latest commit）。

如果 `DemoAVG` 不在同级目录，可指定路径：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/status_all.ps1 -DemoAVGPath "D:\GitHub\DemoAVG"
```

### 4. 安全推送当前分支

```powershell
powershell -ExecutionPolicy Bypass -File scripts/push_safe.ps1
```

默认安全规则：

- 只推送 AVGBuilder 当前分支。
- 工作区必须干净。
- 推送前运行 `scripts/check_all.ps1`。
- 拒绝直接推送 `main` / `master`，避免误推主分支。

如果确实需要推送 `main`，必须显式确认：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/push_safe.ps1 -AllowMain
```

也可以指定远端或分支：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/push_safe.ps1 -Remote origin -Branch feature/my-work
```

## API 测试

### 1. 扫描项目

```bash
curl -X POST http://127.0.0.1:8000/api/project/open \
  -H "Content-Type: application/json" \
  -d '{"path":"D:\\GitHub\\DemoAVG"}'
```

Linux/macOS 示例：

```bash
curl -X POST http://127.0.0.1:8000/api/project/open \
  -H "Content-Type: application/json" \
  -d '{"path":"/path/to/DemoAVG"}'
```

### 2. 查看资源列表

```bash
curl http://127.0.0.1:8000/api/assets/list
```

### 3. 查看 Git 状态

```bash
curl http://127.0.0.1:8000/api/git/status
```

### 4. 查看项目摘要

```bash
curl http://127.0.0.1:8000/api/project/summary
```

> `GET /api/assets/list`、`GET /api/git/status`、`GET /api/project/summary` 返回最近一次 `POST /api/project/open` 的扫描结果；如果尚未扫描，会返回 404。

## 只读说明

后端只读取目标项目路径下的目录、文件元数据与 Git 状态命令输出。它不会在目标项目中创建、修改或删除文件，也不会执行 `git add`、`git commit`、`git push` 等写入类操作。

## Codex Linux 容器验证标准

Codex 在 Linux 容器中运行时只执行与容器环境匹配的静态检查，不把 Windows-only 或本地-only 验证视为失败。

必须执行的检查：

```bash
python -m compileall backend
node --check frontend/app.js
git diff --check
```

如果任务修改 README，需要确认 README 已包含对应新增用法说明。如果任务修改或新增 `scripts/*.ps1`，Codex 只检查以下文件是否存在，并确认 README 写明调用方式：

- `scripts/start_dev.ps1`
- `scripts/check_all.ps1`
- `scripts/status_all.ps1`
- `scripts/push_safe.ps1`

Codex 不需要在 Linux 容器中执行以下 Windows 本地验证，也不要把这些验证缺失或路径不存在计为失败：

- 实际运行 `powershell -ExecutionPolicy Bypass -File scripts/*.ps1`
- 检查 `D:\GitHub\AVGBuilder` 或 `D:\GitHub\DemoAVG`
- 因 `/workspace/DemoAVG` 不存在而失败
- 实际启动 Windows 本地服务或浏览器访问 `http://127.0.0.1:8000`
- 要求 `git push origin main` 成功

Windows 本地验证由用户在本机执行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/status_all.ps1
powershell -ExecutionPolicy Bypass -File scripts/check_all.ps1
powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1
powershell -ExecutionPolicy Bypass -File scripts/push_safe.ps1
```

## Dialogue Block Editor V0.7

AVG Builder V0.7 增加 Dialogue / 对话块编辑器，用于在本地创建、编辑、校验和导出 AVG 剧情对白块。该功能继续保持 FastAPI + 原生 HTML/CSS/JS，不调用真实 AI API，不要求 API Key。

### dialogue_blocks.json

对话块编辑器会把编辑数据保存到被扫描项目的：

```text
tools_data/dialogue_blocks.json
```

文件结构示例：

```json
{
  "version": "0.7",
  "project_name": "DemoAVG",
  "blocks": [
    {
      "id": "block_001",
      "label": "dialogue_block_001",
      "title": "雨夜房间测试对白",
      "background": "bg_room_rainy",
      "music": "",
      "lines": [
        { "type": "narration", "speaker": "", "text": "雨还在下。" },
        { "type": "dialogue", "speaker": "n", "text": "这个点，谁还会来？" }
      ],
      "return_label": "",
      "enabled": true
    }
  ]
}
```

字段说明：

- `id`：AVGBuilder 工具内部 ID。
- `label`：导出的 Ren'Py label 名，必须符合 `^[A-Za-z_][A-Za-z0-9_]*$`。
- `title`：用户可读标题。
- `background`：Ren'Py `scene` 使用的背景名，不是文件路径。
- `music`：可空；填写后导出 `play music "..."`。
- `lines`：对白行数组，`type` 支持 `narration`、`dialogue`、`comment`。
- `speaker`：Ren'Py 角色变量名，例如 `n`、`l`、`narrator`，旁白可空。
- `text`：正文；空文本会产生 warning。
- `return_label`：可空；填写后导出结尾使用 `jump return_label`，否则使用 `return`。
- `enabled`：为 `false` 的 block 不会导出。

### generated_dialogue_blocks.rpy

点击“导出 RPY”会生成：

```text
game/generated_dialogue_blocks.rpy
```

导出文件顶部包含注释：

```renpy
# This file is generated by AVGBuilder. Do not edit manually.
```

导出示例：

```renpy
label dialogue_block_001:

    scene bg_room_rainy

    "雨还在下。"

    n "这个点，谁还会来？"

    return
```

如果 `return_label` 设置为 `test_generated_hotspots`，末尾会导出：

```renpy
    jump test_generated_hotspots
```

`comment` 行不会导出为对白，而是导出为 Ren'Py 注释：

```renpy
    # comment text
```

### 手动在 Ren'Py 中调用

AVGBuilder 不会直接修改 `script.rpy`、`gui.rpy` 或 `options.rpy`。如果需要在 Ren'Py 剧情中使用生成的对话块，请在你的游戏脚本中手动调用：

```renpy
jump dialogue_block_001
```

或：

```renpy
call dialogue_block_001
```

### Dialogue API

在前端先扫描目标 Ren'Py 项目后，可以使用以下 API：

```bash
curl http://127.0.0.1:8000/api/dialogue/blocks
```

```bash
curl -X POST http://127.0.0.1:8000/api/dialogue/blocks/validate \
  -H "Content-Type: application/json" \
  -d '{"document":{"version":"0.7","project_name":"DemoAVG","blocks":[]}}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/dialogue/blocks/save \
  -H "Content-Type: application/json" \
  -d '{"document":{"version":"0.7","project_name":"DemoAVG","blocks":[]}}'
```

```bash
curl -X POST http://127.0.0.1:8000/api/dialogue/export \
  -H "Content-Type: application/json" \
  -d '{"document":{"version":"0.7","project_name":"DemoAVG","blocks":[]}}'
```

### V0.7 安全边界

- 只修改 AVGBuilder 仓库代码。
- 不直接修改 DemoAVG 的 `script.rpy`、`gui.rpy`、`options.rpy`。
- 不移动、不删除、不重命名 DemoAVG 资源。
- 不自动修改已有 `generated_hotspots.rpy`。
- 不调用真实 AI API，也不要求 API Key。
- 对被管理项目的写入仅限用户主动点击保存/导出时写入：
  - `tools_data/dialogue_blocks.json`
  - `game/generated_dialogue_blocks.rpy`
