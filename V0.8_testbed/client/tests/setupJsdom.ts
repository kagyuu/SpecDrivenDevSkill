// Shared jsdom bootstrap for Node's built-in test runner
// (docs/P006-test-plan.md 5章: `@testing-library/react` + `jsdom`).
//
// Must be the FIRST import in any test file that uses
// `@testing-library/react` (e.g. `import './setupJsdom.ts'` as the very
// first line) - ES module evaluation runs each imported module's top-level
// code in source order for sibling imports with no shared dependency, so
// importing this first guarantees `document`/`window` exist as globals
// before `@testing-library/react`'s own module code runs.
import { JSDOM } from 'jsdom'

const dom = new JSDOM('<!doctype html><html><body></body></html>', {
  url: 'http://localhost/',
})

// Node itself defines a read-only global `navigator` getter (its own Web
// Platform API navigator, unrelated to jsdom's), so a plain assignment
// (`globalAny.navigator = ...`) throws "Cannot set property navigator of
// #<Object> which has only a getter". Object.defineProperty with
// configurable:true overrides it instead.
function setGlobal(name: string, value: unknown): void {
  Object.defineProperty(globalThis, name, {
    value,
    writable: true,
    configurable: true,
  })
}

setGlobal('window', dom.window)
setGlobal('document', dom.window.document)
setGlobal('navigator', dom.window.navigator)
setGlobal('HTMLElement', dom.window.HTMLElement)
setGlobal('customElements', dom.window.customElements)
setGlobal('Node', dom.window.Node)
