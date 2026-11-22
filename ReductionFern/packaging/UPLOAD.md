# 工坊上传步骤（还原剂蕨）

> **当前状态（2026-11-22 23:22）**：已上架，条目 id **3844217940**，`visibility 0`（公开）。
> `dist/harness.reduction-fern.vdf` 里已经写死这两个值，`package.sh` 每次都会沿用——
> 更新时只要重跑打包 + 上传，不会新建条目、也不会把公开改回隐藏。
> 链接：https://steamcommunity.com/sharedfiles/filedetails/?id=3844217940

## 1. 打包

```bash
bash scripts/package.sh
```

产物在 `dist/`：

| 文件 | 用途 |
|---|---|
| `ReductionFern-v0.1.0/` | 上传给 Steam 的 contentfolder（只含运行时文件） |
| `ReductionFern-v0.1.0.zip` | 给不在工坊下载的人手动安装 |
| `SHA256SUMS.txt` | 每个文件的校验和 |
| `harness.reduction-fern.vdf` | SteamCMD 用的条目配置 |
| `workshop_description.txt` | 工坊描述全文（中文正文 + 英文附录），复制到 Steam 页面 |

脚本会自己跑：构建、重新生成封面（1280 全画质 + 640 小图）、语言包一致性检查、干净组装、校验（5 张精灵 / 2 个语言包 / 包内 preview 必须是 640×360 / manifest 列了 DLL / 无禁用载荷）、压 zip、算 sha256、写 vdf。

**关键一点**：工坊的 `file_size` 只统计 contentfolder，所以包内只放 640×360 的 `preview.png`（约 228 KB）；1280×720 全画质封面（约 711 KB）放在 `mod/preview.png`，只通过 VDF 的 `previewfile` 上传，不进包。这一条如果搞反，条目体积会从 246 KB 涨到 729 KB。

## 2. 首次上传

1. `.vdf` 里 `publishedfileid` 保持 `"0"`、`visibility` 先 `"2"`（私有），传完在页面检查。
2. 运行 SteamCMD：

```bat
C:\steamcmd\steamcmd.exe +login <账号> +workshop_build_item "C:\Users\zszzl\Documents\deepseek-harness\default-workspace\ReductionFern\dist\harness.reduction-fern.vdf" +quit
```

3. 首次发布需要在浏览器里接受创意工坊协议。
4. 成功标志：`[AppID 4348910] Upload finished for workshop item <id> : OK`。
5. 把 SteamCMD 打印的新 `publishedfileid` 填回 `.vdf`，以后更新同一个条目（脚本会自动沿用已有 id 和 visibility）。
6. 描述：把 `dist/workshop_description.txt` 全文粘进 Steam 页面（VDF 里的 `description` 只是短版，给列表页用）。
7. 检查页面没问题后，把 `visibility` 改成 `"0"` 重新上传（或用 `VIS_OVERRIDE=0 bash scripts/package.sh` 后再传）。

## 3. 更新流程（以后）

1. 改完代码/文案 → 改 `manifest.xml` 的 `ModVersion` → `bash scripts/package.sh`（`changenote` 用 `CHANGENOTEv0.1.1 ...` 覆盖）。
2. 传同一个 vdf（id 已固定）。
3. 别把 `.bak` 留在 `Mods/` 里，加载器会扫描重复 id。

## 4. 安全

- `C:\steamcmd\logs\console_log.txt` 会把 `+login<账号><密码>` 明文写进日志，事后要脱敏并考虑改密码。
- 上传前把 `dist/` 之外的东西都当草稿；只有 `ReductionFern-v0.1.0/` 里的内容会进包。
