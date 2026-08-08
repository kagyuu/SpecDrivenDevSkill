// テスト用の最小DOM実装(ADR-001: 外部パッケージを取得できないため jsdom を使えない)。
// 本番コードが使う API のみを実装する: createElement / createTextNode / appendChild /
// removeChild / setAttribute / querySelector(All) / addEventListener / dispatchEvent /
// textContent / className / value / checked / disabled。

class TextNode {
  constructor(text) {
    this.nodeType = 3;
    this.data = String(text);
    this.parentNode = null;
    this.childNodes = [];
  }
  get textContent() {
    return this.data;
  }
  set textContent(value) {
    this.data = String(value);
  }
}

class Element {
  constructor(tagName) {
    this.nodeType = 1;
    this.tagName = String(tagName).toUpperCase();
    this.childNodes = [];
    this.attributes = {};
    this.parentNode = null;
    this.listeners = {};
    this.value = '';
    this.checked = false;
    this.disabled = false;
  }

  get firstChild() {
    return this.childNodes[0] || null;
  }

  get children() {
    return this.childNodes.filter((n) => n.nodeType === 1);
  }

  get className() {
    return this.attributes.class || '';
  }
  set className(value) {
    this.attributes.class = String(value);
  }

  get id() {
    return this.attributes.id || '';
  }

  get type() {
    return this.attributes.type || '';
  }
  set type(value) {
    this.attributes.type = String(value);
  }

  get name() {
    return this.attributes.name || '';
  }

  appendChild(node) {
    node.parentNode = this;
    this.childNodes.push(node);
    return node;
  }

  removeChild(node) {
    const index = this.childNodes.indexOf(node);
    if (index >= 0) this.childNodes.splice(index, 1);
    node.parentNode = null;
    return node;
  }

  remove() {
    if (this.parentNode) this.parentNode.removeChild(this);
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
  }
  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null;
  }
  hasAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name);
  }
  removeAttribute(name) {
    delete this.attributes[name];
  }

  get textContent() {
    return this.childNodes.map((n) => n.textContent).join('');
  }
  set textContent(value) {
    this.childNodes = [];
    if (value !== '' && value !== null && value !== undefined) {
      this.appendChild(new TextNode(value));
    }
  }

  addEventListener(type, handler) {
    (this.listeners[type] = this.listeners[type] || []).push(handler);
  }

  dispatchEvent(event) {
    const handlers = this.listeners[event.type] || [];
    const results = [];
    for (const handler of handlers) results.push(handler(event));
    return results;
  }

  click() {
    return this.dispatchEvent({ type: 'click', target: this, preventDefault() {} })[0];
  }

  submit() {
    return this.dispatchEvent({ type: 'submit', target: this, preventDefault() {} })[0];
  }

  descendants() {
    const out = [];
    for (const child of this.childNodes) {
      if (child.nodeType !== 1) continue;
      out.push(child);
      out.push(...child.descendants());
    }
    return out;
  }

  querySelectorAll(selector) {
    return selectAll(this, selector);
  }

  querySelector(selector) {
    return selectAll(this, selector)[0] || null;
  }
}

// 単純なセレクタ実装: 子孫結合子(空白)と、タグ / #id / .class / [attr] / [attr="value"]
function parseCompound(text) {
  const parts = { tag: null, id: null, classes: [], attrs: [] };
  const pattern = /(\[[^\]]+\])|(#[\w-]+)|(\.[\w-]+)|([A-Za-z][\w-]*)/g;
  let found;
  while ((found = pattern.exec(text)) !== null) {
    const token = found[0];
    if (token.startsWith('[')) {
      const inner = token.slice(1, -1);
      const eq = inner.indexOf('=');
      if (eq < 0) parts.attrs.push([inner, null]);
      else parts.attrs.push([inner.slice(0, eq), inner.slice(eq + 1).replace(/^["']|["']$/g, '')]);
    } else if (token.startsWith('#')) parts.id = token.slice(1);
    else if (token.startsWith('.')) parts.classes.push(token.slice(1));
    else parts.tag = token.toUpperCase();
  }
  return parts;
}

function matches(node, compound) {
  if (compound.tag && node.tagName !== compound.tag) return false;
  if (compound.id && node.getAttribute('id') !== compound.id) return false;
  for (const cls of compound.classes) {
    if (!node.className.split(/\s+/).includes(cls)) return false;
  }
  for (const [name, value] of compound.attrs) {
    if (!node.hasAttribute(name)) return false;
    if (value !== null && node.getAttribute(name) !== value) return false;
  }
  return true;
}

function selectAll(root, selector) {
  return String(selector)
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .flatMap((single) => {
      const compounds = single.split(/\s+/).map(parseCompound);
      let current = root.descendants();
      compounds.forEach((compound, index) => {
        const matched = current.filter((node) => matches(node, compound));
        current = index === compounds.length - 1 ? matched : matched.flatMap((n) => n.descendants());
      });
      return current;
    });
}

class Document extends Element {
  constructor() {
    super('#document');
    this.body = new Element('body');
    this.appendChild(this.body);
  }
  createElement(tag) {
    return new Element(tag);
  }
  createTextNode(text) {
    return new TextNode(text);
  }
  getElementById(id) {
    return this.querySelector(`#${id}`);
  }
}

// テストごとに新しいDOMを用意し、グローバルへ載せる。
export function installDom() {
  const document = new Document();
  const app = document.createElement('div');
  app.setAttribute('id', 'app');
  const header = document.createElement('div');
  header.setAttribute('id', 'header');
  document.body.appendChild(header);
  document.body.appendChild(app);
  globalThis.document = document;
  globalThis.location = { hash: '' };
  globalThis.addEventListener = () => {};
  globalThis.confirm = () => true;
  return { document, app, header };
}

export { Element, TextNode, Document };
