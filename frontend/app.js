const form = document.querySelector('#scan-form');
const pathInput = document.querySelector('#project-path');
const scanButton = document.querySelector('#scan-button');
const projectStatus = document.querySelector('#project-status');
const gitStatus = document.querySelector('#git-status');
const assetTabs = document.querySelector('#asset-tabs');
const assetList = document.querySelector('#asset-list');
const assetCount = document.querySelector('#asset-count');
const scanLog = document.querySelector('#scan-log');
const selectedBackground = document.querySelector('#selected-background');
const previewWrap = document.querySelector('#preview-wrap');
const hotspotList = document.querySelector('#hotspot-list');
const hotspotForm = document.querySelector('#hotspot-form');
const hotspotIndexInput = document.querySelector('#hotspot-index');
const hotspotIdInput = document.querySelector('#hotspot-id');
const hotspotNameInput = document.querySelector('#hotspot-name');
const hotspotTargetInput = document.querySelector('#hotspot-target');
const hotspotTooltipInput = document.querySelector('#hotspot-tooltip');
const hotspotXInput = document.querySelector('#hotspot-x');
const hotspotYInput = document.querySelector('#hotspot-y');
const hotspotWInput = document.querySelector('#hotspot-w');
const hotspotHInput = document.querySelector('#hotspot-h');
const hotspotEnabledInput = document.querySelector('#hotspot-enabled');
const newHotspotButton = document.querySelector('#new-hotspot-button');
const applyHotspotButton = document.querySelector('#apply-hotspot-button');
const saveHotspotsButton = document.querySelector('#save-hotspots-button');

let currentProjectPath = '';
let currentProjectName = '';
let currentAssets = {};
let activeCategory = 'backgrounds';
let hotspotDocument = { version: '0.1b', project_name: '', scenes: [] };
let activeBackground = '';
let activeScene = null;

const categoryLabels = {
  backgrounds: '背景',
  characters: '角色',
  ui: 'UI',
  audio: '音频',
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  await scanProject(pathInput.value.trim());
});

hotspotForm.addEventListener('submit', (event) => {
  event.preventDefault();
  applyHotspotForm();
});

newHotspotButton.addEventListener('click', () => {
  hotspotIndexInput.value = '-1';
  hotspotIdInput.value = 'test_hotspot';
  hotspotNameInput.value = '测试热区';
  hotspotTargetInput.value = 'test_label';
  hotspotTooltipInput.value = '测试提示';
  hotspotXInput.value = '10';
  hotspotYInput.value = '20';
  hotspotWInput.value = '100';
  hotspotHInput.value = '80';
  hotspotEnabledInput.checked = true;
  hotspotIdInput.focus();
});

saveHotspotsButton.addEventListener('click', async () => {
  await saveHotspots();
});

async function scanProject(projectPath) {
  if (!projectPath) {
    appendLog('请输入项目路径。');
    return;
  }

  setLoading(true);
  scanLog.textContent = '正在扫描...';

  try {
    const response = await fetch('/api/project/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: projectPath }),
    });
    const payload = await response.json();

    if (!response.ok) {
      throw new Error(payload.detail || '扫描失败');
    }

    renderSummary(payload);
    await loadHotspots();
  } catch (error) {
    scanLog.textContent = `扫描失败：${error.message}`;
  } finally {
    setLoading(false);
  }
}

async function loadHotspots() {
  try {
    const response = await fetch('/api/hotspots');
    if (!response.ok) {
      throw new Error('读取热点数据失败');
    }
    hotspotDocument = await response.json();
    if (!hotspotDocument.project_name) {
      hotspotDocument.project_name = currentProjectName;
    }
    if (!Array.isArray(hotspotDocument.scenes)) {
      hotspotDocument.scenes = [];
    }
    if (activeBackground) {
      selectBackground(activeBackground);
    }
  } catch (error) {
    appendLog(error.message);
  }
}

function renderSummary(summary) {
  currentProjectPath = summary.project_path || '';
  currentProjectName = currentProjectPath.split(/[\\/]/).filter(Boolean).pop() || 'RenPyProject';
  renderProjectStatus(summary);
  renderGitStatus(summary.git || {});
  currentAssets = summary.assets?.categories || {};
  activeCategory = 'backgrounds';
  activeBackground = '';
  activeScene = null;
  hotspotDocument = { version: '0.1b', project_name: currentProjectName, scenes: [] };
  renderAssetTabs();
  renderAssetList(activeCategory);
  clearPreview();
  renderHotspotList();
  scanLog.textContent = (summary.logs || []).join('\n') || '扫描完成。';
}

function renderProjectStatus(summary) {
  const checks = summary.checks || {};
  projectStatus.classList.remove('empty');
  projectStatus.innerHTML = [
    statusRow('项目路径', escapeHtml(summary.project_path || '-')),
    statusRow('路径存在', badge(summary.exists, '存在', '不存在')),
    statusRow('game/', badge(checks.game_dir, '存在', '缺失')),
    statusRow('game/script.rpy', badge(checks.script_rpy, '存在', '缺失')),
    statusRow('game/gui.rpy', badge(checks.gui_rpy, '存在', '缺失')),
    statusRow('game/options.rpy', badge(checks.options_rpy, '存在', '缺失')),
    statusRow('.gitignore', badge(checks.gitignore, '存在', '缺失')),
  ].join('');
}

function renderGitStatus(git) {
  gitStatus.classList.remove('empty');
  const shortStatus = git.short_status?.length
    ? `<pre class="mini-log">${escapeHtml(git.short_status.join('\n'))}</pre>`
    : '<span class="empty">无短状态输出</span>';

  gitStatus.innerHTML = [
    statusRow('Git 仓库', badge(git.is_repository, '是', '否')),
    statusRow('当前分支', escapeHtml(git.branch || '-')),
    statusRow('工作区', git.is_repository ? badge(git.clean, 'Clean', '有改动') : '-'),
    statusRow('最新 commit', escapeHtml(git.latest_commit || '-')),
    statusRow('status --short', shortStatus),
    git.error ? statusRow('错误', `<span class="badge bad">${escapeHtml(git.error)}</span>`) : '',
  ].join('');
}

function renderAssetTabs() {
  const total = Object.values(currentAssets).reduce((sum, items) => sum + items.length, 0);
  assetCount.textContent = `${total} 个资源`;
  assetTabs.innerHTML = Object.keys(categoryLabels)
    .map((category) => {
      const count = currentAssets[category]?.length || 0;
      const active = category === activeCategory ? ' active' : '';
      return `<button class="asset-tab${active}" type="button" data-category="${category}">${categoryLabels[category]} (${count})</button>`;
    })
    .join('');

  assetTabs.querySelectorAll('.asset-tab').forEach((tab) => {
    tab.addEventListener('click', () => {
      activeCategory = tab.dataset.category;
      renderAssetTabs();
      renderAssetList(activeCategory);
    });
  });
}

function renderAssetList(category) {
  const items = currentAssets[category] || [];
  assetList.classList.toggle('empty', items.length === 0);

  if (items.length === 0) {
    assetList.textContent = `未发现${categoryLabels[category] || category}资源。`;
    return;
  }

  const rows = items
    .map((item) => {
      const isBackground = category === 'backgrounds';
      const action = isBackground
        ? `<button class="mini-button" type="button" data-bg="${escapeHtml(item.relative_path)}">预览/编辑</button>`
        : '';
      return `<tr>
        <td>${escapeHtml(item.name)}</td>
        <td>${escapeHtml(item.relative_path)}</td>
        <td>${escapeHtml(item.extension)}</td>
        <td>${formatBytes(item.size_bytes)}</td>
        <td>${action}</td>
      </tr>`;
    })
    .join('');

  assetList.innerHTML = `<table class="asset-table">
    <thead>
      <tr><th>名称</th><th>相对路径</th><th>类型</th><th>大小</th><th>操作</th></tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;

  assetList.querySelectorAll('[data-bg]').forEach((button) => {
    button.addEventListener('click', () => selectBackground(button.dataset.bg));
  });
}

function selectBackground(backgroundPath) {
  activeBackground = backgroundPath;
  activeScene = ensureScene(backgroundPath);
  selectedBackground.textContent = backgroundPath;
  previewWrap.classList.remove('empty');
  previewWrap.innerHTML = `<div class="image-frame"><img alt="背景预览" src="/api/assets/file?path=${encodeURIComponent(backgroundPath)}" /></div>`;
  newHotspotButton.disabled = false;
  applyHotspotButton.disabled = false;
  saveHotspotsButton.disabled = false;
  renderHotspotList();
}

function ensureScene(backgroundPath) {
  if (!hotspotDocument.project_name) {
    hotspotDocument.project_name = currentProjectName;
  }
  if (!Array.isArray(hotspotDocument.scenes)) {
    hotspotDocument.scenes = [];
  }
  let scene = hotspotDocument.scenes.find((item) => item.background === backgroundPath);
  if (!scene) {
    scene = {
      scene_id: makeSceneId(backgroundPath),
      background: backgroundPath,
      hotspots: [],
    };
    hotspotDocument.scenes.push(scene);
  }
  return scene;
}

function renderHotspotList() {
  if (!activeScene) {
    hotspotList.classList.add('empty');
    hotspotList.textContent = '选择背景后可新增热区。';
    return;
  }

  const hotspots = activeScene.hotspots || [];
  hotspotList.classList.toggle('empty', hotspots.length === 0);
  if (hotspots.length === 0) {
    hotspotList.textContent = '当前背景还没有热区。';
    return;
  }

  hotspotList.innerHTML = hotspots
    .map(
      (hotspot, index) => `<div class="hotspot-item">
        <div>
          <strong>${escapeHtml(hotspot.id)}</strong>
          <span>${escapeHtml(hotspot.name)}</span>
          <small>${escapeHtml(hotspot.target_label)} · x:${hotspot.x} y:${hotspot.y} w:${hotspot.w} h:${hotspot.h} · ${hotspot.enabled ? 'enabled' : 'disabled'}</small>
        </div>
        <button class="mini-button" type="button" data-hotspot-index="${index}">编辑</button>
      </div>`,
    )
    .join('');

  hotspotList.querySelectorAll('[data-hotspot-index]').forEach((button) => {
    button.addEventListener('click', () => editHotspot(Number(button.dataset.hotspotIndex)));
  });
}

function editHotspot(index) {
  const hotspot = activeScene?.hotspots?.[index];
  if (!hotspot) {
    return;
  }
  hotspotIndexInput.value = String(index);
  hotspotIdInput.value = hotspot.id;
  hotspotNameInput.value = hotspot.name;
  hotspotTargetInput.value = hotspot.target_label;
  hotspotTooltipInput.value = hotspot.tooltip || '';
  hotspotXInput.value = hotspot.x;
  hotspotYInput.value = hotspot.y;
  hotspotWInput.value = hotspot.w;
  hotspotHInput.value = hotspot.h;
  hotspotEnabledInput.checked = Boolean(hotspot.enabled);
}

function applyHotspotForm() {
  if (!activeScene) {
    appendLog('请先选择背景。');
    return;
  }

  const hotspot = {
    id: hotspotIdInput.value.trim(),
    name: hotspotNameInput.value.trim(),
    target_label: hotspotTargetInput.value.trim(),
    tooltip: hotspotTooltipInput.value.trim(),
    x: Number(hotspotXInput.value),
    y: Number(hotspotYInput.value),
    w: Number(hotspotWInput.value),
    h: Number(hotspotHInput.value),
    enabled: hotspotEnabledInput.checked,
  };

  if (!hotspot.id || !hotspot.name || !hotspot.target_label) {
    appendLog('热区 id/name/target_label 不能为空。');
    return;
  }
  if ([hotspot.x, hotspot.y, hotspot.w, hotspot.h].some((value) => !Number.isFinite(value)) || hotspot.w <= 0 || hotspot.h <= 0) {
    appendLog('热区坐标和尺寸必须是有效数字，且 w/h > 0。');
    return;
  }

  const index = Number(hotspotIndexInput.value);
  if (Number.isInteger(index) && index >= 0 && activeScene.hotspots[index]) {
    activeScene.hotspots[index] = hotspot;
  } else {
    activeScene.hotspots.push(hotspot);
  }
  hotspotIndexInput.value = '-1';
  renderHotspotList();
  appendLog(`热区已应用：${hotspot.id}`);
}

async function saveHotspots() {
  try {
    const response = await fetch('/api/hotspots/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(hotspotDocument),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || '保存失败');
    }
    hotspotDocument = payload;
    appendLog('已保存 tools_data/hotspots.json');
  } catch (error) {
    appendLog(`保存失败：${error.message}`);
  }
}

function clearPreview() {
  selectedBackground.textContent = '未选择背景';
  previewWrap.classList.add('empty');
  previewWrap.textContent = '从资源分类里点击一个背景资源。';
  newHotspotButton.disabled = true;
  applyHotspotButton.disabled = true;
  saveHotspotsButton.disabled = true;
}

function makeSceneId(backgroundPath) {
  return `scene_${backgroundPath.split('/').pop().replace(/\.[^.]+$/, '').replace(/[^a-zA-Z0-9_]+/g, '_')}`;
}

function statusRow(label, value) {
  return `<div class="status-row"><span>${label}</span><strong>${value}</strong></div>`;
}

function badge(value, okText, badText) {
  const state = value ? 'ok' : 'bad';
  return `<span class="badge ${state}">${value ? okText : badText}</span>`;
}

function appendLog(line) {
  scanLog.textContent = `${scanLog.textContent}\n${line}`.trim();
}

function setLoading(isLoading) {
  scanButton.disabled = isLoading;
  scanButton.textContent = isLoading ? '扫描中...' : '扫描';
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) {
    return '0 B';
  }
  const units = ['B', 'KB', 'MB', 'GB'];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
