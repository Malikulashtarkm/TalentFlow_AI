@echo off
set mode=%~1
set zip=%~2
set entry=%~3
if "%mode%"=="-Z1" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[System.IO.Compression.ZipFile]::OpenRead($env:zip); try { foreach($entry in $zip.Entries){ $entry.FullName -replace '\\','/' } } finally { $zip.Dispose() }"
  exit /b %ERRORLEVEL%
)
if "%mode%"=="-p" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; $zip=[System.IO.Compression.ZipFile]::OpenRead($env:zip); try { $entry=$zip.GetEntry($env:entry); if($null -eq $entry){ exit 11 }; $stream=$entry.Open(); try { $stdout=[Console]::OpenStandardOutput(); $stream.CopyTo($stdout) } finally { $stream.Dispose() } } finally { $zip.Dispose() }"
  exit /b %ERRORLEVEL%
)
echo Unsupported unzip arguments: %*
exit /b 2
