import path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import { defineConfig, searchForWorkspaceRoot } from 'vite'

const here = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(here, '..', '..')

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Committed, app-ready artifacts produced by pipeline/ (see docs/methodology.md).
      '@data': path.resolve(repoRoot, 'data', 'processed'),
    },
  },
  server: {
    port: 5173,
    fs: {
      allow: [searchForWorkspaceRoot(process.cwd()), repoRoot],
    },
  },
})
