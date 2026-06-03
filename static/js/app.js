/* 职慧Agent v1.1 - 交互逻辑升级 */

// ============ Tab 切换 ============
document.querySelectorAll('.nav-tabs .tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-tabs .tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// ============ API ============
const API = '/api/v1';
async function apiCall(path, body) {
  const resp = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// ============ 1. 岗位能力图谱 ============
let currentSkillData = null;

const genMapBtn = document.getElementById('gen-map-btn');
const mapLoading = document.getElementById('map-loading');
const mapResult = document.getElementById('map-result');

genMapBtn.addEventListener('click', async () => {
  const jobName = document.getElementById('job-input').value.trim();
  const major = document.getElementById('major-select').value;
  if (!jobName) { alert('请输入岗位名称'); return; }

  genMapBtn.disabled = true;
  genMapBtn.textContent = '生成中...';
  mapLoading.style.display = 'block';
  mapResult.style.display = 'none';

  try {
    const data = await apiCall('/skill-map', { job_name: jobName, major });
    currentSkillData = data;
    renderSkillMap(data, jobName, major);
    mapResult.style.display = 'block';
  } catch (e) {
    alert('生成失败：' + e.message);
  } finally {
    genMapBtn.disabled = false;
    genMapBtn.textContent = '🚀 生成能力图谱';
    mapLoading.style.display = 'none';
  }
});

function renderSkillMap(data, jobName, major) {
  document.getElementById('result-job-name').textContent = `${jobName} — 能力图谱`;
  document.getElementById('result-major').textContent = `专业群：${major}`;
  document.getElementById('result-time').textContent = `生成时间：${new Date().toLocaleString('zh-CN')}`;

  const warnEl = document.getElementById('result-warning');
  if (data.warning) {
    warnEl.textContent = '⚠ ' + data.warning;
    warnEl.style.display = 'inline-block';
  } else {
    warnEl.style.display = 'none';
  }

  // 统计卡片
  renderStats(data);
  // 雷达图
  renderRadarChart(data.skill_tree);
  // 技能树
  renderSkillTree(data.skill_tree);
  // 知识点
  renderKnowledgeList(data.knowledge_points || []);
  // 成长路径
  renderCareerPath(data.career_path || []);
  // 关联岗位
  renderRelatedJobs(data.related_jobs || []);
}

function renderStats(data) {
  const st = data.skill_tree || {};
  const stats = [
    { num: Object.values(st).reduce((s, v) => s + (v?.length || 0), 0), label: '技能总数' },
    { num: (st['核心能力'] || []).length, label: '核心能力' },
    { num: (st['专业技能'] || []).length, label: '专业技能' },
    { num: (data.knowledge_points || []).length, label: '知识点' },
    { num: (data.career_path || []).length, label: '成长阶段' },
    { num: (data.related_jobs || []).length, label: '关联岗位' },
  ];
  const container = document.getElementById('stats-row');
  container.innerHTML = stats.map(s =>
    `<div class="stat-card"><div class="stat-num">${s.num}</div><div class="stat-label">${s.label}</div></div>`
  ).join('');
}

function renderRadarChart(skillTree) {
  const canvas = document.getElementById('radar-chart');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  canvas.width = 450 * dpr;
  canvas.height = 400 * dpr;
  canvas.style.width = '450px';
  canvas.style.height = '400px';
  ctx.scale(dpr, dpr);

  const w = 450, h = 400;
  const cx = w / 2, cy = h / 2, r = 140;
  ctx.clearRect(0, 0, w, h);

  // 6维：核心能力/专业技能/工具技能/软技能/知识点覆盖/综合评分
  const cats = ['核心能力', '专业技能', '工具技能', '软技能'];
  const counts = cats.map(c => (skillTree[c]?.length || 0));
  const maxCount = Math.max(...counts, 1);

  // 计算每维得分 (归一化到0-100)
  const scores = counts.map(c => Math.min(100, Math.round(c / maxCount * 100)));

  // 画网格
  for (let ring = 1; ring <= 4; ring++) {
    const rr = r * ring / 4;
    ctx.beginPath();
    for (let i = 0; i < cats.length; i++) {
      const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
      const x = cx + rr * Math.cos(angle);
      const y = cy + rr * Math.sin(angle);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(124,111,255,0.15)';
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // 画轴线
  for (let i = 0; i < cats.length; i++) {
    const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + r * Math.cos(angle), cy + r * Math.sin(angle));
    ctx.strokeStyle = 'rgba(124,111,255,0.2)';
    ctx.stroke();
  }

  // 数据区 - 渐变填充
  ctx.beginPath();
  for (let i = 0; i < cats.length; i++) {
    const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
    const val = (scores[i] / 100) * r;
    const x = cx + val * Math.cos(angle);
    const y = cy + val * Math.sin(angle);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();

  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
  grad.addColorStop(0, 'rgba(124,111,255,0.4)');
  grad.addColorStop(1, 'rgba(124,111,255,0.15)');
  ctx.fillStyle = grad;
  ctx.fill();

  ctx.strokeStyle = '#7c6fff';
  ctx.lineWidth = 2.5;
  ctx.stroke();

  // 数据点 + 标签
  const labelColors = ['#7c6fff', '#b8a9ff', '#ff7eb3', '#00e6a7'];
  for (let i = 0; i < cats.length; i++) {
    const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
    const val = (scores[i] / 100) * r;
    const x = cx + val * Math.cos(angle);
    const y = cy + val * Math.sin(angle);

    // 数据点
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = labelColors[i];
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // 标签
    const lx = cx + (r + 35) * Math.cos(angle);
    const ly = cy + (r + 35) * Math.sin(angle);
    ctx.fillStyle = '#ebebf2';
    ctx.font = '13px -apple-system, "PingFang SC", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(`${cats[i]}`, lx, ly - 8);
    ctx.fillStyle = labelColors[i];
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText(`${counts[i]}项`, lx, ly + 10);
  }
}

// 技能过滤
document.querySelector('.skill-filter')?.addEventListener('click', e => {
  if (!e.target.classList.contains('filter-btn')) return;
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  e.target.classList.add('active');
  const filter = e.target.dataset.filter;
  document.querySelectorAll('.skill-category').forEach(cat => {
    if (filter === 'all' || cat.dataset.cat === filter) {
      cat.style.display = '';
    } else {
      cat.style.display = 'none';
    }
  });
});

function renderSkillTree(skillTree) {
  const container = document.getElementById('skill-tree');
  container.innerHTML = '';
  const emoji = { '核心能力': '🎯', '专业技能': '🔧', '工具技能': '🛠️', '软技能': '🤝' };

  for (const [cat, items] of Object.entries(skillTree)) {
    if (!items || items.length === 0) continue;
    const section = document.createElement('div');
    section.className = 'skill-category';
    section.dataset.cat = cat;
    section.innerHTML = `<h4>${emoji[cat] || '📌'} ${cat}（${items.length}）</h4>`;
    items.forEach(item => {
      const div = document.createElement('div');
      div.className = 'skill-item';
      const name = item.name || item;
      const desc = item.description || item.details || '';
      const level = item.level || '';
      const tools = item.tools ? item.tools.join(', ') : '';
      const prof = item.proficiency || '';
      div.innerHTML = `
        <div>
          <div class="skill-name">${name} ${level ? `<span style="font-size:11px;color:var(--accent-light)">（${level}）</span>` : ''} ${prof ? `<span style="font-size:11px;color:var(--success)">[${prof}]</span>` : ''}</div>
          ${desc ? `<div class="skill-desc">${desc}</div>` : ''}
          ${tools ? `<div class="skill-meta">工具：${tools}</div>` : ''}
        </div>`;
      section.appendChild(div);
    });
    container.appendChild(section);
  }
}

// 知识点搜索
const kpSearch = document.getElementById('kp-search');
kpSearch?.addEventListener('input', () => {
  const q = kpSearch.value.toLowerCase().trim();
  document.querySelectorAll('.knowledge-item').forEach(item => {
    const text = item.textContent.toLowerCase();
    item.style.display = (!q || text.includes(q)) ? '' : 'none';
  });
  const visible = document.querySelectorAll('.knowledge-item:not([style*="display: none"])').length;
  document.getElementById('kp-count').textContent = `${visible} / ${document.querySelectorAll('.knowledge-item').length}`;
});

function renderKnowledgeList(points) {
  const container = document.getElementById('knowledge-list');
  container.innerHTML = '';
  if (!points || points.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted)">暂无知识点数据</p>';
    return;
  }
  const kpCount = document.getElementById('kp-count');
  if (kpCount) kpCount.textContent = `${points.length} / ${points.length}`;

  points.forEach((kp, i) => {
    const div = document.createElement('div');
    div.className = 'knowledge-item';
    const pointText = typeof kp === 'string' ? kp : (kp.point || kp.knowledge_point || JSON.stringify(kp));
    const ref = kp.reference || kp.ref || '';
    const cat = kp.category || '';
    const diff = kp.difficulty || '';
    div.innerHTML = `
      <span class="kp-id">K${String(i + 1).padStart(3, '0')}</span>
      <span class="kp-point">${pointText}</span>
      ${cat ? `<span class="kp-cat">${cat}${diff ? '·' + diff : ''}</span>` : ''}
      ${ref ? `<span class="kp-ref" title="${ref}">${ref}</span>` : ''}
    `;
    container.appendChild(div);
  });
}

function renderCareerPath(path) {
  const container = document.getElementById('career-path');
  container.innerHTML = '';
  if (!path || path.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted)">暂无成长路径数据</p>';
    return;
  }
  path.forEach(stage => {
    const div = document.createElement('div');
    div.className = 'career-stage';
    const name = stage.stage || stage.name || '';
    const duration = stage.duration || stage.time || '';
    const milestones = stage.milestones || stage.milestone || [];
    const msList = Array.isArray(milestones) ? milestones.map(m => `<li>${m}</li>`).join('') : `<li>${milestones}</li>`;
    div.innerHTML = `
      <h4>${name}</h4>
      ${duration ? `<div class="stage-meta">⏱️ ${duration}</div>` : ''}
      <ul>${msList}</ul>
    `;
    container.appendChild(div);
  });
}

function renderRelatedJobs(jobs) {
  const container = document.getElementById('related-jobs');
  container.innerHTML = '';
  if (!jobs || jobs.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted)">暂无关联岗位</p>';
    return;
  }
  const icons = ['💼', '🏗️', '⚡', '📱', '🧑‍💼'];
  jobs.forEach((job, i) => {
    const jobName = typeof job === 'string' ? job : job.name || job.job_name || '';
    const div = document.createElement('div');
    div.className = 'related-job-card';
    div.innerHTML = `
      <div style="font-size:24px;margin-bottom:6px">${icons[i % icons.length]}</div>
      <div class="rj-name">${jobName}</div>
      <div class="rj-arrow">→</div>
    `;
    div.addEventListener('click', () => {
      document.getElementById('job-input').value = jobName;
      document.getElementById('gen-map-btn').click();
    });
    container.appendChild(div);
  });
}

// ============ 2. 学习路径 ============
const genPathBtn = document.getElementById('gen-path-btn');

genPathBtn.addEventListener('click', async () => {
  const targetJob = document.getElementById('lp-target-job').value.trim();
  const skills = document.getElementById('lp-skills').value.split(/[,，]/).map(s => s.trim()).filter(Boolean);
  const experience = document.getElementById('lp-experience').value.trim();
  const weeks = parseInt(document.getElementById('lp-weeks').value) || 12;

  if (!targetJob) { alert('请输入目标岗位'); return; }

  genPathBtn.disabled = true;
  genPathBtn.textContent = '诊断中...';
  document.getElementById('path-loading').style.display = 'block';
  document.getElementById('path-result').style.display = 'none';

  try {
    const diag = await apiCall('/diagnose', {
      user_profile: { skills, experience, projects: [] },
      target_job: targetJob,
    });

    const path = await apiCall('/learn-path', {
      diagnosis: diag,
      target_job: targetJob,
      weeks,
    });

    renderLearnPath(diag, path);
    document.getElementById('path-result').style.display = 'block';
  } catch (e) {
    alert('生成失败：' + e.message);
  } finally {
    genPathBtn.disabled = false;
    genPathBtn.textContent = '🔍 开始诊断';
    document.getElementById('path-loading').style.display = 'none';
  }
});

function renderLearnPath(diag, path) {
  const score = diag.match_score || 0;
  const circle = document.getElementById('score-circle');
  const scoreVal = document.getElementById('score-value');
  scoreVal.textContent = score;

  const deg = (score / 100) * 360;
  circle.style.background = `conic-gradient(var(--accent) ${deg}deg, var(--bg-card) ${deg}deg)`;

  const gapContainer = document.getElementById('gap-analysis');
  gapContainer.innerHTML = '';
  const gapLevel = diag.gap_level || {};
  for (const [key, val] of Object.entries(gapLevel)) {
    const gap = typeof val === 'object' ? (val.gap || 0) : val;
    const detail = typeof val === 'object' ? (val.detail || '') : '';
    const gapClass = gap <= 0 ? 'gap-0' : gap <= 1 ? 'gap-1' : 'gap-2';
    const pct = Math.max(5, 100 - gap * 25);
    const div = document.createElement('div');
    div.className = `gap-item ${gapClass}`;
    div.innerHTML = `
      <span style="min-width:80px;font-size:13px">${key}</span>
      <div class="gap-bar"><div class="gap-bar-fill" style="width:${pct}%"></div></div>
      <span style="font-size:12px;color:var(--text-muted);min-width:120px">${detail}</span>
    `;
    gapContainer.appendChild(div);
  }

  if (diag.diagnosis_summary) {
    const p = document.createElement('p');
    p.style.cssText = 'font-size:13px;color:var(--text-secondary);margin-top:12px;line-height:1.6;';
    p.textContent = '\uD83D\uDCDD ' + diag.diagnosis_summary;
    gapContainer.appendChild(p);
  }

  const pathContainer = document.getElementById('learning-path');
  pathContainer.innerHTML = '';
  const phases = path.path || [];
  phases.forEach(phase => {
    const div = document.createElement('div');
    div.className = 'path-phase';
    let tasksHtml = '';
    (phase.tasks || []).forEach(t => {
      const kps = t.knowledge_points || t.knowledge || [];
      tasksHtml += `<div class="path-task">
        <strong>${t.task_name || t.name || ''}</strong>
        ${kps.length ? `<div style="font-size:12px;color:var(--text-muted);margin-top:4px;">📚 ${kps.join(', ')}</div>` : ''}
        ${t.practice ? `<div style="font-size:12px;color:var(--accent-light);margin-top:4px;">🛠️ 实践：${t.practice}</div>` : ''}
      </div>`;
    });
    div.innerHTML = `
      <h4>${phase.phase || ''}</h4>
      <div class="phase-weeks">⏱️ ${phase.weeks || ''}</div>
      ${tasksHtml}
      ${phase.milestone ? `<div style="font-size:12px;color:var(--success);margin-top:8px;">🎯 里程碑：${phase.milestone}</div>` : ''}
    `;
    pathContainer.appendChild(div);
  });

  renderTrajectoryChart(path.growth_trajectory || []);
}

function renderTrajectoryChart(trajectory) {
  const canvas = document.getElementById('trajectory-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  canvas.width = 600 * dpr;
  canvas.height = 200 * dpr;
  canvas.style.width = '600px';
  canvas.style.height = '200px';
  ctx.scale(dpr, dpr);

  const w = 600, h = 200;
  ctx.clearRect(0, 0, w, h);

  const padding = { top: 30, right: 30, bottom: 50, left: 50 };
  const plotW = w - padding.left - padding.right;
  const plotH = h - padding.top - padding.bottom;

  const weeks = trajectory.map(p => p.week || 0);
  const scores = trajectory.map(p => p.score || 0);
  const maxWeek = Math.max(...weeks, 1);
  const maxScore = Math.max(...scores, 100);

  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding.left, padding.top);
  ctx.lineTo(padding.left, h - padding.bottom);
  ctx.lineTo(w - padding.right, h - padding.bottom);
  ctx.stroke();

  ctx.fillStyle = '#6d6d99';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'right';
  for (let s = 0; s <= maxScore; s += 20) {
    const y = padding.top + plotH * (1 - s / maxScore);
    ctx.fillText(s, padding.left - 8, y + 4);
    if (s > 0) {
      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(w - padding.right, y);
      ctx.stroke();
    }
  }

  ctx.textAlign = 'center';
  weeks.forEach(wk => {
    const x = padding.left + (wk / maxWeek) * plotW;
    ctx.fillText(wk + '周', x, h - padding.bottom + 20);
  });

  // 折线 + 面积
  ctx.beginPath();
  ctx.strokeStyle = '#7c6fff';
  ctx.lineWidth = 3;
  scores.forEach((sc, i) => {
    const x = padding.left + (weeks[i] / maxWeek) * plotW;
    const y = padding.top + plotH * (1 - sc / maxScore);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  ctx.lineTo(padding.left + (weeks[weeks.length - 1] / maxWeek) * plotW, h - padding.bottom);
  ctx.lineTo(padding.left, h - padding.bottom);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, padding.top, 0, h - padding.bottom);
  grad.addColorStop(0, 'rgba(124,111,255,0.2)');
  grad.addColorStop(1, 'rgba(124,111,255,0.02)');
  ctx.fillStyle = grad;
  ctx.fill();

  weeks.forEach((wk, i) => {
    const x = padding.left + (wk / maxWeek) * plotW;
    const y = padding.top + plotH * (1 - scores[i] / maxScore);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#7c6fff';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = '#ebebf2';
    ctx.font = 'bold 11px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(scores[i], x, y - 12);
  });

  ctx.fillStyle = '#a0a0c8';
  ctx.font = '13px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('预测成长轨迹', w / 2, 16);
}

// ============ 3. 新岗位发现 ============
// 趋势标签快捷填入
document.querySelectorAll('.trend-tag').forEach(tag => {
  tag.addEventListener('click', () => {
    document.getElementById('trend-input').value = tag.dataset.val;
  });
});

const genNewJobBtn = document.getElementById('gen-newjob-btn');

genNewJobBtn.addEventListener('click', async () => {
  const trends = document.getElementById('trend-input').value.split(/[,，]/).map(s => s.trim()).filter(Boolean);
  if (trends.length === 0) { alert('请输入技术趋势关键词'); return; }

  genNewJobBtn.disabled = true;
  genNewJobBtn.textContent = '分析中...';
  document.getElementById('newjob-loading').style.display = 'block';
  document.getElementById('newjob-result').style.display = 'none';

  try {
    const data = await apiCall('/new-job', { trend_keywords: trends });
    renderNewJob(data);
    document.getElementById('newjob-result').style.display = 'block';
  } catch (e) {
    alert('生成失败：' + e.message);
  } finally {
    genNewJobBtn.disabled = false;
    genNewJobBtn.textContent = '🧪 发现新岗位';
    document.getElementById('newjob-loading').style.display = 'none';
  }
});

function renderNewJob(data) {
  const card = document.getElementById('newjob-card');
  const jobName = data.job_name || '新兴岗位';
  const resp = data.core_responsibility || '';
  const reqSkills = data.required_skills || [];
  const bonus = data.bonus_skills || [];
  const scenarios = data.scenarios || [];
  const why = data.why_emerging || '';

  card.innerHTML = `
    <h2>🆕 ${jobName}</h2>
    <div class="newjob-field"><h4>📋 核心职责</h4><p>${resp}</p></div>
    ${reqSkills.length ? `<div class="newjob-field"><h4>🔑 必备技能</h4><div class="tag-list">${reqSkills.map(s => `<span class="tag">${s}</span>`).join('')}</div></div>` : ''}
    ${bonus.length ? `<div class="newjob-field"><h4>➕ 加分技能</h4><div class="tag-list">${bonus.map(s => `<span class="tag">${s}</span>`).join('')}</div></div>` : ''}
    ${scenarios.length ? `<div class="newjob-field"><h4>🏢 应用场景</h4><div class="tag-list">${scenarios.map(s => `<span class="tag">${s}</span>`).join('')}</div></div>` : ''}
    ${why ? `<div class="newjob-field"><h4>💡 为什么是新兴岗位？</h4><p>${why}</p></div>` : ''}
  `;

  if (data.warning) {
    const w = document.createElement('div');
    w.className = 'warning-badge';
    w.style.marginTop = '16px';
    w.textContent = '⚠ ' + data.warning;
    card.appendChild(w);
  }
}

// ============ 4. 智能问答 ============
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');
const chatMessages = document.getElementById('chat-messages');

let chatHistory = [
  { role: 'assistant', content: '你好！我是职慧Agent，可以回答关于前端开发岗位能力要求、学习方法、职业规划等问题。支持2-3轮追问哦！' }
];

// 快捷问题
document.querySelectorAll('.quick-q').forEach(q => {
  q.addEventListener('click', () => {
    chatInput.value = q.dataset.q;
    sendChat();
  });
});

function appendChatMsg(role, content) {
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  const avatar = role === 'user' ? '🧑' : '🎓';
  div.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-content">${content.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br>')}</div>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTyping() {
  const div = document.createElement('div');
  div.className = 'chat-msg assistant';
  div.id = 'typing-indicator';
  div.innerHTML = `
    <div class="msg-avatar">🎓</div>
    <div class="msg-content" style="color:var(--text-muted)">思考中...</div>
  `;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTyping() {
  document.getElementById('typing-indicator')?.remove();
}

async function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = '';

  chatHistory.push({ role: 'user', content: text });
  appendChatMsg('user', text);

  const recentHistory = chatHistory.slice(-6);
  showTyping();

  try {
    const data = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: recentHistory }),
    }).then(r => r.json());

    removeTyping();
    const reply = data.reply || '抱歉，我暂时无法回答这个问题。';
    chatHistory.push({ role: 'assistant', content: reply });
    appendChatMsg('assistant', reply);
  } catch (e) {
    removeTyping();
    appendChatMsg('assistant', '抱歉，服务暂时不可用，请稍后再试。');
  }
}

chatSendBtn.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

// ============ 初始化 ============
// 按Enter键触发生成
document.getElementById('job-input')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('gen-map-btn').click();
});
document.getElementById('trend-input')?.addEventListener('keydown', e => {
  if (e.key === 'Enter') document.getElementById('gen-newjob-btn').click();
});
