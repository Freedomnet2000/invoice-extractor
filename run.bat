@echo off
cd /d "%~dp0"
if not exist .env copy .env.example .env
echo Building image...
docker build -t invoice-extractor . || goto :error
docker rm -f invoice-extractor >nul 2>&1
echo Starting container...
docker run -d --name invoice-extractor --env-file .env -p 8000:8000 invoice-extractor || goto :error
echo.
echo Running at http://localhost:8000  (API docs: http://localhost:8000/docs)
start http://localhost:8000
pause
exit /b 0
:error
echo.
echo Failed. Is Docker Desktop running?
pause
exit /b 1
