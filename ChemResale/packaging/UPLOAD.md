# 工坊上传步骤（试剂可售）

> **当前状态（2026-11-25 13:20）**：包已打好（`dist/ReagentResale-v1.0.0.zip`），**尚未上传**。
> `.vdf` 里 `publishedfileid` 还是 `"0"`、`visibility "2"`（隐藏），首次上传后 SteamCMD 会把 id 写回。

## 1. 打包

```bash
bash ChemResale/scripts/package.sh
```

产物在 `dist/`：

| 文件 | 用途 |
|---|---|
| `ReagentResale-v1.0.0/` | 上传给 Steam 的 contentfolder（只含运行时文件：DLL / manifest / 640×360 preview / README） |
| `ReagentResale-v1.0.0.zip` | 给不在工坊下载的人手动安装 |
| `SHA256SUMS.txt` | 每个文件的校验和 |
| `harness.chem-resale.vdf` | SteamCMD 用的条目配置 |
| `workshop_description.txt` | 工坊描述全文（中文正文 + 英文附录），复制到 Steam 页面 |

脚本会自己跑：构建、画封面（`scripts/make_cover.py`，纯代码绘制）、干净组装、
校验（preview 必须 640×360 且 <1 MB、manifest 版本一致、DLL 里含 `CHEMICAL_SUPPLIES`、无禁用载荷）、
压 zip、算 sha256、写 vdf。

封面 1280×720 在 `mod/preview.png`，只通过 VDF 的 `previewfile` 上传，不进包——
工坊的 `file_size` 只统计 contentfolder。

## 2. 首次上传

1. `.vdf` 里 `publishedfileid` 保持 `"0"`、`visibility` 先 `"2"`（隐藏），传完在页面检查。
2. 运行 SteamCMD：

```bat
C:\steamcmd\steamcmd.exe +login <账号> +workshop_build_item "C:\Users\zszzl\Documents\deepseek-harness\default-workspace\ChemResale\dist\harness.chem-resale.vdf" +quit
```

3. 首次发布需要在浏览器里接受创意工坊协议。
4. 成功标志：`[AppID 4348910] Upload finished for workshop item <id> : OK`，
   以及 `Uploaded new workshop preview file ...`。
5. 把 id 记在这份文件里，然后 `package.sh` 会沿用它。

## 3. 上线前检查

- [ ] 页面描述 = `dist/workshop_description.txt` 全文（**手动粘贴**，SteamCMD 只传 vdf 里的短描述）
- [ ] 封面 = 1280×720 的 `mod/preview.png`
- [ ] 可见性改公开
- [ ] 本地装好 1.0.0 后重启游戏，确认模组列表显示 1.0.0 且能启用

## 4. 本地部署（开发用）

```bash
bash ChemResale/scripts/build.sh      # 需先关游戏（DLL 被占用）
python tools/trust_local.py --folder "/f/SteamLibrary/steamapps/common/Probably Stolen/Mods/ChemResale" --id harness.chem-resale --dll ChemResaleMod.dll
```

注意：本地 `Mods/ChemResale/` 只有 `manifest.xml` + DLL，所以 `folderHash` 是空列表的 SHA256
（`e3b0c442…`）——这是**正确值**，不是 bug；工坊下载的版本由 Steam 的完整性校验覆盖，不走这条。
