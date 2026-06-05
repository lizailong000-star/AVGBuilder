const form = document.querySelector('#scan-form');
const pathInput = document.querySelector('#project-path');
const scanButton = document.querySelector('#scan-button');
const projectStatus = document.querySelector('#project-status');
const gitStatus = document.querySelector('#git-status');
const assetTabs = document.querySelector('#asset-tabs');
const assetList = document.querySelector('#asset-list');
const assetCount = document.querySelector('#asset-count');
const scanLog = document.querySelector('#scan-log');

let currentAssets = {};
let activeCategory = 'backgrounds';

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
  } catch (error) {
    scanLog.textContent = `扫描失败：${error.message}`;
  } finally {
    setLoading(false);
  }
}

function renderSummary(summary) {
  renderProjectStatus(summary);
  renderGitStatus(summary.git || {});
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
