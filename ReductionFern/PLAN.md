# 还原蕨 Mod — 计划书 v0.4（三档产量）

> 状态：**P1 骨架完成并实机验收**（加载、物品注册、种植、生长、收获、`_p` 立绘、拥有标记、第三方预览兼容均已验）；P2 产出数值待验，P3–P5 未做。开发经验与踩坑见同目录 `RETROSPECTIVE.md`。
> v0.4（2026-11-22）：产物改成**三档同 ID**（小叶 20.5 g / 标准 40 g / 大叶 75 g，按血量出），所有数值按 0.25 ml 还原剂/克、0.45 信用点/克重算；梦帽菇与咖啡的对照数字也按满血出大果修正（见 §4.1）。D7 见 §10.1。
> v0.3（2026-11-22）：D1–D5 拍板（Reduction Fern / 网络升级 2 颗孢子 / 120 ml 一茬 / 全合法 / 不做专属模组），参数冻结，可进 P1。
> v0.2（2026-11-22）：D6 定为「对齐原版」——注册完产出特质后把 `potent`/`weak` 挪到有序表末尾；效力强 I → 18.75 ml/片，效力弱 I → 11.25 ml/片。
> 对象：深空当铺（Probably Stolen）0.46D，Unity 2021.3.45f2 / Mono，内置 ModLoader + Harmony。
> 工作名 `ReductionFern`；模组 ID `harness.reduction-fern`（沿用 `harness.filter-printer` / `harness.district-pharmacy` 命名）。
> 原版数字全部来自本仓库反编译 `probably_stolen_decomp/`，行号可直接跳过去看。

---

## 0. 一句话目标

加一种**能种出还原剂**的合法作物：孢子 → 还原蕨 → 还原蕨叶 → 搅碎得还原剂，把目前只能拆违禁化学品箱才拿得到的试剂，变成一条可自给的农业线。

### 为什么要它

- 还原剂（`reducing_agent`）是奥克莫吸合成的必需试剂：梦帽菇萃取液 + 等量还原剂 + 1/4 脂合剂，45–55 °C（`note_li_formula_s4_body`）。
- 原版里它没有正常购买渠道：代码里唯一的成品来源是**违禁**化学品补给箱——价值 100、违禁等级 2，拆开给 2 瓶芬太前体 + 1 瓶 250 ml 还原剂（`MaterialDirectory.cs:136-155`）。战利品表是数据资产、没有逐条审计，但不影响这个定位。
- 所以「合法种出还原剂」本身就是一个有位置的缺口，而不是又一件可卖的东西。副产品是它和 `Pharmacy`（澄心剂）、`FilterPrinter` 能串成一条产业链。

---

## 1. 参考对象（已核对反编译）

### 1.1 梦帽菇 —— 植物结构参考

| 项 | 原版值 | 出处 |
|---|---|---|
| 植物 ID / 种子物品 | `dream_cap_seed` | `PlantList.cs:54` |
| 产物物品 | `dream_cap`（梦帽菇） | `HydroponicDirectory.cs:109-121` |
| 生长进度 | 28 | `PlantList.cs:54` |
| 基础产量 | 8 | 同上 |
| 养分 | 250 ± 75，消耗 30 | `.Nutriment(250, 75, 30)` |
| 污染系数 | 1.01（几乎不敏感） | `.Contaminant(1.01)` |
| 耗水 | 未调用 `.Water()` → 默认 100 ml/次 | `PlantDefinition.cs:24` |
| 返还种子 | 是（收获时输出 1 颗） | `PlantList.cs:188` |
| 天生特质 | 产出梦帽菇糊（2 ml，复杂度 4）+ 效力弱（−25% 活性成分）+ 丰产（+25% 种子） | `PlantList.cs:55-57` |
| 收获 | 8 个，按血量拆小/中/大三档物品；有中和模组时改出食用帽菇 | `PlantList.cs:185-197` |

关键点：每颗梦帽菇的物品组成里**本来就带 27.33 ml 梦帽菇糊**（`ChemicalCompositionHelper.cs:19-46`），产出特质只是在这之上再加，并且会吃「效力弱」的 −25%。所以「产出还原剂 I」的 5 ml 是**特质加成**，不是这株的全部产量——叶子基础还带 10 ml。

### 1.2 咖啡 —— 产出与收获写法参考

| 项 | 原版值 | 出处 |
|---|---|---|
| 植物 ID | `coffee_bean`（种子本身就是可种物品） | `PlantList.cs:60` |
| 生长进度 / 产量 | 21 / 8 | 同上 |
| 耗水 | 默认 100 ml/次 | 同上 |
| 返还种子 | 否（种一次消耗一颗） | 同上 |
| 天生特质 | 产出咖啡因（2 ml，复杂度 3）、产出咖啡豆糊（10 ml，复杂度 2）、效力强（+25% 活性成分） | `PlantList.cs:60-62`、`PlantTraitList.cs:177-178` |
| 产物组成 | 配方基准 50 g；实际豆重 80 g → 每颗 25.84 ml 咖啡豆糊 + 4.4 ml 咖啡因 | `ChemicalCompositionHelper.cs:53-63`、`HydroponicDirectory.cs:103` |
| 收获 | **单一物品 ID × 数量**，按血量乘算（≤15 血 ×0.5、≤30 ×0.6、≤50 ×0.7、≤70 ×0.8），最少 1 | `PlantList.cs:199-219` |

### 1.3 结论：还原蕨怎么长

1. **结构照梦帽菇**：孢子是种子，收获物是另一种物品（不是「种子即产物」），收获返还 1 颗孢子 → 单株即可永续。
2. **收获照梦帽菇（三档）**：只做一种物品 `restoring_fern`，但按血量拆小/标/大三档（20.5 / 40 / 75 g），三档共用一张图集、三种精灵尺寸——这样「养得好→出大叶」的原版手感保留，物品 ID 仍然只有一个。
3. **产出照原版 `production_` 特质**：液体用现成的 `reducing_agent`，显示名、提示文案全部走原版模板，不新增液体、不加新 key。

---

## 2. ID 与命名（D1）

| 项 | 值 | 说明 |
|---|---|---|
| 模组 ID | `harness.reduction-fern` | 与现有三个模组同前缀 |
| 植物 ID | `restoring_fern_seed` | 与原版 `<plant>_seed` 习惯一致；`PlantRegistry` 的 key 也是它 |
| 孢子物品 ID | `restoring_fern_seed` | 植物 ID = 种子物品 ID（梦帽菇同款） |
| 产物物品 ID | `restoring_fern` | 收获物 = 植物 ID 去掉 `_seed`（梦帽菇同款） |
| 产出特质 ID | `production_reducing_agent` | `PlantTraitList.ProductionId()` 的拼法，必须完全一致 |
| 中文名 | 还原蕨 / 还原蕨孢子 / 还原蕨叶 | 孢子比「种子」更贴切，也对上「梦帽菇孢子」 |
| 英文名 | Reduction Fern / Reduction Fern Spores / Reduction Fern Fronds | **不用 Restoring**：这里的「还原」是化学还原，不是「恢复」 |
| 贴图 key | `restoring_fern_seed` / `restoring_fern` / `restoring_fern_p` | `_p` 是水培槽里的立绘 |

> **D1 已定：`Reduction Fern`**（2026-11-22）。备选 `Reducer Fern`（更短，但玩家不一定懂）与 `Restoring Fern`（只在对「还原=恢复」的双关时才用）均不采用——这里的「还原」是化学还原。

> 关于模组 ID：v1 只做这一株，按窄 ID `harness.reduction-fern` 冻结。以后若真要做「产酸蕨」「产碱蕨」系列，用**新的模组 ID + 新物品 ID** 另起一个包，不迁移旧存档——物品 ID 可以随时加，模组 ID 一改会让已存档物品的精灵命名空间对不上（现在改便宜、以后改贵，所以这条先按住不动）。

---

## 3. 参数总表

### 3.1 植物定义

| 字段 | 值 | 梦帽菇 | 说明 |
|---|---|---|---|
| `requiredProgress` | **26** | 28 | 基础速度 8/次 → 4 次机器动作（`MachineHydroponic.cs:6`）；比梦帽菇略快，但仍在同一档 |
| `harvestQuantity` | **8** | 8 | 满血 8 片叶，按血量拆小/标/大（§3.3） |
| `Nutriment` | **250 / 75 / 30** | 同 | 与梦帽菇、咖啡完全一致 |
| `Contaminant` | **1.01** | 同 1.01 | 不额外惩罚水质 |
| `Water` | **不调用**（默认 100） | 100 | 耐旱 I 后实际 75 ml/次 |
| `ReturnsSeeds()` | **是** | 是 | 收获返还 1 颗孢子 |
| 天生特质 | `drought_resistant` 1、`production_reducing_agent` 1 | — | 只有这两条，不加负面特质 |
| `onHarvest` | `SplitByHealth` 三档拆分 + 返还孢子（照梦帽菇） | 三档拆分 | 见 §5.2 |

### 3.2 特质

| 特质 | 来源 | 复杂度 | 效果 | 备注 |
|---|---|---|---|---|
| 耐旱 I | 原版 `drought_resistant`（`PlantTraitList.cs:149`） | 2 | 耗水 −25%（每级 ×rank^0.75，无上限） | rank I 时 100 → 75 ml/次 |
| 产出还原剂 I | **新增** `production_reducing_agent` | 3 | 每片叶 +5 ml 还原剂（每级 ×rank^0.75，无上限） | 显示名/描述走原版模板，见下 |

- 基础复杂度 = 2 + 3 = **5** → 基因编辑成功率 70%、单次进度 40（`PlantGeneticsHelper.cs:243-256`）。比梦帽菇（4）稍难，比咖啡（8）容易，符合「两条正面特质」的定位。
- 原版所有 `production_` 特质都不绑作物（没有 `RequiresCrop`），所以「产出还原剂」也能被抽成基因盘、接到梦帽菇或咖啡上——这是原版育种玩法的一部分，不是漏洞。要禁止就得额外加作物限制，但那会跟原版行为不一致。
- 产出特质的显示文案由原版自动拼出，**不需要新 key**：
  - 名称：`产出{0}` + `还原剂` → 「产出还原剂」
  - 描述：`每件收获物都带有{0}。` → 「每件收获物都带有还原剂。」
  - 效果：`每件收获物中增加{0}毫升的{1}。` → 「每件收获物中增加5毫升的还原剂。」
  - 出处：`PlantGeneticsText.cs:53-70` + 游戏 Mechanic 语言表（`mech_dna_production_name` / `_desc` / `mech_dna_effect_production`）。

### 3.3 产物：还原蕨叶 `restoring_fern`（三档同 ID）

和一株多果的梦帽菇一样：**同一个物品 ID，三种尺寸**，只是换精灵、重量、含量与价值。重量照梦帽菇的三档 20.5 / 40 / 75 g。

| 字段 | 小叶 `_s` | 标准叶 | 大叶 `_l` |
|---|---|---|---|
| 重量 | 20.5 g | 40 g | 75 g |
| 基础价值 | 9 | **18** | 34 |
| 还原剂（基础） | 5.13 ml | **10 ml** | 18.75 ml |
| 水 | 7.18 | 14 | 26.25 |
| 植物质 | 5.13 | 10 | 18.75 |
| 脂肪 | 1.03 | 2 | 3.75 |
| 矿物质 | 0.26 | 0.5 | 0.94 |
| 物理污染物 | 0.77 | 1.5 | 2.81 |
| 微生物 | 0.51 | 1 | 1.88 |
| 单叶还原剂（含 +5 特质） | 10.1 ml | **15 ml** | 23.75 ml |

- 换算基准（写代码时用常量，不要手抄表）：**还原剂 0.25 ml/g、价值 0.45 信用点/g、热量 1.2 kcal/g**；其余成分按标准叶的 40 g 配方等比缩放。
- 物品类型、违禁、音效、`ApplyFactoryGenetics` 三档一致：`CHEMICAL_SUPPLIES` + `MATERIAL` + `CHEM_ITEM_TAG` / `BLENDABLE_TAG`，**全部合法**，`AudioHelper.InitLeafy`，工厂里 `ApplyFactoryGenetics(item, "restoring_fern_seed")`。`MATERIAL` 是 P1 实测后补的（否则熔炉和材料类客户不认）。
- **可食用基因兼容**：叶子的 `FOOD` 不由我们写死，而是留给 `edible` 特质——收获时 `MakeEdible` 会把每一片叶原地改成 `FOOD` + `PLANT_EDIBLE_PRODUCE_TAG` 并给 100 kcal（原版梦帽菇同一条路径）。我们要做的只有三件事：① 工厂里照原版给一个按克重的热量底座（`FoodItemHelper.InitFoodItem`，40 g = 48 kcal）；② `onLoaded` 里若带 `PLANT_EDIBLE_PRODUCE_TAG` 就调一次 `PlantTraitList.LoadEdibleProduce`；③ 别在工厂/`onLoaded` 里 `RemoveGameItemType("FOOD")` 或重置类型。
- 用法不变：丢搅拌机、挂液体容器，还原剂随水分和植物质一起进容器，再过滤/纯化——产的是**原料**，接 `FilterPrinter`。

### 3.4 孢子 `restoring_fern_seed`

| 字段 | 值 |
|---|---|
| 物品类型 | `SEED` |
| 违禁 | 否 |
| 基础价值 | **28** 信用点/颗 |
| 初始化 | `HydroponicHelper.InitSeedItem(item, "restoring_fern_seed")` |
| 说明 | 返还 1 颗/茬，单株永续；价格是「一次投入」，所以比梦帽菇孢子（24）略贵 |

---

## 4. 数值验算

### 4.1 一茬（满血、rank I、无模组）

> 原版对照数字修正：`SplitByHealth` 在血量 > 90 时**全部出大果**（`PlantHarvest.cs:85-88`），所以满血的梦帽菇是 8 颗 75 g 大帽、咖啡是 8 颗 80 g 豆。v0.3 里按 32.5 g / 50 g 算的 176 / 309 ml 是「中等果」的数字。

| 项 | 还原蕨（满血=8 片大叶） | 梦帽菇（8 颗大帽） | 咖啡（8 颗豆） |
|---|---|---|---|
| 机器动作 | 4 次（26 ÷ 8 上取整） | 4 次（28） | 3 次（21） |
| 耗水 | 4 × 75 = **300 ml** | 4 × 100 = 400 ml | 3 × 100 = 300 ml |
| 产物 | 8 片 75 g 大叶 | 8 颗 75 g 大帽 | 8 颗 80 g 豆 |
| 有效成分 | 8 × 23.75 = **190 ml** 还原剂 | 8 × 48.8 ≈ 390 ml 梦帽菇糊 | 8 × 52.8 ≈ 422 ml（糊+咖啡因） |
| 基础价值 | 8 × 34 = **272** | 248 | 224 |
| 返还种子 | 1 颗 | 1 颗 | 0（要重买） |
| 每次动作 | 47.5 ml / 68 点 | 97.5 ml / 62 点 | 141 ml / 75 点 |

按血量分档（rank I、无效力强/效力弱，`harvestQuantity` 8）：

| 血量 | 会出什么 | 一茬还原剂 | 一茬价值 |
|---|---|---|---|
| ≤15 | 4 片小叶（数量 ×0.5） | 40.5 ml | 36 |
| 16–30 | 5 片：3 小 + 2 标 | 60.4 ml | 63 |
| 31–50 | 6 片：1 小 + 5 标 | 85.1 ml | 99 |
| 51–70 | 7 片标准叶 | 105 ml | 126 |
| 71–80 | 8 片：6 标 + 2 大 | 137.5 ml | 176 |
| 81–90 | 8 片：2 标 + 6 大 | 172.5 ml | 240 |
| 91–100 | 8 片大叶 | **190 ml** | **272** |

结论：满血产量比梦帽菇低一半、和咖啡同级但**合法、可再生、省水**；品种定位是「试剂田」不是「摇钱树」。D3 冻结的 120 ml 对应的是**标准叶**（血量 51–70 或 71 以上出标准叶的场合），满血因为出大叶变成 190 ml——这是照搬原版「养得好→出大果」的机制，不是数值膨胀。价值一栏比梦帽菇略高（272 vs 248），是因为还原剂本身的单价高于梦帽菇糊；它是「卖原料换钱」，不是「卖成品赚差价」，实际收益还要扣孢子和水电。

### 4.2 与现有还原剂来源对比

- 违禁化学品箱：价值 100 / 违禁 2 → 250 ml 还原剂 + 2 瓶芬太前体。
- 还原蕨一茬：满血 190 ml（标准叶 105–120 ml），成本是 1 颗孢子（一次性）+ 300 ml 水 + 4 次机器动作。
- 也就是**约 1.3 茬（满血）≈ 1 个违禁箱的还原剂**；养得差一点要 2–3 茬。这是有意的：农场省的是「跑违禁渠道的风险」，不是「完全替代采购」。

### 4.3 育种曲线（每片叶 / 每茬）

标准叶（40 g，基础 10 ml）随特质等级：

| 特质等级 | 特质加成 | 单片还原剂 | 每茬（8 片） |
|---|---|---|---|
| I | 5.0 | 15.0 | 120 |
| II | 8.4 | 18.4 | 147 |
| IV | 14.1 | 24.1 | 193 |
| VI | 19.2 | 29.2 | 234 |
| X | 28.1 | 38.1 | 305 |
| XVI | 40.0 | 50.0 | 400 |
| XX | 47.3 | 57.3 | 458 |

（加成 = 5 × rank^0.75，`PlantGeneticsHelper.cs:54-61`；基础 10 ml 不随等级变。）

小叶 / 大叶只把「基础 10 ml」换成 5.13 / 18.75，**特质加成那一列不变**（特质是每件 +固定量，与重量无关）：满血大叶 I = 18.75 + 5 = 23.75 ml（每茬 190）；小叶 I = 5.13 + 5 = 10.1 ml；大叶 VI = 18.75 + 19.2 = 38 ml。

**效力强/效力弱的作用域（重要，v0.1 曾写错）**：原版三个产出特质排在「效力强/效力弱」**之前**注册（`PlantTraitList.cs:177-193`），而 `RunHarvestHooks` 严格按 `PlantTraitRegistry.All` 的注册顺序执行（`PlantGeneticsHelper.cs:474-492`、`PlantTraitRegistry.cs:9-31`）。所以原版梦帽菇的 `weak` 会把「物品自带 27.33 ml + 特质 2 ml」**一起**乘 0.75（32.5 g 标准帽 22 ml/颗；满血 75 g 大帽 48.8 ml/颗）；咖啡的 `potent` 也把 10 ml 特质加成一起乘 1.25（80 g 豆 52.8 ml/颗）。mod 特质默认追加在末尾，会漏掉这层乘算，和原版口径不一致——v1 **按 D6 对齐原版**：用公开 API 把 `potent`/`weak` 重新 Add 一次挪到末尾（§5.4 第 7 条）。

对齐后（标准叶 40 g）：效力弱 I → (10 + 5) × 0.75 = **11.25 ml/片（90 ml/茬）**；效力强 I → **18.75 ml/片（150 ml/茬）**。不对齐则是 12.5 / 17.5 ml/片。

大叶 75 g 同理：效力弱 I → (18.75 + 5) × 0.75 = **17.8 ml/片（满血 142.5 ml/茬）**；效力强 I → **29.7 ml/片（237.5 ml/茬）**。小叶 20.5 g：效力弱 7.6、效力强 12.7 ml/片。

---

## 5. 行为口径（写代码时按这个）

### 5.1 注册顺序

1. `Init()`：`PlantRegistry.Add(...)` 注册植物；`PlantTraitRegistry.Add(...)` 注册产出特质。两者都是公开静态方法（`PlantRegistry.cs:15`、`PlantTraitRegistry.cs:18`），不需要 Harmony。
2. 紧接着把原版 `potent`/`weak` 重新 `Add` 一次（同一对象），把它们在有序表里挪到末尾，让本 mod 的产出特质排到它们前面，和原版梦帽菇/咖啡的注册顺序一致（`PlantTraitRegistry.cs:25-31`）。
3. 物品目录注册（照 BrewingExpansion）：`OnEnable` 里先 `foreach (var d in Resources.FindObjectsOfTypeAll<ModItemDirectory>()) Register(d);`，同时挂 `ModHook.OnModItemDirectoryInit += Register`；`Register` 内先查 `d.factoryDictionary.ContainsKey(id)`，再 `d.Add(id, factory)` 并检查返回值（`Directory.Add` 返回 bool，`Directory.cs:61-72`）。`OnDisable` 时按记录的 `(directory, id)` 逐个移除。
4. 两个物品的 `name` 一律用 `ModHelper.GetLocalized(ModId, key)` 取，**不能用 `LocHelper`**（§5.4）。

### 5.2 收获

```csharp
// 照抄 HarvestDreamCap（PlantList.cs:185-197），把三档工厂换成我们的
static void HarvestRestoringFern(PlantHarvestContext ctx)
{
    PlantHarvest.SizeSplit split = PlantHarvest.SplitByHealth(
        ctx.harvestCount, ctx.health, reduceCount: true, allowHuge: false);

    ctx.OutputById("restoring_fern_seed");                       // 返还 1 颗，走原版 OutputOwnSeed
    PlantHarvest.OutputSplit(ctx, split,
        FernItems.CreateSmallFern,      // 20.5 g
        FernItems.CreateFern,           // 40 g
        FernItems.CreateLargeFern);     // 75 g
}
```

- `SplitByHealth` 的档位（`PlantHarvest.cs:38-99`）：≤15 全小；≤30 小 70%；≤50 小 30%；≤70 全标准；≤80 标准 80%；≤90 标准 30%；>90 全大。`allowHuge: false`，不会出更大一档。
- `OutputSplit` 内部对每个产物跑 `PlantGeneticsHelper.RunHarvestHooks`，所以「产出还原剂」的 +5 ml 是**逐片**加的（`PlantHarvest.cs:129-146`）——大叶不是 5 × 3，因为原版特质就是「每件收获物 +固定量」。
- 种子那一路走 `OutputOwnSeed`，会继承亲本特质；`SEED_YIELD` 默认 1.0 → 1 颗（`PlantHarvest.cs:157-187`）。

### 5.3 产出特质

原版 `PlantTraitList.Production()` 是 **private**（`PlantTraitList.cs:196`），mod 里调不到，必须自己拼同样的 20 行：

```csharp
Func<string> liquidName = () => Liquid.GetLiquidFromId("reducing_agent").displayName;

new PlantTrait("production_reducing_agent", "Reducing Agent Production", 3)
    .Named(() => PlantGeneticsText.ProductionName(liquidName()),
           () => PlantGeneticsText.ProductionDescription(liquidName()))
    .Infuses("reducing_agent")
    .Unlimited()
    .AppliesToSeedProduce()
    .OnHarvestItem(ctx => {
        if (!ctx.item.IsTag("CHEM_ITEM_TAG"))
            ChemicalHelper.InitChemItem(ctx.item, isBlendable: true);
        ChemicalHelper.AddChemContentUL(ctx.item, "reducing_agent",
            Mathf.RoundToInt(5f * PlantGeneticsHelper.RankScale(ctx.rank) * 1000f));
    })
    .Describe(rank => PlantGeneticsText.EffectProduction(
        (5f * PlantGeneticsHelper.RankScale(rank)).ToString("0.#"),
        liquidName()));
```

液体名**必须延迟取**：注册发生在 `Init()`，这时原版 `Liquid` 的显示名可能还没从语言表里加载完；用 `Func`/lambda 到提示框打开时再取，才会是「还原剂」而不是 key。不传违禁等级、不调 `ConvertedBy`，所以叶子始终合法。

### 5.4 九个必须避开的坑

1. **特质不会双份**：`ApplyFactoryGenetics` 在 `PlantHarvest.isHarvesting == true` 时直接 return（`PlantGeneticsHelper.cs:496`）——收获时工厂跳过、由 `RunHarvestHooks` 加一次；平时生成（调试、商店）时由工厂加一次。两条路径结果一致：标准叶 10 + 5 = 15 ml（大叶 18.75 + 5 = 23.75、小叶 5.13 + 5 = 10.1）。如果自己在工厂里再手写一遍加液体，才会双份。
2. **本地化用错表**：mod 的 `Localization/zh.csv` 不会进游戏的 StringTable，`LocHelper.GetLocalizedItem("item_restoring_fern_name")` 只会返回裸 key。必须用 `ModHelper.GetLocalized(ModId, key)`（`ModHelper.cs:107`）。
3. **`_p` 立绘缺失**：水培槽运行时会加载 `<harvestItemId>_p`（`MachineHydroponic.cs:88-110`），找不到就画 unknown 精灵盖在机器上。处理办法见 §6.2。
4. **精灵形状别全靠贴图**：`SetSpriteAndShapeFromMod` 按 `gridSize`（16）切格、取每格中心 alpha 定形状（`GameItem.cs:398-415`）。我们的图铺了 `(0,0,0,3)` 底，本来能算对；但保险起见三档工厂都再 `SetShape(new GridShapeBuilder(w, h).SetDataFill(w, h, 1).Build())` 兜一次（BrewingExpansion 同款做法）。
5. **名字/描述要在 `onLoaded` 里重新取**：玩家中途切语言时，存档里旧物品的名字不会自己刷新；BrewingExpansion 的每个工厂都挂 `onLoaded = Loaded` 重新 `SetName`/`shortDescription`，我们照做。
6. **mod 物品要标来源**：`ModHelper.SetSource(item, ModId, 显示名)` 会写 `MOD_ID_TAG` / `MOD_NAME_TAG`（`ModHelper.cs:172-182`），工具提示才会显示「来自某 mod」；另外要让透明像素也能点中，得把 `background.image.alphaHitTestMinimumThreshold = 0`（BrewingExpansion 的 `ItemHitArea`）。
7. **特质注册顺序会改数值**：`PlantTraitRegistry.All` 就是注册顺序，`RunHarvestHooks` 按这个顺序调用（`PlantGeneticsHelper.cs:474-492`）。原版产出特质排在效力强/效力弱之前，所以它们的加成会被乘算；mod 特质默认排在最后，会漏掉。D6 已定，**用公开 API 把原版两个特质挪到末尾**（不要反射）：

   ```csharp
   // Init() 里，注册完 production_reducing_agent 之后
   if (PlantTraitRegistry.Get(PlantTraitList.POTENT) is PlantTrait p) PlantTraitRegistry.Add(p);
   if (PlantTraitRegistry.Get(PlantTraitList.WEAK) is PlantTrait w) PlantTraitRegistry.Add(w);
   ```

   `Add` 遇到同 id 会先 `ordered.RemoveAll` 再 `ordered.Add`（`PlantTraitRegistry.cs:25-31`），所以这是「原对象挪位」：定义不变、存档不变。而且原版 `potent`/`weak` 本来就是最后注册的两个（`PlantTraitList.cs:180-193`），对原版植物的行为和 UI 顺序**零影响**，只是把本 mod 的特质插到它们前面。验收：给孢子加 `potent` I，单叶应从 15 变 18.75。

8. **物品必须带 `IS_OWNED_TAG`，否则工具提示前面挂「（未拥有）」**：`DirectoryMaster.Item(id)` 默认 `isOwned: true`（`DirectoryMaster.cs:246-262`），原版水培工厂全都从它起步（`PreBuiltItemHelper.cs:1657`）；而 mod 工厂走 `ItemDirectory.CreateEmptyItem()`，拿不到这个 tag。`GeneralHelper.CreateGeneralItemTooltip` 一看到 `!IsItemEffectivelyOwned(item)` 就加红字「未拥有」（`GeneralHelper.cs:230-236`），玩家会以为这叶子不是自己的。修法：三个工厂在末尾 `GeneralHelper.SetItemOwned(item)`，并在 `onLoaded` 里再补一次（自动修好本次修复之前种出来的叶子）。
9. **别先调原函数再替换精灵**：`RenderHandler.LoadFromAtlas` 找不到就 `Debug.LogWarning`（`RenderHandler.cs:359-368`），先调一次原函数就会在每次重绘时刷一条警告（一次会话实测 298 条）。改成「先判断原版图集有没有 `<harvestId>_p`，没有才自己造列表」，原版委托不再被调用，警告归零。

### 5.5 参考实现（BrewingExpansion 3.6.8.7）

订阅的 `3829730904`（酿酒拓展）做了同类的「水培作物 + 新物品 + 新机器」内容，它的实现已经在本仓库反编译到 `refs/ref_mods/brewing/`，可直接对照：

| 我们要做的事 | 它怎么做 | 文件 |
|---|---|---|
| 注册 16 种作物 | `PlantRegistry.Contains` 守卫 + `.OnHarvest(ctx => ...)` | `BrewingHydroponics.cs:116-135` |
| 收获拆档 | `SplitByHealth` + `OutputById(smallId, n)` + `context.Output(item)` | `BrewingHydroponics.cs:316-352` |
| 物品工厂 | `ItemDirectory.CreateEmptyItem` + `SetValue` + `SetGameItemType` + `SetSpriteAndShapeFromMod` + 显式 `SetShape` + `onLoaded` | `BrewingSeeds.cs:53-80`、`BrewingFruits.cs:85-109` |
| 目录注册时机 | OnEnable 遍历 `Resources.FindObjectsOfTypeAll<ModItemDirectory>()` + `OnModItemDirectoryInit` 钩子 + 去重 | `ModEntry.cs:110-114`、`298-367` |
| 水培立绘注入 | patch `MachineHydroponic.Hydroponic`，替换 `getItemSpriteModifierForItemFunc` | `BrewingHydroponicMachine.cs` |
| 本地化 | `Localization/<locale>.csv` → `ModHelper.GetLocalized(modId, key)` | `ModText.cs` |

我们**没有**采用它的：多 ID 的小果（`_small` 是另一个物品 ID，我们是同 ID 三档）、证书解锁、自定义机器。它的代码与贴图有版权（README 明写禁止二次使用），这里只学 API 用法，不复制实现。

---

## 6. 素材与本地化

### 6.1 五张图（16 px 网格，透明底，alpha 决定占格）

尺寸与 `ART_SPEC.md` 定稿一致（都从 `refs/final/` 拷过去）：

| 文件 | 用途 | 尺寸 | 对应物品 |
|---|---|---|---|
| `Textures/Items/restoring_fern_seed.png` | 孢子 | 16 × 16 | `restoring_fern_seed` |
| `Textures/Items/restoring_fern_s.png` | 小叶 | 16 × 16 | `restoring_fern`（20.5 g 档） |
| `Textures/Items/restoring_fern.png` | 标准叶 | 16 × 32 | `restoring_fern`（40 g 档） |
| `Textures/Items/restoring_fern_l.png` | 大叶 | 32 × 32 | `restoring_fern`（75 g 档） |
| `Textures/Items/restoring_fern_p.png` | 水培槽立绘 | 48 × 64 | 生长期 |

- 加载方式：`Textures/Items/` 下 PNG 自动成为 `mod.Sprites["名字"]`（`ModLoader.cs:1717-1750`），三档工厂各自 `SetSpriteAndShapeFromMod(ModId, "restoring_fern_s" / "restoring_fern" / "restoring_fern_l")`（`GameItem.cs:386`）。
- 画风：全部手排（`tools/draw_fern*.py`）+ 48×64 立绘用模型定形状再像素化；色板、留边、描边规则见 `ART_SPEC.md`。

### 6.2 `_p` 立绘怎么进原版图集

原版水培机会用 `RenderHandler.LoadFromAtlas("Items/items_hydroponic_plant", harvestItemId + "_p")` 取立绘（`MachineHydroponic.cs:88-110`），而 mod 精灵进不了这个图集（`RenderHandler.cs:331-368`）。

**已实现，`src/HydroponicPlantArt.cs`**（照 BrewingExpansion 的 patch 位置，但更通用）：不碰 `RenderHandler`，在 `MachineHydroponic.Hydroponic()` 的 postfix 里**包一层** `getItemSpriteModifierForItemFunc`：机器 `STATE_WORKING` + 原版图集里没有 `<harvestItemId>_p` 时，直接用 mod 精灵**自己造列表**；其余情况原样调原版委托（`original(self)`）。

```csharp
if (TryModPlantSprite(self, out Sprite sprite))          // 状态 + 种子 + 图集里没有 + mod 里有
    return new List<ItemSpriteModifier> { new ItemSpriteModifier(sprite, Vector2.zero, 0, false, 0, false, Color.white) };
return original == null ? null : original(self);          // 原版植物 / 没在长：完全交给原版
```

- 健壮性：原版植物一定会先命中图集，所以这条路径只对「图集里没有的 harvest id」生效，不影响原版；`_p2`（多年生快熟）同样按 mod sprite 兜一次。
- 用「遍历 mod 精灵」而不是写死 `GetModSprite(ModId, ...)`：别的种田 mod 的作物也能一起显示（不动别人代码，只是兜底）。
- 查找结果带缓存（含未命中），`OnModAssetsLoaded` 时清一次；找不到就退回原版 unknown 图并打一条 warning，不会抛异常。
- **先判断再委托**：原版委托里 `RenderHandler.LoadFromAtlas` 找不到就 `LogWarning`，先调后换会在每次重绘时刷一条（一次会话实测 298 条）；现在的写法原版委托根本不会被调用，警告归零。
- 验收：`Player.log` 里 `restoring_fern_p ... was not found` 不再出现，水培槽里显示的是 48×64 的蕨叶立绘；实测 `Using mod sprite 'restoring_fern_p' for the growing plant` 已出现。（用户在游戏里确认：**原版机器里的 `_p` 立绘已正常显示**。）
- 参考实现：`refs/ref_mods/brewing/BrewingExpansion.Formal/BrewingHydroponicMachine.cs`（44 行）。

不采用：Harmony prefix `RenderHandler.LoadFromAtlas`（能用，但要模拟图集语义、每帧调用，风险更大）；反射塞 `atlasCache`（私有字段，版本一改就断）。

### 6.3 与 Hydroponic Seed Preview（3835902034）的兼容

那个 mod 会在「种子进了槽但还没开始长」时，在机器上叠一层半透明的**幽灵立绘**。它对两个 mod 做了硬编码支持（`AgriPreview.Harvests` 只认 `agri_expansion` 的 19 个种子，`BrewingPreview` 只认 `brewing_expansion`），其余 mod 种子走到 `sprite = null` → 回退成**种子自己的图**（`HydroponicSeedPreview.ModEntry.AddPreview` 里 `(string.IsNullOrEmpty(harvestItemId) || val.useSpriteFromMod) ? null : RenderHandler.TryLoadFromAtlas(...)`），所以我们的预览显示的是孢子包而不是蕨叶。

我们的处理（`src/SeedPreviewCompat.cs`）：**反射找 `HydroponicSeedPreview.ModEntry.AddPreview`，挂 postfix 换图**，不硬引用那个 dll。

- 只在「机器不是 `STATE_WORKING`（也就是幽灵预览场景）」+ 种子是本 mod 的 + `<harvestId>_p` 不在原版图集、但在某个 mod 的精灵里有 时动手；
- 只替换「精灵正好等于种子自己的图」的那一条，保留它设定的 `position` / `color`（不透明度 25% 是玩家的配置，不碰）；
- 找不到类型/方法就静默跳过，改名或卸载后自动失效；`Init` + `OnGameLoadedInit` 各试一次，防它比我们晚加载；
- 它 Upstream 将来若支持「任意 mod 的 `_p`」，我们这个 shim 会因为「已经是蕨叶图」而不改任何东西，可以原样留着。

### 6.4 文案（已定稿）

| key | 中文 | 英文 |
|---|---|---|
| `plant_restoring_fern_name` | 还原蕨 | Reduction Fern |
| `item_restoring_fern_seed_name` | 还原蕨孢子 | Reduction Fern Spores |
| `item_restoring_fern_seed_desc` | 一小撮覆着细绒的孢子。能在贫水的水培槽里扎根，成熟后叶脉里会积起一层淡青色的还原剂。 | A pinch of downy spores. They take root in a water-poor hydroponic tray, and the mature fronds store a pale teal reducing agent in their veins. |
| `item_restoring_fern_name` | 还原蕨叶 | Reduction Fern Fronds |
| `item_restoring_fern_desc` | 一把泛着青灰的蕨叶。揉碎后会渗出还原剂，是奥克莫吸合成里少见的合法来源。 | A handful of grey-green fronds. Crushed, they seep reducing agent — one of the few legal sources for Nomore synthesis. |
| `item_restoring_fern_flavor` | 它不挑水，只挑电。 | It doesn't mind the water. It minds the power. |

### 6.5 本地化文件

- `mod/Localization/zh.csv`、`en.csv`，格式 `key,"value"`（同 `Pharmacy`），各 12 条。
- 不需要新增 `Mechanic` 表条目：产出特质的三段文案全部复用原版模板 + 液体名。
- **一致性检查脚本 `scripts/check_locales.py`**：校验两语言 key 集合相同、无重复、无空值，并核对 `src/**/*.cs` 里 `Text.Get("…")` 用到的 key 都在语言包里（当前输出 `en 12 / zh 12 / OK`）。改文案后跑一遍，比进游戏点开每个提示框快。

### 6.6 封面（1280 × 720，系列版式）

- 关键图：ComfyUI + Qwen-Image 2.1，1280×720、30 steps、seed 772，提示词描述「右侧三分线的旧水培柜 + 青灰蕨叶 + 左侧深阴影 + 右后暖黄工作灯」；原图存 `refs/gen/keyart_b.png`，调色版 `refs/gen/keyart_b_graded2.png`（提亮 3%、对比 7%、饱和 10%，蕨叶区叠 32% 淡青辉光 + 暗角）。
- 排版 `scripts/make_cover.py`（照 `FilterPrinter/scripts/make_cover.py` 的系列版式）：左侧 eyebrow → 96 px 中文标题 → 琥珀英文副标题 → 分隔线 → 三条青色方块要点 → 粗体卖点 → 细节行 → 页脚；左侧压暗曲线沿用 `0.93 - 0.58·x^0.72`。
- 产物 `mod/preview.png` 1280×720 / 711 KB（Steam 上限 1 MB）；`build.sh` 会一并部署到 `Mods/ReductionFern/preview.png`，工坊 `previewfile` 直接指它。
- **包内另存 640×360 / 228 KB 的小图**（`build/preview_640.png`）：工坊 `file_size` 只统计 contentfolder，1280 全画质塞进包会白多 0.7 MB（这次就踩了一次，zip 从 729 KB 降到 246 KB）。`package.sh` 里有尺寸断言，包内 preview 不是 640×360 就直接失败。
- `refs/gen/keyart.png` 存的是**已调色**的最终关键图，`package.sh` 每次都用它重出封面；未调色的候选保留为 `keyart_a/b/c.png`。
- 画面里没有模型生成的文字；标题/要点全部由 PIL 排。

---

## 7. 获取方式（D2 = 已定：网络升级）

单株就能永续（1 颗孢子/茬），所以**只需要一次获取**，不用进货系统。

- **一次性解锁**：`ModHelper.AddNetworkUpgrade(ModId, "harness.reduction-fern.unlock_fern", cost, subtitle, title, desc, GrantSpores)`，解锁时给 **2 颗孢子**（留一颗容错）。
- 注册时机照 `FilterPrinter`：新档开始时注册 + 注册标志位去重（`FilterPrinterMod.cs:109-137`）；图标用孢子精灵 `ModId:restoring_fern_seed`，`tab` 用默认。
- **价格与前置已定（2026-11-22）**：**450 信用点、无前置**（参照 `FilterPrinter` 的 900，那台是生产机器，这里只是种子）。升级 id `harness.reduction_fern.unlock`，图标 `harness.reduction-fern:restoring_fern_seed`，解锁动作 `GrantSpores` 发 2 颗。
- 附带调试生成按钮（`ModHelper.AddDebugFunction`，同 `Pharmacy`/`FilterPrinter`），方便 P1/P2 验收。

未采用：**拾荒掉落**（纯看运气、要挑对表）与**供货商上架**（要侵入客户报价表生成，最容易和其他 mod 打架）。

---

## 8. 风险

1. **平衡外溢**：还原剂从「违禁箱专属」变成「田里长」，会让奥克莫吸/澄心剂产业链脱离违禁品经济。D3（标准叶 120 ml/茬、满血 190 ml）与 D4（全合法）已经按「低于梦帽菇（390 ml）、约 1.3–2 茬抵 1 个违禁箱」的口径定稿；如果发售后反馈过强，v2 的旋钮是下调产量档位（§10.2 备注），**不**再改合法性——孢子违禁会让「种田流」变回「走私流」，和这个 mod 的立意相反。
2. **`_p` 立绘缺失**会让水培机显示 unknown 图——已修（§6.2、`src/HydroponicPlantArt.cs`），`Player.log` 里那串 `restoring_fern_p ... was not found` 应彻底消失。
3. **本地化 API 用错**会满屏裸 key（§5.4）。
4. **存档**：中途加 mod 安全；卸载后存档里的孢子/叶会变成未知物品（所有加物品的 mod 都这样）。
5. **兼容**：不改 `PlantList`、不改原版特质定义（只把 `potent`/`weak` 在有序表里挪到末尾，语义不变）、不动 `Liquid` 静态表，与其他种田 mod 冲突概率低；但如果别人也注册 `production_reducing_agent`，后加载的会覆盖先加载的。
6. **时间口径**：4 次机器动作是基础速度下的值，速度模组会改变实际时长，文档里不写死「几分钟一茬」。

---

## 9. 里程碑

| 阶段 | 内容 | 验收 |
|---|---|---|
| **P0 参数冻结（已完成）** | 本文档；ID、数值、文案、获取方式定稿 | §10.1 的 D1–D6 全部拍板（v0.3） |
| **P1 骨架（已完成）** | 工程骨架、注册植物+特质+两件物品、调试生成 | 已验：mod 以 `trust=Match` 加载、读档后 `Registered item id: restoring_fern(_seed)`、调试面板「生成还原蕨孢子」、Item Spawner 里的两件物品、叶子的工具提示（`化学用品 \| 材料`、48 千卡、售价 18）、**新档 · 改造水培系统里种进孢子后 `状态: 正在生长`，用一次性涡轮增压器模拟过夜后进度 `6/26 (4天)`、水 2000→1924 ml、能耗扣 3 kJ**。立绘 unknown 的显示问题已由 §6.2 的 postfix 修掉 |
| P2 产出链路 | 产出特质、顺序对齐、收获返还、搅拌验证 | 满血一茬 8 片大叶 = 190 ml；标准叶一茬 120 ml；效力强 I 满血 237.5 ml、效力弱 I 142.5 ml；搅碎后容器里是还原剂 |
| P3 获取（代码完成，待实机验收） | 网络升级「还原蕨孢子」450 cr / 无前置 / 解锁给 2 颗孢子；`_p` 立绘注入见 §6.2、预览兼容见 §6.3 | 新档网络界面能看到该条目、花 450 解锁后收到 2 颗孢子；水培槽显示正常 |
| P4 素材与本地化（封面已完成，中英切换待验收） | 五张图、中英文案、封面（系列版式 1280×720，`mod/preview.png` 711 KB） | 封面已出图；待验：游戏内切英文后名称/描述/升级条目全部英文 |
| P5 发布（已上架） | 工坊条目 **3844217940**（`visibility 0` 公开），标题「还原剂蕨 / Reduction Fern」，描述 `packaging/workshop_description.txt` | `dist/ReductionFern-v0.1.0.zip` 246 KB；SteamCMD 两次 `Upload finished ... : OK`（先私有后公开）；英文界面验收交给玩家反馈 |

v1 只做这一株。同一套模板以后可以复制出「产酸蕨」「产碱蕨」，但不在本计划内——先把一株从参数做到工坊，再谈第二株。

### 9.1 预期文件结构（P1 起）

```text
ReductionFern/
├─ src/ReductionFernMod.cs   IMod 入口：Init 注册植物/特质，挂 ModHook
├─ src/Plant.cs              PlantDefinition + 收获函数
├─ src/Items.cs              孢子 / 蕨叶两个工厂
├─ src/Text.cs              ModHelper.GetLocalized 的薄包装
├─ mod/manifest.xml          ID=harness.reduction-fern, Version=0.1.0
├─ mod/Localization/{zh,en}.csv
├─ mod/Textures/Items/*.png
├─ mod/preview.png           工坊封面（系列版式）
├─ packaging/workshop_description.txt   工坊描述（中文正文 + 英文附录）
├─ packaging/README.txt      包内说明（给玩家）
├─ packaging/UPLOAD.md       上传步骤（SteamCMD / 描述 / 更新流程）
└─ scripts/{build,deploy,package}.sh
```

---

## 10. 拍板（v0.4：D1–D7 全部定稿）

### 10.1 已定

- **D1 英文名 → Reduction Fern**（2026-11-22）。中文 `还原蕨`；物品名 `Reduction Fern Spores` / `Reduction Fern Fronds`，对应 `还原蕨孢子` / `还原蕨叶`（§6.4）。
- **D2 获取方式 → 网络升级，一次性给 2 颗孢子**（2026-11-22）。实现见 §7：**450 信用点、无前置**（2026-11-22 定）。
- **D3 产量档位 → 120 ml/茬（标准叶）；满血出大叶时 190 ml/茬**（2026-11-22 定 120；v0.4 按三档重算）。每片 = 基础 0.25 ml/g + 5 ml 特质加成，标准叶 40 g = 15 ml、价值 18；大叶 75 g = 23.75 ml、价值 34；小叶 20.5 g = 10.1 ml、价值 9。
- **D4 合法性 → 叶子与孢子都合法**（2026-11-22）。不调 `ContrabandHelper`、不传违禁等级，孢子和叶子都不带 `CONTRABAND_ITEM_TAG`。
- **D5 专属水培模组 → v1 不做**（2026-11-22）。v2 若加，按「+50% 还原剂、−25% 产量」设计。
- **D6 效力强/效力弱口径 → 对齐原版**（2026-11-22）。注册完产出特质后把 `potent`/`weak` 挪到有序表末尾（§5.4 第 7 条）。冻结结果（标准叶）：效力强 I **18.75 ml/片（150 ml/茬）**、效力弱 I **11.25 ml/片（90 ml/茬）**、无 potency 特质 **15 ml/片（120 ml/茬）**；大叶对应 29.7 / 17.8 / 23.75 ml/片，小叶 12.7 / 7.6 / 10.1 ml/片。
- **D7 三档结构 → 同 ID、按血量拆小/标/大**（v0.4）。照梦帽菇：`SplitByHealth(reduceCount: true, allowHuge: false)`，重量 20.5 / 40 / 75 g。这样「养得好才出大叶」，也让三张叶片图（16×16 / 16×32 / 32×32）各自对应一个重量档。

### 10.2 后续可调（都不阻塞 v1）

- 产量整体偏高/偏低时，只改两个常数：还原剂 `0.25 ml/g`、价值 `0.45 信用点/g`（三档按重量自动跟着变），不要单独调某一档。
- D5 专属模组，留到 v2。

---

## 11. 参数落点速查

| 参数 | 代码位置 | 原版参照 |
|---|---|---|
| 植物数值 | `new PlantDefinition("restoring_fern_seed", "还原蕨", "restoring_fern", 26, 8)` | `PlantList.cs:54` |
| 养分/污染/水 | `.Nutriment(250, 75, 30).Contaminant(1.01)`，不调 `.Water()` | 同上 |
| 返还种子 | `.ReturnsSeeds()` + 收获里 `OutputById("restoring_fern_seed")` | `PlantList.cs:188` |
| 三档收获 | `SplitByHealth(8, health, reduceCount: true, allowHuge: false)` + `OutputSplit` | `PlantList.cs:185-197` |
| 天生特质 | `.Innate("drought_resistant")`、`.Innate("production_reducing_agent")` | `PlantList.cs:55-57` |
| 产出 ml | 特质 `5f * RankScale(rank)`；物品基础 `0.25f * weightGrams` | `PlantTraitList.cs:196-214` |
| 顺序对齐 | 注册后 `PlantTraitRegistry.Add(Get("potent"))`、`Get("weak")` | `PlantTraitList.cs:180-193` |
| 产物组成 | `SetChemContentML(item, "reducing_agent", 0.25f * weightGrams)`，其余成分同理按克重 | `ChemicalCompositionHelper.cs:19-39` |
| 物品注册 | `directory.Add(id, factory)` | `HydroponicDirectory.cs:11`（`Add` 那一行） |
| 精灵 | `SetSpriteAndShapeFromMod(ModId, key)` + 显式 `SetShape` 兜底 | `GameItem.cs:386` |
| 立绘注入 | patch `MachineHydroponic.Hydroponic`，`GetModSprite` 取图 | `MachineHydroponic.cs:88-110` |
| 物品来源 | `ModHelper.SetSource(item, ModId, 显示名)` | `ModHelper.cs:172-182` |
| 本地化 | `ModHelper.GetLocalized(ModId, key)` | `ModHelper.cs:107` |

---

## 12. 附：为什么不开新液体

`reducing_agent` 已存在：`Liquid.cs:101` 常量、`Liquid.cs:361-368` 定义（显示名「还原剂」、颜色 `67aaa5`、非违禁）。新开液体要动 `Liquid` 的静态表、化学反应的 tag 分配和存档兼容，收益为零，所以**只用现成液体**。
