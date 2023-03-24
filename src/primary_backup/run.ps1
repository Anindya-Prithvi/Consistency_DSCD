Start-Process python "registry_server.py" -PassThru

# ask for number of servers to run
$numServers = Read-Host -Prompt "Enter number of servers to run"

# run servers
for ($i = 0; $i -lt $numServers; $i++) {
    Start-Process python "server.py --port 1200$i" -PassThru
}

# Confirm launches
Write-Host "Servers launched"

$null = Read-Host -Prompt "Press Enter to kill all windows terminal instances"
Stop-process -Name WindowsTerminal
