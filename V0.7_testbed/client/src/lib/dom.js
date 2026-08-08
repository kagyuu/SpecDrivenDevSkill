// DOM生成とエラー表示のヘルパ(P002 2.4)。document への参照は関数の内側に閉じる。

export function el(tag, props = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (key === 'class') node.className = value;
    else if (key === 'text') node.textContent = value;
    else if (key.startsWith('on') && typeof value === 'function') {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (key === 'value' || key === 'checked' || key === 'disabled') {
      node[key] = value;
    } else {
      node.setAttribute(key, value);
    }
  }
  for (const child of [].concat(children)) {
    if (child === null || child === undefined) continue;
    node.appendChild(typeof child === 'string' ? document.createTextNode(child) : child);
  }
  return node;
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

// フィールド単位のエラー表示(P002 2.4 の 400 VALIDATION_ERROR 行)
export function showFieldError(root, field, message) {
  const holder = root.querySelector(`[data-error-for="${field}"]`);
  if (!holder) return;
  holder.textContent = message || '';
}

export function clearFieldErrors(root) {
  for (const holder of root.querySelectorAll('[data-error-for]')) holder.textContent = '';
}

export function showTopMessage(root, message, isError = true) {
  const holder = root.querySelector('[data-top-message]');
  if (!holder) return;
  holder.textContent = message || '';
  holder.className = isError ? 'top-message is-error' : 'top-message';
}

// P002 2.4 の対応表を1つの関数にまとめる。
export function showApiError(root, error) {
  if (!error) return;
  if (error.status === 400 && error.code === 'VALIDATION_ERROR' && error.details.length > 0) {
    let unmapped = false;
    for (const detail of error.details) {
      const holder = root.querySelector(`[data-error-for="${detail.field}"]`);
      if (holder) holder.textContent = detail.message;
      else unmapped = true;
    }
    if (unmapped) showTopMessage(root, error.message);
    return;
  }
  if (error.status === 409 && error.code === 'DUPLICATE_KEY') {
    const field = duplicateField(root);
    if (field) {
      // APIが具体的な文言を返す場合はそれを優先する(P008 T010 / P002 2.4 の既定文言はfallback)
      showFieldError(root, field, error.message || '同じ値がすでに登録されています。');
      return;
    }
  }
  showTopMessage(root, error.message);
}

// 409 DUPLICATE_KEY を表示するフィールド。画面側が data-duplicate-field で指定する。
function duplicateField(root) {
  const marker = root.querySelector('[data-duplicate-field]');
  if (marker) return marker.getAttribute('data-duplicate-field');
  for (const field of ['name', 'user_id']) {
    if (root.querySelector(`[data-error-for="${field}"]`)) return field;
  }
  return null;
}

export function setSubmitting(button, submitting) {
  if (button) button.disabled = !!submitting;
}
