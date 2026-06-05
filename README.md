# AVG Builder V0.1b

AVG Builder 是一个本地 HTTP 工具，用于只读扫描本地 Ren'Py 项目结构、资源列表与 Git 状态，并在 V0.1b 中支持背景预览与手填热区 JSON 编辑。

安全边界：V0.1b 保存热区时，只允许写入被管理项目的 `tools_data/hotspots.json`。它不会修改 `game/script.rpy`、`game/gui.rpy`、`game/options.rpy`，也不会修改 `game/images`、`game/gui`、`game/audio`，不会自动提交或推送被管理游戏项目。

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
- V0.1b 热区功能：
  - 点击背景资源后预览背景图
  - 手填热区 `id/name/target_label/tooltip/x/y/w/h/enabled`
  - 按背景组织场景热区
  - 保存 `tools_data/hotspots.json`

## 项目结构

```text
AVGBuilder/
├─ backend/
│  ├─ __init__.py
│  ├─ app.py
│  ├─ project_scanner.py
│  ├─ asset_scanner.py
│  ├─ hotspot_manager.py
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

### 2. 预览资源文件

先扫描项目，再请求项目相对路径：

```bash
curl "http://127.0.0.1:8000/api/assets/file?path=game/images/bg/bg_room_rainy.png"
```

### 3. 查看/保存热区 JSON

```bash
curl http://127.0.0.1:8000/api/hotspots
```

```bash
curl -X POST http://127.0.0.1:8000/api/hotspots/save \
  -H "Content-Type: application/json" \
  -d '{"version":"0.1b","project_name":"DemoAVG","scenes":[]}'
```

保存目标固定为：

```text
<被扫描项目>/tools_data/hotspots.json
```

### 4. 查看资源列表

```bash
curl http://127.0.0.1:8000/api/assets/list
```

### 5. 查看 Git 状态

```bash
curl http://127.0.0.1:8000/api/git/status
```

### 6. 查看项目摘要

```bash
curl http://127.0.0.1:8000/api/project/summary
```

> `GET /api/assets/list`、`GET /api/git/status`、`GET /api/project/summary`、`GET /api/hotspots` 返回最近一次 `POST /api/project/open` 的扫描上下文；如果尚未扫描，会返回 404。

## hotspots.json 数据结构

```json
{
  "version": "0.1b",
  "project_name": "DemoAVG",
  "scenes": [
    {
      "scene_id": "scene_bg_room_rainy",
      "background": "game/images/bg/bg_room_rainy.png",
      "hotspots": [
        {
          "id": "security_room",
          "name": "监控室",
          "target_label": "test_security_room",
          "tooltip": "去监控室",
          "x": 320,
          "y": 180,
          "w": 240,
          "h": 160,
          "enabled": true
        }
      ]
    }
  ]
}
```

## 只读/受限写入说明

项目扫描、资源预览和 Git 状态读取均为只读。V0.1b 唯一写入动作是 `POST /api/hotspots/save`，且后端固定只写入当前扫描项目的 `tools_data/hotspots.json`。
