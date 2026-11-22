# 工坊上传步骤（奢侈品奥克莫吸注射器）

> **当前状态（2026-11-23 00:48）**：已上传，条目 id **3844271622**，`visibility 2`（隐藏）。
> SteamCMD 会把新 id 写回 `.vdf`，之后 `package.sh` 每次都会沿用这个 id 和可见性。
> 剩下两步：① 在页面粘贴 `dist/workshop_description.txt` 全文；② 改成公开（见 §2.7）。

## 1. 打包

```bash
bash scripts/package.sh
```

产物在 `dist/`：

| 文件 | 用途 |
|---|---|
| `LuxuryNomoreInjector-v1.0.0/` | 上传给 Steam 的 contentfolder（只含运行时文件） |
| `LuxuryNomoreInjector-v1.0.0.zip` | 给不在工坊下载的人手动安装 |
| `SHA256SUMS.txt` | 每个文件的校验和 |
| `harness.luxury-nomore-injector.vdf` | SteamCMD 用的条目配置 |
| `workshop_description.txt` | 工坊描述全文（中文正文 + 英文附录），复制到 Steam 页面 |

脚本会自己跑：构建、重出封面（1280 全画质 + 640 小图）、干净组装、
校验（包内 preview 必须是 640×360、manifest 列了 DLL、无禁用载荷）、压 zip、算 sha256、写 vdf。

**关键一点**：工坊的 `file_size` 只统计 contentfolder，所以包内只放 640×360 的 `preview.png`（约 238 KB）；
1280×720 全画质封面（约 718 KB）放在 `mod/preview.png`，只通过 VDF 的 `previewfile` 上传，不进包。

## 2. 首次上传

1. `.vdf` 里 `publishedfileid` 保持 `"0"`、`visibility` 先 `"2"`（隐藏），传完在页面检查。
2. 运行 SteamCMD：

```bat
C:\steamcmd\steamcmd.exe +login <账号> +workshop_build_item "C:\Users\zszzl\Documents\deepseek-harness\default-workspace\LuxuryNomoreInjector\dist\harness.luxury-nomore-injector.vdf" +quit
```

3. 首次发布需要在浏览器里接受创意工坊协议。
4. 成功标志：`[AppID 4348910] Upload finished for workshop item <id> : OK`，
   以及 `Uploaded new workshop preview file ...`。
5. SteamCMD 会把新 `publishedfileid` 写回 `.vdf`（本次是 **3844271622**），以后更新同一个条目。
6. 描述：把 `dist/workshop_description.txt` 全文粘进 Steam 页面
   （VDF 里的 `description` 只是短版，给列表页用）。
7. 检查页面没问题后，`VIS_OVERRIDE=0 bash scripts/package.sh` 再传一次，把可见性改成公开。

## 3. 更新流程（以后）

1. 改完代码/文案 → 改 `manifest.xml` 的 `ModVersion` → `bash scripts/package.sh`
   （`changenote` 用 `CHANGENOTE="v1.0.1 ..."` 覆盖）。
2. 传同一个 vdf（id 已固定）。
3. 改完价格/类型先想一下老存档：已有的注射器不会变，只有新的才是 350。

## 4. 安全

- `C:\steamcmd\logs\console_log.txt` 会把 `+login<账号><密码>` 明文写进日志，事后要脱敏并考虑改密码。
- 上传前把 `dist/` 之外的东西都当草稿；只有 `LuxuryNomoreInjector-v1.0.0/` 里的内容会进包。
