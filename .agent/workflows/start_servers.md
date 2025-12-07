---
description: Start the FactBomb Fitting Room application (Full Stack)
---

To start the full application stack (Backend + Frontend) and open the browser:

// turbo
1. Run the auto-launcher script:
```powershell
.\start_app.bat
```
This script will automatically:
- Check/Create Python virtual environment
- Install dependencies
- Start the Backend server (uvicorn) in a new window
- Start the Frontend server (npm run dev) in a new window
- Open the application in the default browser

ALWAYS use this script to start the application unless specifically debugging a single component.
