# 《拾荒手记 / Scavenger's Notes》开发复盘

> 2026-11-18 · v0.3.0 · 从技术探针到工坊发布包

## 0. 一句话

这次真正花时间的不是“写一个 6×4 网格”，而是三件事：把原版拾荒的判定拆对、把 UI 重建和玩家操作区分开、把验证从“看屏幕”改成“看状态”。

## 1. 交付结果

| 项 | 结果 |
|---|---|
| 游戏 | *Probably Stolen* 0.46D，Unity 2021.3.45f2 Mono |
| 形态 | 6×4 / 24 格，进本时用原版判定预生成，点击只结算 |
| 核心文件 | `mod/src/ArcadeWindow.cs` 约 2000 行；`ArcadePatches.cs`、`TextBank.cs`、`ScavArcadeMod.cs` |
| 本地化 | 中英各 166 条；启动日志 `2 locale(s), 332 localization entries loaded` |
| 音效 | 5 个自生成三角波 WAV |
| 自检 | 上一轮 `PASS=32 FAIL=0`；新增线索断言后尚未重跑 |
| 构建 | 0 warning / 0 error；部署 hash `de469b` |
| 发布包 | `dist/ScavengerNotes-0.3.0.zip` 约 397 KB |
| 封面 | 1280×720，`preview.png` 约 337 KB，低于 Steam 1 MB 限制 |
| 文档 | 工坊中英文案、SteamCMD VDF、干净安装说明 |

## 2. 做对的五个决策

### 2.1 先做一次性探针，再写正式工程

先用 `ScavProbe` 验证 `ModHook` 进出垃圾场、空窗口、音效、层级、Harmony 补丁，再动正式结构。  
好处是：所有“这游戏能不能这么改”的问题，在正式代码之前就有了答案，后面踩的坑基本都是业务逻辑，不是平台未知。

### 2.2 原版判定预生成，点击只结算

进本时对 24 格各跑一次原版掉落/受伤判定，点击时只揭示已经生成好的结果。  
这个设计同时解决了三个问题：

- 掉落、伤害、幸运、免疫仍然走原版，平衡不会被我改坏。
- 关窗重开不会重 roll，避免“刷新棋盘”的刷物品漏洞。
- 线索可以基于真实结果生成，不会出现“线索和实际不一致”。

### 2.3 线索以“点击格”为单位缓存

这是最后才想明白、但最关键的模型：

- `clued[source]` 只解决“同一个来源不要重复指”。
- `clueText[click]` / `clueSource[click]` 解决“同一个点击只产生一次线索”。
- `ShowClueForLast()` 只回放，`GenerateClue()` 才抽取。

把“生成线索”和“显示线索”分开之后，窗口重建、包扎恢复、关窗重开都不会再偷偷消耗一个候选。

### 2.4 敢砍

砍掉了：夜间遭遇、逐件揭示动画、快速模式/文本速度/难度配置。  
这些功能都“能做”，但都不改变核心循环；每砍一个，就少一套文案、一套状态、一套测试。  
最终保留下来的只有：网格、线索、工具、受伤暂停、多件标签、音效。

### 2.5 把自测放进 mod 里

AutoHotkey 做屏幕级自动化失败之后，改用 mod 内部的 `AutoTest`：

- 用 `ModHelper` 的 ModData API 放 `autotest.flag`。
- `OnArrive("dumping_ground")` 后自动跑：开窗、棋盘、密封箱、手电、放大镜、多件、点击。
- 结果写 `autotest-report.txt`，不依赖窗口焦点和鼠标坐标。

结论：能进程内验证的，不要做屏幕级自动化；屏幕级只留给最终视觉验收。

## 3. 踩过的坑

| 现象 | 根因 | 修法 / 教训 |
|---|---|---|
| 密封箱线索报“机器零件” | `价值 ≥70 → clue.rare` 优先级高于类型 | 类型优先：箱/机/空 → 基础/多件才用稀有 |
| 线索指到 8 邻外，还标绿远处格子 | 旧逻辑取全场最高价值 | 候选只取 8 邻；不在 8 邻内不标记、不揭示 |
| 同一格连续给线索 | `clued` 只记录“给过线索的来源”，但每次点击仍重新抽取 | 增加 `clueText[click]` / `clueSource[click]`，一个点击只抽一次 |
| 关窗重开又出一条线索 | `Open()` 重建窗口时再次调用 `UpdateClue()`；`clued` 本身没坏 | **日志证据**：点 15 后 `clue.sealed source=10`，紧接着 `clue.extra source=21`，然后才 `window opened`。改成 `ShowClueForLast()` 只回放 |
| 中文硬编码漏网 | 单字标记、罗盘、物品名分隔、入口按钮不在 CSV | 抽 `mark.*`、`dir.*`、`ui.list_sep`、`ui.enter`、`ui.legend`，全量扫源码 |
| mod 被拒载：未声明文件权限 | 用了 `System.IO` 读写 flag/report | 改用 `ModHelper.GetModDataFolder` / `WriteModDataFileText`；manifest 保持 `<Capabilities />` |
| 自测 flag 不触发 | `harness.scav-arcade` 被 ModData 目录把 `.` 换成 `_` | 实际路径是 `harness_scav-arcade`；用 API，别硬编码 |
| 干净安装出现重复 ID | `ScavArcade.bak` 留在 `Mods/` 里，ModLoader 会扫描 | 备份必须放到 `Mods/` 外 |
| 预览图超过 1 MB | 1280×720 原图约 1.1 MB | 256 色 + Floyd 抖动 → 337 KB，PSNR 约 41 dB |
| 本地生图出抽象纹理 | 文生图用错文本编码器：`qwen3.5_9b...pe_i2i` 不是 T2I 那一路 | 换 `qwen3vl_8b_w4a8`；模型组件要按官方 T2I 组合配对 |
| 文档和代码漂移 | 手改 README/MEMO/两份 CSV | 计数、规则、hash 尽量自动生成；至少用脚本做 key/占位符对比 |

### 3.1 最值得记住的一次误判

线索“重复”问题，第一反应是 `clued` 去重没生效，于是继续加排除逻辑。  
实际日志显示：**同一点击产生了两次线索**，第二次来自窗口重建，不是来自下一次点击。

教训：

- 先看“状态在什么时候被谁改了”，再看“条件写没写对”。
- 任何会在 `Open()` / `Refresh()` / `Show()` 里被调用的方法，都必须是幂等的，或者只读缓存。
- 随机逻辑不要放在渲染路径上。

## 4. 技术经验

### 4.1 Mod / Harmony

- 优先 `ModHook` 生命周期；需要 UI 时再 Harmony。
- Prefix 里用 `return !ArcadeWindow.Open()` 决定是否吞掉原版行为；补丁方法全部 try/catch。
- `ItemSpawner.Spawn` 的 Postfix 用来精确归因材料工具，比在掉落表里猜 ID 可靠。
- 修改 UI 时，`MapUIManager.Return/ReturnNow` 都要收口，否则从不同路径退出会留下窗口。
- 任何 BCL 文件 IO 先查 capability 模型；有 ModHelper API 就用 API。

### 4.2 UI / 状态

- `CustomUIElement` 的文本/颜色/交互要显式恢复；`MarkCell` 同时负责“显示”和“`revealed` 状态”，调用点要清楚是消费还是揭示。
- 窗口重建会重新跑构建代码，所有显示逻辑要能从状态数组恢复。
- 网格按钮是 62×62；英文标记用 `H/E/B/M/I`，配合开头图例行，比塞 4 个字母更稳。
- 日志是第二套 UI：`cell`、`clue`、`window opened`、`resumed` 这几类事件要能拼出完整因果链。

### 4.3 本地化

- key 前缀 `scavarcade.` 由 `TextBank` 统一加。
- CSV 必须逐条对齐 key 和 `{0}`；这次用 Perl 一次性校验了 166 条，key/占位符完全一致。
- 英文不是逐字翻：`Searches left`、`Shine`、`Inspect`、`Bandage to continue` 都是按 UI 语义重写的。
- 最容易漏的不是长文案，是单字标记、方向、分隔符、按钮；做本地化时要先列“所有玩家可见字符串”的清单。
- Steam 预览图 1 MB 限制会反过来影响封面导出策略。

### 4.4 音效与封面

- 音效：`ffmpeg` 生成三角波，短、轻、不盖原版 debris；5 个文件分别对应开窗/点击/稀有/受伤/结算。
- 封面：本地 ComfyUI + Qwen-Image 2.1 Turbo（int8 UNet + Qwen3-VL 8B 文本编码器 + VAE + Turbo LoRA），1280×720，8 steps / cfg 1 / shift 0.69。
- 生图只负责画面，标题和排版交给 ImageMagick；不要把文字交给生图模型。
- 判断封面不要只看“好不好看”，要看：缩略图主体是否清楚、标题区是否有干净暗部、文字是否压到脸/手/光柱。
- 这次最终采用用户专用流程交付的 A 构图，我只做标题排版和压缩；分工比让一个模型全包更稳。

### 4.5 发布

- 发布包只放运行时需要的文件：`manifest.xml`、DLL、`Localization/`、`Sounds/`、`preview.png`、`README.md`。
- `preview.png` 1280×720、337 KB；Steam 1 MB 限制下留了足够余量。
- SteamCMD VDF 用 `publishedfileid 0` 首次创建，`visibility 2` 先私有；上传后回填 ID。
- 干净安装要真的把 `Mods/ScavArcade` 移走再装，不能只看旧目录还能启动。

## 5. 协作经验

### 5.1 有效的部分

- 需求拍板很快：“砍遭遇 / 砍动画 / 不做配置 / 最后做发布”，每次都能立刻缩小范围。
- Bug 报告带可观察行为（“箱子给机器线索”“8 邻外也被揭示”“同一格重复”），比“感觉不对”好定位。
- 构建 → 部署 → 日志 → 下一版 的循环很短；hash 和 `PASS/FAIL` 让每次改动可追踪。
- 人肉测试发现了自检没覆盖的线索问题；自检覆盖结构，人眼覆盖“看起来对不对”。

### 5.2 不够好的部分

- 在线索重复问题上，先信代码、后看日志，绕了一圈；应该第一步就把 `cell`/`clue`/`opened` 的时间序列拉出来。
- 在 AutoHotkey 屏幕自动化上投入过多；窗口焦点、缩放、输入注入都不稳定，应该更早切到 mod 内自测。
- 文档多次落后于代码：README 一度还写“重开重新生成”、MEMO 还留旧 hash、CSV 从 150 条变 166 条后计数没同步。
- 英文只验证了“加载 332 条”，没有真正切英文看布局；这是发布前还欠的一次目视验收。
- 发布包和封面都做完后，`MEMO` 里仍有一些旧 hash/旧结论，说明“只记没解决的事”的备忘录也需要定期清理。

## 6. 如果重来

1. **先画状态机**：`BoardOpened`、`CellOpened`、`ClueShown`、`Paused`、`Resumed`、`Ended`，每个事件只允许改一次状态。
2. **先写纯函数**：`SelectClueSource(board, click)`、`SettleCell(cell)` 不依赖 UI，方便直接测。
3. **自测从第一天就进 mod**：不要等 UI 自动化失败才做。
4. **本地化从第一天就用 key**：单字标记、方向、按钮、分隔符全部进 CSV；加一个 key/占位符对比脚本。
5. **拆文件**：`ArcadeWindow` 2000 行能跑，但定位线索/工具/棋盘逻辑时成本很高；至少拆成 Board / Clue / Tools / UI / Tests。
6. **文档生成化**：README 的规则、CSV 条数、hash 尽量从代码/文件生成，减少手改。
7. **备份永远放 `Mods/` 外**；发布前跑一次真正的干净安装。
8. **封面先定排版安全区，再生成画面**；标题区和主体分开考虑，别让生图模型顺便写字。

## 7. 可复用清单

### 新 mod 开工前

- [ ] 确认游戏版本、Unity/运行时、ModLoader 版本。
- [ ] 确认可用的 Hook / Harmony 目标，先做一次性探针。
- [ ] 确认 capability 模型：哪些 API 需要声明，哪些有 ModHelper 替代。
- [ ] 确认存档行为：是否新增字段、读档回滚会不会刷物品。
- [ ] 确认 UI 尺寸、最小分辨率、字体/中文支持。

### 每次改动后

- [ ] `dotnet build -t:Rebuild` 0 warning。
- [ ] 游戏关闭再部署；部署后核对 DLL hash。
- [ ] 启动日志有无 `enabled`、locale 数、异常堆栈。
- [ ] 自检 flag / 报告；结构断言是否覆盖这次改动。
- [ ] 人肉看一遍：布局、文本溢出、颜色、音效。
- [ ] 更新 MEMO/README/CSV 计数，不留旧 hash。

### 发布前

- [ ] 干净安装：`Mods` 下只留发布包一份，启动无重复 ID/信任拦截。
- [ ] `preview.png` 1280×720，<1 MB；缩略图能读标题。
- [ ] manifest 名称/版本/描述/GameVersions 正确。
- [ ] zip 里没有 `obj/`、`build/`、`.bak`、`art/`。
- [ ] 工坊标题、短描述、full description、VDF 路径一致。
- [ ] 实际上传后回填 `publishedfileid`，再改公开。

## 8. 还没解决的

- SteamCMD 实际上传（需要账号和 Steam Guard），以及上传后的页面检查。
- 卸载后读档是否正常，没有单独跑。
- 英文界面只验证了加载，没有切英文做视觉验收。
- 自检新增的线索绑定断言还没重跑；机器格、空格、无撬棍仍可能被跳过。
- 免疫在游戏里不可见；扫描仪双倍仍会让格子变绿；密封箱数量与计划书不一致；读档回滚、背包满计数、线索稀有文案、780×600 布局都还没收口。
- `mod/src/ArcadeWindow.cs.bak2` 和部分旧文档还在；`MEMO` 里仍有旧 hash / 旧 PASS 行。

## 9. 结论

这次最值钱的经验不是“怎么用 Harmony”，而是：

> **把随机和状态从 UI 生命周期里拿出来，把验证从屏幕搬到状态，把“看起来像 bug”先还原成一条事件时间线。**

只要这三件事做到，mod 的功能可以慢慢加；做不到，功能越多，重复和不可复现的问题就越多。
