# PowerShell 行为探针：同一份脚本在 5.1 和 7.x 下各跑一次，用来看哪些坑被修好了。
#
#   pwsh -NoProfile -File tools/ps_probe.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File tools/ps_probe.ps1
#
# 注意：Windows PowerShell 5.1 的默认执行策略是 Restricted，不加 -ExecutionPolicy Bypass 直接拒跑
# （这本身也是一条差异，见 BUILDING.md §10）。
$ErrorActionPreference = 'Continue'
$root = "C:\Users\zszzl\Documents\deepseek-harness\default-workspace"

"ps_version=" + $PSVersionTable.PSVersion.ToString()
"execution_policy=" + (Get-ExecutionPolicy)
"outputencoding=" + $OutputEncoding.WebName
"console_out=" + [Console]::OutputEncoding.WebName

# 1) curl 是别名还是真程序（5.1: Invoke-WebRequest 别名，-s/-X 全不认；7.x: 真 curl.exe）
$c = Get-Command curl -ErrorAction SilentlyContinue
"curl_type=" + $(if ($c) { $c.CommandType } else { "missing" })

# 2) Compress-Archive 能否直接调用（5.1 靠自动加载模块，PSModulePath 混入 PS7 时会失败）
$z = Get-Command Compress-Archive -ErrorAction SilentlyContinue
"compress_archive=" + $(if ($z) { "present" } else { "missing" })

# 3) 读无 BOM 的 UTF-8 中文文件（5.1 默认按 ANSI 解 -> 乱码；7.x 默认 UTF-8）
$tmpdir = [System.IO.Path]::GetTempPath(); if (-not $tmpdir) { $tmpdir = "$root\" }; $cn = Join-Path $tmpdir "ps_probe_cn.txt"
[System.IO.File]::WriteAllBytes($cn, [System.Text.Encoding]::UTF8.GetBytes("试剂可售 中文测试"))
$read = Get-Content $cn -ErrorAction SilentlyContinue
"utf8_read_ok=" + [bool]($read -and $read -match "试剂可售")
Remove-Item $cn -ErrorAction SilentlyContinue

# 4) 当前目录里的程序能否按名字直接调用（两版都不搜 cwd）
$cmd = "$root\tmp_probe_hello.cmd"
Set-Content -Path $cmd -Value "@echo hello-cwd" -Encoding Ascii
"cwd_direct_lookup=" + $(if (Get-Command tmp_probe_hello -ErrorAction SilentlyContinue) { "found" } else { "not-found" })
"cwd_dot_prefix=" + $(if (Get-Command ".\tmp_probe_hello.cmd" -ErrorAction SilentlyContinue) { "found" } else { "not-found" })
Remove-Item $cmd -ErrorAction SilentlyContinue

# 5) MSYS 路径（/c/...）认不认
"msys_path=" + $(if (Test-Path "/c/Windows") { "ok" } else { "not-found" })
"win_path=" + $(if (Test-Path "C:/Windows") { "ok" } else { "not-found" })

