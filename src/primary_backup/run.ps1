# run servers in background
$bgServer = Read-Host -Prompt "Run servers in background? [hidden/ normal(default)]"

# list to store all pids
$pidList = @()

if ($bgServer -eq "hidden") {
    $bgServer = "hidden"
}
else {
    $bgServer = "normal"
}

Start-Process python "registry_server.py" -PassThru -WindowStyle $bgServer

# ask for number of servers to run
$numServers = Read-Host -Prompt "Enter number of servers to run"

# run servers
for ($i = 0; $i -lt $numServers; $i++) {
    # start server and add to pidlist using Start-Process python "server.py --port 1200$i" -PassThru -WindowStyle $bgServer
    $pidList += Start-Process python "server.py --port 1200$i" -PassThru -WindowStyle $bgServer
}

# Confirm launches
Write-Host "Servers launched"

# ask for number of clients to run
$numServers = Read-Host -Prompt "Enter number of clients to run"

# run clients
for ($i = 0; $i -lt $numServers; $i++) {
    $pidList += Start-Process python "client.py" -PassThru
}

$null = Read-Host -Prompt "Press Enter to kill all windows terminal instances"

# kill all processes
foreach ($pid_i in $pidList) {
    Stop-Process -Id $pid_i.Id
}