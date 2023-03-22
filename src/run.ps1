$registrar = Start-Process python "registry_server.py" -PassThru
$s1 = Start-Process python "community_server.py Venti 12000" -PassThru
$s2 = Start-Process python "community_server.py Raiden-Shogun 12001" -PassThru
$s3 = Start-Process python "community_server.py Zhongli 12002" -PassThru
$client = Start-Process python "grpc_client.py" -PassThru

# get keyboard interrupt
$null = Read-Host -Prompt "Press Enter to stop"

Stop-Process -Id $registrar.Id
Stop-Process -Id $s1.Id
Stop-Process -Id $s2.Id
Stop-Process -Id $s3.Id
Stop-Process -Id $client.Id

$null = Read-Host -Prompt "Press Enter to kill all windows terminal instances"
Stop-process -Name WindowsTerminal
