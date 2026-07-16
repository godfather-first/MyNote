$ErrorActionPreference = "Stop"

$vboxManage = "C:\Program Files\VBoxManage.exe"
$baseDir = "D:\A-downloads\Software\Trae-English\workplace\first-3"
$vmRoot = "D:\VirtualBox VMs"
$assetsDir = Join-Path $baseDir "vm-assets"
$isoPath = Join-Path $assetsDir "ubuntu-24.04.4-live-server-amd64.iso"
$isoUrls = @(
    "https://mirrors.tuna.tsinghua.edu.cn/ubuntu-releases/24.04/ubuntu-24.04.4-live-server-amd64.iso",
    "https://mirrors.ustc.edu.cn/ubuntu-releases/24.04/ubuntu-24.04.4-live-server-amd64.iso",
    "https://mirrors.aliyun.com/ubuntu-releases/24.04/ubuntu-24.04.4-live-server-amd64.iso",
    "https://releases.ubuntu.com/noble/ubuntu-24.04.4-live-server-amd64.iso"
)
$expectedIsoSize = 3405469696
$vmName = "MyNote-Ubuntu-Builder"
$diskPath = Join-Path $vmRoot "$vmName\$vmName.vdi"

if (!(Test-Path $vboxManage)) {
    throw "VBoxManage not found at $vboxManage"
}

New-Item -ItemType Directory -Force -Path $vmRoot, $assetsDir | Out-Null
& $vboxManage setproperty machinefolder $vmRoot

Write-Host "Downloading Ubuntu ISO to D drive. This resumes if a partial file exists."
foreach ($isoUrl in $isoUrls) {
    Write-Host "Trying: $isoUrl"
    if (Test-Path $isoPath) {
        curl.exe -L -C - --fail --progress-bar -o $isoPath $isoUrl
    } else {
        curl.exe -L --fail --progress-bar -o $isoPath $isoUrl
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Download failed, trying next mirror..."
        continue
    }

    $actualIsoSize = (Get-Item $isoPath).Length
    if ($actualIsoSize -ge $expectedIsoSize) {
        break
    }

    Write-Host "ISO is still incomplete: $actualIsoSize / $expectedIsoSize bytes"
}

$actualIsoSize = (Get-Item $isoPath).Length
if ($actualIsoSize -lt $expectedIsoSize) {
    throw "Ubuntu ISO is incomplete: $actualIsoSize / $expectedIsoSize bytes. Run this script again or download the ISO manually."
}

Write-Host "Creating VirtualBox VM on D drive..."
$existingVm = & $vboxManage list vms | Select-String "`"$vmName`""
if (-not $existingVm) {
    & $vboxManage createvm --name $vmName --ostype Ubuntu_64 --register --basefolder $vmRoot
    & $vboxManage modifyvm $vmName --memory 4096 --cpus 4 --vram 32 --graphicscontroller vmsvga --nic1 nat --audio none
    & $vboxManage createhd --filename $diskPath --size 61440 --format VDI
    & $vboxManage storagectl $vmName --name "SATA" --add sata --controller IntelAhci
    & $vboxManage storageattach $vmName --storagectl "SATA" --port 0 --device 0 --type hdd --medium $diskPath
    & $vboxManage storageattach $vmName --storagectl "SATA" --port 1 --device 0 --type dvddrive --medium $isoPath
    & $vboxManage sharedfolder add $vmName --name "first-3" --hostpath $baseDir --automount
} else {
    Write-Host "VM already exists: $vmName"
}

Write-Host ""
Write-Host "Done. Start the VM in VirtualBox and install Ubuntu to the virtual disk."
Write-Host "VM name: $vmName"
Write-Host "VM folder: $vmRoot"
Write-Host "Project path inside Ubuntu after shared folder/manual copy:"
Write-Host "  /media/sf_first-3/MyNote  or  ~/MyNote"
