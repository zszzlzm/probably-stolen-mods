# 工坊上传步骤（滤芯打印机）

> **当前状态（2026-11-25 23:45）**：条目 id **3840097356**，`visibility 0`（公开）。
> v1.1.0 已上传；**v1.1.1 已打包、已本地部署，待游戏内确认后上传**（见 §5）。
> SteamCMD 会把 id 写回 `.vdf`，之后 `package.sh` 每次都会沿用这个 id 和可见性。
> 从 v1.1.1 起，工坊长描述也由 `package.sh` 写进 vdf 的 `description` 字段，不用再手动粘贴。

## 1. 打包

```bash
CHANGENOTE="v1.1.1：修老存档里机器显示成「？」问号图的问题。" bash scripts/package.sh
```

产物在 `dist/`：

| 文件 | 用途 |
|---|---|
| `FilterPrinter-v1.1.0/` | 上传给 Steam 的 contentfolder（dll、manifest、语言包、preview、Textures） |
| `FilterPrinter-v1.1.0.zip` | 给不在工坊下载的人手动安装 |
| `SHA256SUMS.txt` | 每个文件的校验和 |
| `harness.filter-printer.vdf` | SteamCMD 用的条目配置 |
| `workshop_description.txt` | 工坊描述全文（中文正文 + 英文附录） |

脚本会自己跑：构建、重出封面（1280×720）、干净组装、校验、压 zip、算 sha256、写 vdf。
校验里新增两项：`Textures/Items/fp_printer.png` 必须是 48×48 RGBA；DLL 里必须真的引用了
`fp_printer` 这个 sprite key（.NET 字符串是 UTF-16，用 python 按 UTF-16LE 查，别用 grep）。

## 2. 上传

```bash
"C:/steamcmd/steamcmd.exe" +login zszzlzm +workshop_build_item \
  "C:/Users/zszzl/Documents/deepseek-harness/default-workspace/FilterPrinter/dist/harness.filter-printer.vdf" +quit
```

看到 `Upload finished ... : OK` 即成功。日志里有账号名，提交前别把日志原样贴进仓库。

## 3. v1.1.0：为什么现在才有专用贴图

1.0.x 直接借用原版 3D 打印机的贴图（`Items/items_tool2` / `printer_off`），占位相同（48×48 = 16px 网格的
3×3），所以同一个存档里两台机器长得一模一样，玩家分不清哪台是原版、哪台是这个模组。

v1.1.0 起改用模组自带贴图：

| 项 | 做法 |
|---|---|
| 文件 | `mod/Textures/Items/fp_printer.png`，48×48 RGBA，全不透明 |
| 游戏内加载 | 游戏原生支持 `Textures/Items/*.png`，以文件名作为 sprite key，point 过滤、无 mipmap |
| 代码 | `GameItem.SetSpriteAndShapeFromMod(ModId, "fp_printer")`；找不到时回退原版 `printer_off` |
| 旧存档 | 存档按物品记录 `spriteAtlasPath`/`spritePath`，所以在 `onLoaded` 里把旧机器的贴图就地改成新贴图 |
| 占位 | 依旧 3×3 格（9 个格心都不透明），商店摆放不受影响 |
| 美术 | 布局来自 Qwen-Image 概念图（`refs/gen/machine_s22.png`），最终像素图按原版机器调色板和 16px 网格手工重画（`scripts/make_machine_sprite.py`，可复现） |

调色板全部取自原版 `items_tool2`：`#292234` 描边、`#5F6868` 机身、`#D5D2B8` 米色滤芯、
`#275654`/`#45918B` 青绿饰条、`#4B5B5D` 玻璃、`#3D823F`/`#9F526D`/`#D5A54A` 指示灯。

## 4. 本地部署与信任

```bash
bash scripts/build.sh      # 构建 + 部署到 <游戏>/Mods/FilterPrinter（含 Textures）
python tools/trust_local.py --folder "<游戏>/Mods/FilterPrinter" \
  --id harness.filter-printer --dll FilterPrinterMod.dll
```

**加文件会改 folderHash**：v1.1.0 新增了 `Textures/Items/fp_printer.png`，不重新跑 trust 脚本，
游戏会以「文件指纹不符」拒绝加载这个模组。部署和信任都要在游戏关闭时做（DLL 被占用）。

## 5. v1.1.1：老存档里的机器显示成「？」问号图

**症状**：1.0.x 时代存档里留下的那台打印机，图标和工具提示里的图变成一个紫色「？」。
`Player.log` 里恰好一条：

```
Mod sprite 'printer_off' from mod 'Items/items_tool2' not found. Loading dummy sprite.
```

**这条日志就是判据**：`GameItemElement.ResolveSpriteByName`（`GameItemElement.cs:222-232`）只会在
`useSpriteFromMod == true` 时走这个分支，并且把 `spriteAtlasPath` 当成 **mod id** 去查。它说
mod 叫 `Items/items_tool2` —— 一个原版图集路径 —— 说明物品处在「标志说用 mod 贴图、路径却是原版值」
这种自相矛盾的状态，查不到就画 `RenderHandler.unknownSprite`（`Items/itematlas` 里的 `unknown`，
正是那张问号图）。

**为什么会出现**：读档顺序是 `SaveManager.cs:182`

1. `DirectoryMaster.Item(id)` 先跑我们的工厂 → `SetSpriteAndShapeFromMod` 成功，标志置 true；
2. 紧接着 `GameItem.SetSprite(saved.atlas, saved.path)` 用存档里的值把两个路径覆盖掉，
   **但不清 `useSpriteFromMod`**；
3. v1.0.x 存档里存的是原版 `Items/items_tool2` / `printer_off` → 状态自相矛盾；
4. `onLoaded` 里我们的修复被 `if (item.useSpriteFromMod) return;` 挡住 —— 这个守卫恰好只在
   「不需要修」的情况下放行，在真正需要修的时候跳过。

**修法**（`src/FilterPrinterMachine.cs` 的 `RepointSprite`）：

- 判据从「`useSpriteFromMod` 是否为真」改成「标志 + `spriteAtlasPath == ModId` + `spritePath == fp_printer` 三者同时成立」才跳过；
- 走原版兜底（安装里没有 PNG）时显式 `item.useSpriteFromMod = false`，否则原版路径会继续被当 mod id 查，
  问号图依旧；
- 工厂里也复用这一个函数，创建和读档只有一条代码路径。

**教训**：`useSpriteFromMod` 是个**不可信的缓存**——它只有一个写入点（`GameItem.cs:396`），
且从不被 `SetSprite` / `SetSpriteAndShape` 清掉。任何「已设置过就别再设」的守卫都要连路径一起验证。
