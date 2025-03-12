module.exports = {
    apps: [
      {
        name: 'stock-express-api',
        script: 'server/src/app.js',
        env: {
          PORT: 3001,
          FASTAPI_URL: 'http://localhost:8000',
          NODE_ENV: 'production'
        },
        autorestart: true,
        time: true
      },
      {
        name: 'stock-fastapi',
        script: 'uvicorn',
        args: 'app:app --host 0.0.0.0 --port 8000',
        cwd: './api/',
        interpreter: '/home/ubuntu/project/stock-alert-backend/api/venv/bin/python',
        autorestart: true,
        time: true
      }
    ]
  };