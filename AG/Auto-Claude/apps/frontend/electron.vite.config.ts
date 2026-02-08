import { defineConfig, externalizeDepsPlugin } from 'electron-vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

/**
 * Sentry configuration embedded at build time.
 *
 * In CI builds, these come from GitHub secrets.
 * In local development, these come from apps/AG-Frontend/.env (loaded by dotenv).
 *
 * The `define` option replaces these values at build time, so they're
 * embedded in the bundle and available at runtime in packaged apps.
 */
const sentryDefines = {
  '__SENTRY_DSN__': JSON.stringify(process.env.SENTRY_DSN || ''),
  '__SENTRY_TRACES_SAMPLE_RATE__': JSON.stringify(process.env.SENTRY_TRACES_SAMPLE_RATE || '0.1'),
  '__SENTRY_PROFILES_SAMPLE_RATE__': JSON.stringify(process.env.SENTRY_PROFILES_SAMPLE_RATE || '0.1'),
};

export default defineConfig({
  main: {
    define: sentryDefines,
    plugins: [externalizeDepsPlugin({
      // Bundle these packages into the main process (they won't be in node_modules in packaged app)
      exclude: [
        'uuid',
        'chokidar',
        'dotenv',
        'electron-log',
        'proper-lockfile',
        'semver',
        'zod',
        '@anthropic-ai/sdk',
        'kuzu',
        'electron-updater',
        '@electron-toolkit/utils',
        // Sentry and its transitive dependencies (opentelemetry -> debug -> ms)
        '@sentry/electron',
        '@sentry/core',
        '@sentry/node',
        '@sentry/utils',
        '@opentelemetry/instrumentation',
        'debug',
        'ms',
        // Minimatch for glob pattern matching in worktree handlers
        'minimatch'
      ]
    })],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/main/index.ts')
        },
        // Only node-pty needs to be external (native module rebuilt by electron-builder)
        external: ['@lydell/node-pty']
      }
    }
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/preload/index.ts')
        }
      }
    }
  },
  renderer: {
    define: sentryDefines,
    root: resolve(__dirname, 'src/renderer'),
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, 'src/renderer/index.html')
        }
      }
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src/renderer'),
        '@shared': resolve(__dirname, 'src/shared'),
        '@features': resolve(__dirname, 'src/renderer/features'),
        '@components': resolve(__dirname, 'src/renderer/shared/components'),
        '@hooks': resolve(__dirname, 'src/renderer/shared/hooks'),
        '@lib': resolve(__dirname, 'src/renderer/shared/lib')
      }
    },
    server: {
      // ★ Proxy for browser mode - CORS 회피
      proxy: {
        // AutoGen Studio 직접 연결
        // ★ followRedirects: AutoGen이 trailing slash 307 redirect를 반환하므로
        //    프록시 레벨에서 redirect를 따라가야 브라우저에 CORS 노출 안 됨
        '/api/autogen': {
          target: 'http://localhost:8081',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/autogen/, '/api'),
          configure: (proxy) => {
            proxy.on('proxyRes', (proxyRes, req, res) => {
              // Handle 307/301/302 redirects at proxy level to avoid CORS
              const location = proxyRes.headers['location'];
              if (location && proxyRes.statusCode && proxyRes.statusCode >= 300 && proxyRes.statusCode < 400) {
                // Rewrite the redirect location through the proxy
                const rewritten = location.replace(/^https?:\/\/localhost:8081\/api/, '/api/autogen');
                proxyRes.headers['location'] = rewritten;
              }
            });
          }
        },
        // AG-ACE-BRIDGE Pipeline API
        '/api/bridge': {
          target: 'http://localhost:8080',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api\/bridge/, '')
        }
      },
      watch: {
        // Ignore directories to prevent HMR conflicts during merge operations
        // Using absolute paths and broader patterns
        ignored: [
          '**/node_modules/**',
          '**/.git/**',
          '**/.worktrees/**',
          '**/.auto-claude/**',
          '**/out/**',
          // Ignore the parent autonomous-coding directory's worktrees
          resolve(__dirname, '../.worktrees/**'),
          resolve(__dirname, '../.auto-claude/**'),
        ]
      }
    }
  }
});
