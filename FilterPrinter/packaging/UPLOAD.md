# 工坊上传步骤（滤芯打印机）

> **当前状态（2026-11-26 18:00）**：条目 id **3840097356**，`visibility 0`（公开），**v1.1.2 已打包、待上传**。
> v1.1.1 修了两件事：老存档的机器显示成「？」（§5），以及贴图背景不透明导致的黑色边框（§6）。
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

## 6. v1.1.1 追加：贴图四周的黑色边框

**症状**：1.1.0 的机器图标外面一圈纯黑，像贴了张黑底图片。

**原因在我自己写的手册里**：`SPRITES.md` 当时写「机器类整张不透明」，`make_machine_sprite.py` 就照着把
48×48 画布整张填了不透明黑。核原版才发现这条不成立——

| 原版机器 | 不透明像素 | 四周 |
|---|---|---|
| `printer_off` | 2070/2304 | 看着满幅，其实是机箱顶到了画布边，黑边是机身自己的边缘 |
| `chem_finisher` | 1917/2304 | 透明 |
| `blender` | 1483/2304 | 透明 |

**修法**（`scripts/make_machine_sprite.py`）：

- 画布默认 `"."`（alpha 0），渲染时透明；
- 删掉后来试过的 `silhouette_outline()`——`shell()` 已经沿轮廓描了 1 px 藏青边（`#292234`），
  那就是机身边缘，外面再加黑环只是把边框加厚；
- **占格不受影响**：`SetSpriteAndShapeFromMod` 只采样 9 个格心，机身仍压住全部 9 点 → 3×3 不变。

**教训**：机器贴图是「机身盖住 9 个格心 + 其余透明」，不是「整张不透明」。`SPRITES.md` §2/§3 已按这个改正。

## 7. v1.1.2：贴图改成原版机器的俯视正面

**症状**：1.1.0 / 1.1.1 的机器是纯正面平视图，和原版机器放一起风格不一致——原版机身贴满格子、
顶面是一条向后收窄的梯形；我们是留 3 px 边距、还加了两只脚的「正视图」。

**量出来的差距**（`refs/vanilla/items_tool2__*`）：

| 指标 | 原版 printer_off / furnace | 1.1.1 |
|---|---|---|
| 占用 | 列 1–46、行 2–46，顶格 | 列 3–44、行 4–44 + 两只脚 |
| 顶面 | 梯形，每往下 1 行左右各放 1 px | 正交井壁，没有「面」 |
| 侧壁 | 左右各 2–3 px 竖亮列 | 无 |
| 底边 | 4 行内收 | 平底 |
| 色数 | 9–12 | 18 |

**修法**（`scripts/make_machine_sprite.py`）：

- 轮廓照 furnace 的梯形重画：顶面 4 行收边、底部 4 行内收、左右顶到 1..46、去掉两只脚；
- 顶面开一个**矩形装料舱口**（不是梯形敞口——梯形加两侧亮壁会被读成 `furnace` 的提手）；
  舱底最暗、远壁受光，舱口在顶面和正面各投 1 px 影；
- 三支滤芯填满舱口，中间只留 1 px 暗缝；
- 色数压到 12；
- 光影照 `scripts/gen_render3d.py` 跑出来的三维打光渲染补：两侧轮廓光、顶面比正面亮一档、
  凹槽上沿亮下沿暗、底部接触阴影（见 `docs/SPRITES.md` §6.1「光影」）。

**占格不受影响**：2030 实心像素、9 个格心全盖住，仍是 3×3。
