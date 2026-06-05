# AVG Builder V0.2a

AVG Builder 是一个本地 HTTP 工具，用于只读扫描本地 Ren'Py 项目结构、资源列表与 Git 状态，并支持背景预览、可视化矩形热区编辑、基础编辑工作流优化与 Ren'Py 热区导出。V0.2b 可以把 `tools_data/hotspots.json` 导出为 `game/generated_hotspots.rpy`，但不会修改 `script.rpy`、`gui.rpy`、`options.rpy`，也不会自动提交被管理项目。

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
- V0.1c/V0.2a 热区功能：
  - 点击背景资源后预览背景图
  - 在背景画布上拖拽绘制矩形热区
  - 点击热区选中，拖动内部移动，拖动右下角控制点缩放
  - 右侧表单与画布坐标双向同步
  - 坐标保存为原始背景图坐标，页面缩放只影响显示
  - Ctrl+Z 撤销，Ctrl+Y / Ctrl+Shift+Z 重做
  - 缩放按钮：25/50/75/100/125/150/200
  - Ctrl+鼠标滚轮、Ctrl+Plus、Ctrl+Minus、Ctrl+0 缩放
  - Ctrl+D 复制热区并自动偏移 20,20，ID 自动去重
  - 热区上移/下移调整层级
  - Delete 删除，Esc 取消选中
  - 保存状态显示 Saved / Unsaved / Saving / Save failed
  - 保存 `tools_data/hotspots.json`
- V0.2b 导出功能：
  - 点击“导出 Ren'Py 热区”调用 `POST /api/export/hotspots`
  - 读取 `tools_data/hotspots.json`
  - 写入 `game/generated_hotspots.rpy`
  - 每个 scene 生成 `screen hotspots_<scene_id>()`
  - 每个 enabled=true 的 hotspot 生成 `imagebutton`
  - `target_label` 非空时使用 `Jump("target_label")`，为空时使用 `NullAction()`
  - tooltip 以注释形式输出
  - 不自动 include，不修改任何现有 `.rpy` 文件
- V0.4 热区生产规范检查：
  - `GET /api/labels` 扫描 `game/**/*.rpy` 中的 Ren'Py label
  - `GET /api/hotspots/check` 检查 `target_label` 是否 ok/missing/empty/disabled/invalid
  - `GET /api/hotspots/label-templates` 为问题热区生成测试 label 模板
  - 导出前先调用检查接口并在页面显示 warning
  - 只读检查，不保存、不导出、不修改 DemoAVG
- V0.5 / V0.5.2 资源管理器：
  - `GET /api/resources/inspect` 返回资源总览、命名 warning、缺失引用、未使用资源
  - `GET /api/resources/summary` 返回统计摘要
  - `GET /api/resources/missing` 返回缺失引用
  - `GET /api/resources/unused` 返回未使用资源
  - 扫描 `game/images/`、`game/gui/`、`game/audio/`、`game/sounds/`
  - 检查空格/中文/特殊字符、背景 bg_ 前缀、UI 命名、音频 bgm_/sfx_/amb_ 前缀
  - Resource Manager 页面提供资源统计卡、类型筛选、资源列表、命名 warning、缺失引用、未使用资源、资源详情与图片预览
  - 图片预览统一走 `/api/assets/file`
  - 只读扫描，不移动、不删除、不重命名、不自动修复 DemoAVG 资源
- V0.6 Label / 剧情节点管理器：
  - `GET /api/labels/graph` 返回 label、jump/call 边、死链、可能未使用 label
  - `GET /api/labels/detail?name=xxx` 返回单个 label 的入边、出边、关联热区
  - `GET /api/labels/health` 返回 label 健康摘要
  - Label / Nodes 页面提供分类筛选、搜索、关系列表、死链列表、未使用列表和详情面板
  - V0.6.1 增加 SVG Label 图谱：节点、jump/call 连线、missing/dynamic/unused 状态、点击节点查看详情、搜索/分类同步过滤、缩放/适配、拖动画布平移
  - V0.6.2 增加状态筛选、关系类型筛选、分组背景、Show Neighbors / Show All、相关边高亮、非相关节点淡化、Fix Suggestions 诊断建议
  - 只读扫描 `.rpy` 与 `tools_data/hotspots.json`，不修改 DemoAVG

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
