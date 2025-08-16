@echo off
echo Testing Smart Invoice OCR API Endpoints
echo ======================================

echo.
echo 1. Testing Health Endpoint...
curl -s http://localhost:5000/health
echo.
echo.

echo 2. Testing Main Page...
curl -s http://localhost:5000/ | findstr /n ".*" | findstr "^1:"
echo.

echo 3. Testing Upload Endpoint (No File)...
curl -s -X POST http://localhost:5000/upload
echo.
echo.

echo 4. Testing OCR Test Page...
curl -s http://localhost:5000/ocr-test | findstr /n ".*" | findstr "^1:"
echo.

echo 5. Testing Cleanup Endpoint...
curl -s -X POST http://localhost:5000/cleanup
echo.
echo.

echo API Testing Complete!
pause
