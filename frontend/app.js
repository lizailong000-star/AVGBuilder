const form = document.querySelector('#scan-form');
const pathInput = document.querySelector('#project-path');
const scanButton = document.querySelector('#scan-button');
const projectStatus = document.querySelector('#project-status');
const gitStatus = document.querySelector('#git-status');
const assetTabs = document.querySelector('#asset-tabs');
const assetList = document.querySelector('#asset-list');
const assetCount = document.querySelector('#asset-count');
const scanLog = document.querySelector('#scan-log');

const dialogueBlockList = document.querySelector('#dialogue-block-list');
const dialogueBlockNew = document.querySelector('#dialogue-block-new');
const dialogueBlockDuplicate = document.querySelector('#dialogue-block-duplicate');
const dialogueBlockDelete = document.querySelector('#dialogue-block-delete');
const dialogueBlockSave = document.querySelector('#dialogue-block-save');
const dialogueBlockValidate = document.querySelector('#dialogue-block-validate');
const dialogueBlockExport = document.querySelector('#dialogue-block-export');
const dialogueBlockId = document.querySelector('#dialogue-block-id');
const dialogueBlockLabel = document.querySelector('#dialogue-block-label');
const dialogueBlockTitle = document.querySelector('#dialogue-block-title');
const dialogueBlockBackground = document.querySelector('#dialogue-block-background');
const dialogueBlockMusic = document.querySelector('#dialogue-block-music');
const dialogueBlockReturnLabel = document.querySelector('#dialogue-block-return-label');
const dialogueBlockEnabled = document.querySelector('#dialogue-block-enabled');
const dialogueLineList = document.querySelector('#dialogue-line-list');
const dialogueLineAddNarration = document.querySelector('#dialogue-line-add-narration');
const dialogueLineAddDialogue = document.querySelector('#dialogue-line-add-dialogue');
const dialogueLineAddComment = document.querySelector('#dialogue-line-add-comment');
const dialogueRenpyPreview = document.querySelector('#dialogue-renpy-preview');
const dialogueValidationResult = document.querySelector('#dialogue-validation-result');
const dialogueExportResult = document.querySelector('#dialogue-export-result');

let currentAssets = {};
let activeCategory = 'backgrounds';
let dialogueDocument = { version: '0.7', project_name: 'DemoAVG', blocks: [] };
let selectedBlockIndex = -1;

const categoryLabels = {
  backgrounds: '背景',
  characters: '角色',
  ui: 'UI',
  audio: '音频',
};

const lineTypeLabels = {
  narration: 'narration',
  dialogue: 'dialogue',
  comment: 'comment',
};

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  await scanProject(pathInput.value.trim());
});

dialogueBlockNew.addEventListener('click', () => createDialogueBlock());
dialogueBlockDuplicate.addEventListener('click', () => duplicateDialogueBlock());
dialogueBlockDelete.addEventListener('click', () => deleteDialogueBlock());
dialogueBlockSave.addEventListener('click', () => saveDialogueBlocks());
dialogueBlockValidate.addEventListener('click', () => validateDialogueBlocks(true));
dialogueBlockExport.addEventListener('click', () => exportDialogueBlocks());
dialogueLineAddNarration.addEventListener('click', () => addDialogueLine('narration'));
dialogueLineAddDialogue.addEventListener('click', () => addDialogueLine('dialogue'));
dialogueLineAddComment.addEventListener('click', () => addDialogueLine('comment'));
[
  dialogueBlockId,
  dialogueBlockLabel,
  dialogueBlockTitle,
  dialogueBlockBackground,
  dialogueBlockMusic,
  dialogueBlockReturnLabel,
].forEach((input) => input.addEventListener('input', syncSelectedBlockFromForm));
dialogueBlockEnabled.addEventListener('change', syncSelectedBlockFromForm);

loadDialogueBlocks();

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
      throw new Error(formatApiError(payload.detail) || '扫描失败');
    }

    renderSummary(payload);
    await loadDialogueBlocks();
  } catch (error) {
    scanLog.textContent = `扫描失败：${error.message}`;
  } finally {
    setLoading(false);
  }
}

function renderSummary(summary) {
  renderProjectStatus(summary);
  renderGitStatus(summary.git);
  currentAssets = summary.assets?.categories || {};
  activeCategory = Object.keys(currentAssets)[0] || 'backgrounds';
  renderAssetTabs();
  renderAssetList(activeCategory);
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
    .map(
      (item) => `<tr>
        <td>${escapeHtml(item.name)}</td>
        <td>${escapeHtml(item.relative_path)}</td>
        <td>${escapeHtml(item.extension)}</td>
        <td>${formatBytes(item.size_bytes)}</td>
      </tr>`,
    )
    .join('');

  assetList.innerHTML = `<table class="asset-table">
    <thead>
      <tr><th>名称</th><th>相对路径</th><th>类型</th><th>大小</th></tr>
    </thead>
    <tbody>${rows}</tbody>
  </table>`;
}

async function loadDialogueBlocks() {
  try {
    const payload = await apiFetch('/api/dialogue/blocks');
    dialogueDocument = normalizeDialogueDocument(payload.document);
    selectedBlockIndex = dialogueDocument.blocks.length > 0 ? 0 : -1;
    renderDialogueEditor();
  } catch (error) {
    dialogueValidationResult.textContent = `加载失败：${error.message}`;
    dialogueValidationResult.className = 'dialogue-result bad';
  }
}

function normalizeDialogueDocument(document) {
  return {
    version: document?.version || '0.7',
    project_name: document?.project_name || 'DemoAVG',
    blocks: (document?.blocks || []).map(normalizeDialogueBlock),
  };
}

function normalizeDialogueBlock(block) {
  return {
    id: block?.id || nextBlockId(),
    label: block?.label || nextBlockLabel(),
    title: block?.title || '',
    background: block?.background || '',
    music: block?.music || '',
    lines: (block?.lines || []).map(normalizeDialogueLine),
    return_label: block?.return_label || '',
    enabled: block?.enabled !== false,
  };
}

function normalizeDialogueLine(line) {
  return {
    type: line?.type || 'narration',
    speaker: line?.speaker || '',
    text: line?.text || '',
  };
}

function renderDialogueEditor() {
  renderDialogueBlockList();
  renderDialogueForm();
  renderDialogueLines();
  renderDialoguePreview();
}

function renderDialogueBlockList() {
  dialogueBlockList.classList.toggle('empty', dialogueDocument.blocks.length === 0);
  if (dialogueDocument.blocks.length === 0) {
    dialogueBlockList.textContent = '暂无对话块，请点击“新建”。';
    return;
  }

  dialogueBlockList.innerHTML = dialogueDocument.blocks
    .map((block, index) => {
      const active = index === selectedBlockIndex ? ' active' : '';
      const disabled = block.enabled ? '' : ' disabled';
      const title = block.title || block.label || block.id;
      return `<button class="dialogue-block-item${active}${disabled}" type="button" data-index="${index}">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(block.label || '-')}</span>
      </button>`;
    })
    .join('');

  dialogueBlockList.querySelectorAll('.dialogue-block-item').forEach((button) => {
    button.addEventListener('click', () => {
      selectedBlockIndex = Number(button.dataset.index);
      renderDialogueEditor();
    });
  });
}

function renderDialogueForm() {
  const block = getSelectedBlock();
  const disabled = !block;
  [
    dialogueBlockId,
    dialogueBlockLabel,
    dialogueBlockTitle,
    dialogueBlockBackground,
    dialogueBlockMusic,
    dialogueBlockReturnLabel,
    dialogueBlockEnabled,
  ].forEach((input) => {
    input.disabled = disabled;
  });

  dialogueBlockId.value = block?.id || '';
  dialogueBlockLabel.value = block?.label || '';
  dialogueBlockTitle.value = block?.title || '';
  dialogueBlockBackground.value = block?.background || '';
  dialogueBlockMusic.value = block?.music || '';
  dialogueBlockReturnLabel.value = block?.return_label || '';
  dialogueBlockEnabled.checked = block?.enabled !== false;
}

function renderDialogueLines() {
  const block = getSelectedBlock();
  dialogueLineList.classList.toggle('empty', !block || block.lines.length === 0);
  if (!block) {
    dialogueLineList.textContent = '请选择或新建一个对话块。';
    return;
  }
  if (block.lines.length === 0) {
    dialogueLineList.textContent = '暂无对白行，请添加 narration / dialogue / comment。';
    return;
  }

  dialogueLineList.innerHTML = block.lines
    .map(
      (line, index) => `<div class="dialogue-line" data-index="${index}">
        <select class="line-type" aria-label="line type">
          ${Object.keys(lineTypeLabels)
            .map((type) => `<option value="${type}"${type === line.type ? ' selected' : ''}>${lineTypeLabels[type]}</option>`)
            .join('')}
        </select>
        <input class="line-speaker" type="text" placeholder="speaker" value="${escapeAttribute(line.speaker)}" />
        <textarea class="line-text" rows="2" placeholder="对白文本或注释">${escapeHtml(line.text)}</textarea>
        <div class="line-actions">
          <button type="button" class="line-up secondary-button">↑</button>
          <button type="button" class="line-down secondary-button">↓</button>
          <button type="button" class="line-delete danger-button">删除</button>
        </div>
      </div>`,
    )
    .join('');

  dialogueLineList.querySelectorAll('.dialogue-line').forEach((row) => {
    const index = Number(row.dataset.index);
    row.querySelector('.line-type').addEventListener('change', (event) => updateDialogueLine(index, 'type', event.target.value));
    row.querySelector('.line-speaker').addEventListener('input', (event) => updateDialogueLine(index, 'speaker', event.target.value));
    row.querySelector('.line-text').addEventListener('input', (event) => updateDialogueLine(index, 'text', event.target.value));
    row.querySelector('.line-up').addEventListener('click', () => moveDialogueLine(index, -1));
    row.querySelector('.line-down').addEventListener('click', () => moveDialogueLine(index, 1));
    row.querySelector('.line-delete').addEventListener('click', () => deleteDialogueLine(index));
  });
}

function renderDialoguePreview() {
  const block = getSelectedBlock();
  dialogueRenpyPreview.textContent = block ? renderRenpyBlock(block) : '请选择或新建一个对话块。';
}

function syncSelectedBlockFromForm() {
  const block = getSelectedBlock();
  if (!block) {
    return;
  }
  block.id = dialogueBlockId.value.trim();
  block.label = dialogueBlockLabel.value.trim();
  block.title = dialogueBlockTitle.value;
  block.background = dialogueBlockBackground.value.trim();
  block.music = dialogueBlockMusic.value.trim();
  block.return_label = dialogueBlockReturnLabel.value.trim();
  block.enabled = dialogueBlockEnabled.checked;
  renderDialogueBlockList();
  renderDialoguePreview();
}

function createDialogueBlock() {
  const block = {
    id: nextBlockId(),
    label: nextBlockLabel(),
    title: '新对话块',
    background: '',
    music: '',
    lines: [{ type: 'narration', speaker: '', text: '' }],
    return_label: '',
    enabled: true,
  };
  dialogueDocument.blocks.push(block);
  selectedBlockIndex = dialogueDocument.blocks.length - 1;
  dialogueValidationResult.textContent = '已新建对话块，记得保存。';
  dialogueValidationResult.className = 'dialogue-result warn';
  renderDialogueEditor();
}

function duplicateDialogueBlock() {
  const block = getSelectedBlock();
  if (!block) {
    return;
  }
  const clone = JSON.parse(JSON.stringify(block));
  clone.id = nextBlockId();
  clone.label = nextBlockLabel();
  clone.title = `${clone.title || clone.label} 副本`;
  dialogueDocument.blocks.splice(selectedBlockIndex + 1, 0, clone);
  selectedBlockIndex += 1;
  renderDialogueEditor();
}

function deleteDialogueBlock() {
  if (!getSelectedBlock()) {
    return;
  }
  dialogueDocument.blocks.splice(selectedBlockIndex, 1);
  selectedBlockIndex = Math.min(selectedBlockIndex, dialogueDocument.blocks.length - 1);
  renderDialogueEditor();
}

function addDialogueLine(type) {
  const block = getSelectedBlock();
  if (!block) {
    createDialogueBlock();
    return;
  }
  block.lines.push({ type, speaker: type === 'dialogue' ? 'n' : '', text: '' });
  renderDialogueLines();
  renderDialoguePreview();
}

function updateDialogueLine(index, key, value) {
  const block = getSelectedBlock();
  if (!block || !block.lines[index]) {
    return;
  }
  block.lines[index][key] = value;
  renderDialoguePreview();
}

function moveDialogueLine(index, direction) {
  const block = getSelectedBlock();
  const target = index + direction;
  if (!block || target < 0 || target >= block.lines.length) {
    return;
  }
  const [line] = block.lines.splice(index, 1);
  block.lines.splice(target, 0, line);
  renderDialogueLines();
  renderDialoguePreview();
}

function deleteDialogueLine(index) {
  const block = getSelectedBlock();
  if (!block) {
    return;
  }
  block.lines.splice(index, 1);
  renderDialogueLines();
  renderDialoguePreview();
}

async function saveDialogueBlocks() {
  try {
    const payload = await apiFetch('/api/dialogue/blocks/save', {
      method: 'POST',
      body: JSON.stringify({ document: dialogueDocument }),
    });
    dialogueExportResult.textContent = `已保存：${payload.path}（${payload.block_count} 个 block）`;
    dialogueExportResult.className = 'dialogue-result ok';
  } catch (error) {
    dialogueExportResult.textContent = `保存失败：${error.message}`;
    dialogueExportResult.className = 'dialogue-result bad';
  }
}

async function validateDialogueBlocks(showResult) {
  const payload = await apiFetch('/api/dialogue/blocks/validate', {
    method: 'POST',
    body: JSON.stringify({ document: dialogueDocument }),
  });
  if (showResult) {
    renderValidationResult(payload);
  }
  return payload;
}

async function exportDialogueBlocks() {
  try {
    const validation = await validateDialogueBlocks(true);
    if (validation.errors?.length) {
      dialogueExportResult.textContent = '存在 error，已取消导出。';
      dialogueExportResult.className = 'dialogue-result bad';
      return;
    }
    const payload = await apiFetch('/api/dialogue/export', {
      method: 'POST',
      body: JSON.stringify({ document: dialogueDocument }),
    });
    dialogueExportResult.textContent = `已导出：${payload.path}\n导出 ${payload.exported_count} 个，跳过 ${payload.skipped_count} 个。`;
    dialogueExportResult.className = 'dialogue-result ok';
  } catch (error) {
    dialogueExportResult.textContent = `导出失败：${error.message}`;
    dialogueExportResult.className = 'dialogue-result bad';
  }
}

function renderValidationResult(payload) {
  const errors = payload.errors || [];
  const warnings = payload.warnings || [];
  if (errors.length === 0 && warnings.length === 0) {
    dialogueValidationResult.textContent = '校验通过，没有 error / warning。';
    dialogueValidationResult.className = 'dialogue-result ok';
    return;
  }
  dialogueValidationResult.innerHTML = [
    ...errors.map((item) => `<div class="issue bad">ERROR: ${escapeHtml(item)}</div>`),
    ...warnings.map((item) => `<div class="issue warn">WARN: ${escapeHtml(item)}</div>`),
  ].join('');
  dialogueValidationResult.className = `dialogue-result ${errors.length ? 'bad' : 'warn'}`;
}

function renderRenpyBlock(block) {
  const lines = [`label ${block.label || 'dialogue_block_001'}:`, ''];
  if (block.background) {
    lines.push(`    scene ${block.background}`, '');
  }
  if (block.music) {
    lines.push(`    play music "${escapeRenpyString(block.music)}"`, '');
  }
  block.lines.forEach((line) => {
    if (line.type === 'comment') {
      lines.push(`    # ${line.text || ''}`, '');
    } else if (line.type === 'dialogue' && line.speaker.trim()) {
      lines.push(`    ${line.speaker.trim()} "${escapeRenpyString(line.text)}"`, '');
    } else {
      lines.push(`    "${escapeRenpyString(line.text)}"`, '');
    }
  });
  lines.push(block.return_label ? `    jump ${block.return_label}` : '    return');
  return lines.join('\n');
}

function nextBlockId() {
  return nextIndexedValue('block_', 'id');
}

function nextBlockLabel() {
  return nextIndexedValue('dialogue_block_', 'label');
}

function nextIndexedValue(prefix, key) {
  const used = new Set(dialogueDocument.blocks.map((block) => block[key]));
  let index = 1;
  let value = `${prefix}${String(index).padStart(3, '0')}`;
  while (used.has(value)) {
    index += 1;
    value = `${prefix}${String(index).padStart(3, '0')}`;
  }
  return value;
}

function getSelectedBlock() {
  return dialogueDocument.blocks[selectedBlockIndex] || null;
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(formatApiError(payload.detail) || '请求失败');
  }
  return payload;
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

function formatApiError(detail) {
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail.map(formatApiError).join('; ');
  }
  if (detail && typeof detail === 'object') {
    if (Array.isArray(detail.errors)) {
      return detail.errors.join('; ');
    }
    return JSON.stringify(detail);
  }
  return '';
}

function escapeRenpyString(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/"/g, '\\"');
}

function escapeAttribute(value) {
  return escapeHtml(value).replace(/`/g, '&#096;');
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
