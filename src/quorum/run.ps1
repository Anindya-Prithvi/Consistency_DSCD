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

# ask for read replicas
$readServers = Read-Host -Prompt "Enter number of read replicas"

# ask for write replicas
$writeServers = Read-Host -Prompt "Enter number of write replicas"

# ask for total replicas
$numServers = Read-Host -Prompt "Enter total number of replicas"

$pidList += Start-Process python "quorum_registry.py --n $numServers --nr $readServers --nw $writeServers" -PassThru -WindowStyle $bgServer

# run servers
for ($i = 0; $i -lt $numServers; $i++) {
    # start server and add to pidlist using Start-Process python "server.py --port 1200$i" -PassThru -WindowStyle $bgServer
    $pidList += Start-Process python "quorum_replica.py --port 1200$i" -PassThru -WindowStyle $bgServer
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
