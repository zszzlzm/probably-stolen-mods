"""Recompute PLAN numbers for the three leaf tiers and write them back.

The frozen v0.3 numbers assumed one 40 g leaf. The art now ships three tiers (20.5 /
40 / 75 g) chosen by plant health, like the dream cap, so every derived number moves:

    base reducing agent = 0.25 ml/g   (40 g -> 10 ml, unchanged)
    value               = 0.45 cr/g   (40 g -> 18 cr, unchanged)
    production trait    = +5 ml per item, flat (vanilla convention)

Run:  python tools/update_plan_tiers.py
"""
import pathlib

PLAN = pathlib.Path(__file__).resolve().parent.parent / "PLAN.md"

# Derivation used throughout the new tables (see the module docstring):
#   small 20.5 g  -> 5.13 base + 5 trait = 10.13 ml,  9 cr,  cycle 8x = 81 ml  (all small)
#   normal 40 g   -> 10.00 base + 5     = 15.00 ml, 18 cr,  cycle 8x = 120 ml
#   large 75 g    -> 18.75 base + 5     = 23.75 ml, 34 cr,  cycle 8x = 190 ml
TRAIT_ML = 5.0


def main():
    text = PLAN.read_text(encoding="utf-8")

    def swap(old, new):
        nonlocal text
        assert old in text, old[:60]
        text = text.replace(old, new, 1)

    # ---- header -------------------------------------------------------------
    swap(
        "> v0.3（2026-11-22）：D1–D5 拍板（Reduction Fern / 网络升级 2 颗孢子 / 120 ml 一茬 / 全合法 / 不做专属模组），参数冻结，可进 P1。",
        "> v0.4（2026-11-22）：产物改成**三档同 ID**（小叶 20.5 g / 标准 40 g / 大叶 75 g，按血量出），所有数值按 0.25 ml 还原剂/克、0.45 信用点/克重算；梦帽菇与咖啡的对照数字也按满血出大果修正（见 §4.1）。D7 见 §10.1。\n"
        "> v0.3（2026-11-22）：D1–D5 拍板（Reduction Fern / 网络升级 2 颗孢子 / 120 ml 一茬 / 全合法 / 不做专属模组），参数冻结，可进 P1。",
    )

    # ---- 3.1 harvest --------------------------------------------------------
    swap(
        "| `harvestQuantity` | **8** | 8 | 满血 8 片叶 |",
        "| `harvestQuantity` | **8** | 8 | 满血 8 片叶，按血量拆小/标/大（§3.3） |",
    )
    swap(
        "| `onHarvest` | 咖啡式血量乘算 + 返还孢子 | 三档拆分 | 见 §5.2 |",
        "| `onHarvest` | `SplitByHealth` 三档拆分 + 返还孢子（照梦帽菇） | 三档拆分 | 见 §5.2 |",
    )

    # ---- 3.3 three tiers ----------------------------------------------------
    old33_start = text.index("### 3.3 产物：还原蕨叶 `restoring_fern`")
    old33_end = text.index("### 3.4 孢子")
    new33 = """### 3.3 产物：还原蕨叶 `restoring_fern`（三档同 ID）

和一株多果的梦帽菇一样：**同一个物品 ID，三种尺寸**，只是换精灵、重量、含量与价值。重量照梦帽菇的三档 20.5 / 40 / 75 g。

| 字段 | 小叶 `_s` | 标准叶 | 大叶 `_l` |
|---|---|---|---|
| 重量 | 20.5 g | 40 g | 75 g |
| 基础价值 | 9 | **18** | 34 |
| 还原剂（基础） | 5.13 ml | **10 ml** | 18.75 ml |
| 水 | 7.18 | 14 | 26.25 |
| 植物质 | 5.13 | 10 | 18.75 |
| 蛋白质 | 1.03 | 2 | 3.75 |
| 矿物质 | 0.26 | 0.5 | 0.94 |
| 物理污染物 | 0.77 | 1.5 | 2.81 |
| 微生物 | 0.51 | 1 | 1.88 |
| 单叶还原剂（含 +5 特质） | 10.1 ml | **15 ml** | 23.75 ml |

- 换算基准（写代码时用常量，不要手抄表）：**还原剂 0.25 ml/g、价值 0.45 信用点/g**；其余成分按标准叶的 40 g 配方等比缩放。
- 物品类型、违禁、音效、`ApplyFactoryGenetics` 三档一致：`CHEMICAL_SUPPLIES` + `CHEM_ITEM_TAG` / `BLENDABLE_TAG`，**全部合法**，`AudioHelper.InitLeafy`，工厂里 `ApplyFactoryGenetics(item, "restoring_fern_seed")`。
- 用法不变：丢搅拌机、挂液体容器，还原剂随水分和植物质一起进容器，再过滤/纯化——产的是**原料**，接 `FilterPrinter`。

"""
    text = text[:old33_start] + new33 + text[old33_end:]

    # ---- 4.1 anchors --------------------------------------------------------
    old41_start = text.index("### 4.1 一茬（满血、rank I、无模组）")
    old41_end = text.index("### 4.2 与现有还原剂来源对比")
    new41 = """### 4.1 一茬（满血、rank I、无模组）

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

按血量分档（rank I、无浓效/虚弱，`harvestQuantity` 8）：

| 血量 | 会出什么 | 一茬还原剂 | 一茬价值 |
|---|---|---|---|
| ≤15 | 4 片小叶（数量 ×0.5） | 40.5 ml | 36 |
| 16–30 | 5 片：3 小 + 2 标 | 60.3 ml | 63 |
| 31–50 | 6 片：1 小 + 5 标 | 85.1 ml | 99 |
| 51–70 | 7 片标准叶 | 105 ml | 126 |
| 71–80 | 8 片：6 标 + 2 大 | 137.5 ml | 176 |
| 81–90 | 8 片：2 标 + 6 大 | 172.5 ml | 240 |
| 91–100 | 8 片大叶 | **190 ml** | **272** |

结论：满血产量比梦帽菇低一半、和咖啡同级但**合法、可再生、省水**；品种定位是「试剂田」不是「摇钱树」。D3 冻结的 120 ml 对应的是**标准叶**（血量 51–70 或 71 以上出标准叶的场合），满血因为出大叶变成 190 ml——这是照搬原版「养得好→出大果」的机制，不是数值膨胀。

"""
    text = text[:old41_start] + new41 + text[old41_end:]

    # ---- 4.2 box comparison -------------------------------------------------
    swap(
        "- 还原蕨一茬：120 ml，成本是 1 颗孢子（一次性）+ 300 ml 水 + 4 次机器动作。\n- 也就是**约 2 茬 ≈ 1 个违禁箱的还原剂**。这是有意的：农场省的是「跑违禁渠道的风险」，不是「完全替代采购」。",
        "- 还原蕨一茬：满血 190 ml（标准叶 105–120 ml），成本是 1 颗孢子（一次性）+ 300 ml 水 + 4 次机器动作。\n- 也就是**约 1.3 茬（满血）≈ 1 个违禁箱的还原剂**；养得差一点要 2–3 茬。这是有意的：农场省的是「跑违禁渠道的风险」，不是「完全替代采购」。",
    )

    # ---- 4.3 curve ----------------------------------------------------------
    old43_start = text.index("### 4.3 育种曲线（每片叶 / 每茬）")
    old43_end = text.index("**浓效/虚弱的作用域")
    new43 = """### 4.3 育种曲线（每片叶 / 每茬）

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

小叶 / 大叶是同一张表乘 `基础 / 10` 再加回固定的 +5：满血大叶 I = 18.75 + 5 = 23.75 ml（每茬 190）；小叶 I = 5.13 + 5 = 10.1 ml。

"""
    text = text[:old43_start] + new43 + text[old43_end:]

    # ---- 5.2 harvest code ---------------------------------------------------
    old52_start = text.index("### 5.2 收获")
    old52_end = text.index("### 5.3 产出特质")
    new52 = """### 5.2 收获

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

"""
    text = text[:old52_start] + new52 + text[old52_end:]

    # ---- 6.1 textures -------------------------------------------------------
    old61_start = text.index("### 6.1 三张图（16 px 网格，透明底，alpha 决定占格）")
    old61_end = text.index("### 6.2 `_p` 立绘怎么进原版图集")
    new61 = """### 6.1 五张图（16 px 网格，透明底，alpha 决定占格）

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

"""
    text = text[:old61_start] + new61 + text[old61_end:]

    # ---- 9 P2 acceptance ----------------------------------------------------
    swap(
        "| P2 产出链路 | 产出特质、顺序对齐、收获返还、搅拌验证 | 一茬出 8 叶、每叶 15 ml；加浓效 I 后每叶 18.75 ml；搅碎后容器里是还原剂 |",
        "| P2 产出链路 | 产出特质、顺序对齐、收获返还、搅拌验证 | 满血一茬 8 片大叶 = 190 ml；标准叶一茬 120 ml；浓效 I 满血 237.5 ml、虚弱 I 142.5 ml；搅碎后容器里是还原剂 |",
    )

    # ---- 10.1 D3 + D7 -------------------------------------------------------
    swap(
        "- **D3 产量档位 → 120 ml/茬**（2026-11-22）。每片 10 ml 基础 + 5 ml 特质加成，产物价值 18；88 / 152 两档不采用，仅在售后调参时作备选。",
        "- **D3 产量档位 → 120 ml/茬（标准叶）；满血出大叶时 190 ml/茬**（2026-11-22 定 120；v0.4 按三档重算）。每片 = 基础 0.25 ml/g + 5 ml 特质加成，标准叶 40 g = 15 ml、价值 18；大叶 75 g = 23.75 ml、价值 34；小叶 20.5 g = 10.1 ml、价值 9。\n"
        "- **D7 三档结构 → 同 ID、按血量拆小/标/大**（v0.4）。照梦帽菇：`SplitByHealth(reduceCount: true, allowHuge: false)`，重量 20.5 / 40 / 75 g。这样「养得好才出大叶」，也让 5 px 的三张图有对应的物品档位。",
    )

    # ---- 11 quick table -----------------------------------------------------
    swap(
        "| 返还种子 | `.ReturnsSeeds()` + 收获里 `OutputById(\"restoring_fern_seed\")` | `PlantList.cs:188` |",
        "| 返还种子 | `.ReturnsSeeds()` + 收获里 `OutputById(\"restoring_fern_seed\")` | `PlantList.cs:188` |\n"
        "| 三档收获 | `SplitByHealth(8, health, reduceCount: true, allowHuge: false)` + `OutputSplit` | `PlantList.cs:185-197` |",
    )
    swap(
        "| 产出 ml | `5f * PlantGeneticsHelper.RankScale(ctx.rank)` | `PlantTraitList.cs:196-214` |",
        "| 产出 ml | 特质 `5f * RankScale(rank)`；物品基础 `0.25f * weightGrams` | `PlantTraitList.cs:196-214` |",
    )

    PLAN.write_text(text, encoding="utf-8")
    print("PLAN.md updated,", len(text.splitlines()), "lines")


if __name__ == "__main__":
    main()
