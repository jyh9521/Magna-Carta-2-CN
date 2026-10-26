/* Local, offline review. Arrow keys are navigation even inside an input. */
const items = JSON.parse(document.getElementById('review-data').textContent);
const $ = id => document.getElementById(id);
const reviewRound = Number(document.body.dataset.round || 2);
const namespace = 'image-review-v' + reviewRound + '-' + document.body.dataset.revision + '-';
const comments = new Map();
let storageAvailable = true, order = items.map((_, i) => i), pos = 0, current = null;
for (const item of items) {
  try { comments.set(item.id, localStorage.getItem(namespace + item.id) || ''); }
  catch { storageAvailable = false; comments.set(item.id, ''); }
}
function save() {
  if (!current) return;
  comments.set(current.id, $('comment').value);
  try { localStorage.setItem(namespace + current.id, $('comment').value); }
  catch { storageAvailable = false; }
  $('saved').textContent = storageAvailable ? '反馈已自动保存' : '当前仅保存在本页内存中，请下载 CSV 留存';
}
function render(focus = true) {
  if (!order.length) {
    current = null; $('count').textContent = '无匹配图片'; $('comment').value = '';
    $('comment').disabled = true; $('prev').disabled = $('next').disabled = true;
    $('orig').removeAttribute('src'); $('trans').removeAttribute('src');
    $('meta').textContent = ''; $('previous').textContent = ''; return;
  }
  pos = Math.max(0, Math.min(pos, order.length - 1)); current = items[order[pos]];
  $('comment').disabled = false; $('prev').disabled = $('next').disabled = false;
  $('orig').src = $('origlink').href = current.original_image;
  $('trans').src = $('translink').href = current.chinese_image;
  $('oldlink').href = current.previous_image;
  $('count').textContent = `${current.number} / ${items.length} · 当前筛选 ${pos + 1} / ${order.length}`;
  $('jump').value = current.number;
  $('meta').textContent = `${current.id} · ${current.width}×${current.height} · ${current.alias_count} 个别名`;
  $('previous').textContent = current.previous_feedback || '上轮未填写反馈，本轮保持原版汉化图';
  if (current.retained_note) $('previous').textContent += '\n\n本轮待证项：' + current.retained_note;
  $('action').textContent = current.action === 'restore-original' ? '已按反馈恢复原图' : current.action === 'unchanged' ? '本轮未改动：保留上轮版本' : '本轮修订：请重新审阅';
  $('quality').textContent = current.native_review_focus_note || '';
  $('comment').value = comments.get(current.id) || '';
  $('saved').textContent = storageAvailable ? '本轮反馈独立保存，不覆盖上轮 CSV' : '请下载 CSV 留存';
  if (focus) $('comment').focus({ preventScroll: true });
}
function move(delta) {
  save();
  if (!order.length) return;
  pos = (pos + delta + order.length) % order.length;
  render(true);
}
document.addEventListener('keydown', event => {
  const arrow = ['ArrowLeft', 'ArrowRight'].includes(event.code) ? event.code : event.key;
  if (arrow !== 'ArrowLeft' && arrow !== 'ArrowRight') return;
  event.preventDefault();
  event.stopImmediatePropagation();
  move(arrow === 'ArrowLeft' ? -1 : 1);
}, { capture: true });
$('prev').onclick = () => move(-1);
$('next').onclick = () => move(1);
$('comment').addEventListener('input', save);
$('go').onclick = () => {
  const target = Number($('jump').value), index = order.findIndex(i => items[i].number === target);
  if (index < 0) { $('saved').textContent = '该编号不在当前筛选中'; return; }
  save(); pos = index; render(true);
};
$('jump').addEventListener('keydown', e => { if (e.key === 'Enter') $('go').click(); });
let onlyRevised = false;
function filter() {
  save(); const q = $('filter').value.toLowerCase();
  order = items.flatMap((item, i) => {
    const haystack = item.id + ' ' + item.aliases.map(a => a.object + ' ' + a.resource).join(' ');
    return (!onlyRevised || Boolean((item.previous_feedback || '').trim())) && haystack.toLowerCase().includes(q) ? [i] : [];
  });
  pos = 0; render(false);
}
$('filter').addEventListener('input', filter);
$('all').onclick = () => { onlyRevised = false; filter(); render(true); };
$('revised').onclick = () => { onlyRevised = true; filter(); render(true); };
$('download').onclick = () => {
  save();
  const rows = [['number', 'image_id', 'feedback'], ...items.map(item => [item.number, item.id, comments.get(item.id) || ''])];
  const csv = rows.map(row => row.map(v => '"' + String(v).replaceAll('"', '""') + '"').join(',')).join('\r\n');
  const link = document.createElement('a');
  const url = URL.createObjectURL(new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' }));
  link.href = url; link.download = `image-review-feedback-v${reviewRound}.csv`; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
};
render(true);
