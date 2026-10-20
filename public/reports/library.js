const input = document.getElementById('search');
if (input) {
  const cards = [...document.querySelectorAll('.report-card')];
  const buttons = [...document.querySelectorAll('[data-filter]')];
  const requested = new URLSearchParams(location.search).get('category');
  let category = buttons.some(button => button.dataset.filter === requested) ? requested : '全部';
  const filter = () => {
    const query = input.value.trim().toLowerCase();
    let count = 0;
    cards.forEach(card => {
      const show = (category === '全部' || card.dataset.category === category)
        && card.dataset.search.toLowerCase().includes(query);
      card.hidden = !show;
      if (show) count++;
    });
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === category)));
    document.getElementById('result-count').textContent = '共 ' + count + ' 份';
    document.getElementById('empty').hidden = count !== 0;
  };
  input.addEventListener('input', filter);
  buttons.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.filter;
    const url = new URL(location.href);
    if (category === '全部') url.searchParams.delete('category');
    else url.searchParams.set('category', category);
    // The same pages also work when opened as local files.
    try { history.replaceState(null, '', url); } catch {}
    filter();
  }));
  filter();
}
document.querySelectorAll('.copy').forEach(button => button.addEventListener('click', async () => {
  const section = button.closest('section');
  const text = section.querySelector('code').textContent;
  let copied = false;
  try {
    if (navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      copied = true;
    }
  } catch {}
  if (!copied) {
    const area = document.createElement('textarea');
    area.value = text;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.append(area);
    area.select();
    copied = document.execCommand('copy');
    area.remove();
    button.focus();
  }
  section.querySelector('.copy-status').textContent = copied ? '代码已复制。' : '请选中上方代码后复制。';
}));
