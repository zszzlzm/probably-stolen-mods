# 工坊上传步骤（奢侈品奥克莫吸注射器）

> **当前状态（2026-11-27 11:00）**：条目 id **3844271622**，**已公开**（`visibility 0`，Steam API 实查），
> 最新上传 v1.1.0（加价倍数改成设置）。
> **注意**：仓库里的 `.vdf` 仍是首次发布时写的 `visibility 2`，`package.sh` 会沿用旧值——
> 直接打包上传会把已经公开的条目改回隐藏。**每次打包都要带 `VIS_OVERRIDE=0`**。

## 1. 打包

```bash
VIS_OVERRIDE=0 CHANGENOTE="v1.1.0：加价倍数改成设置（1–10 倍，默认 4 倍）。" bash scripts/package.sh
```

产物在 `dist/`：

| 文件 | 用途 |
|---|---|
| `LuxuryNomoreInjector-v<版本>/` | 上传给 Steam 的 contentfolder（只含运行时文件） |
| `LuxuryNomoreInjector-v<版本>.zip` | 给不在工坊下载的人手动安装 |
| `SHA256SUMS.txt` | 每个文件的校验和 |
| `harness.luxury-nomore-injector.vdf` | SteamCMD 用的条目配置 |
| `workshop_description.txt` | 工坊描述全文（中文正文 + 英文附录），1.1.0 起由 `package.sh` 自动写进 vdf |

脚本会自己跑：构建、重出封面（1280 全画质 + 640 小图）、干净组装、
校验（包内 preview 必须是 640×360、manifest 列了 DLL、`Localization/*.csv` 两份且含 `config.multiplier`、无禁用载荷）、
压 zip、算 sha256、写 vdf。

**关键一点**：工坊的 `file_size` 只统计 contentfolder，所以包内只放 640×360 的 `preview.png`（约 238 KB）；
1280×720 全画质封面（约 718 KB）放在 `mod/preview.png`，只通过 VDF 的 `previewfile` 上传，不进包。

## 2. 上传 / 更新

```bat
C:\steamcmd\steamcmd.exe +login <账号> +workshop_build_item "C:\Users\zszzl\Documents\deepseek-harness\default-workspace\LuxuryNomoreInjector\dist\harness.luxury-nomore-injector.vdf" +quit
```

成功标志：`Committing update...Success`，以及 `Uploading preview image...`。

验证（不用开页面）：

```powershell
$b = @{ itemcount = 1; "publishedfileids[0]" = "3844271622" }
(Invoke-RestMethod "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/" -Method Post -Body $b).response.publishedfiledetails[0] |
  Select-Object title, visibility, time_updated, file_size
```

`visibility` 必须是 `0`；`time_updated` 应该是刚上传的时间。

## 3. 描述

1.1.0 起 `package.sh` 把 `packaging/workshop_description.txt` 全文写进 vdf 的 `description` 字段，
**不用再手动粘贴**。源文件里禁止 ASCII 双引号（KeyValues 无法转义，会整份解析失败），
需要引号的地方用「」。改完重新打包上传即可。

## 4. 更新流程

1. 改代码/文案 → 改 `mod/manifest.xml` 的 `ModVersion` → `VIS_OVERRIDE=0 CHANGENOTE="..." bash scripts/package.sh`
2. 传同一个 vdf（id 已固定）
3. `bash scripts/build.sh` 部署到本地 `Mods/LuxuryNomoreInjector`，然后重签信任：
   `python tools/trust_local.py --folder "<游戏>/Mods/LuxuryNomoreInjector" --id harness.luxury-nomore-injector --dll LuxuryNomoreInjectorMod.dll`

## 5. 老存档

价格存在物品实例上：已经造出来的注射器不会跟着新倍率变，只有新生成/新合成的才按当前倍数计价。
这条要写进更新说明，免得玩家以为设置没生效。

## 6. 安全

- `C:\steamcmd\logs\console_log.txt` 会把账号名写进日志，外发前脱敏。
- 上传前把 `dist/` 之外的东西都当草稿；只有 `LuxuryNomoreInjector-v<版本>/` 里的内容会进包。
