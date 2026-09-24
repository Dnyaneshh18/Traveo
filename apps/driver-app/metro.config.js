// Expo SDK 52+ auto-configures Metro for npm workspaces; we additionally force
// singletons (react, react-dom, react-native, react-native-web) so hoisted packages
// and app code never resolve two copies of React.
// Dev proxy: forward /api, /uploads to backend on port 8000 so web previews
// never face cross-origin port mapping issues in browser preview environments.
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const http = require('http');

const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);
config.watchFolders = [workspaceRoot];
config.resolver.nodeModulesPaths = [
  path.resolve(projectRoot, 'node_modules'),
  path.resolve(workspaceRoot, 'node_modules'),
];
config.resolver.sourceExts = [...config.resolver.sourceExts, 'cjs'];

const SINGLETONS = ['react', 'react-dom', 'react-native', 'react-native-web', 'react-native-safe-area-context', 'zustand', '@tanstack/react-query'];
const defaultResolver = config.resolver.resolveRequest;
config.resolver.resolveRequest = (context, moduleName, platform) => {
  const pkg = SINGLETONS.find((s) => moduleName === s || moduleName.startsWith(`${s}/`));
  if (pkg) {
    const dir = [projectRoot, workspaceRoot].map((r) => path.join(r, 'node_modules', pkg)).find((d) => require('fs').existsSync(d));
    if (dir) {
      const rest = moduleName.slice(pkg.length);
      const resolved = require.resolve(dir + rest, { paths: [projectRoot] });
      return { type: 'sourceFile', filePath: resolved };
    }
  }
  return defaultResolver ? defaultResolver(context, moduleName, platform) : context.resolveRequest(context, moduleName, platform);
};

// Dev proxy middleware forwarding /api, /uploads, /health to backend (:8000)
const originalEnhanceMiddleware = config.server.enhanceMiddleware;
config.server.enhanceMiddleware = (metroMiddleware, server) => {
  const backendTarget = new URL(process.env.BACKEND_PROXY_URL || 'http://127.0.0.1:8000');
  const enhanced = originalEnhanceMiddleware ? originalEnhanceMiddleware(metroMiddleware, server) : metroMiddleware;

  return (req, res, next) => {
    if (req.url && (req.url.startsWith('/api') || req.url.startsWith('/uploads') || req.url.startsWith('/health'))) {
      const incomingHeaders = { ...req.headers };
      if (!incomingHeaders.authorization && incomingHeaders.cookie) {
        const match = incomingHeaders.cookie.match(/traveo_token=([^;]+)/);
        if (match) {
          incomingHeaders.authorization = `Bearer ${decodeURIComponent(match[1])}`;
        }
      }
      if (!incomingHeaders.authorization && req.url && req.url.includes('_token=')) {
        const match = req.url.match(/_token=([^&]+)/);
        if (match) {
          incomingHeaders.authorization = `Bearer ${decodeURIComponent(match[1])}`;
        }
      }
      const opts = {
        hostname: backendTarget.hostname,
        port: backendTarget.port,
        path: req.url,
        method: req.method,
        headers: {
          ...incomingHeaders,
          host: `${backendTarget.hostname}:${backendTarget.port}`,
        },
      };
      const proxyReq = http.request(opts, (proxyRes) => {
        res.writeHead(proxyRes.statusCode, proxyRes.headers);
        proxyRes.pipe(res, { end: true });
      });
      proxyReq.on('error', (err) => {
        res.writeHead(502, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ error: 'Backend unreachable', details: String(err) }));
      });
      req.pipe(proxyReq, { end: true });
      return;
    }
    return enhanced(req, res, next);
  };
};

module.exports = config;
