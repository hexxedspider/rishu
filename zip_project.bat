@echo off
echo Creating project zip excluding .gitignore files...

for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value') do set datetime=%%i
set timestamp=%datetime:~0,8%_%datetime:~8,6%

if exist temp_zip rmdir /s /q temp_zip
mkdir temp_zip

copy "main.py" "temp_zip\" >nul
copy "requirements.txt" "temp_zip\" >nul
copy "status.json" "temp_zip\" >nul
copy "config.json.example" "temp_zip\" >nul
copy ".gitignore" "temp_zip\" >nul
xcopy "cogs" "temp_zip\cogs\" /E /I /H /Y >nul

powershell -command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('temp_zip', '%timestamp%_rishu.zip')}"
rmdir /s /q temp_zip

echo successful.