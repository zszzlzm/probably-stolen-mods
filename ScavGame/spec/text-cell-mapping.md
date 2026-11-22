# 文字层 × 格子：当前关联

> 对应代码：`ScavArcade.dll` `960463…`
> 文字源：`mod/Localization/zh.csv`（178 条）

## 0. 生成阶段

进本时 `GenerateBoard()` 静默跑 24 次原版判定，不产生任何文字；只决定每格的 Kind 和 `extra` 属性。

额外掉落不是独立 Kind，而是挂在基础/密封箱/机器上的 `extra` 标签。

## 1. 开窗

| 位置 | 内容 | 触发 |
|---|---|---|
| 标题 | `ui.title` | 总是 |
| 状态行 | `ui.remaining`；带手电追加 `ui.battery`；带放大镜追加 `ui.magnifier`；暂停追加 `ui.bandage` | 总是 |
| 线索行 | `clue.initial`（从哪一格开始？） | 只在还没点过格子时 |
| 日志 | `intro.base` + 事件句 / 特性句 + `intro.tool.*`；固定加一句 `ui.hint_mark` | 每晚第一次开窗 |

## 2. 格子 → 标记 / 线索 / 工具 / 结果

| Kind | 生成条件 | 点开标记 | 线索 | 照一下 | 细看 | 点开文本 |
|---|---|---|---|---|---|---|
| 受伤 0 | 对应免疫为 0，轻/重伤命中且幸运没救下 | 伤（红） | 只作邻格危险：`clue.hazard` ×4 | `result.light.hazard.1` | `result.inspect.hazard.1` | `result.minor.1` / `result.major.1`；之后 `status.wounded_pause` / `status.resume` / `end.injured.1` |
| 空 1 | 霉运命中，或受伤被幸运救下 | 空（灰） | `clue.empty` ×3 | `result.light.safe.1` | `result.inspect.empty.1` | `result.empty.1` |
| 基础 2 | 首件不是六类、不是 tier1/2 模组 | 物（白）；有 `extra` 时绿 | `clue.item` ×3；有 `extra` 时 `clue.extra` ×2 | `result.light.base.1`；有 `extra` 时 `result.light.extra.1` | `result.inspect.named`（具体物品名） | `result.common` ×4 / `result.rare` ×3；≥2 件再 `result.extra.more` |
| 密封箱 4 | 首件属于材料/医疗/日用/食品/工具/武器 | 箱（金）；有 `extra` 时绿 | `clue.sealed` ×2（类型优先，有 `extra` 时仍报箱） | `result.light.sealed.1`；有 `extra` 时 `result.light.extra.1` | `result.inspect.sealed_named`（清单上的物品名） | `result.pry.1/2` + `result.common/rare`；≥2 件再 `result.extra.more`；没撬棍只出 `status.no_crowbar` |
| 机器 5 | 首件是 `MODULE` 且 `MODULE_TIER_INT` 为 1/2 | 机（蓝）；有 `extra` 时绿 | `clue.machine` ×2（类型优先，有 `extra` 时仍报机） | `result.light.machine.1`；有 `extra` 时 `result.light.extra.1` | `result.inspect.machine_named`（插槽里的物品名） | `result.machine.1` + `result.common/rare`；≥2 件再 `result.extra.more` |

线索方向：从刚点的格子指向来源格的罗盘方位：东/东南/南/西南/西/西北/北/东北。

容器判定先排除杂物：基础掉落来自 `junkTable`，或首件带 `JUNK` 类型 → 不标箱/机，按基础格处理。

线索选择顺序：

1. 候选只取刚点格子周围 8 格，且必须未揭示、没给过线索（`clued`）。
2. 候选里有受伤格 → `clue.hazard`，优先；否则取候选里总价值最高的一格（并列随机）。
3. 类型优先：机器 → `clue.machine`，密封箱 → `clue.sealed`，空 → `clue.empty`；基础格价值 ≥70 → `clue.rare`，有 `extra` → `clue.extra`，否则 `clue.item`。
4. 选中后写入 `clued`，下次排除，顺延第二/第三；8 格全部排完才 `clue.quiet`。
5. 多件格仍会 `MarkCell` 变绿；不在 8 邻内的格子不会被揭示。
6. 线索按点击格序号缓存：`clueSource[click]` / `clueText[click]`，同一格只抽一次。关窗重开或包扎恢复调用 `ShowClueForLast()` 回放缓存，不重新抽取；因此不会因为开关窗口换线索或多消耗候选。

## 3. 结算

| 时机 | 文本 |
|---|---|
| 出手 | 状态行 `ui.remaining` 减 1 |
| 受伤 | `result.minor/major` → 受伤覆盖层 → `status.wounded_pause`；包扎后 `status.resume` |
| 结束 | 次数用完/受伤：`end.done.1` / `end.injured.1` + `end.summary`（0 件时 `end.summary.empty`） |
| 离开 | 没有「收工」按钮；点原版「返回」直接关窗，不出结算 |

## 4. 目前的缺口

- 扫描仪双倍也会被算成 `extra`，和这格本来多件无法区分。
- 线索指到 `extra` 格时会 `MarkCell`，等于免费揭示箱/机/物类型。
- 结算文本只看 `items[0]` 的价值，第二件更值钱时文案会偏。
- `end.withdraw`、`result.luck`、`result.hazard_passed` 还在 CSV 里，但当前流程不用。
