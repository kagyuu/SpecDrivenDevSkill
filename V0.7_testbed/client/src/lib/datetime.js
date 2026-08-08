// 日付・時刻ユーティリティ(P002 2.1 / 3.2)。壁時計時刻として扱いタイムゾーン変換を行わない。

export function formatDate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export function parseDate(text) {
  const [y, m, d] = String(text).split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function addDays(text, days) {
  const date = parseDate(text);
  date.setDate(date.getDate() + days);
  return formatDate(date);
}

// 週の開始日(月曜)。P002 3.2「選択日を含む週(月曜起点)」
export function startOfWeek(text) {
  const date = parseDate(text);
  const day = date.getDay(); // 0=日曜
  const offset = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + offset);
  return formatDate(date);
}

export function endOfWeek(text) {
  return addDays(startOfWeek(text), 6);
}

export function weekDates(text) {
  const start = startOfWeek(text);
  return Array.from({ length: 7 }, (_, i) => addDays(start, i));
}

export function today() {
  return formatDate(new Date());
}

// 30分刻みの時刻リスト(08:00〜20:00。25要素)
export function timeOptions(from = '08:00', to = '20:00', stepMinutes = 30) {
  const list = [];
  for (let m = toMinutes(from); m <= toMinutes(to); m += stepMinutes) {
    list.push(formatTime(m));
  }
  return list;
}

export function toMinutes(hhmm) {
  const [h, m] = String(hhmm).split(':').map(Number);
  return h * 60 + m;
}

export function formatTime(minutes) {
  const h = String(Math.floor(minutes / 60)).padStart(2, '0');
  const m = String(minutes % 60).padStart(2, '0');
  return `${h}:${m}`;
}

export function addMinutes(hhmm, minutes) {
  return formatTime(toMinutes(hhmm) + minutes);
}
