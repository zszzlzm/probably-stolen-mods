# 工坊上传步骤（试剂可售）

> **当前状态（2026-11-25 13:22）**：**已发布** →
> <https://steamcommunity.com/sharedfiles/filedetails/?id=3845593063>（公开，`visibility 0`）。
> 1.0.0 已上线，长描述与封面都由 vdf 自动写入，无需再手动粘贴。

## 0. 已发布条目

| 项 | 值 |
|---|---|
| publishedfileid | `3845593063` |
| 页面 | <https://steamcommunity.com/sharedfiles/filedetails/?id=3845593063> |
| 可见性 | `0` 公开（先在 `2` 隐藏状态传过一次，确认后改公开） |
| file_size | 90764 = contentfolder 四个文件之和 |
| 封面 | 1280×720 `mod/preview.png`（`previewfile`，不进包） |

发布后回查（匿名 GET 即可，公开条目）：

```bash
curl -s -X POST "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/" \
  -d "itemcount=1&publishedfileids[0]=3845593063" | grep -o '"visibility":[0-9]*'
```


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
4. **SteamCMD 会把新 id 直接写回 `.vdf`**（不用手抄）；`package.sh` 之后会沿用它。
5. 成功标志：`Committing update...Success.`，退出码 0。

> **坑：KeyValues 没有转义。** 长描述整个塞进 vdf 的 `description` 字段时，值里出现
> ASCII 双引号（`"`）会让 KeyValues 提前截断字符串，报
> `Bad expression token` / `key name too long` / `Failed to parse build config file`。
> 所以 `packaging/workshop_description.txt` 里禁止 ASCII 引号，一律用中文引号 `“ ”`
> （`package.sh` 会检查，命中就报错退出）。反斜杠是字面量、不用转义，换行在值里合法。
> 顺带一个环境坑：中文 Windows 上 Python 的 stdout 默认 GBK，`−90%` 这类字符会
> `UnicodeEncodeError`，`package.sh` 里统一 `export PYTHONIOENCODING=utf-8`。

## 3. 上线前检查

- [x] 页面描述 = `dist/workshop_description.txt` 全文（**已由 vdf 自动写入**，回查见上面 `curl`）
- [x] 封面 = 1280×720 的 `mod/preview.png`
- [x] 可见性改公开
- [ ] 本地装好 1.0.0 后重启游戏，确认模组列表显示 1.0.0 且能启用


## 4. 本地部署（开发用）

```bash
bash ChemResale/scripts/build.sh      # 需先关游戏（DLL 被占用）
python tools/trust_local.py --folder "/f/SteamLibrary/steamapps/common/Probably Stolen/Mods/ChemResale" --id harness.chem-resale --dll ChemResaleMod.dll
```

注意：本地 `Mods/ChemResale/` 只有 `manifest.xml` + DLL，所以 `folderHash` 是空列表的 SHA256
（`e3b0c442…`）——这是**正确值**，不是 bug；工坊下载的版本由 Steam 的完整性校验覆盖，不走这条。
