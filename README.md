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
│  ├─ __init__.py
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
├─ README.md
├─ requirements.txt
└─ .gitignore
```

## 安装与启动

建议使用 Python 3.10+。

```bash
python -m venv .venv
source .venv/bin/activate # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

启动后访问：

```text
http://127.0.0.1:8000
```

## API 测试

### 1. 扫描项目

```bash
curl -X POST http://127.0.0.1:8000/api/project/open \
  -H "Content-Type: application/json" \
  -d '{"path":"D:\\GitHub\\DemoAVG"}'
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
