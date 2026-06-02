/* 职慧Agent — 主交互逻辑 */

// ============ Tab 切换 ============
document.querySelectorAll('.nav-tabs .tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-tabs .tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.tab).classList.add('active');
  });
});

// ============ API 基础 ============
const API = '/api/v1';

async function apiCall(path, body) {
  const resp = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(await resp.text());
  return resp.json();
}

// ============ 1. 岗位能力图谱 ============
const genMapBtn = document.getElementById('gen-map-btn');
const mapLoading = document.getElementById('map-loading');
const mapResult = document.getElementById('map-result');

genMapBtn.addEventListener('click', async () => {
  const jobName = document.getElementById('job-input').value.trim();
  const major = document.getElementById('major-select').value;
  if (!jobName) { alert('请输入岗位名称'); return; }

  genMapBtn.disabled = true;
  mapLoading.style.display = 'block';
  mapResult.style.display = 'none';

  try {
    const data = await apiCall('/skill-map', { job_name: jobName, major });
    renderSkillMap(data, jobName, major);
    mapResult.style.display = 'block';
  } catch (e) {
    alert('生成失败：' + e.message);
  } finally {
    genMapBtn.disabled = false;
    mapLoading.style.display = 'none';
  }
});

function renderSkillMap(data, jobName, major) {
  // 标题
  document.getElementById('result-job-name').textContent = `📌 ${jobName} — 能力图谱`;
  document.getElementById('result-major').textContent = `专业群：${major}`;
  document.getElementById('result-time').textContent = `生成时间：${new Date().toLocaleString('zh-CN')}`;

  // 雷达图
  renderRadarChart(data.skill_tree);

  // 技能树
  renderSkillTree(data.skill_tree);

  // 知识点
  renderKnowledgeList(data.knowledge_points || []);

  // 成长路径
  renderCareerPath(data.career_path || []);
}

function renderRadarChart(skillTree) {
  const canvas = document.getElementById('radar-chart');
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  const cx = w / 2, cy = h / 2, r = 150;

  ctx.clearRect(0, 0, w, h);

  const cats = ['核心能力', '专业技能', '工具技能', '软技能'];
  const counts = [
    skillTree['核心能力']?.length || 0,
    skillTree['专业技能']?.length || 0,
    skillTree['工具技能']?.length || 0,
    skillTree['软技能']?.length || 0,
  ];
  const maxCount = Math.max(...counts, 1);

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
    ctx.strokeStyle = 'rgba(108,99,255,0.2)';
    ctx.stroke();
  }

  // 画轴线
  for (let i = 0; i < cats.length; i++) {
    const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + r * Math.cos(angle), cy + r * Math.sin(angle));
    ctx.strokeStyle = 'rgba(108,99,255,0.3)';
    ctx.stroke();
  }

  // 数据区
  ctx.beginPath();
  for (let i = 0; i < cats.length; i++) {
    const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
    const val = (counts[i] / maxCount) * r;
    const x = cx + val * Math.cos(angle);
    const y = cy + val * Math.sin(angle);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
  ctx.fillStyle = 'rgba(108,99,255,0.35)';
  ctx.fill();
  ctx.strokeStyle = '#6c63ff';
  ctx.lineWidth = 2;
  ctx.stroke();

  // 标签
  ctx.fillStyle = '#e8e8f0';
  ctx.font = '13px sans-serif';
  ctx.textAlign = 'center';
  for (let i = 0; i < cats.length; i++) {
    const angle = (Math.PI * 2 * i / cats.length) - Math.PI / 2;
    const lx = cx + (r + 30) * Math.cos(angle);
    const ly = cy + (r + 30) * Math.sin(angle);
    ctx.fillText(`${cats[i]}(${counts[i]})`, lx, ly + 4);
  }
}

function renderSkillTree(skillTree) {
  const container = document.getElementById('skill-tree');
  container.innerHTML = '';
  const emoji = { '核心能力': '🎯', '专业技能': '🔧', '工具技能': '🛠️', '软技能': '🤝' };

  for (const [cat, items] of Object.entries(skillTree)) {
    if (!items || items.length === 0) continue;
    const section = document.createElement('div');
    section.className = 'skill-category';
    section.innerHTML = `<h4>${emoji[cat] || '📌'} ${cat}</h4>`;
    items.forEach(item => {
      const div = document.createElement('div');
      div.className = 'skill-item';
      const name = item.name || item;
      const desc = item.description || item.details || '';
      const level = item.level || '';
      const tools = item.tools ? item.tools.join(', ') : '';
      div.innerHTML = `
        <div>
          <div class="skill-name">${name} ${level ? `<span style="font-size:11px;color:var(--accent-light)">（${level}）</span>` : ''}</div>
          ${desc ? `<div class="skill-desc">${desc}</div>` : ''}
          ${tools ? `<div class="skill-meta">工具：${tools}</div>` : ''}
        </div>`;
      section.appendChild(div);
    });
    container.appendChild(section);
  }
}

function renderKnowledgeList(points) {
  const container = document.getElementById('knowledge-list');
  container.innerHTML = '';
  if (!points || points.length === 0) {
    container.innerHTML = '<p style="color:var(--text-muted)">暂无知识点数据</p>';
    return;
  }
  points.forEach((kp, i) => {
    const div = document.createElement('div');
    div.className = 'knowledge-item';
    const pointText = typeof kp === 'string' ? kp : (kp.point || kp.knowledge_point || JSON.stringify(kp));
    const ref = kp.reference || kp.ref || '';
    const cat = kp.category || '';
    div.innerHTML = `
      <span class="kp-id">K${String(i + 1).padStart(3, '0')}</span>
      <span class="kp-point">${pointText}</span>
      ${cat ? `<span class="kp-cat">${cat}</span>` : ''}
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

// ============ 2. 学习路径 ============
const genPathBtn = document.getElementById('gen-path-btn');

genPathBtn.addEventListener('click', async () => {
  const targetJob = document.getElementById('lp-target-job').value.trim();
  const skills = document.getElementById('lp-skills').value.split(/[,，]/).map(s => s.trim()).filter(Boolean);
  const experience = document.getElementById('lp-experience').value.trim();
  const weeks = parseInt(document.getElementById('lp-weeks').value) || 12;

  if (!targetJob) { alert('请输入目标岗位'); return; }

  genPathBtn.disabled = true;
  document.getElementById('path-loading').style.display = 'block';
  document.getElementById('path-result').style.display = 'none';

  try {
    // Step 1: 诊断
    const diag = await apiCall('/diagnose', {
      user_profile: { skills, experience, projects: [] },
      target_job: targetJob,
    });

    // Step 2: 生成学习路径
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
    document.getElementById('path-loading').style.display = 'none';
  }
});

function renderLearnPath(diag, path) {
  // 诊断分数
  const score = diag.match_score || 0;
  const circle = document.getElementById('score-circle');
  const scoreVal = document.getElementById('score-value');
  scoreVal.textContent = score;

  const deg = (score / 100) * 360;
  circle.style.background = `conic-gradient(var(--accent) ${deg}deg, var(--bg-card) ${deg}deg)`;
  circle.classList.add('animated');

  // 差距分析
  const gapContainer = document.getElementById('gap-analysis');
  gapContainer.innerHTML = '';
  const gapLevel = diag.gap_level || {};
  for (const [key, val] of Object.entries(gapLevel)) {
    const gapClass = val.gap <= 0 ? 'gap-0' : val.gap <= 1 ? 'gap-1' : 'gap-2';
    const pct = Math.max(5, 100 - val.gap * 25);
    const div = document.createElement('div');
    div.className = `gap-item ${gapClass}`;
    div.innerHTML = `
      <span style="min-width:80px;font-size:13px">${key}</span>
      <div class="gap-bar"><div class="gap-bar-fill" style="width:${pct}%"></div></div>
      <span style="font-size:12px;color:var(--text-muted);min-width:120px">${val.detail || ''}</span>
    `;
    gapContainer.appendChild(div);
  }

  if (diag.diagnosis_summary) {
    const p = document.createElement('p');
    p.style.cssText = 'font-size:13px;color:var(--text-secondary);margin-top:12px;line-height:1.6;';
    p.textContent = '📝 ' + diag.diagnosis_summary;
    gapContainer.appendChild(p);
  }

  // 学习路径
  const pathContainer = document.getElementById('learning-path');
  pathContainer.innerHTML = '';
  const phases = path.path || [];
  phases.forEach(phase => {
    const div = document.createElement('div');
    div.className = 'path-phase';
    let tasksHtml = '';
    (phase.tasks || []).forEach(t => {
      tasksHtml += `<div class="path-task">
        <strong>${t.task_name || t.name || ''}</strong>
        ${(t.knowledge_points || t.knowledge || []).length ? `<div style="font-size:12px;color:var(--text-muted);margin-top:4px;">📚 ${(t.knowledge_points || t.knowledge).join(', ')}</div>` : ''}
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

  // 成长轨迹图
  renderTrajectoryChart(path.growth_trajectory || []);
}

function renderTrajectoryChart(trajectory) {
  const canvas = document.getElementById('trajectory-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);

  const padding = { top: 30, right: 30, bottom: 50, left: 50 };
  const plotW = w - padding.left - padding.right;
  const plotH = h - padding.top - padding.bottom;

  const weeks = trajectory.map(p => p.week || 0);
  const scores = trajectory.map(p => p.score || 0);
  const maxWeek = Math.max(...weeks, 1);
  const maxScore = Math.max(...scores, 100);

  // 坐标轴
  ctx.strokeStyle = 'rgba(255,255,255,0.2)';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(padding.left, padding.top); ctx.lineTo(padding.left, h - padding.bottom); ctx.lineTo(w - padding.right, h - padding.bottom); ctx.stroke();

  // Y轴标签
  ctx.fillStyle = '#9999bb';
  ctx.font = '11px sans-serif';
  ctx.textAlign = 'right';
  for (let s = 0; s <= maxScore; s += 20) {
    const y = padding.top + plotH * (1 - s / maxScore);
    ctx.fillText(s, padding.left - 6, y + 4);
    if (s > 0) {
      ctx.strokeStyle = 'rgba(255,255,255,0.05)';
      ctx.beginPath(); ctx.moveTo(padding.left, y); ctx.lineTo(w - padding.right, y); ctx.stroke();
    }
  }

  // X轴标签
  ctx.textAlign = 'center';
  weeks.forEach(wk => {
    const x = padding.left + (wk / maxWeek) * plotW;
    ctx.fillText(wk + '周', x, h - padding.bottom + 20);
  });

  // 折线
  ctx.beginPath();
  ctx.strokeStyle = '#6c63ff';
  ctx.lineWidth = 3;
  scores.forEach((sc, i) => {
    const x = padding.left + (weeks[i] / maxWeek) * plotW;
    const y = padding.top + plotH * (1 - sc / maxScore);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // 面积
  ctx.lineTo(padding.left + (weeks[weeks.length - 1] / maxWeek) * plotW, h - padding.bottom);
  ctx.lineTo(padding.left, h - padding.bottom);
  ctx.closePath();
  ctx.fillStyle = 'rgba(108,99,255,0.15)';
  ctx.fill();

  // 点
  weeks.forEach((wk, i) => {
    const x = padding.left + (wk / maxWeek) * plotW;
    const y = padding.top + plotH * (1 - scores[i] / maxScore);
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#6c63ff';
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(scores[i], x, y - 10);
  });

  // 标题
  ctx.fillStyle = '#e8e8f0';
  ctx.font = '13px sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText('预测成长轨迹（分数）', w / 2, 16);
}

// ============ 3. 新岗位发现 ============
const genNewJobBtn = document.getElementById('gen-newjob-btn');

genNewJobBtn.addEventListener('click', async () => {
  const trends = document.getElementById('trend-input').value.split(/[,，]/).map(s => s.trim()).filter(Boolean);
  if (trends.length === 0) { alert('请输入技术趋势关键词'); return; }

  genNewJobBtn.disabled = true;
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
    document.getElementById('newjob-loading').style.display = 'none';
  }
});

function renderNewJob(data) {
  const card = document.getElementById('newjob-card');
  const jobName = data.job_name || '新兴岗位';
  const resp = data.core_responsibility || data.core_responsibility || '';
  const reqSkills = data.required_skills || [];
  const bonus = data.bonus_skills || [];
  const scenarios = data.scenarios || [];
  const why = data.why_emerging || data.why_emerging || '';

  card.innerHTML = `
    <h2>🆕 ${jobName}</h2>
    <div class="newjob-field">
      <h4>📋 核心职责</h4>
      <p>${resp}</p>
    </div>
    ${reqSkills.length ? `<div class="newjob-field">
      <h4>🔑 必备技能</h4>
      <div class="tag-list">${reqSkills.map(s => `<span class="tag">${s}</span>`).join('')}</div>
    </div>` : ''}
    ${bonus.length ? `<div class="newjob-field">
      <h4>➕ 加分技能</h4>
      <div class="tag-list">${bonus.map(s => `<span class="tag">${s}</span>`).join('')}</div>
    </div>` : ''}
    ${scenarios.length ? `<div class="newjob-field">
      <h4>🏢 应用场景</h4>
      <div class="tag-list">${scenarios.map(s => `<span class="tag">${s}</span>`).join('')}</div>
    </div>` : ''}
    ${why ? `<div class="newjob-field">
      <h4>💡 为什么是新兴岗位？</h4>
      <p>${why}</p>
    </div>` : ''}
  `;
}

// ============ 4. 智能问答（支持2-3轮追问）============
const chatInput = document.getElementById('chat-input');
const chatSendBtn = document.getElementById('chat-send-btn');
const chatMessages = document.getElementById('chat-messages');

let chatHistory = [
  { role: 'assistant', content: '你好！我是职慧Agent，可以回答关于前端开发岗位能力要求、学习方法、职业规划等问题。请问有什么可以帮你的？' }
];

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

async function sendChat() {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = '';

  // 追加到历史
  chatHistory.push({ role: 'user', content: text });
  appendChatMsg('user', text);

  // 只保留最近6条（支持2-3轮追问）
  const recentHistory = chatHistory.slice(-6);

  try {
    const data = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: recentHistory }),
    }).then(r => r.json());

    const reply = data.reply || '抱歉，我暂时无法回答这个问题。';
    chatHistory.push({ role: 'assistant', content: reply });
    appendChatMsg('assistant', reply);
  } catch (e) {
    appendChatMsg('assistant', '抱歉，服务暂时不可用，请稍后再试。');
  }
}

chatSendBtn.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});
