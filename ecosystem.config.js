module.exports = {
    apps: [
      {
        name: "landing_page",
        script: "npm",
        args: "run start",
        watch: false,
        cwd: "./landing_page",  
        env: {
          NODE_ENV: "production",
          PORT: 3000
        }
      },
      {
        name: "bank-back",
        script: "./venv/bin/python",
        args: "run_fast.py",
        cwd: "./backend",
        env: {
          PYTHONUNBUFFERED: "1"
        }
      },
      {
        name: "bank-front",
        script: "npm",
        args: "run dev",
        watch: false,
        cwd: "./frontend",
        env: {
          NODE_ENV: "development",
          PORT: 5173 
        }
      },
    ]
  }