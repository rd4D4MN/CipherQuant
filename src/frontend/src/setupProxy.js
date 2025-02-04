const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Health check endpoint
  app.get('/api/health', (req, res) => {
    fetch('http://localhost:5000/api/health')
      .then(response => response.json())
      .then(data => res.json(data))
      .catch(error => {
        console.error('Health check failed:', error);
        res.status(503).json({
          status: 'unhealthy',
          error: error.message
        });
      });
  });

  const apiProxy = createProxyMiddleware({
    target: 'http://localhost:5000',
    changeOrigin: true,
    secure: false,
    ws: false, // Disable WebSocket
    logLevel: 'debug',
    timeout: 30000,  // 30 second timeout
    proxyTimeout: 30000,  // 30 second proxy timeout
    onError: (err, req, res) => {
      console.error('Proxy Error:', {
        error: err.message,
        url: req.url,
        method: req.method,
        headers: req.headers
      });

      // Check if backend is running
      fetch('http://localhost:5000/api/health')
        .then(response => response.json())
        .then(health => {
          console.log('Backend health check:', health);
          res.writeHead(503, {
            'Content-Type': 'application/json'
          });
          res.end(JSON.stringify({
            error: 'Backend Connection Error',
            message: 'Could not connect to the backend server.',
            details: err.message,
            health: health,
            url: req.url,
            method: req.method
          }));
        })
        .catch(healthError => {
          console.error('Backend health check failed:', healthError);
          res.writeHead(503, {
            'Content-Type': 'application/json'
          });
          res.end(JSON.stringify({
            error: 'Backend Connection Error',
            message: 'Backend server is not responding.',
            details: err.message,
            healthError: healthError.message,
            url: req.url,
            method: req.method
          }));
        });
    },
    onProxyReq: (proxyReq, req, res) => {
      console.log('Proxying request:', {
        url: req.url,
        method: req.method,
        headers: req.headers,
        query: req.query
      });
    },
    onProxyRes: (proxyRes, req, res) => {
      console.log('Received response:', {
        statusCode: proxyRes.statusCode,
        url: req.url,
        headers: proxyRes.headers
      });

      // Add CORS headers
      proxyRes.headers['Access-Control-Allow-Origin'] = '*';
      proxyRes.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
      proxyRes.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization';
    },
    pathRewrite: {
      '^/api': '/api'
    }
  });

  // Use the proxy middleware for /api routes
  app.use('/api', apiProxy);

  // Add OPTIONS handling for CORS preflight requests
  app.options('/api/*', (req, res) => {
    console.log('Handling OPTIONS request:', req.url);
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    res.sendStatus(200);
  });

  // Log all requests
  app.use((req, res, next) => {
    console.log('Request:', {
      method: req.method,
      url: req.url,
      query: req.query,
      headers: req.headers
    });
    next();
  });
}; 