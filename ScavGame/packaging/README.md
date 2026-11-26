# Workshop upload

1. 先确认 `dist/ScavengerNotes/` 是最新构建：`manifest.xml`、`ScavArcade.dll`、`Localization/`、`Sounds/`、`preview.png`、`README.md`。
2. 首次发布用 `upload.vdf`，`publishedfileid` 保持 `"0"`，`visibility` 先设 `"2"`（私有），传完在 Steam 页面检查后再改公开。
3. 运行 SteamCMD，按提示登录并完成 Steam Guard：

```bat
C:\steamcmd\steamcmd.exe +login <你的账号> +workshop_build_item "C:\Users\zszzl\Documents\deepseek-harness\default-workspace\ScavGame\workshop\upload.vdf" +quit
```

4. 上传完成后，SteamCMD 会输出新的 `publishedfileid`。把它填回 `upload.vdf`，以后更新同一个条目。
5. 工坊描述用 `description_zh.bbcode` / `description_en.bbcode` 里的内容粘贴；VDF 里的 `description` 只是短版。
6. 预览图 `dist/ScavengerNotes/preview.png` 是 1280x720、约 345 KB，低于 Steam 的 1 MB 限制。

注意：`contentfolder` 里的内容会整包上传；不要把 `art/`、`build/`、`.bak` 带进去。
