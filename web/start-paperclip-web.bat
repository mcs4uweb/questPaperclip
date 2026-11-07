@echo off
cd /d C:\Projects\paperclip-app\web
echo Starting Quest Paperclip web (pnpm run start) on port 3003
echo Run "pnpm run build" first if .next is missing.
pnpm run start
if errorlevel 1 pause
