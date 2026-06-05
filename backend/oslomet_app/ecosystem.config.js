module.exports = {
  apps: [
    {
      name: "oslomet-app",
      script: "/home/ubuntu/github_oslomet_f2026/backend/oslomet_app/.venv/bin/python",
      args: "-m uvicorn app.server:app --host 172.19.0.1 --port 9000 --workers 2",
      cwd: "/home/ubuntu/github_oslomet_f2026/backend/oslomet_app",
      exec_mode: "fork",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      out_file: "/home/ubuntu/github_oslomet_f2026/backend/oslomet_app/logs/fastapi-out.log",
      error_file: "/home/ubuntu/github_oslomet_f2026/backend/oslomet_app/logs/fastapi-error.log",
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      merge_logs: true,
      env: {
        PYTHONUNBUFFERED: "1",
        OSLOMET_ENV: "prod"
      }
    }
  ]
}
