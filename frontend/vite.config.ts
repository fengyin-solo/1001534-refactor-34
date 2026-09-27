import { execFileSync } from 'node:child_process'
import { fileURLToPath, URL } from 'node:url'
import { defineConfig, type Plugin } from 'vite'
import vue from '@vitejs/plugin-vue'

// 后端地址默认取本文件里写的端口，起服务时可以用 VITE_PROXY_TARGET 覆盖，
// 这样换端口调试或做启动探针时前端不用改代码。
const proxyTarget = process.env.VITE_PROXY_TARGET ?? 'http://127.0.0.1:8000'

// 直接起 vite（绕过 npm run dev）时也先做模块对齐校验，配置对不上就让 dev server 起不来。
function moduleAlignmentPlugin(): Plugin {
  return {
    name: 'module-alignment-check',
    buildStart() {
      try {
        execFileSync('node', ['scripts/check-modules.cjs'], { stdio: 'inherit' })
      } catch {
        this.error('模块对齐校验未通过，请按提示运行 scripts/sync_modules.py 后重试。')
      }
    },
  }
}

export default defineConfig({
  plugins: [vue(), moduleAlignmentPlugin()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    host: '127.0.0.1',
    port: 5173,
    // 关掉自动打开页面：起服务时只打印地址，不拉起浏览器
    open: false,
    strictPort: false,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
