import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

// U001-T1 (docs/P007-impl-direction/U001-foundation-and-auth.md): minimal
// entry point only. Routing (react-router-dom) is wired up starting with
// U001-T5 (S01 login screen) / U003-T4 (S02 calendar screen).
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
