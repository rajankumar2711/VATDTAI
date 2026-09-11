param(
    [double]$Hours = 6,
    [string]$StopFile = "$PSScriptRoot\..\reports\keep_awake.stop"
)

Add-Type -AssemblyName System.Windows.Forms

$sig = @'
[DllImport("kernel32.dll", SetLastError=true)]
public static extern uint SetThreadExecutionState(uint esFlags);
'@
$power = Add-Type -MemberDefinition $sig -Name PowerUtil -Namespace Win32 -PassThru

$ES_CONTINUOUS       = [uint32]"0x80000000"
$ES_SYSTEM_REQUIRED  = [uint32]"0x00000001"
$ES_DISPLAY_REQUIRED = [uint32]"0x00000002"

if (Test-Path $StopFile) { Remove-Item $StopFile -Force -ErrorAction SilentlyContinue }

$deadline = (Get-Date).AddHours($Hours)
Write-Output ("[keep_awake] Active until {0}. Create '{1}' to stop early." -f $deadline, $StopFile)

while ((Get-Date) -lt $deadline) {
    if (Test-Path $StopFile) { Write-Output "[keep_awake] Stop file detected, exiting."; break }
    $power::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED) | Out-Null
    try { [System.Windows.Forms.SendKeys]::SendWait('{F15}') } catch {}
    Start-Sleep -Seconds 50
}

$power::SetThreadExecutionState($ES_CONTINUOUS) | Out-Null
Write-Output "[keep_awake] Released. System may sleep/lock normally now."
