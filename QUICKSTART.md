# Quick Start Guide

This guide will help you get Contract OS Simple up and running in 10 minutes.

## Step 1: Prerequisites

Ensure you have:
- Python 3.11+ installed
- Node.js 18+ installed
- A ZhipuAI API key ([Get one here](https://open.bigmodel.cn/))

## Step 2: Backend Setup (3 minutes)

```bash
# Navigate to project
cd /Users/robin/project/contract_os_simple

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
cd server
pip install -r requirements.txt

# Configure environment
cp ../.env.example ../.env
# Edit .env and add your ZHIPU_API_KEY
nano ../.env  # or use your preferred editor

# Initialize database
cd ..
python scripts/init_db.py

# Seed sample KB data (optional)
python scripts/seed_kb.py

# Start backend
cd server
python main.py
```

Backend will run on `http://localhost:8000`

## Step 3: Frontend Setup (2 minutes)

Open a new terminal:

```bash
# Copy frontend from original project
cp -r /Users/robin/project/contract_os/client /Users/robin/project/contract_os_simple/client

# Navigate to client
cd /Users/robin/project/contract_os_simple/client

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend will run on `http://localhost:5173`

## Step 4: Test the System (5 minutes)

1. **Open the UI**: Navigate to `http://localhost:5173`

2. **Create a Knowledge Base Collection**:
   - Go to KB Admin page
   - Create a new collection (e.g., "Contract Regulations")
   - Upload a sample document (TXT/PDF/DOCX)

3. **Upload a Contract**:
   - Go to Contracts page
   - Create a new contract
   - Upload a contract file (PDF/DOCX)

4. **Create a Precheck Task**:
   - Go to New Task page
   - Select the contract version
   - Select KB collections
   - Submit task

5. **Monitor Progress**:
   - Go to Processing page
   - Watch the task progress through 8 stages
   - View event logs

6. **Review Results**:
   - Go to Results page
   - View identified risks
   - Check evidence and KB citations
   - Generate report

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check .env file
cat ../.env  # Verify ZHIPU_API_KEY is set
```

### Frontend can't connect to backend

```bash
# Check backend is running
curl http://localhost:8000/api/health

# Check CORS settings in .env
grep CORS_ORIGINS ../.env
```

### Task fails during processing

Check the logs in the UI or database:
```bash
# View task events
sqlite3 data/database.db "SELECT * FROM task_events ORDER BY ts DESC LIMIT 10;"
```

### Database errors

```bash
# Reinitialize database
rm data/database.db
python scripts/init_db.py
python scripts/seed_kb.py
```

## Next Steps

- Customize the risk detection rules in `server/agents/stub_agents.py`
- Adjust LLM prompts in `server/agents/llm_risk_agent.py`
- Add more KB documents for better context
- Configure concurrency settings in `.env`

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Stopping the System

```bash
# Stop backend: Ctrl+C in terminal

# Stop frontend: Ctrl+C in terminal

# Deactivate virtual environment
deactivate
```

## Production Deployment

For production deployment:

1. Use a production WSGI server:
   ```bash
   pip install gunicorn
   gunicorn server.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. Set up a reverse proxy (nginx)

3. Configure proper CORS origins

4. Use environment-specific `.env` file

5. Set up logging and monitoring

See [README.md](./README.md) for more details.
