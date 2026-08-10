import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// U001-T1 (docs/P007-impl-direction/U001-foundation-and-auth.md): minimal
// Vite + React + TypeScript scaffolding only. Dev-server proxy to the
// backend API is configured when the first real API call is wired up.
export default defineConfig({
  plugins: [react()],
})
