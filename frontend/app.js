const state = {
  projectPath: '',
  projectName: '',
  assets: null,
  hotspotsDoc: { version: '0.1b', project_name: '', scenes: [] },
  currentBackground: null,
  currentScene: null,
  selectedHotspotId: null,
  imageNaturalWidth: 0,
  imageNaturalHeight: 0,
  imageDisplayWidth: 0,
  imageDisplayHeight: 0,
  mode: 'idle',
  dragState: null,
  dirty: false,
};

const el = {
  form: document.querySelector('#scan-form'),
  pathInput: document.querySelector('#project-path'),
  scanButton: document.querySelector('#scan-button'),
  saveButton: document.querySelector('#save-hotspots-button'),
  gitChip: document.querySelector('#git-chip'),
  projectStatus: document.querySelector('#project-status'),
  assetTabs: document.querySelector('#asset-tabs'),
  assetCount: document.querySelector('#asset-count'),
  assetList: document.querySelector('#asset-list'),
  selectedBackground: document.querySelector('#selected-background'),
  mousePosition: document.querySelector('#mouse-position'),
  canvasScale: document.querySelector('#canvas-scale'),
  canvasEmpty: document.querySelector('#canvas-empty'),
  canvasWrap: document.querySelector('#canvas-wrap'),
  bgPreview: document.querySelector('#background-preview'),
  hotspotLayer: document.querySelector('#hotspot-layer'),
  hotspotList: document.querySelector('#hotspot-list'),
  hotspotForm: document.querySelector('#hotspot-form'),
  hotspotIdHidden: document.querySelector('#hotspot-id-hidden'),
  hotspotId: document.querySelector('#hotspot-id'),
  hotspotName: document.querySelector('#hotspot-name'),
  hotspotTarget: document.querySelector('#hotspot-target'),
  hotspotTooltip: document.querySelector('#hotspot-tooltip'),
  hotspotX: document.querySelector('#hotspot-x'),
  hotspotY: document.querySelector('#hotspot-y'),
  hotspotW: document.querySelector('#hotspot-w'),
  hotspotH: document.querySelector('#hotspot-h'),
  hotspotEnabled: document.querySelector('#hotspot-enabled'),
  applyButton: document.querySelector('#apply-hotspot-button'),
  deleteButton: document.querySelector('#delete-hotspot-button'),
  duplicateButton: document.querySelector('#duplicate-hotspot-button'),
  log: document.querySelector('#scan-log'),
};

const categoryLabels = { backgrounds: '背景', characters: '角色', ui: 'UI', audio: '音频' };
let activeCategory = 'backgrounds';

el.form.addEventListener('submit', async (event) => {
  event.preventDefault();
  await scanProject(el.pathInput.value.trim());
});
el.saveButton.addEventListener('click', saveHotspots);
el.hotspotForm.addEventListener('submit', (event) => {
  event.preventDefault();
  applyFormToSelected();
});
el.deleteButton.addEventListener('click', deleteSelectedHotspot);
el.duplicateButton.addEventListener('click', duplicateSelectedHotspot);

['input', 'change'].forEach((eventName) => {
  [el.hotspotId, el.hotspotName, el.hotspotTarget, el.hotspotTooltip, el.hotspotX, el.hotspotY, el.hotspotW, el.hotspotH, el.hotspotEnabled]
    .forEach((input) => input.addEventListener(eventName, syncSelectedFromForm));
});

el.bgPreview.addEventListener('load', () => {
  state.imageNaturalWidth = el.bgPreview.naturalWidth;
  state.imageNaturalHeight = el.bgPreview.naturalHeight;
  updateCanvasMetrics();
  renderHotspotLayer();
});
el.canvasWrap.addEventListener('pointerdown', onCanvasPointerDown);
el.canvasWrap.addEventListener('pointermove', onCanvasPointerMove);
el.canvasWrap.addEventListener('pointerup', onCanvasPointerUp);
el.canvasWrap.addEventListener('pointercancel', onCanvasPointerUp);
el.canvasWrap.addEventListener('pointerleave', updateMousePositionFromEvent);
window.addEventListener('resize', () => {
  updateCanvasMetrics();
  renderHotspotLayer();
});
document.addEventListener('keydown', onKeyDown);

async function scanProject(projectPath) {
  if (!projectPath) return appendLog('请输入项目路径。');
  setLoading(true);
  el.log.textContent = '正在扫描...';
  try {
    const response = await fetch('/api/project/open', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: projectPath }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || '扫描失败');
    renderSummary(payload);
    await loadHotspots();
  } catch (error) {
    appendLog(`扫描失败：${error.message}`);
  } finally {
    setLoading(false);
  }
}

function renderSummary(summary) {
  state.projectPath = summary.project_path || '';
  state.projectName = state.projectPath.split(/[\\/]/).filter(Boolean).pop() || 'RenPyProject';
  state.assets = summary.assets?.categories || {};
  state.currentBackground = null;
  state.currentScene = null;
  state.selectedHotspotId = null;
  state.hotspotsDoc = { version: '0.1b', project_name: state.projectName, scenes: [] };
  state.dirty = false;
  renderProjectStatus(summary);
  renderGitChip(summary.git || {});
  renderAssetTabs();
  renderAssetList(activeCategory);
  clearCanvas();
  renderHotspotList();
  updateInspectorState();
  el.log.textContent = (summary.logs || []).join('\n') || '扫描完成。';
}

async function loadHotspots() {
  const response = await fetch('/api/hotspots');
  if (!response.ok) throw new Error('读取热点数据失败');
  state.hotspotsDoc = await response.json();
  if (!state.hotspotsDoc.project_name) state.hotspotsDoc.project_name = state.projectName;
  if (!Array.isArray(state.hotspotsDoc.scenes)) state.hotspotsDoc.scenes = [];
}

function renderProjectStatus(summary) {
  const checks = summary.checks || {};
  el.projectStatus.classList.remove('empty');
  el.projectStatus.innerHTML = [
    statusRow('script.rpy', badge(checks.script_rpy, '存在', '缺失')),
    statusRow('gui.rpy', badge(checks.gui_rpy, '存在', '缺失')),
    statusRow('options.rpy', badge(checks.options_rpy, '存在', '缺失')),
    statusRow('.gitignore', badge(checks.gitignore, '存在', '缺失')),
  ].join('');
}

function renderGitChip(git) {
  el.gitChip.textContent = git.is_repository
    ? `Git：${git.branch || '-'} · ${git.clean ? 'clean' : 'dirty'} · ${git.latest_commit || '-'}`
    : 'Git：非仓库';
  el.gitChip.classList.toggle('dirty', Boolean(git.is_repository && !git.clean));
}

function renderAssetTabs() {
  const total = Object.values(state.assets || {}).reduce((sum, items) => sum + items.length, 0);
  el.assetCount.textContent = `${total} 个资源`;
  el.assetTabs.innerHTML = Object.keys(categoryLabels).map((category) => {
    const count = state.assets?.[category]?.length || 0;
    const active = category === activeCategory ? ' active' : '';
    return `<button class="asset-tab${active}" type="button" data-category="${category}">${categoryLabels[category]} (${count})</button>`;
  }).join('');
  el.assetTabs.querySelectorAll('[data-category]').forEach((button) => {
    button.addEventListener('click', () => {
      activeCategory = button.dataset.category;
      renderAssetTabs();
      renderAssetList(activeCategory);
    });
  });
}

function renderAssetList(category) {
  const items = state.assets?.[category] || [];
  el.assetList.classList.toggle('empty', items.length === 0);
  if (items.length === 0) {
    el.assetList.textContent = `未发现${categoryLabels[category] || category}资源。`;
    return;
  }
  el.assetList.innerHTML = items.map((item) => {
    const selected = item.relative_path === state.currentBackground ? ' selected' : '';
    const action = category === 'backgrounds' ? `<button class="mini-button" data-bg="${escapeHtml(item.relative_path)}">打开</button>` : '';
    return `<div class="asset-row${selected}">
      <div><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(item.relative_path)} · ${formatBytes(item.size_bytes)}</small></div>
      ${action}
    </div>`;
  }).join('');
  el.assetList.querySelectorAll('[data-bg]').forEach((button) => button.addEventListener('click', () => selectBackground(button.dataset.bg)));
}

function selectBackground(backgroundPath) {
  state.currentBackground = backgroundPath;
  state.currentScene = ensureScene(backgroundPath);
  state.selectedHotspotId = null;
  el.selectedBackground.textContent = backgroundPath;
  el.canvasEmpty.classList.add('hidden');
  el.canvasWrap.classList.remove('hidden');
  el.bgPreview.src = `/api/assets/file?path=${encodeURIComponent(backgroundPath)}`;
  renderAssetList(activeCategory);
  fillForm(null);
  renderHotspotList();
  updateInspectorState();
}

function clearCanvas() {
  state.currentBackground = null;
  state.currentScene = null;
  el.selectedBackground.textContent = '未选择背景';
  el.canvasEmpty.classList.remove('hidden');
  el.canvasWrap.classList.add('hidden');
  el.bgPreview.removeAttribute('src');
  el.hotspotLayer.innerHTML = '';
  el.mousePosition.textContent = '鼠标：-';
  el.canvasScale.textContent = '缩放：-';
}

function ensureScene(backgroundPath) {
  let scene = state.hotspotsDoc.scenes.find((item) => item.background === backgroundPath);
  if (!scene) {
    scene = { scene_id: makeSceneId(backgroundPath), background: backgroundPath, hotspots: [] };
    state.hotspotsDoc.scenes.push(scene);
    markDirty();
  }
  return scene;
}

function updateCanvasMetrics() {
  const rect = el.bgPreview.getBoundingClientRect();
  state.imageDisplayWidth = rect.width;
  state.imageDisplayHeight = rect.height;
  if (state.imageNaturalWidth && state.imageDisplayWidth) {
    const sx = getScaleX().toFixed(3);
    const sy = getScaleY().toFixed(3);
    el.canvasScale.textContent = `缩放：x${sx} / y${sy}`;
  }
}

function renderHotspotLayer() {
  if (!state.currentScene || !state.imageDisplayWidth) return;
  updateCanvasMetrics();
  el.hotspotLayer.innerHTML = '';
  for (const hotspot of state.currentScene.hotspots) {
    if (!hotspot.enabled) continue;
    const box = document.createElement('div');
    box.className = `hotspot-box${hotspot.id === state.selectedHotspotId ? ' selected' : ''}`;
    box.dataset.hotspotId = hotspot.id;
    box.style.left = `${hotspot.x / getScaleX()}px`;
    box.style.top = `${hotspot.y / getScaleY()}px`;
    box.style.width = `${hotspot.w / getScaleX()}px`;
    box.style.height = `${hotspot.h / getScaleY()}px`;
    box.innerHTML = `<span>${escapeHtml(hotspot.name || hotspot.id)}</span><i class="resize-handle" data-resize="se"></i>`;
    el.hotspotLayer.appendChild(box);
  }
}

function renderHotspotList() {
  if (!state.currentScene) {
    el.hotspotList.classList.add('empty');
    el.hotspotList.textContent = '选择背景后可编辑热区。';
    return;
  }
  const hotspots = state.currentScene.hotspots || [];
  el.hotspotList.classList.toggle('empty', hotspots.length === 0);
  if (hotspots.length === 0) {
    el.hotspotList.textContent = '当前背景还没有热区。';
    return;
  }
  el.hotspotList.innerHTML = hotspots.map((hotspot) => {
    const selected = hotspot.id === state.selectedHotspotId ? ' selected' : '';
    return `<button class="hotspot-list-item${selected}" data-hotspot-id="${escapeHtml(hotspot.id)}" type="button">
      <strong>${escapeHtml(hotspot.id)}</strong>
      <span>${escapeHtml(hotspot.name)} · x:${hotspot.x} y:${hotspot.y} w:${hotspot.w} h:${hotspot.h}</span>
    </button>`;
  }).join('');
  el.hotspotList.querySelectorAll('[data-hotspot-id]').forEach((button) => button.addEventListener('click', () => selectHotspot(button.dataset.hotspotId)));
}

function onCanvasPointerDown(event) {
  if (!state.currentScene || event.button !== 0) return;
  updateCanvasMetrics();
  const point = displayPointFromEvent(event);
  const targetBox = event.target.closest?.('.hotspot-box');
  const resizeHandle = event.target.closest?.('.resize-handle');

  if (targetBox) {
    const hotspot = findHotspot(targetBox.dataset.hotspotId);
    if (!hotspot) return;
    selectHotspot(hotspot.id);
    event.preventDefault();
    el.canvasWrap.setPointerCapture(event.pointerId);
    state.dragState = { start: point, original: { ...hotspot }, hotspotId: hotspot.id };
    state.mode = resizeHandle ? 'resizing' : 'moving';
    return;
  }

  event.preventDefault();
  el.canvasWrap.setPointerCapture(event.pointerId);
  state.mode = 'drawing';
  state.dragState = { start: point, currentId: null };
  const hotspot = {
    id: nextHotspotId(),
    name: '新热区',
    target_label: '',
    tooltip: '',
    x: Math.round(point.realX),
    y: Math.round(point.realY),
    w: 1,
    h: 1,
    enabled: true,
  };
  state.currentScene.hotspots.push(hotspot);
  state.dragState.currentId = hotspot.id;
  selectHotspot(hotspot.id);
  markDirty();
}

function onCanvasPointerMove(event) {
  updateMousePositionFromEvent(event);
  if (state.mode === 'idle' || !state.dragState) return;
  const point = displayPointFromEvent(event);
  const hotspot = findHotspot(state.dragState.hotspotId || state.dragState.currentId);
  if (!hotspot) return;

  if (state.mode === 'drawing') {
    const start = state.dragState.start;
    hotspot.x = Math.round(Math.min(start.realX, point.realX));
    hotspot.y = Math.round(Math.min(start.realY, point.realY));
    hotspot.w = Math.max(1, Math.round(Math.abs(point.realX - start.realX)));
    hotspot.h = Math.max(1, Math.round(Math.abs(point.realY - start.realY)));
  } else if (state.mode === 'moving') {
    const original = state.dragState.original;
    hotspot.x = clamp(Math.round(original.x + (point.realX - state.dragState.start.realX)), 0, state.imageNaturalWidth - hotspot.w);
    hotspot.y = clamp(Math.round(original.y + (point.realY - state.dragState.start.realY)), 0, state.imageNaturalHeight - hotspot.h);
  } else if (state.mode === 'resizing') {
    const original = state.dragState.original;
    hotspot.w = Math.max(1, Math.round(original.w + (point.realX - state.dragState.start.realX)));
    hotspot.h = Math.max(1, Math.round(original.h + (point.realY - state.dragState.start.realY)));
  }
  fillForm(hotspot);
  renderHotspotLayer();
  renderHotspotList();
  markDirty();
}

function onCanvasPointerUp(event) {
  if (state.mode !== 'idle') {
    try { el.canvasWrap.releasePointerCapture(event.pointerId); } catch (_error) { /* already released */ }
  }
  if (state.mode === 'drawing') {
    const hotspot = findHotspot(state.dragState?.currentId);
    if (hotspot && (hotspot.w < 3 || hotspot.h < 3)) {
      removeHotspot(hotspot.id);
    }
  }
  state.mode = 'idle';
  state.dragState = null;
  renderHotspotLayer();
  renderHotspotList();
}

function displayPointFromEvent(event) {
  const rect = el.bgPreview.getBoundingClientRect();
  const displayX = clamp(event.clientX - rect.left, 0, rect.width);
  const displayY = clamp(event.clientY - rect.top, 0, rect.height);
  return {
    displayX,
    displayY,
    realX: displayX * getScaleX(),
    realY: displayY * getScaleY(),
  };
}

function updateMousePositionFromEvent(event) {
  if (!state.currentBackground || !state.imageDisplayWidth) {
    el.mousePosition.textContent = '鼠标：-';
    return;
  }
  const point = displayPointFromEvent(event);
  el.mousePosition.textContent = `鼠标：${Math.round(point.realX)}, ${Math.round(point.realY)}`;
}

function selectHotspot(id) {
  const hotspot = findHotspot(id);
  if (!hotspot) return;
  state.selectedHotspotId = id;
  fillForm(hotspot);
  updateInspectorState();
  renderHotspotLayer();
  renderHotspotList();
}

function fillForm(hotspot) {
  if (!hotspot) {
    el.hotspotIdHidden.value = '';
    el.hotspotId.value = '';
    el.hotspotName.value = '';
    el.hotspotTarget.value = '';
    el.hotspotTooltip.value = '';
    el.hotspotX.value = 0;
    el.hotspotY.value = 0;
    el.hotspotW.value = 100;
    el.hotspotH.value = 100;
    el.hotspotEnabled.checked = true;
    return;
  }
  el.hotspotIdHidden.value = hotspot.id;
  el.hotspotId.value = hotspot.id;
  el.hotspotName.value = hotspot.name;
  el.hotspotTarget.value = hotspot.target_label || '';
  el.hotspotTooltip.value = hotspot.tooltip || '';
  el.hotspotX.value = hotspot.x;
  el.hotspotY.value = hotspot.y;
  el.hotspotW.value = hotspot.w;
  el.hotspotH.value = hotspot.h;
  el.hotspotEnabled.checked = Boolean(hotspot.enabled);
}

function syncSelectedFromForm() {
  const originalId = state.selectedHotspotId;
  const hotspot = findHotspot(originalId);
  if (!hotspot) return;
  const nextId = el.hotspotId.value.trim();
  if (!nextId) return;
  hotspot.id = nextId;
  hotspot.name = el.hotspotName.value.trim() || '新热区';
  hotspot.target_label = el.hotspotTarget.value.trim();
  hotspot.tooltip = el.hotspotTooltip.value.trim();
  hotspot.x = Math.max(0, numberFromInput(el.hotspotX, hotspot.x));
  hotspot.y = Math.max(0, numberFromInput(el.hotspotY, hotspot.y));
  hotspot.w = Math.max(1, numberFromInput(el.hotspotW, hotspot.w));
  hotspot.h = Math.max(1, numberFromInput(el.hotspotH, hotspot.h));
  hotspot.enabled = el.hotspotEnabled.checked;
  state.selectedHotspotId = nextId;
  markDirty();
  renderHotspotLayer();
  renderHotspotList();
}

function applyFormToSelected() {
  if (!state.selectedHotspotId) {
    appendLog('请先选择或绘制一个热区。');
    return;
  }
  syncSelectedFromForm();
  appendLog(`表单已应用：${state.selectedHotspotId}`);
}

function deleteSelectedHotspot() {
  if (!state.selectedHotspotId) return;
  removeHotspot(state.selectedHotspotId);
  state.selectedHotspotId = null;
  fillForm(null);
  updateInspectorState();
  renderHotspotLayer();
  renderHotspotList();
  markDirty();
}

function duplicateSelectedHotspot() {
  const hotspot = findHotspot(state.selectedHotspotId);
  if (!hotspot || !state.currentScene) return;
  const copy = {
    ...hotspot,
    id: nextHotspotId(),
    name: `${hotspot.name || '新热区'} 副本`,
    x: hotspot.x + 20,
    y: hotspot.y + 20,
  };
  state.currentScene.hotspots.push(copy);
  selectHotspot(copy.id);
  markDirty();
}

function removeHotspot(id) {
  if (!state.currentScene) return;
  state.currentScene.hotspots = state.currentScene.hotspots.filter((hotspot) => hotspot.id !== id);
}

async function saveHotspots() {
  try {
    validateHotspotsDocument();
    const response = await fetch('/api/hotspots/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(state.hotspotsDoc),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || '保存失败');
    state.hotspotsDoc = payload;
    state.dirty = false;
    updateInspectorState();
    appendLog('已保存 tools_data/hotspots.json');
  } catch (error) {
    appendLog(`保存失败：${error.message}`);
  }
}

function validateHotspotsDocument() {
  for (const scene of state.hotspotsDoc.scenes || []) {
    if (!scene.background || scene.background.includes('..') || /^[a-zA-Z]:/.test(scene.background)) {
      throw new Error(`背景路径非法：${scene.background}`);
    }
    const ids = new Set();
    for (const hotspot of scene.hotspots || []) {
      if (!hotspot.id) throw new Error('热区 id 不能为空。');
      if (ids.has(hotspot.id)) throw new Error(`同一场景内 id 重复：${hotspot.id}`);
      ids.add(hotspot.id);
      if (![hotspot.x, hotspot.y, hotspot.w, hotspot.h].every(Number.isFinite)) throw new Error(`坐标非法：${hotspot.id}`);
      if (hotspot.w <= 0 || hotspot.h <= 0) throw new Error(`w/h 必须 > 0：${hotspot.id}`);
    }
  }
}

function updateInspectorState() {
  const hasScene = Boolean(state.currentScene);
  const hasSelection = Boolean(state.selectedHotspotId);
  el.saveButton.disabled = !hasScene;
  el.applyButton.disabled = !hasSelection;
  el.deleteButton.disabled = !hasSelection;
  el.duplicateButton.disabled = !hasSelection;
  el.saveButton.textContent = state.dirty ? '保存 hotspots.json *' : '保存 hotspots.json';
}

function onKeyDown(event) {
  if (event.target.matches('input')) return;
  if (event.key === 'Delete') {
    event.preventDefault();
    deleteSelectedHotspot();
  } else if (event.key === 'Escape') {
    state.selectedHotspotId = null;
    fillForm(null);
    updateInspectorState();
    renderHotspotLayer();
    renderHotspotList();
  } else if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'd') {
    event.preventDefault();
    duplicateSelectedHotspot();
  }
}

function findHotspot(id) {
  if (!id || !state.currentScene) return null;
  return state.currentScene.hotspots.find((hotspot) => hotspot.id === id) || null;
}

function nextHotspotId() {
  const existing = new Set((state.currentScene?.hotspots || []).map((hotspot) => hotspot.id));
  let index = existing.size + 1;
  let id = `hotspot_${String(index).padStart(3, '0')}`;
  while (existing.has(id)) {
    index += 1;
    id = `hotspot_${String(index).padStart(3, '0')}`;
  }
  return id;
}

function markDirty() {
  state.dirty = true;
  updateInspectorState();
}

function makeSceneId(backgroundPath) {
  return `scene_${backgroundPath.split('/').pop().replace(/\.[^.]+$/, '').replace(/[^a-zA-Z0-9_]+/g, '_')}`;
}

function getScaleX() {
  return state.imageDisplayWidth ? state.imageNaturalWidth / state.imageDisplayWidth : 1;
}

function getScaleY() {
  return state.imageDisplayHeight ? state.imageNaturalHeight / state.imageDisplayHeight : 1;
}

function numberFromInput(input, fallback) {
  const value = Number(input.value);
  return Number.isFinite(value) ? Math.round(value) : fallback;
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function statusRow(label, value) {
  return `<div class="status-row"><span>${label}</span><strong>${value}</strong></div>`;
}

function badge(value, okText, badText) {
  const stateName = value ? 'ok' : 'bad';
  return `<span class="badge ${stateName}">${value ? okText : badText}</span>`;
}

function appendLog(line) {
  el.log.textContent = `${el.log.textContent}\n${line}`.trim();
}

function setLoading(isLoading) {
  el.scanButton.disabled = isLoading;
  el.scanButton.textContent = isLoading ? '扫描中...' : '扫描';
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 B';
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
