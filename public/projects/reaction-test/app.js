(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const stage = $('stage');
  const key = 'reaction-lab-records-v1';
  let state = 'idle', rounds = 5, trials = [], timer = null, frame = null, startedAt = 0, saved = false, records = [];
  let storageAvailable = true;
  try {
    const stored = JSON.parse(localStorage.getItem(key) || '[]');
    records = Array.isArray(stored) ? stored.filter(r => typeof r.name === 'string' && Number.isFinite(r.average) && r.average > 0 && Number.isInteger(r.rounds) && typeof r.date === 'string').slice(0, 10) : [];
  } catch { storageAvailable = false; }
  const active = () => ['waiting', 'ready', 'early', 'paused', 'between'].includes(state);
  const clearTimers = () => { clearTimeout(timer); cancelAnimationFrame(frame); timer = null; frame = null; };
  const average = () => trials.reduce((sum, value) => sum + value, 0) / trials.length;
  function progress() {
    $('progress').replaceChildren(...Array.from({length: rounds}, (_, i) => {
      const segment = document.createElement('i');
      segment.className = i < trials.length ? 'complete' : i === trials.length && active() ? 'active' : '';
      return segment;
    }));
    $('progress').setAttribute('aria-valuemax', rounds);
    $('progress').setAttribute('aria-valuenow', trials.length);
    $('progress-count').textContent = `${trials.length} / ${rounds}`;
  }
  function render(next, title, description, action = '') {
    state = next;
    stage.dataset.state = state;
    stage.classList.toggle('assisted', $('assist').checked);
    $('stage-title').textContent = title;
    $('stage-description').textContent = description;
    $('stage-action').textContent = action;
    $('stage-action').hidden = !action;
    $('keyboard-hint').hidden = !['idle', 'between', 'done'].includes(state);
    $('stage-label').textContent = ({idle: '准备好了吗？', waiting: '保持专注', ready: '就是现在！', early: '提前点击', paused: '本轮已暂停', between: '本轮完成', done: '测试完成'})[state];
    $('round-label').textContent = active() ? `第 ${Math.min(trials.length + 1, rounds)} / ${rounds} 次` : `共 ${rounds} 次测试`;
    $('stage-footer').textContent = active() ? '点击页面任意空白处或按空格键' : '保持专注，无需提前猜测';
    $('signal-icon').hidden = ['waiting', 'ready'].includes(state) && $('assist').checked;
    $('signal-word').hidden = !['waiting', 'ready'].includes(state) || !$('assist').checked;
    $('signal-word').textContent = state === 'ready' ? '点' : '等';
    stage.setAttribute('aria-label', `${title}。${description}${action ? '。' + action : ''}`);
    document.querySelectorAll('[data-rounds]').forEach(button => { button.disabled = active(); });
    $('assist').disabled = active();
    $('cancel').hidden = !active();
    progress();
  }
  function idle() {
    clearTimers(); trials = []; saved = false;
    $('result').hidden = true;
    render('idle', $('assist').checked ? '等待变黄，即刻点击' : '等待变绿，即刻点击', $('assist').checked ? '看到蓝灯时等待，变黄并显示“点”时立即点击。' : '看到红灯时等待，变绿后尽快点击任意位置。', '开始测试');
  }
  function wait() {
    clearTimers();
    render('waiting', $('assist').checked ? '等待变黄…' : '等待变绿…', '保持专注，信号出现后立即点击。');
    timer = setTimeout(() => {
      frame = requestAnimationFrame(() => {
        if (state !== 'waiting' || document.hidden) return;
        render('ready', '点击！', '现在点击任意位置');
        startedAt = performance.now();
      });
    }, 1500 + Math.random() * 3000);
  }
  function start() {
    trials = []; saved = false;
    $('result').hidden = true;
    $('save-button').disabled = false;
    $('save-status').textContent = '';
    wait();
  }
  function act(now = performance.now()) {
    if (state === 'idle' || state === 'done') { start(); return; }
    if (state === 'waiting') {
      clearTimers();
      render('early', '太快啦！', '信号还没出现。这次不计入成绩，点击后重新等待。', '重试本轮');
      return;
    }
    if (['early', 'paused', 'between'].includes(state)) { wait(); return; }
    if (state === 'ready') {
      trials.push(Math.max(0.1, now - startedAt));
      if (trials.length === rounds) {
        render('done', `${average().toFixed(1)} ms`, '全部完成！你的平均成绩和逐次记录已生成。', '再测一次');
        showResult();
      } else render('between', `${trials.at(-1).toFixed(1)} ms`, `已完成 ${trials.length} 次，点击继续下一轮。`, '继续测试');
    }
  }
  function showResult() {
    $('average').textContent = average().toFixed(1);
    $('fastest').textContent = `${Math.min(...trials).toFixed(1)} ms`;
    $('slowest').textContent = `${Math.max(...trials).toFixed(1)} ms`;
    $('total').textContent = `${trials.length} 次`;
    $('trial-results').replaceChildren(...trials.map((value, i) => {
      const span = document.createElement('span'), label = document.createElement('small');
      label.textContent = `#${i + 1}`;
      span.append(label, `${value.toFixed(1)} ms`);
      return span;
    }));
    $('result').hidden = false;
  }
  document.addEventListener('pointerdown', event => {
    const now = performance.now();
    if (event.button !== 0 || event.isPrimary === false) return;
    if (!stage.contains(event.target) && (event.target.closest('a,button,input,label,summary,dialog,#result') || !active())) return;
    if (stage.contains(event.target)) event.preventDefault();
    act(now);
  });
  // Screen-reader synthesized activation has no pointerdown.
  stage.addEventListener('click', event => { if (event.detail === 0) act(); });
  document.addEventListener('keydown', event => {
    if (event.repeat || event.target.closest('input,button,summary,dialog,a')) return;
    if (event.code === 'Space' || event.code === 'Enter' && event.target === stage) {
      event.preventDefault(); act(performance.now());
    }
  });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && ['waiting', 'ready'].includes(state)) {
      clearTimers(); render('paused', '回来后再继续', '页面已切换，本轮不计成绩。点击重新开始这一轮。', '继续测试');
    }
  });
  $('rounds').addEventListener('click', event => {
    const button = event.target.closest('[data-rounds]');
    if (!button || active()) return;
    rounds = Number(button.dataset.rounds);
    document.querySelectorAll('[data-rounds]').forEach(b => {
      const selected = Number(b.dataset.rounds) === rounds;
      b.classList.toggle('selected', selected); b.setAttribute('aria-pressed', selected);
    });
    idle();
  });
  $('assist').addEventListener('change', () => {
    if (active()) return;
    idle();
    if ($('assist').checked) {
      $('stage-title').textContent = '等待变黄，即刻点击';
      $('stage-description').textContent = '看到蓝灯时等待，变黄并显示“点”时立即点击。';
    }
  });
  $('cancel').addEventListener('click', idle);
  $('retry').addEventListener('click', () => { start(); stage.focus({preventScroll: true}); stage.scrollIntoView({block: 'center'}); });
  function renderRecords() {
    records.sort((a, b) => a.average - b.average);
    $('record-body').replaceChildren(...records.map((record, i) => {
      const row = document.createElement('tr');
      const rank = document.createElement('td'); rank.textContent = String(i + 1).padStart(2, '0');
      const identity = document.createElement('td'), name = document.createElement('strong'), date = document.createElement('small');
      name.textContent = record.name; date.textContent = record.date;
      identity.append(name, date);
      const count = document.createElement('td'); count.textContent = record.rounds;
      const score = document.createElement('td'); score.className = 'score align-right'; score.textContent = `${record.average.toFixed(1)} ms`;
      row.append(rank, identity, count, score); return row;
    }));
    $('empty-records').hidden = records.length > 0;
    $('clear-records').disabled = records.length === 0;
    $('storage-note').textContent = storageAvailable ? '记录仅保存在当前浏览器，不会上传。保留用时最短的 10 条。' : '浏览器存储不可用，记录仅在本次页面打开期间保留。';
  }
  function persist() {
    try { localStorage.setItem(key, JSON.stringify(records)); storageAvailable = true; }
    catch { storageAvailable = false; }
    renderRecords();
  }
  $('save-form').addEventListener('submit', event => {
    event.preventDefault();
    if (saved || state !== 'done' || trials.length !== rounds) return;
    records.push({name: $('player').value.trim().slice(0, 24) || '我的成绩', average: average(), rounds, date: new Date().toLocaleDateString('zh-CN')});
    records.sort((a, b) => a.average - b.average); records = records.slice(0, 10);
    saved = true; persist(); $('save-button').disabled = true;
    $('save-status').textContent = storageAvailable ? '成绩已提交，高分榜保留最快的 10 条记录。' : '已记录本次成绩，但浏览器阻止了持久保存。';
  });
  $('clear-records').addEventListener('click', () => $('clear-dialog').showModal());
  $('keep-records').addEventListener('click', () => $('clear-dialog').close());
  $('confirm-clear').addEventListener('click', () => { records = []; persist(); $('clear-dialog').close(); });
  renderRecords(); idle();
  if (document.modelContext?.registerTool) {
    try {
      Promise.resolve(document.modelContext.registerTool({
        name: 'read_reaction_results', title: '读取反应测试成绩',
        description: '读取当前真人反应测试的进度、已完成成绩和本地高分记录，不执行或模拟点击。',
        inputSchema: {type: 'object', properties: {}, additionalProperties: false},
        annotations: {readOnlyHint: true, untrustedContentHint: true},
        execute(input) {
          if (!input || typeof input !== 'object' || Array.isArray(input) || Object.keys(input).length) throw new Error('Expected an empty object');
          return {state, rounds, completed: trials.length, trials: [...trials], average: trials.length ? average() : null, records: records.map(r => ({...r}))};
        }
      })).catch(() => {});
    } catch { /* The test also works in browsers without WebMCP support. */ }
  }
})();
