# 《还原蕨 / Reduction Fern》开发复盘（进行中）

> 2026-11-22 · Probably Stolen 0.46D（Unity 2021.3.45f2 / Mono / netstandard2.1）
> 进度：P1 骨架已完成并实机验收；P2 产出数值待验；P3 网络升级 / P4 封面 / P5 发布未做。
> 相关文档：`PLAN.md`（参数、里程碑、拍板记录）、`ART_SPEC.md`（五张图的像素规格）。
> 平台通用经验（Hook、打包、SteamCMD、封面流水线）见仓库根 `docs/RETROSPECTIVE.md`，本文只写**这一株植物带来的新东西**。

## 0. 一句话

一株「能种、能收、数值对」的植物一天就写完了；真正费时间的是把它接进游戏既有的三条约定：**物品的拥有标记、水培立绘的图集、第三方 UI mod 的硬编码白名单**。三个真 bug 全部出在这三条接缝上，没有一个是植物参数。

## 1. 目前验证到什么程度

| 项 | 状态 | 证据 |
|---|---|---|
| mod 加载 | ✅ | `trust=Match`；`[ModLoader] Loading: ReductionFernMod.dll`；`2 locale(s), 18 entries`、`5 item sprite(s)` |
| 物品注册 | ✅ | `Registered item id: restoring_fern_seed` / `restoring_fern`（读档后仍在） |
| 调试生成 | ✅ | F9 面板「生成还原蕨孢子」按钮；Item Spawner 里两个 id 都在 |
| 种植 / 生长 | ✅ | 新档「改造水培系统」里进槽 → `状态: 正在生长`；一个一次性涡轮增压器推进 `6/26 (4天)`，水 2000→1924 ml、能耗 -3 kJ |
| 收获 | ✅ | 产出「小型还原蕨叶」20.5 g / 售价 9 / 25 千卡，符合设计 |
| 工具提示 | ✅ | 分类 `化学用品 \| 材料`、来源「还原蕨 / Reduction Fern」 |
| 立绘 `_p` | ✅ | `Using mod sprite 'restoring_fern_p' for the growing plant`；实机正常 |
| 拥有标记 | ✅ 已修 | `（未拥有）` 消失（修复见 §3.1） |
| 第三方预览 mod | ✅ 已修 | 孢子预览改为蕨叶立绘（修复见 §3.3） |
| 产出数值（120/190 ml） | ⬜ 待验 | `PLAN.md` §9 P2 |
| 网络解锁（450 cr / 2 孢子） | 🟡 代码完成 | 待实机：新档网络界面看到「还原蕨孢子」→ 解锁后收到 2 颗 |
| 工坊描述 | 🟡 待你审 | `packaging/workshop_description.txt`（中文正文 + 英文附录，系列版式，含「与 Hydroponic Seed Preview 兼容」） |
| 封面 | ✅ | `mod/preview.png` 1280×720 / 711 KB，系列版式；关键图 Qwen-Image seed 772 |
| 中英切换 / 发布 | ✅ 已上架 | 工坊条目 **3844217940**（公开）；`dist/ReductionFern-v0.1.0.zip` 246 KB（包内 preview 640×360 / 228 KB，工坊 previewfile 指 1280 全画质）；语言包离线校验 12/12 OK；**英文界面验收交给玩家反馈**（无人反馈即视为通过） |

## 2. 新增的平台事实（写代码前就该知道）

### 2.1 mod 物品工厂绕过了 `DirectoryMaster`

- `DirectoryMaster.Item(id, isOwned: true)` 是原版所有水培产物工厂的起点（`probably_stolen_decomp/PreBuiltItemHelper.cs:1657` 起，一排 `CreateNutrifruitSmall` 之类），它顺手做了两件事：`GeneralHelper.SetItemOwned`（`DirectoryMaster.cs:246-262`）和分配 `uniqueId`。
- mod 工厂习惯用 `ItemDirectory.CreateEmptyItem(id)`，**这两件事都不会发生**：没有 `IS_OWNED_TAG`、`uniqueId` 靠别处补。
- 后果不只是显示：`GeneralHelper.IsItemEffectivelyOwned` 会往上遍历父级（`GeneralHelper.cs:214-228`），没有 tag 的物品在出售、被机器接受、放进某些容器时都会被卡。

### 2.2 水培立绘只认原版图集

- 机器「长着的东西」不是物品模型，是 `getItemSpriteModifierForItemFunc` 里临时叠的一张精灵：`RenderHandler.LoadFromAtlas("Items/items_hydroponic_plant", harvestItemId + "_p")`（`MachineHydroponic.cs:88-110`），多年生快熟再试 `_p2`。
- `LoadFromAtlas` 找不到**不报错**，而是返回 `unknownSprite` 并 `LogWarning`（`RenderHandler.cs:359-368`）——所以 mod 植物不会崩，只会「画一个白方块」+ 刷日志。

### 2.3 取图路径要「先判断再委托」

第一版实现是「调原版委托 → 发现是 unknown → 换成自己的图」。这不崩，但原版委托在**每次重绘**时都会走一次 `LoadFromAtlas`，于是每次都刷一条 warning（一次会话实测 298 条）。正确做法是先判断条件（图集里有没有 `_p`），条件成立才自己造列表，否则才调原版委托。

### 2.4 第三方 UI mod 的硬编码白名单

`Hydroponic Seed Preview`（3835902034）在机器上叠一层半透明「幽灵立绘」，但它只认两个 mod：`AgriPreview.Harvests` 写死 19 个 `agri_expansion` 种子（`tmp/hsp/HydroponicSeedPreview.decompiled.cs:302-346`），`BrewingPreview` 只认 `brewing_expansion`；**其余 mod 种子一律在 `AddPreview` 里 `sprite = null` → 回退成种子自己的图**（`:146-162`、`:256-269`）。这类「看起来是通用预览、实际是白名单」的 mod 会长期存在，别指望它读我们的 `_p`。

### 2.5 水培状态机（读代码 + 实测对齐）

| 条件 | 位置 | 说明 |
|---|---|---|
| 种子准入 | `inputSlot.mayInventoryAddItemFunc`：`IsTag("SEED") && !IsTag("CONTAINER_TAG")` | 我们的孢子靠 `SetGameItemType("SEED")` 满足 |
| 一个周期 | `onCycleEndSlotItemFunc` → `CanPower` + `CanWater` → `StartGrowing` / `GrowOneCycle` | 没电/没水就只有 `UpdateSprite`，进度不动 |
| 生长中 | `STATE_WORKING` | 期间种子取不出来 |
| 水耗 | `HydroponicHelper.GetWaterUsePerCycle` | 我们没调 `.Water()`，用默认值 |
| 收获 | `PlantHarvest.Output` → `SplitByHealth` / `OutputSplit` → `GraphUtils.TryAcceptAll` | 输出格满时溢出到船上，不阻塞 |

## 3. 三个真 bug 的复盘

### 3.1 收下来的叶子写着「（未拥有）」

- **现象**：机器输出格里 20.5 g 的小叶，售价、热量、分类都对，但工具提示第一行是红字「（未拥有）」。
- **定位**：`GeneralHelper.CreateGeneralItemTooltip` 在 `!IsItemEffectivelyOwned(item)` 时加这行（`GeneralHelper.cs:230-236`）；进一步看 `SetItemOwned` 只由 `DirectoryMaster.Item` 等少数路径调用，而我们的工厂是 `CreateEmptyItem` 起步（详见 §2.1）。
- **修法**：两个工厂末尾 `GeneralHelper.SetItemOwned(item)`；同时在 `LoadedSeed` / `LoadedFronds`（`onLoaded`）里再补一次，**旧存档里已经种出来的叶子读档时自动修好**，不用重种。
- **教训**：mod 物品不是「属性对就行」。原版工厂里那些「顺手做掉的事」（拥有标记、uniqueId、来源 tag、重量）要逐条对照抄，抄漏了只会以「看起来像 bug 的 UI 文案」出现。

### 3.2 机器上画白方块 + 日志刷屏

- **现象**：`Player.log` 里 74 → 298 条 `Sprite name 'restoring_fern_p' in atlas 'Items/items_hydroponic_plant' was not found. Loading dummy sprite.`，机器上是一个 unknown 占位图。
- **定位**：见 §2.2 / §2.3。
- **修法**：`src/HydroponicPlantArt.cs` —— postfix `MachineHydroponic.Hydroponic()`，包一层 `getItemSpriteModifierForItemFunc`：`STATE_WORKING` + 原版图集没有 `<harvestId>_p` + 某个 mod 的 `Sprites` 里有 → 自己造 `List<ItemSpriteModifier>`（位置 `(0,0)`、`Color.white`，和原版一致）；否则原样调原版委托。
- **教训**：① 修「取不到就退化成占位」的路径时，要连**日志噪音**一起修，否则下一个人会以为 bug 还在；② 用「遍历所有已加载 mod 的精灵」而不是写死自己的 mod id，顺手把别的种田 mod 也救了，且不需要它们配合。

### 3.3 预览里是孢子包，不是蕨叶

- **现象**：种子进槽、还没开始长时，机器上的幽灵预览是孢子图；用户明确说「原版已经能正常显示 `restoring_fern_p` 了，但预览还是孢子」。
- **定位**：不是我们的 bug（§2.4），是那个 mod 的白名单。
- **修法**：`src/SeedPreviewCompat.cs` —— **反射**找 `HydroponicSeedPreview.ModEntry.AddPreview(GameItem, ref List<ItemSpriteModifier>)`，挂 postfix：
  - 只在机器不是 `STATE_WORKING`（幽灵场景）、且 `HydroponicPlantArt.TryPlantArt(seed)` 能解析出 `_p` 时动手；
  - 只替换「精灵正好等于种子自己的图」那一条，保留它设的 `position` 与 `color`（25% 不透明度是玩家配置，不碰）；
  - 找不到类型/方法就静默跳过；`Init` / `OnGameLoadedInit` / `OnModAssetsLoaded` 各试一次防晚加载；卸载 mod 后自动失效。
- **教训**：给别人 mod 打兼容补丁要满足三条——**不硬引用**（反射找目标）、**只在它做不到的地方接管**（其余原样）、**失效即静默**。这样对方更新/改名/卸载都不会把我们拖崩。

## 4. 游戏内调试手法（本次最大收获）

| 手法 | 怎么用 | 为什么值 |
|---|---|---|
| F9 调试面板 | 「Generate Hydroponic Kit」一次性放 4 台带模组的机器；「Skip Night (Machines Only)」推进机器 | 不用攒钱、不用等睡觉 |
| Item Spawner | F9 → Open Debug Spawner，552 个物品可搜 | 直接生成孢子 |
| **一次性涡轮增压器 `turbo_booster`** | **拖到机器上 = 该机器立刻跑完一个周期（等价于过一夜）** | 验生长/收获不用真的过夜，几十秒一轮 |
| 工具提示当仪表盘 | 读 `状态` / `作业速度 6/26 (4天)` / `水量 1924mL (75mL/天)` / `能耗 97/100kJ` | 能区分「没进槽」「没水没电」「在长但慢」 |
| 日志当硬证据 | `grep restoring_fern Player.log` | 立绘/警告/注册这类事，屏幕看不出来，日志一眼定论 |

**一次误判值得单独记**：老存档里我判定「种下去过夜没反应 = 代码问题」，实际是**种子根本没进槽**（那台机器里还是原版种子，输出格被 7 个营养果塞满）。新档里同一个孢子进槽后进度条立刻走。教训：**先验证输入条件成立（槽里有东西、状态在长），再怀疑进度逻辑**；「没反应」多数时候是前置条件没满足，而不是时间不长。

## 5. 工具与协作

- **桌面自动化（Windows-MCP）**：坐标要按「区域截图 → `screen = origin + 图片像素 × scale`」换算，180% DPI 下 3840×2160 的 scale 是 2.0，预览图还会再缩 0.75；一次算错就点到别的窗口上。更重要的不是坐标，而是**动别人桌面之前先说清楚要做什么并等一句同意**——这次因为没说，被两次叫停（「干啥呢」「你要干什么跟我说」）。
- **长任务不要占前台**：`uv sync`、`dotnet restore` 这类几十秒到几分钟的操作放后台任务，别让用户对着「运行工具好半天了」发呆。
- **部署**：游戏运行时 DLL 被锁，所以 `build.sh` 先复制 DLL、失败即 `exit 1`，别的文件一个都不动；人不在电脑前就用 `deploy-when-closed.sh` 挂后台等退出再部署，部署完用 `sha256sum` 对比 build 与 `Mods/` 两份。
- **构建脚本自检**：`build.sh` 末尾会校验 ≥2 个语言包、5 张精灵都在、dll/manifest 非空——这三项正好对应「裸 key」「unknown 图」「半套文件」三种最容易被忽略的发布事故。
- **文案自检前移**：`scripts/check_locales.py` 把「两语言 key 是否对齐、代码用到的 key 是否都在」变成一条命令（`en 12 / zh 12 / OK`），不用进游戏逐个点提示框。
- **封面是两步**：关键图（ComfyUI + Qwen-Image，暗调写实、画面里绝不出现模型文字）+ 排版（PIL，系列版式）。调色也在脚本外先做一版备选，再决定用哪版进 `preview.png`。

## 6. 踩坑总表

| 现象 | 根因 | 修法 / 教训 |
|---|---|---|
| 收获物显示「（未拥有）」 | 工厂从 `CreateEmptyItem` 起步，`DirectoryMaster.Item` 的 `IS_OWNED_TAG` 没被设置 | 工厂里显式 `GeneralHelper.SetItemOwned`，`onLoaded` 再补一次修旧档 |
| 水培机里画白方块 | `<harvestId>_p` 不在原版图集，`LoadFromAtlas` 退化 unknown | patch `MachineHydroponic.Hydroponic`，从 mod 精灵解析 `_p` |
| 日志每次重绘刷 `sprite not found` | 先调原版委托再替换精灵 | 先判断再委托，原版委托不调用 |
| 预览显示孢子图 | 第三方预览 mod 只认两个 mod 的硬编码白名单 | 反射 postfix 它的 `AddPreview`，只换种子图那一条，失效即静默 |
| 「过夜没反应」 | 种子根本没进槽（输出格还满着） | 先验证输入条件，再怀疑进度 |
| 特质加成没被效力强/效力弱放大 | mod 特质排在 `potent`/`weak` 之后注册 | 注册完把原版两个特质重新 `Add` 一遍挪到末尾（同对象，不动存档） |
| 拖放总是抓到别的窗口 | 机器窗口大半在屏幕外、坐标按预览图算的 | 区域截图 + `origin + px × scale` 换算，先确认窗口可见再拖 |
| 部署时 dll 覆盖失败 | 游戏还开着 | dll 先复制、失败即退出；或用 `deploy-when-closed.sh` |
| 工坊 file_size 被封面撑到 729 KB | `package.sh` 把 1280×720 封面（711 KB）放进了 contentfolder | 包内改放 640×360（228 KB），`previewfile` 单独指 1280；脚本加尺寸断言 |

## 7. 如果重来

1. **先列「原版工厂顺手做了什么」清单**（拥有标记、uniqueId、来源、重量、分类、`Init*Helper`），再动笔写 mod 工厂，别等 UI 报错才发现。
2. **凡是「原版从图集取图」的地方，默认 mod 拿不到**：立绘、封面、图标、预览，全部提前规划注入点。
3. **改行为之前先把日志看干净**：这次两个「显示问题」都先由一条 warning 定位，比在屏幕上猜快一个数量级。
4. **调试流程先问用户**：他们知道的捷径（`turbo_booster`）比我自己摸索强得多；先问「你们平时怎么快进一个周期」，再动手。
5. **给别人 mod 写兼容层要按「不硬引用 / 只补缺口 / 失效静默」三条来**，否则补丁本身会变成新的维护负担。

## 8. 待办（承接 `PLAN.md`）

- **P2**：满血一茬 8 片大叶 = 190 ml；标准叶 120 ml；效力强 I 237.5 ml、效力弱 I 142.5 ml；搅碎后容器里是还原剂。
- **P3**：代码已完成（`harness.reduction_fern.unlock`，450 cr、无前置、解锁给 2 颗孢子，图标 `harness.reduction-fern:restoring_fern_seed`），待实机验收解锁与到账。
- **P4**：封面已完成（`mod/preview.png`，1280×720 / 711 KB，系列版式）；剩游戏内中英切换验收。工坊描述已按系列版式重写（`packaging/workshop_description.txt`，中文正文 + 英文附录，含「与 Hydroponic Seed Preview 兼容」），等用户审。
- **P5**：已上架工坊 **3844217940**（公开，`visibility 0`）。包在 `dist/ReductionFern-v0.1.0.zip` 246 KB；更新流程见 `packaging/UPLOAD.md`（`package.sh` 会沿用这个 id 和可见性）。
- **命名分工**：工坊**标题**用「还原剂蕨」，方便玩家搜「还原剂」找到；**游戏内**植物名仍然是「还原蕨」，两边不冲突（标题在 VDF 里，名字在语言包里）。
