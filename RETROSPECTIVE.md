# Probably Stolen 模组开发复盘（六个模组 + 一条发布流水线）

> 2026-11-15 ~ 2026-11-23 · 游戏 0.46D（Unity 2021.3.45f2 / Mono / netstandard2.1）
> 本文整合了 `ScavGame/RETROSPECTIVE.md`（拾荒手记专项复盘）与另外三个模组的经验，按"平台 → 各模组 → 流水线 → 验证 → 清单"重排。
> 2026-11-22 追加：第五个模组《还原蕨 / Reduction Fern》（新植物），专项复盘在 `ReductionFern/RETROSPECTIVE.md`，本文 §3.5 与 §7 只留跨模组的结论。
> 2026-11-23 追加：第六个模组《更好的奥克莫吸注射器 / Luxury Nomore Injector》（改一件原版物品的类型与价格），专项复盘在 `LuxuryNomoreInjector/RETROSPECTIVE.md`，本文 §3.6 只留跨模组结论。

## 0. 一句话

真正花时间的从来不是"写功能"，而是三件事：**先把平台事实摸清（Hook / 扫描器 / 存档 / 上传规则）、把状态和 UI 生命周期分开、把验证从"看屏幕"改成"看日志和数值"**。四次翻车——电力没扣、语言包被删、工坊条目被隐藏、补丁打上了却静默无效——都出在这三件事上，而不是功能本身。

## 1. 交付

| 模组 | 工坊 ID | 版本 | 形态 | 关键改动 |
|---|---|---|---|---|
| 滤芯打印机 / Filter Cartridge Printer | 3840097356 | 1.1.0 | 新机器 + 37 种自选截留物质的滤芯 + 专用机身贴图 | 机器面板选物质，打印一次 120 电 |
| 下层药房 / Lower-District Pharmacy | 3840842240 | 1.0.2 | 化学精制机两条配方 | 澄心剂（0.8 ml 梦帽菇萃取液，价值 12）、消痛片（0.08 ml 芬太，价值 20） |
| 净化无上限 / Purifying Uncapped | 3841246322 | 1.0.0 | 单个 Harmony Prefix | `PurifyingShare` 的 95% 上限改成 100% |
| 拾荒手记 / Scavenger's Notes | 3841523504 | 0.3.0 | 6×4 拾荒小游戏 | 24 格预生成、线索、手电/放大镜、受伤暂停 |
| 还原蕨 / Reduction Fern | 3844217940 | 0.1.0 | 新植物 + 两件物品 | 还原蕨孢子 → 还原蕨叶（三档），产出还原剂；工坊标题用「还原剂蕨」便于搜索。复盘见 `ReductionFern/RETROSPECTIVE.md` |
| 更好的奥克莫吸注射器 / Luxury Nomore Injector | 3844271622 | 1.0.0 | 单个 Harmony Postfix | 给 `pink_alt_injector` 加 `LUXURY_ITEM`、基础价值 50 → 350（对齐赛纳普斯注射器）。复盘见 `LuxuryNomoreInjector/RETROSPECTIVE.md` |

四个已公开（滤芯打印机、下层药房、净化无上限、还原蕨），拾荒手记仍是隐藏状态（审核通过后由作者手动公开），奢侈品注射器已上传（3844271622）但还停在隐藏，等页面确认后改公开。

六个模组的源码已公开在 **https://github.com/zszzlzm/probably-stolen-mods**（Apache-2.0，单仓库六个目录），
release `builds-2026-11-23` 附了六个可直接安装的 zip。仓库里只放源码与文档，**不含**反编译的游戏代码、
游戏资源与构建产物；README / BUILDING 说明了怎么用本机游戏编译。

## 2. 平台事实（一次摸清，后面一直用）

- **加载**：`Mods/<文件夹>/manifest.xml` + `<Assemblies>`；`ModLoader` 会 `Assembly.LoadFrom` → 找 `IMod` 实现 → `new Harmony("mod."+ID).PatchAll(assembly)` → `Init/OnEnable`。所以 mod 里**不需要自己 new Harmony**，只要有一个 `IMod` 和一个带 `[HarmonyPatch]` 的类。
- **扫描器**：加载前会静态扫程序集，`[ModRestricted]` 只标在 `files` / `process-start` / `loader-target` 这类 API 上。**改玩法类（PlantWaterQuality、ChemicalFeedbackHelper）不受限；碰 ModLoader/审批/文件 IO 会被拒绝或要求声明 capability。**
- **文件读写**：要写自己的数据，用 `ModHelper.GetModDataFolder` / `WriteModDataFileText`，manifest 保持 `<Capabilities />`。直接用 `System.IO` 会被拒载（拾荒手记踩过）。
- **本地化**：`Localization/<lang>.csv`，缺 key 时日志会打 `Localization key 'x' not found` 并把 key 原样显示——这是最可靠的"漏翻"信号。
- **反编译**：`ilspycmd`（`~/.dotnet/tools/.store/...`）能直接出可读 C#；设计前先看原版实现，比猜快得多。`ChemicalFeedbackHelper` 里 `CanReport()` 的返回值被丢弃这种原版 bug，就是反编译才看见的。
- **素材**：`UnityPy` 能从 `resources.assets` / `sharedassets*.assets` 导出 Sprite（含图集切图），做封面参考图、核对像素规格都靠它。
- **物品工厂**：`Directory<T>.Create(id)` 是**先跑工厂、再赋 `identifier`**（`Directory.cs:24-38`）。所以挂在工厂上的 postfix，返回时 `identifier` 还是 `null`，判断要用工厂自己设好的字段（`spritePath`、`name`）。

## 3. 各模组的关键决策

### 3.1 滤芯打印机：数据驱动 + 顺序陷阱

- 滤芯是"同一个物品 + 运行期选物质"的结构，37 种物质走一张表生成，避免 37 个手写物品。
- **最大的一次翻车**：`GraphUtils.TryAcceptAll(...)` 返回的是"没放进去的剩余数量"，代码却写成 `> 0` 当作成功，结果滤芯被判定放不进输出槽、随后被销毁/退款，电力也永远不扣。修正为 `leftover == 0`。
- 教训：任何 `TryXxx` 命名先确认返回值语义（bool？剩余？错误码？），再写条件。
- **v1.1.0 换专用贴图**：游戏原生支持 `Textures/Items/*.png`，代码走 `GameItem.SetSpriteAndShapeFromMod(modId, "文件名")`，占位仍按 48×48 的九个格心算，所以 3×3 摆放不变。两个容易漏的点：①存档按物品记 `spriteAtlasPath/spritePath`，老档里的机器要在 `onLoaded` 里改贴图，否则只有新造的机器换皮；②目录里多一个 PNG 会改 `folderHash`，不重新跑 `tools/trust_local.py` 游戏会以"指纹不符"拒绝加载。
- **像素贴图要按原版的体积语言画**：2px 纯黑边 → 1px 藏青描边 → 上亮下暗的 1px 斜面 → 内凹面板（上/左内沿亮、下/右内沿暗）→ 凸出部件底下一行投影。纯正面平描在 48px 上会像一张海报，和原版机器摆一起就露怯。生图模型只用来定构图（参考图喂原版图集），最终仍要按 16px 网格手绘。

### 3.2 下层药房：跟原版物品同构，别自创字段

- 两件药完全照 `dream_dust` / `oxycodone_pill` 的结构搭：`InitChemItem` + `SetCompositionByPurity` + `InitChemicalProduct` + `InitNarcotic`。
- 配方不改存档：`ChemFinisherRecipe.chemFinisherRecipes` 是 `public static List`，而 `ChemFinisherUIManager.OpenUI()` 每次打开都重新遍历它，所以**在 `OnModAssetsLoaded` / `OnGameLoadedInit` 里追加、在 `Uninstall` 里按 id 移除**即可，不需要 Harmony。
- **投诉问题**：原版对"意图=麻醉品、euphoria 等级只有 0/1"的商品会判"药效太弱"，扣声望并可能派索赔顾客。我们的剂量（800 = 等级 1）正好踩中。修法是**不打 `CHEMICAL_INTENT_TAG`**——`GetChemicalIntent` 全库只有 4 处调用，全在反馈逻辑，去掉不影响效果/定价/成瘾/扫描。
- 教训：设计"弱效但合法"的物品前，先确认原版有没有对"弱"的惩罚逻辑；有的话，选择"不参与该判定"比"打补丁绕过判定"更干净。

### 3.3 净化无上限：一个 Prefix，一次数值验证

- 95% 上限全游戏只有一处：`Mathf.Min(0.95f, 0.1f * RankScale(rank))`，且只有两个调用点（`Purify` 与 `DescribePurifying`），所以改一处，玩法与 tooltip 同时生效。
- 用 `Prefix + ref __result + return false` 直接替换返回值，比 transpiler 改 IL 稳。
- 用"反射调用 Prefix、和原函数逐等级对比"的方式做离线验证（21 级 98.10%、22 级起 100%、≤20 级不变）。
- **踩坑**：游戏自带的 `0Harmony` 不能在 .NET 8+ 里直接跑——.NET 10 移除了 `BinaryFormatter`（Harmony 共享状态序列化要用），.NET 8 则缺 `ILGenerator.MarkSequencePoint` 重载（`MissingMethodException`）。所以离线只验证数值，Harmony 是否打上交给游戏日志。

### 3.4 拾荒手记：把随机和状态从 UI 里拿出来

（完整版见 `ScavGame/RETROSPECTIVE.md`，这里只留结论）

- 进本时用原版判定预生成 24 格，点击只结算——平衡不被改坏、关窗重开不重 roll、线索不会和实际不一致。
- 线索缓存以"点击"为单位（`clueText[click]` / `clueSource[click]`），`ShowClueForLast()` 只回放、`GenerateClue()` 才抽取，窗口重建/包扎恢复都不会偷偷多消耗一次。
- 敢砍：夜间遭遇、逐件动画、难度配置全砍掉，只留网格/线索/工具/受伤/音效。
- 自测进 mod（`AutoTest` + `ModData` 写报告），比 AutoHotkey 屏幕自动化可靠得多。
- **最值钱的一条**：`Open()/Refresh()/Show()` 里调用的方法必须幂等或只读缓存；随机逻辑绝不能放在渲染路径上。

### 3.5 还原蕨：新植物类模组的接缝在哪（2026-11-22）

（完整版见 `ReductionFern/RETROSPECTIVE.md`，这里只留跨模组的结论）

- **mod 物品工厂要手工补上 `DirectoryMaster.Item` 顺手做的事**：`IS_OWNED_TAG`（没有就显示红字「未拥有」、且不能正常出售/被机器接受）、`uniqueId`、来源 tag、重量。`CreateEmptyItem` 起步的工厂最容易漏这一层。
- **原版从图集取图的地方，mod 一律拿不到**：水培立绘是 `RenderHandler.LoadFromAtlas("Items/items_hydroponic_plant", harvestId + "_p")`，找不到只是退化成 unknown 占位图 + 每次重绘都 `LogWarning`（不会崩，所以很容易被当成「图没画好」）。注入点在 `MachineHydroponic.Hydroponic()` 的 postfix。
- **第三方 UI mod 的「通用预览」可能只是白名单**：`Hydroponic Seed Preview` 只认两个 mod 的作物，其余 mod 种子回退成种子图。兼容要按「反射找目标 / 只补缺口 / 失效静默」写补丁。
- **调试用 `turbo_booster`（一次性涡轮增压器）拖到机器上 = 跑完一个周期**：验生长/收获不必真的过夜，这是这次最有用的游戏内技巧。

### 3.6 奢侈品注射器：改一件原版物品（2026-11-23）

（完整版见 `LuxuryNomoreInjector/RETROSPECTIVE.md`，这里只留跨模组的结论）

- **原版物品只有一个创建入口，就是它的目录工厂**：`pink_alt_injector` 全库只由 `MedsItemDirectory.Injector(...)` 造出来（`MedsItemDirectory.cs:27`、`:361`），目录生成、化工合成、商店存货、调试生成器全部经过它。**patch 工厂 = 覆盖全部路径**；patch 任何"某个调用点的返回值"都会漏。
- **`Directory<T>.Create` 是先造、后命名**（`Directory.cs:24-38`）：工厂返回时 `identifier` 还是 `null`。所以工厂 postfix 里**不能拿 identifier 当判据**，要用工厂自己设好的字段（`spritePath`）。这个坑直接导致第一版"补丁打了但静默无效"。
- **补丁要有正向自证日志**：只有 `patched` 一行时，"装上了"和"生效了"在日志里无法区分。第一次真正命中时打一行 `Applied: ...`，验收才不用靠猜。
- **`SetGameItemType(x)` = `EnableTag(x)` + 类型表**（`GameItem.cs:2279-2291`），一次调用两种查询都命中；但改类型的副作用要先全库 grep：`LUXURY_ITEM` 会被求购客读、被"买水的客人"拒收（`StoreClient.cs:425-449`，台词 `dialogue_no_luxury`）、被展示柜统计，而且**不在 `MAJOR_TYPES_LIST` 里**，所以不会自动招来收藏家（那要靠 `UL_DISCERNING_TASTE` 特权）。
- **改价格先找原版锚点**：350 来自赛纳普斯注射器（`MedsItemDirectory.cs:345`），不是拍脑袋；把锚点 + 经济账一起写进工坊描述，玩家才不会觉得作者在调数值玩。
- **价格存在物品实例上**（存档里 `unitValue` 与物品数一一对应），所以改价只影响新生成/新合成的物品，老档里已有的还是旧价——这条要么写进描述，要么写读档迁移。

## 4. 发布流水线（各模组共用）

### 4.1 构建 → 部署

- 每个项目一套 `scripts/build.sh`：`dotnet build -c Release -o build` → 复制 DLL → manifest → 贴图/语言包。
- **顺序必须是 DLL 先复制**：DLL 被运行中的游戏锁住时，先复制它会失败并 `exit 1`；如果先删语言包再复制 DLL，就会留下"英文界面 + 原样 key"的半残状态（下层药房和滤芯打印机都中过）。脚本现在写成"复制 DLL 失败就退出，别的文件一个都不动"。
- `scripts/deploy-when-closed.sh`：等 `Probably Stolen.exe` 退出再重试，最多 60 分钟。
- **部署目录里也要有 `preview.png`**：游戏内模组列表的缩略图读的是 `Mods/<文件夹>/preview.png`，不是工坊封面。六个 mod 里只有这次漏了（只复制了 dll + manifest）。补图之后 `folderHash` 会变（`tools/trust_local.py` 把它算进整包哈希），本地条目必须重跑一次 `trust_local.py`，否则会被当成"文件被改过"。

### 4.2 打包

- 发布包只放运行时文件：`manifest.xml`、DLL、`Localization/`、`Textures/`（若有）、`README`、`preview.png`；zip 里不许有 `obj/`、`build/`、`.bak`、`art/`。
- 校验项：DLL 与部署一致（sha256）、≥2 个语言包且非空、preview < 1 MB、manifest 列了 DLL、`<Capabilities>` 存在、没有可执行/压缩包/未知 DLL。
- **SteamCMD 的 VDF 必须沿用已有的 `publishedfileid` 和 `visibility`**。早期 `package.sh` 每次都写死 `0` + `2`，照跑会新建重复条目、并把已公开的条目改回隐藏（滤芯打印机差点中招；拾荒手记第一次也差点因为 id 写死而重建）。
- `changenote` 用环境变量注入，避免脚本里写死"首次发布"。

### 4.3 封面

- 统一版式（六个模组共用）：左侧 eyebrow `PROBABLY STOLEN · 模组` → 中文主标题 96px → 英文副标题（琥珀）→ 分隔线 → 三条青色方块要点 → 粗体卖点 → 细节行 → 页脚。左侧用 `0.93 - 0.58*x^0.72` 的渐变压暗保证文字可读。
- 画面用本地 ComfyUI + Qwen-Image 2.1（`qwen_img.py`，30 steps / cfg 1.0 / 1280×720），参考图优先用**游戏原版素材**（UnityPy 导出的 Sprite）：滤芯用 `purifier`/`water_filter`，药房用 `items_medical` 图集，拾荒用 `debris_pile*`。
- 排版交给 PIL，绝不让生图模型写字。
- **构图要为文字让位**：9 字中文标题 96px ≈ 864px，左侧约 1000px 是禁区。要么生图时就要求"主体偏右下、左上留空"，要么用 `make_cover.py --zoom/--dx/--dy` 重新构图（`--zoom` 裁一刀再缩回 1280×720，`--dx/--dy` 平移），不要手工搓中间文件。
- 体积：Steam 预览图上限 1 MB；1280×720 的照片型 PNG 通常 600–900 KB。**包内 preview 降成 640×360（约 250 KB）供游戏内模组列表用，工坊封面仍上传 1280×720 全画质**（`previewfile` 指向 `mod/preview.png`，不计入包体积）。这样整包比原来还小。
- 256 色 + Floyd 抖动能压到 130 KB 左右，但暗部会起噪点，正式封面不建议。

### 4.4 SteamCMD

- `steamcmd` 不在 PATH：要么 `& "C:\steamcmd\steamcmd.exe" ...`，要么 `cd C:\steamcmd; .\steamcmd.exe ...`；在 `Steam>` 提示符里再输 `steamcmd` 是错的。
- 登录：`+login <账号>` 会优先用缓存凭据；失败才要求密码（输入无回显）和 Steam Guard。
- 首次发布要在浏览器里接受创意工坊协议，否则提交会失败。
- `visibility`：`2` 隐藏 / `1` 好友 / `0` 公开。稳妥流程是先用 2 上传、检查页面、再改 0 重传。
- **`Access Denied` 不一定是权限问题**：拾荒手记在"审核中"状态下，内容能传、提交被拒；审核通过后同样的 VDF 直接 `OK`。遇到就等一会儿重试，别急着改 id。
- 上传后以 `[AppID 4348910] Upload finished for workshop item <id> : OK` 和 `Uploaded new workshop preview file ...` 作为成功证据；可用 `ISteamRemoteStorage/GetPublishedFileDetails` 查询 `visibility` / `file_size` / `time_updated`（私有条目会返回 `result: 9`）。
- **安全**：`C:\steamcmd\logs\console_log.txt` 会把 `+login<账号><密码>` 明文写进日志。事后要脱敏（`(\+login<[^<>]*><)[^<>]*>` → `\1REDACTED>`），并建议改密码。

## 5. 验证阶梯

1. **编译**：`0 warning / 0 error`。
2. **反编译自检**：`ilspycmd` 看打包后的 DLL，确认补丁目标、常量、是否误留旧调用。
3. **离线数值**：用反射直接调 Prefix/纯函数，和原版逐项对比（净化 mod 的 `tools/VerifyShare`）。不要试图在 .NET 8+ 里跑游戏自带 Harmony。
4. **游戏日志**：`[ModLoader] Loading: X.dll`、`Harmony: N method(s) patched`、mod 自己的初始化行；这是"补丁真的生效"的唯一硬证据。警告也要读——`Sprite name 'x' ... was not found` 这类「退化 + 刷日志」的路径，往往是显示类 bug 的唯一线索。
   - **但"打到方法"不等于"改到物品"**：一定要有一条只在真正命中时打印的日志（这次是 `Applied: pink_alt_injector is now LUXURY_ITEM with value 350`），否则 `patched` 是唯一证据，而它会骗人。
5. **游戏内快进**：涉及时长/循环的改动，用调试手段一次跑完一周期（例如水培机用一次性涡轮增压器 `turbo_booster` 拖上去 = 一个周期），再读工具提示里的状态/进度/水量/能耗。
6. **人眼**：tooltip 文案、布局、缩略图可读性。这一层替代不了。

## 6. 协作经验

- 需求拍板越快越好：拾荒手记"砍遭遇/砍动画/不做配置"、药房"药效弱就该不被投诉"，每次都能立刻缩小范围。
- 用户偏好**脚本化改动**而不是手改：数值、文案、封面都走脚本，可复现、可 diff。
- Bug 报告带可观察行为（"电力没扣""反抗军声望 -1""字体变英文"）比"感觉不对"好定位。
- 先给方案再动手：药房投诉那次先解释根因、给 A/B/C 三个选项，确认后才改，避免白做。
- 分工要明确：生图模型只出画面，标题排版、裁切、发布包由脚本/人做；"让一个模型全包"会得到歪字和错版式。

## 7. 踩坑总表

| 现象 | 根因 | 修法 / 教训 |
|---|---|---|
| 打印了滤芯但电力没扣、输出槽"被占用" | `TryAcceptAll` 返回剩余数，被当成 bool 用反了 | 确认 `Try*` 的返回值语义 |
| 界面变英文、显示原始 key | 部署脚本先删语言包、复制 DLL 失败后 `set -e` 中断 | DLL 先复制，失败即退出；语言包最后动 |
| 药卖出去被投诉"药效太弱"、掉声望 | 物品带 `CHEMICAL_INTENT_TAG=NARCOTIC`，euphoria 800 = 等级 1，命中"弱效麻醉品"分支 | 不打该标签（只被反馈逻辑使用），或按需打 Prefix |
| 工坊条目"文件大小翻倍" | 包内 `preview.png` 从 345 KB（扁平图）换成 817 KB（照片型封面） | 包内放 640×360，封面单独 1280 上传 |
| 工坊提交 `Access Denied` | 条目审核中 / 未审批完成 | 等审核通过后重试，不要重建条目 |
| 差点新建重复工坊条目 / 把公开条目改隐藏 | `package.sh` 写死 `publishedfileid 0` + `visibility 2` | 打包脚本沿用现有 vdf 的 id 和 visibility |
| `steamcmd` 命令找不到 | 不在 PATH，PowerShell 不搜当前目录 | 全路径 + `&`，或 `cd` 后用 `.\` |
| 明文密码进日志 | steamcmd 把 `+login` 参数原样写入 `console_log.txt` | 脱敏 + 改密码 |
| mod 被拒载（用了 System.IO） | 未声明 capability | 改用 `ModHelper` 的 ModData API |
| 干净安装出现重复 ID | `Mods/` 里留了 `.bak`，加载器会扫描 | 备份放 `Mods/` 外 |
| 线索重复/关窗重开又多一条 | 窗口重建时再次调用生成逻辑 | 生成与显示分离，`Open/Refresh/Show` 必须幂等 |
| 中文硬编码漏网 | 单字标记、方向、分隔符、按钮没进 CSV | 先列"所有玩家可见字符串"清单，再全量扫源码 |
| 生图出抽象纹理 | 文生图用错文本编码器（i2i 那一路） | 按官方 T2I 组合配 UNet + 文本编码器 + VAE |
| 预览图超 1 MB | 1280×720 照片型 PNG | 降分辨率或量化；缩略图可读比像素数重要 |
| 收获物显示「（未拥有）」、卖不掉 | mod 工厂从 `CreateEmptyItem` 起步，缺 `IS_OWNED_TAG` | 工厂里显式 `GeneralHelper.SetItemOwned`，`onLoaded` 再补一次（顺手修旧档） |
| 水培机里画 unknown 白方块、日志每次重绘刷 `sprite not found` | 缺 `<harvestId>_p`；且「先调原版再换图」会每次重绘都走一次 `LoadFromAtlas` | patch `MachineHydroponic.Hydroponic`，**先判断再委托** |
| 第三方预览 mod 显示种子图 | 那个 mod 只认硬编码的两个 mod 作物 | 反射 postfix 它的 `AddPreview`，只替换种子图那一条，失效即静默 |
| 「种下去过夜没反应」 | 种子其实没进槽 / 输出格还满着 | 先验证输入条件（槽里有种子、状态在长），再怀疑进度逻辑 |
| 拖放总抓到别的窗口 | 目标窗口大半在屏幕外，点击坐标按预览图算的 | 区域截图 + `screen = origin + 像素 × scale`，先确认可见再拖 |
| 补丁明明打上了，游戏里没变化 | 工厂 postfix 里 `identifier` 还是 null（`Directory.Create` 先造后命名），匹配永远失败 | 用工厂自己设好的字段（`spritePath`）判定；首次命中打一行 `Applied:` |
| 日志里看不出补丁到底生效没有 | 只在 patch 成功时打日志，匹配失败静默 | "装上了"和"生效了"必须是两条不同的日志 |
| 改了价，老档里的物品还是旧价 | 价格存在物品实例上（存档里 `unitValue` 逐件保存） | 接受并写进描述「注意」，或加读档迁移 |
| 加奢侈品标签后，收废品/水客拒收这支药 | `IsRefusingLuxuryItem`：求购表含 `WATER` 的客人拒收奢侈品（游客与上层除外） | 改标签前全库 grep 它被谁读；副作用写进更新说明 |
| 以为摆进展示柜就会有收藏家 | `MAJOR_TYPES_LIST` 不含 `LUXURY_ITEM`，`CreateClientByStockType` 无奢侈品分支 | 奢侈品客靠 `UL_DISCERNING_TASTE` 特权 + `GetTypeCount`；描述别写过头 |
| 加了专用贴图的机器，老档里显示成「？」问号图 | 读档顺序：`SaveManager.cs:182` 先用工厂造（工厂把 `useSpriteFromMod` 置 true），**再**用存档里的 `SetSprite(atlas, path)` 覆盖两个路径——覆盖不清标志位。于是旧档（存的是原版 `Items/items_tool2`/`printer_off`）变成「标志说用 mod 贴图、路径却是原版」，`GameItemElement.ResolveSpriteByName` 把 atlas 当 mod id 找，找不到就画 `RenderHandler.unknownSprite`（问号） | 换皮逻辑的判据永远不要只看 `item.useSpriteFromMod`：确认「标志 + atlas + key」三者都对才跳过，否则重指一次；走原版兜底时**手动把 `useSpriteFromMod = false`**，否则原版路径也被塞进 mod 查找 |

## 8. 可复用清单

### 新 mod 开工前

- [ ] 确认游戏版本、运行时、ModLoader 行为（`PatchAll` 自动调用）。
- [ ] 用 `ilspycmd` 找到要改的唯一位置，确认调用点数量。
- [ ] 判断需不需要 Harmony：能用数据/静态列表/Hook 解决的，不写补丁。
- [ ] 确认 capability 模型，文件读写走 `ModHelper`。
- [ ] 确认存档影响：新增 tag/字段会不会读档回滚、刷物品。
- [ ] 新增物品时，列一遍原版工厂「顺手做掉的事」：`IS_OWNED_TAG`、`uniqueId`、来源 tag、重量、分类、`Init*Helper`。
- [ ] 新增「会进画面」的内容时，找出原版是从**图集**还是**mod 精灵包**取图（水培立绘、预览、图标各自不同）。
- [ ] 改原版物品：确认它**唯一**的创建入口（通常是 `XxxItemDirectory` 里的 `Add(id, () => 工厂(...))`），以及这个工厂跑完时哪些字段已就绪（`identifier` 多半还是 null）。
- [ ] 改物品类型/标签前，全库 grep 这个标签被谁读：求购客、拒收规则、展示柜统计、UI 类型行各查一遍，把副作用先列出来。
- [ ] 改任何一个数字（价格、上限、倍率）前，先找到原版的同档锚点，并算一遍经济账。

### 每次改动后

- [ ] `dotnet build` 0 warning。
- [ ] 关游戏再部署（DLL 会锁），部署后核对 `build/` 与 `Mods/` 两份 sha256 一致。
- [ ] 启动日志：`Loading`、`Harmony: N patched`、locale 数量、异常堆栈；顺带看有没有新增的 `was not found` 类警告。
- [ ] 补丁类改动：确认 mod 自己的"首次命中"日志出现，并且是**新生成一件物品**之后才出现。
- [ ] 反编译或离线数值核对这次改动的常量/分支。
- [ ] 游戏内用快捷手段跑一轮（`turbo_booster` 之类的「一次一周期」道具），读工具提示里的状态/进度/数值。
- [ ] 人眼看一遍布局和文案。

### 发布前

- [ ] 干净安装：`Mods/` 下只留发布包一份。
- [ ] 包内只有运行时文件，`preview` < 1 MB（包内 640×360，工坊 1280×720）。
- [ ] manifest 名称/版本/描述/GameVersions 正确。
- [ ] VDF 的 `publishedfileid` / `visibility` 是想要的值，`changenote` 已更新。
- [ ] 上传后看 `workshop_log.txt` 的 `OK`，并到页面确认封面和描述。
- [ ] 检查 `steamcmd` 日志里没有明文凭据。

## 9. 如果重来

1. 每个 mod 开工先写"平台探针"（一个最小 DLL，验证 Hook/补丁/日志），再写正式功能。
2. 所有"弱效/劣质/违规"判定，先查原版有没有惩罚逻辑，再决定物品标签。
3. 打包脚本第一天就做成"保留 id、保留 visibility、校验体积"，别等到第二次上传才改。
4. 封面从第一天就拆成"关键图"和"排版"两步，脚本化，尺寸/体积作为验收项。
5. 验证顺序固定为：编译 → 反编译 → 离线数值 → 游戏日志 → 人眼，任何一步失败都不进入下一步。
6. 部署脚本永远先复制会被锁的文件（DLL），再动可重建的文件（语言包、贴图）。
7. 新物品第一天就把原版工厂的隐藏约定抄全（`IS_OWNED_TAG`、`uniqueId`、来源、重量），别等 UI 报「未拥有」才回头查。
8. 遇到「找不到就退化成占位图 + 刷日志」的取图路径，连日志噪音一起修；不然下一个人会以为 bug 还在。
9. **每个补丁从第一行就配一条"首次命中"日志**：`patched` 只证明挂上了，`Applied` 才证明生效。
10. 改原版物品的工厂补丁，先把「工厂返回时哪些字段已就绪」列成表（`identifier` 几乎总是 null），再写判断条件。
11. 改标签/类型/数值之前先全库 grep 这个标识被谁读，把玩家能感知的副作用写进描述或更新说明；数字要有原版锚点。

## 10. 附录：常用工具与路径

| 用途 | 位置 / 用法 |
|---|---|
| 反编译 | `~/.dotnet/tools/.store/ilspycmd/11.2.0.10050/.../ilspycmd.exe -t <类名> <Assembly-CSharp.dll>`；已导出的源码在 `probably_stolen_decomp/` |
| 素材导出 | `pip install UnityPy`，脚本示例 `ScavGame/scripts/extract_game_refs.py`、`Pharmacy/scripts/extract_sprites.py` |
| Python | `C:\Users\zszzl\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`（带 Pillow / numpy；UnityPy 需另装） |
| 生图 | 本地 ComfyUI `http://127.0.0.1:8188`，入口 `F:\随笔集\完全自由的异世界之旅\04_工具\qwen_img.py` 的 `generate(...)` |
| 封面排版 | 每个模组的 `scripts/make_cover.py`（PIL，1280×720，统一版式）；`--zoom/--dx/--dy` 可直接重构图 |
| 本地信任 | `tools/trust_local.py --folder <Mods/xxx> --id <mod id> --dll <dll>`：按 `ModTrust.ModFingerprint` 重算 manifest/combined/folderHash 并写进存档，游戏关闭时跑 |
| 上传 | `C:\steamcmd\steamcmd.exe +login <账号> +workshop_build_item <vdf> +quit`；日志在 `C:\steamcmd\logs\workshop_log.txt` |
| 游戏 | `F:\SteamLibrary\steamapps\common\Probably Stolen`，Mods 在游戏根目录 `Mods/` |

## 11. 未解决 / 待办

- 拾荒手记条目仍是隐藏状态，需作者手动公开；英文界面的视觉验收也还没做。
- 下层药房更新前做好的旧存货是否会带着旧 `CHEMICAL_INTENT_TAG` 继续触发投诉，没有实机验证。
- Steam 预览图 CDN 在本机不可达，上传后的封面无法自动抓回比对，只能靠页面人眼确认。
- `steamcmd` 账号密码曾以明文形式在本地日志中存在约 5 小时，已脱敏，但改密码这件事尚未确认。
- 《还原蕨 / Reduction Fern》已上架（3844217940）：P1–P5 全部完成，包 `dist/ReductionFern-v0.1.0.zip`；它对 `Hydroponic Seed Preview` 的兼容层依赖对方内部方法名 `AddPreview`，对方大改后需要重验（失效时只会静默跳过，不会崩）。
- 《更好的奥克莫吸注射器 / Luxury Nomore Injector》还没打包上架：`scripts/package.sh`、`packaging/README.txt`、`packaging/UPLOAD.md` 未做；部署目录还缺 `preview.png`（补完要重跑 `trust_local.py`，`folderHash` 会变）。可选：给老存档里已有的注射器补一次类型 + 改价。
- 奢侈品标签会让「买水的客人」拒收这支药（`IsRefusingLuxuryItem`），目前只写进了复盘、没写进工坊描述；下次更新说明补一句。
