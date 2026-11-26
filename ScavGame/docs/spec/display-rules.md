# 显示规则 v0.1 — 条件 → 条目

> 2026-11-18：夜间遭遇已砍，§6 仅作废案；逐件动画/配置项也不做。

> 目标：把「文案池」变成「什么条件下显示哪一条」的确定规则，程序可以照表实现。
> 配套：[文字层内容](../content/text-layer.md)、[夜间遭遇](../content/encounters.md)、[zh.csv](../content/zh.csv)。
> 本文只定规则，不定最终数值（数值在网格草案里）。

## 0. 记号

| 记号 | 含义 |
|---|---|
| `carried(id)` | `EmporiumEntry.Instance.IsAfterhourHaveOwnedItems(id)` |
| `attemptsUsed` | `PlayerStore.Instance.scavengingAttempts` |
| `attemptsLeft` | `ScavHelper.GetScavTimeLeft()` |
| `cell(x,y).kind` | `common / rare / empty / hazard / sealed / machine` |
| `revealed` | 已照亮/已细看，玩家知道内容 |
| `knownHazard` | 已知危险（红框） |
| `zone` | 左（x=0..1）/ 中（x=2..3）/ 右（x=4..5） |
| `recent(key,n)` | 最近 n 次同类抽取里出现过 |
| `onceNight` | 本晚只用一次 |

## 1. 状态输入

| 变量 | 来源 | 用途 |
|---|---|---|
| `canScavenge` | `ScavHelper.CanScavenge()` | 为 false 不打开窗口 |
| `wounded` | `PlayerStore.Instance.healthData.isWoundedFresh` | 受伤即结束 |
| `minorChance` / `majorChance` | `ScavHelper.GetMinorWoundChance()` / `GetMajorWoundChance()` | 危险格掷骰；UI 可显示 |
| `eventFreshDump` | `ActiveEvents` 含 `fresh_dump` | 开篇/权重 |
| `eventGeorgio` | `ActiveEvents` 含 `georgio_assistance` | 开篇/免伤 |
| `perkCareful` | `StartingPerk.IsCarefulScavenger()` | 开篇/免伤 |
| `perkProficient` | `StartingPerk.IsProficientScavenger()` | 次数（原版） |
| `perkOsteo` | `StartingPerk.IsDegenerativeOsteoarthritis()` | 开篇/次数（原版） |
| `serpicoWindow` | `SerpicoStoryline.IsFoodWindowOpen()` | 塞皮科遭遇 |
| `hasFood` | 夜间背包里 FOOD 的卡路里 > 0 | 塞皮科「留点吃的」 |
| `battery` | mod 状态 | 手电 |
| `inspectCharges` | mod 状态，初始 1 | 放大镜 |
| `listenUsed` | mod 状态，每回合重置 | 听 |
| `foundCount` | 本局已入包件数 | 结算 |

## 2. 全局规则

1. 每条文案必须有 key；缺 key 时显示 key 本身（开发期暴露问题）。
2. 同一时机最多 1 条主文案；结果最多 3 行（主结果 + 1 条额外物品 + 1 条工具/扫描）。
3. 固定句优先：受伤 > 免伤 > 空手 > 掉落。
4. **未携带的工具不出现任何风味文案/按钮**；只有 `status.no_crowbar` / `status.no_magnifier` 这类提示允许出现。
5. 线索由真实区域状态生成；可以说得模糊，**不能撒谎**。
6. 冷却：开篇 `base` 2 晚；`clue.*` / `result.*` 2 回合；固定句不冷却。
7. 池子抽空时回退到该槽位第 1 条。
8. 所有随机都用「权重 1 + 冷却」；没有特殊情况不做加权。

## 3. 进入垃圾场（开篇）

先检查 `canScavenge`：为 false 不打开小游戏窗口，保留原版面板的提示。

| 顺序 | 条件 | 槽位 | 条数 | 冷却 |
|---|---|---|---|---|
| 1 | 总是 | `intro.base` | 1 | 2 晚 |
| 2 | `eventFreshDump` | `intro.new_trash` | 1 | 2 晚 |
| 3 | 否则 `eventGeorgio` | `intro.george` | 1 | 2 晚 |
| 4 | 否则 `perkCareful` | `intro.careful` | 1 | 2 晚 |
| 5 | 否则 `perkOsteo` | `intro.osteo` | 1 | 2 晚 |
| 6 | 有携带工具 | `intro.tool.<id>` | 最多 1 | 1 晚 |

- 总行数 ≤ 3：`base` + 1 条事件/特性 + 1 条工具。
- 工具句从携带的工具里随机抽；优先抽上一晚没出现过的。
- 同时有 `fresh_dump` 和 `georgio_assistance` 时只显示 `fresh_dump`（更具体）。
- 没带工具就不出工具句，不允许「替玩家想象」。

## 4. 每回合开始

### 4.1 线索（罗盘方向 + 类型）

每次下手后：

- 先检查刚点格子周围 **8 格**（横、竖、斜）：有未揭示危险，就以该危险格为来源，输出 `{方向} · clue.hazard`。
- 没有邻格危险时，在全部未揭示的**非危险**格中取优先级最高的一格（并列随机）作为来源格。
- 方向 = 从刚点的格子指向来源格的罗盘方向：东 / 东南 / 南 / 西南 / 西 / 西北 / 北 / 东北（屏幕上为北）。
- 危险格不参与普通来源格选择。

| 内容 | 槽位 | 优先级 |
|---|---|---|
| 稀有（未揭示） | `clue.rare` | 4 |
| 密封箱（未开） | `clue.sealed` | 3 |
| 机器（未拆） | `clue.machine` | 3 |
| 普通物 | `clue.item` | 2 |
| 空 | `clue.empty` | 1 |
| 都没有 | `clue.quiet` | 0 |

- 显示格式：`{方向} · {线索}`；线索只说类型，不说距离、不说具体格。
- 冷却：同一条 key 2 回合内不重复；`clue.quiet` 不参与冷却。

### 4.2 状态行 / 按钮

| 条目 | 显示条件 | 备注 |
|---|---|---|
| `ui.remaining` | 总是 | `剩余下手：{0}` |
| `ui.battery` | `carried("flashlight")` | `手电：{0}` |
| `action.reach` | 总是 | 主操作 |
| `action.pry` | `carried("crowbar")` 且选中格是 `sealed` | 否则不显示；点密封箱时给 `status.no_crowbar` |
| `action.light` | `carried("flashlight")` 且 `battery > 0` | 电量 0 隐藏 |
| `action.inspect` | `carried("magnifier")` 且 `inspectCharges > 0` | 用完后置灰 |
| `action.listen` | 本回合未用 | 每回合 1 次 |
| `action.mark` | 总是 | 右键点未揭示的格子切换红标；不消耗下手、不触发线索 |

- 红标是玩家自己的笔记，不改变该格真实类型；翻格后自动清除，窗口关闭/重开也重置。
- `status.last_attempt`：`attemptsLeft == 1` 时显示。
- `status.low_battery`：手电用后 `battery == 1` 时显示一次。
- 受伤后 `wounded` 为 true → 立刻走结算，不再显示动作栏。

### 4.3 扫描仪

- 被动生效，不设按钮；双倍仍由原版掷骰。
- 双倍触发时追加 `status.scan_double`（「扫描仪又叫了一声」），不加物品，不指坐标。
- 不做每回合 ping。

## 5. 动作与结果

### 5.1 伸手（主操作）

结算顺序必须与原版一致：轻伤 → 重伤 → 霉运空手 → 基础掉落 → 额外掉落。

| 情况 | 显示 | 是否消耗下手 |
|---|---|---|
| 格是 `hazard`，轻伤掷骰命中，幸运未救 | `result.minor` → 结束 | 是 |
| 格是 `hazard`，重伤掷骰命中，幸运未救 | `result.major` → 结束 | 是 |
| 掷骰命中但 `HealthData.RollLuck()` 救下 | `result.luck`，无物品 | 是 |
| 教程/乔治奥免疫生效 | `result.immunity`，继续掉落 | 是 |
| 负幸运空手 | `result.empty` | 是 |
| 普通物品 | `result.common`（`{0}`） | 是 |
| 稀有物品 | `result.rare`（`{0}`） | 是 |
| 额外：背包 | 追加 `result.extra.backpack` | 是 |
| 额外：磁带 | 追加 `result.extra.cassette` | 是 |
| 额外：工具材料 | 追加 `result.dismantle.<tool>`（`{0}`） | 是 |
| 额外超过 2 条 | 追加 `result.extra.more`，不再逐条列 | 是 |
| 扫描仪双倍 | 追加 `status.scan_double` | 是 |

- 危险格的判定用**原版掷骰**，不是「踩到必伤」；这是小游戏只改变「你敢不敢碰」、不改变概率的关键。
- 日志：`NN · 物品名` / `NN · 空手` / `NN · 躲过` / `NN · 受伤`。
- 同一次结算最多 3 行：主结果 + 1 条额外 + 1 条工具/扫描文案。

### 5.2 撬开（密封箱）

| 条件 | 显示 | 消耗 |
|---|---|---|
| 没带撬棍 | `status.no_crowbar` | 否 |
| 带了撬棍 | `result.pry` → 走一次掉落（不出空手/危险） | 是 |

- 密封箱每局固定 2 个，占普通格位。
- 掉落仍走 `ScavHelper.GetRandomScavengedItem`（或等价的基础掉落），保证事件/扫描仪/工具逻辑一致。

### 5.3 照一下

- 条件：手电 + 电量 > 0。
- 效果：电量 −1；照亮所选格并显示类型；危险格标红。
- 文案：不额外播句子；高亮就是反馈。电量降到 1 时播 `status.low_battery`。
- 不消耗下手。

### 5.4 细看（放大镜）

| 情况 | 显示 | 消耗 |
|---|---|---|
| 已用完 | `status.inspect_used` | 否 |
| 普通/空 | `result.inspect.safe` | 次数 −1，不消耗下手 |
| 危险 | `result.inspect.hazard`，标红 | 同上 |
| 稀有 | `result.inspect.rare`，标黄 | 同上 |
| 密封箱 | `result.inspect.sealed` | 同上 |

### 5.5 听

- 条件：本回合未用。
- 效果：重新按 §4.1 抽一条线索；不消耗下手、不消耗电量。
- 文案：直接换线索，不额外播「你听了听」。

### 5.6 退出（原版返回）

- 小游戏内不再有「收工 / 关闭」按钮。
- 点游戏原版「返回」时，小游戏窗口自动关闭（`MapUIManager.Return` / `ReturnNow` 前缀）。
- 不额外弹小游戏结算；已拾到的物品照常带回。
- 如果玩家点的是窗口右上角关闭，也只关闭窗口，网格下次重开时重生成。

## 6. 夜间遭遇（已砍，废案）

触发：`attemptsUsed >= 2` 且本晚未触发 且 30% 掷骰通过。

| 遭遇 | 条件 | 选项（不满足时置灰） | 效果 |
|---|---|---|---|
| 塞皮科 | `serpicoWindow` | 留点吃的（需 `hasFood`）/ 问一句 / 装作没听见 | 问一句揭示 1 稀有格；其余无数值 |
| 同行 | 场上有未翻普通格 | 让一格 / 赶他走 / 各翻各的 | 让一格：1 普通格变空 + 随机揭示 1 格 |
| 机器人 | 总是 | 螺丝刀（需 `carried("screwdriver")`）/ 剪线钳（需 `carried("wire_cutter")`）/ 绕开 | 揭示 2 格 / 揭示 1 危险格 |

- 遭遇不消耗下手、不改电量、不调伤害函数。
- 优先级：塞皮科 > 同行 60% / 机器人 40%。
- 选择结果写一行日志：`遭遇 · 塞皮科` 等。

## 7. 结束与结算

| 触发 | 主文案 | 附加 |
|---|---|---|
| `wounded` | `end.injured` | `end.summary` |
| `attemptsLeft == 0` | `end.done` | `end.summary` |
| 玩家点原版返回 | 小游戏直接关闭，不弹结算 | — |

- `foundCount == 0` 时用 `end.summary.empty`，不用「今晚收获 0 件」。
- 结算后关闭窗口；原版「返回」按钮仍在。

## 8. 槽位总表（优先级 / 冷却 / 上限）

| 槽位 | 每局上限 | 冷却 | 固定 | 回退 |
|---|---|---|---|---|
| `intro.base` | 1 | 2 晚 | 否 | 第 1 条 |
| `intro.new_trash` / `george` / `careful` / `osteo` | 1 | 2 晚 | 否 | 第 1 条 |
| `intro.tool.*` | 1 | 1 晚 | 否 | 第 1 条 |
| `clue.*` | 1/回合 | 2 回合 | 否 | `clue.quiet` |
| `result.common/rare` | 1/次 | 2 回合 | 否 | 第 1 条 |
| `result.minor/major/luck/immunity` | 1/次 | 无 | 是 | 第 1 条 |
| `result.pry` | 1/次 | 2 回合 | 否 | 第 1 条 |
| `result.inspect.*` | 1/次 | 2 回合 | 否 | 第 1 条 |
| `result.dismantle.*` | 1/次 | 2 回合 | 否 | 第 1 条 |
| `status.*` | 按条件 | 1 回合 | 是 | — |
| `end.withdraw / injured / done` | 1 | 无 | 是 | — |
| `end.summary` | 1 | 2 回合 | 否 | 第 1 条 |
| `end.summary.empty` | 1 | 无 | 是 | — |

## 9. 选择算法（伪代码）

```text
Pick(slot, ctx):
  pool = entries[slot]
  cand = pool.where(e => e.when(ctx) && !recent(e.key, e.cooldown) && !usedTonight(e.key))
  if cand.empty: cand = pool.where(e => e.when(ctx))
  if cand.empty: cand = [pool[0]]
  return weightedRandom(cand)

Clue(ctx):
  zones = [left, center, right]
  score(zone) = max(cell.priority for hidden cells in zone)
  best = maxScore(zones)
  if best == 0: return "quiet"
  zone = random(zones with best)
  kind = random(cell.kind in zone with priority == best)
  return direction(zone) + " · " + Pick("clue." + kind, ctx)
```

## 10. 测试矩阵

| 场景 | 预期 |
|---|---|
| 第一晚、无工具、无事件 | 开篇 1 条 base；每回合 1 条 clue；物品走 common/rare；按 end.done 结算 |
| 刚点完一格、8 邻内有危险 | 显示「{罗盘方向} · 危险线索」；邻格无危险时不报远处危险 |
| 右键未揭示的格子 | 格子变红、显示「!」，再右键恢复；不扣下手 |
| 新倒的垃圾 + 切割机 | 开篇 base + new_trash + tool.welder；触发额外废金属时出现 dismantle.welder |
| 带撬棍、选密封箱 | 出现「撬开」；result.pry + common；不判空手/危险 |
| 不带撬棍、点密封箱 | 只出现 `status.no_crowbar`；下手数不变 |
| 放大镜 + 危险格 | result.inspect.hazard；该格标红；不消耗下手 |
| 塞皮科窗口 + 有食物 | 遭遇面板出现；「留点吃的」可用；食物数量不变 |
| 电量 1 时照一下 | battery→0，出现 `status.low_battery`；按钮隐藏 |
| 轻伤 | result.minor → end.injured → summary；剩余次数作废 |
| 0 件结束 | end.summary.empty，而不是「0 件」 |

## 11. 待确认

- **危险格判定**：推荐用原版掷骰（本文）；如果改成「踩到必伤」，谨慎特性、幸运、免疫都会失真。
- **线索粒度**：危险只在刚点格子的 8 邻内提示，其它类型指向全场最高优先级格；都用罗盘方向（东/东南/…），不再用「左/中/右」。
- **方向词本地化**：v0.1 先用「左边/中间/右边」硬编码，M4 再进 CSV。
