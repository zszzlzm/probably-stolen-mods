# 格子生成：用原版拾荒结果预生成

> 状态：已按此实现（2026-11-17）
> 目标：进入垃圾场时，为 6×4 每一格预生成一次「原版拾荒」的结果；点击只结算已经生成好的结果，不在点击时重新 roll。

## 1. 原版一次拾荒的判定链

`ScavHelper.ScavengeDumpingGrounds()` 的顺序：

1. 轻伤 `RollMinorWound()`：5% + 已下手次数 ×1%，手电减半，事件 `injury_chance` 修正。
2. 重伤 `RollMajorWound()`：1% + 已下手次数 ×0.25%，同上。
3. 霉运空手 `HealthData.RollBadLuck()`：只有负幸运时才会触发。
4. 否则 `GetRandomScavengedItem()`：
   - 基础掉落 ×1；
   - 背包 3%（`satchel` / `kids_backpack`）；
   - 损坏磁带 1%；
   - 捕鼠夹 1%；
   - 螺丝刀 / 剪线钳 / 切割机各 10% 追加材料；
   - 双倍掉落：事件 `loot_double_chance` + 扫描仪 tag。
5. 每次拾荒后，轻/重伤免疫次数各减 1。

## 2. 预生成（每格一次）

在玩家进入垃圾场（`Arrive`）时执行，24 格全部生成；窗口关掉再开不重 roll。

```text
for each of 24 cells:
    if 无轻伤免疫 && RollMinorWound():
        outcome = RollLuck() ? Empty : Injured(minor)
    else if 无重伤免疫 && RollMajorWound():
        outcome = RollLuck() ? Empty : Injured(major)
    else if RollBadLuck():
        outcome = Empty
    else:
        items = GetRandomScavengedItem()
        if 首件是 MODULE 且 MODULE_TIER_INT ∈ {1,2}: outcome = Machine
        else if 首件属于六类物品: outcome = Sealed
        else: outcome = items.Count >= 2 ? Extra : Base
```

- 受伤用进本时的几率（已下手 = 0），进本时定死，点击不再 roll。
- **免疫不生成受伤格**：轻/重伤免疫次数 > 0 时，生成阶段直接跳过对应的受伤判定；免疫次数在每次点击时照常递减（原版每次拾荒消耗）。
- **幸运在生成时 roll**：救下就按原版空手，记作空格。
- 空格只来自「霉运」或「幸运救下」；幸运不是负数时没有空格，符合原版。
- 物品在进本时生成并挂在棋盘上；点击入包时才写「背包已发现」。
- 关窗/离开时未点击的格子直接丢弃，下次进本重生成。
- 同一块板上 `satchel` / `kids_backpack` 最多各出现一次。

## 3. 分类

| 结果 | 判定 | 点击后 |
|---|---|---|
| 受伤格 | 对应免疫为 0，且轻/重伤 roll 命中、幸运没救下 | 扣 1 次下手；受伤则暂停或结束 |
| 空格 | 霉运命中，或受伤被幸运救下 | 扣 1 次下手；无物品 |
| 密封箱 | 首件掉落属于「材料/医疗品/日用品/食品/工具/武器」 | 扣 1 次下手；没撬棍不能开；开箱拿全部物品 |
| 机器 | 首件掉落是 MODULE 且 `MODULE_TIER_INT` 为 1 或 2 | 扣 1 次下手；拆开拿全部物品 |
| 基础格 | 首件不是箱/机；1 件或多件（多件加 `extra` 标签） | 扣 1 次下手；入包；多件时标记变绿 |

额外掉落不再单独分类：`extra` 是挂在密封箱/机器/基础格上的属性，不生成「多」格。

## 4. 点击结算顺序

1. 已是翻开/暂停/结束状态 → 不处理。
2. 密封箱且没撬棍 → 只提示 `status.no_crowbar`，不扣下手。
3. 扣 1 次下手，`RunStats.OnScavengeAttempt()`，标记该格。
4. 按预生成结果结算：
   - 受伤格：`ReceiveMinor/MajorWound()`（幸运已在生成时结算；生成时已排除有免疫的情况）；
   - 空格：无物品；
   - 密封箱/机器/基础：逐件 `TryAcceptAll`，成功则计入 foundCount；密封箱先播 `result.pry`。
5. 更新状态行；下手为 0 则结束，否则更新线索。

## 5. 与现版本的差异

- 危险不再随下手次数增长：24 格在进本时一次性 roll，全部用 5%/1% 的初始几率。
- 空格只由负幸运触发；正常夜晚可能一个空格都没有。
- 预生成会实例化约 24 组物品；未点击的随窗口关闭/离开丢弃。
- 免疫只在点击受伤格时消耗；点普通格不消耗免疫。
- 旧的手调 `Counts`（11 普通 / 4 空 / 5 危险 / 2 箱 / 2 机）废弃。

## 6. 实现口径（已定）

1. 24 格在进本时各跑一次原版判定；点击只结算已生成结果，不另造奖池。
2. 先排除杂物：基础掉落来自 `junkTable`，或首件带 `JUNK` 类型 → 只按件数分基础/额外，不标箱/机。
3. 其余首件类型属于六类 → 密封箱；首件是 `MODULE` 且 `MODULE_TIER_INT` 为 1/2 → 机器；否则按件数分基础/额外。额外掉落的第二件不参与容器判定。
4. 六类 type tag（初版）：
   - 材料：`MATERIAL`、`BASIC_MATERIAL`
   - 医疗品：`MEDICAL`、`MEDICAL_TOOL`、`ORGAN`
   - 日用品：`HOUSEHOLD_GOOD`
   - 食品：`FOOD`、`PROCESSED_FOOD`、`BREVAGE`、`ALCOHOL`
   - 工具：`TOOL`
   - 武器：`WEAPON`、`MELEE_WEAPON`、`FIREARM`
5. 密封箱没撬棍不能开（不扣下手）；机器不需要工具，直接拆。
6. 免疫 > 0 时，对应受伤判定在生成阶段跳过；免疫次数按点击递减。
