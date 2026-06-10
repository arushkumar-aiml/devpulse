@echo off
REM ================================================================
REM  DevPulse — Full Project Setup for Windows CMD
REM  Run this ONCE from any folder. It creates devpulse\ next to it.
REM ================================================================

echo [1/6] Creating folder structure...

mkdir devpulse
cd devpulse

mkdir .github
mkdir .github\workflows
mkdir agent
mkdir modules
mkdir frontend
mkdir frontend\public
mkdir frontend\src
mkdir frontend\src\components
mkdir tests

REM Empty init files
type nul > agent\__init__.py
type nul > modules\__init__.py

echo [2/6] Initialising Git repo...

git init
git branch -M main

REM ── Global identity (repo-level default = Arush as project lead) ──
git config user.name "arushkumar-aiml"
git config user.email "arush@devpulse.dev"

echo [3/6] Creating placeholder files so git has something to commit...

REM Root files
type nul > .env.example
type nul > .gitignore
type nul > requirements.txt
type nul > README.md
type nul > LICENSE

REM Agent files
type nul > agent\main.py
type nul > agent\server.py

REM Module files
type nul > modules\contribution_analyzer.py
type nul > modules\standup_generator.py
type nul > modules\blocker_detection.py
type nul > modules\action_executor.py

REM Test files
type nul > tests\test_contribution_analyzer.py
type nul > tests\test_standup_generator.py
type nul > tests\test_blocker_detection.py
type nul > tests\test_action_executor.py

REM Frontend files
type nul > frontend\index.html
type nul > frontend\package.json
type nul > frontend\vite.config.js
type nul > frontend\src\App.jsx
type nul > frontend\src\main.jsx
type nul > frontend\src\index.css
type nul > frontend\src\components\ActivityFeed.jsx
type nul > frontend\src\components\BlockerList.jsx
type nul > frontend\src\components\StandupReport.jsx
type nul > frontend\src\components\ActionButton.jsx
type nul > .github\workflows\deploy.yml

echo [4/6] Done! All files created.
echo.
echo  Next: paste actual code into each file (see steps 4-13),
echo  then follow the PER-MEMBER commit instructions below.
echo.
echo [5/6] Setting remote origin...
echo  Replace YOUR_PAT and YOUR_USERNAME below, then run manually:
echo.
echo   git remote add origin https://YOUR_PAT@github.com/YOUR_USERNAME/devpulse.git
echo.
echo [6/6] Setup complete. See COMMIT_GUIDE.txt for per-member commits.
