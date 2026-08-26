# #region agent log
$logPath = "d:\TalentFlow_AI\.cursor\debug.log"
function Write-DebugLog($hypothesisId, $location, $message, $data) {
    $entry = @{
        id = "log_$(Get-Date -UFormat %s)_$hypothesisId"
        timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
        hypothesisId = $hypothesisId
        location = $location
        message = $message
        data = $data
        runId = "pre-fix"
    } | ConvertTo-Json -Compress
    Add-Content -Path $logPath -Value $entry -Encoding utf8
}
# #endregion

$py311 = "C:\Users\Acer\AppData\Local\Programs\Python\Python311\python.exe"
$py310 = "C:\Users\Acer\AppData\Local\Programs\Python\Python310\python.exe"
$storePy = "C:\Users\Acer\AppData\Local\Microsoft\WindowsApps\PythonSoftwareFoundation.Python.3.10_qbz5n2kfra8p0\python.exe"
$condaPy = "C:\Users\Acer\anaconda3\python.exe"

Write-DebugLog "H1" "debug_python_env.ps1:py311" "Python311 path exists" @{ exists = (Test-Path $py311); path = $py311 }
Write-DebugLog "H2" "debug_python_env.ps1:py310" "Python310 path exists" @{ exists = (Test-Path $py310); path = $py310 }
Write-DebugLog "H3" "debug_python_env.ps1:py-list" "py launcher default" @{ pyList = (py --list 2>&1 | Out-String).Trim() }
Write-DebugLog "H4" "debug_python_env.ps1:alternates" "Alternate interpreters" @{
    storeExists = (Test-Path $storePy)
    condaExists = (Test-Path $condaPy)
    pythonVersion = (python --version 2>&1 | Out-String).Trim()
}
try {
    py test_azure_conn.py 2>&1 | Out-Null
    $pyExit = $LASTEXITCODE
    $pyErr = $null
} catch {
    $pyExit = -1
    $pyErr = $_.Exception.Message
}
Write-DebugLog "H5" "debug_python_env.ps1:py-run" "py test_azure_conn.py result" @{ exitCode = $pyExit; error = $pyErr }
