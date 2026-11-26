# 试剂可售 复盘 / Reagent Resale retrospective

## 一句话

原版把"拆包 = 退出流通"做成了不可逆的取舍，代价是拆包产物既没有价签也没有买家；
本模组把价格、类型、水质评级三件事补齐，让拆包从"纯亏"变成"止损"。

## 平台事实（反编译，`probably_stolen_decomp/`）

| 事实 | 位置 |
|---|---|
| 交易资格链：黑名单 → `ALL_TYPE` → id 表 → tag 表 → `willAcceptItem` | `StoreClient.cs:449-482` |
| 化学买家只挂 `CHEMICAL_SUPPLIES`，共 4 处 | `StoreClientList.cs:185 / 1453 / 3327`、`StoreClientListSupplier.cs:181` |
| 拆包：普通包 50 → 2×迷你酒精 + 亲脂结合剂 + 酸 + 碱；管制包 100 → 2×芬太前体 + 还原剂 | `MaterialDirectory.cs:94-158` |
| 拆包弹窗明写"不可交易 / untradable" | `mech_chemical_supplies_unpack_warning` |
| 水价是全局费率 40 / 1000 ml（基础水档） | `WaterFeatureHelper.cs:369-377` |
| `AddLiquid` → `UpdateWaterFeature` **不重算** `unitValue`，所以瓶装试剂一直是空瓶价 3 | `WaterHelper.cs:893-917`、`FoodItemDirectory.cs:196-205` |
| 非水液体一律被判成"沟渠水"：`GetPurityArrayIndex` 兜底返回 5，而 5 的 `modValue = -90` | `WaterFeatureHelper.cs:451-461`、`ItemConditionList.cs:385-395` |
| 容器基价走 `marketScaledValue`，在乘数之后相加 | `GameItem.ComposeStagedValue` |

最后两条是本模组存在的全部理由：内容值 13 会先被 ×0.1，再加 3 块瓶价，最后成交价 ≈4。

## 设计判断

- **不是 bug，是取舍**。弹窗文案 + "可食用梦帽显式摘掉 `CHEMICAL_SUPPLIES`"两处证据说明工作室清楚这个 tag 的含义。
- **套利不是理由**。这游戏的核心循环就是低买高卖（供应商批发 −15%~−33%，玩家按原价卖给顾客），
  所以"有差价所以禁止"这个论证对水不成立，对化学品也不成立。第一版复盘里写过这个错误论证，已撤回。
- **真正的风险是空价签**：化学液体从来没有价格表，因为它们是中间品。缺的不是"允许出售"，是"定价"。
- **数值落点**：按水的基础水档 40/L，普通包 50 拆出卖 61（+22%），落在游戏自身批发区间内；
  化学品包没有批量补货渠道，构不成刷钱。做成药再卖仍然远高于散装，激励没被破坏。

## 踩过的坑

1. **−90% 兜底**：第一版只改价格，实测成交价掉到一成。原因是水质特性的条件被算成沟渠水。
   修法是把 `CATEGORY_WATER_PURITY` 特性 `isDisabled = true`，并在三个钩子里各关一次
   （液体变化 / 卖出判定 / 读价）。
2. **高频重置**：原版有个每秒触发的循环会把 `isDisabled` 重置成 `false`，所以"关一次"不够；
   也在提醒我们：不要在这种高频路径上放重活。
3. **读价路径不能重**：`GetTagReadonly` 会 `Clone()` 一个 `TagState`，`GetTotalVolume` 要遍历 36 种液体。
   所以 `GetNegociatedValue` 的前置只做"关水质评级"（靠物品上的 `CHEM_RESALE_REAGENT_TAG` 标记），
   完整归一化只在液体变化和卖出判定时做。
4. **日志刷屏**：第 2 条的副产品——第一版每秒一行日志。改成"首次归一化 / 价格或类型真的变了"才打。
5. **`python` 是商店占位程序**：`package.sh` 里 `command -v python3` 拿到的是 WindowsApps 的桩，
   什么都不做就退出 49。加了 `scripts/find-python.sh`，按 `$DSH_PYTHON` → DSH 运行时 → PATH 的顺序验证 `import PIL, numpy`。

## 没做的事（留给后来的人）

- **覆盖那句"不可交易"的文案**：文本在 Unity 本地化 bundle 里，需要确认能否安全替换；没验证。
- **按试剂分价**：现在一律按水价。酒精/亲脂结合剂显然比酸碱值钱，做一张价目表是下一步。
- **专门的回收商**：现在靠补 `CHEMICAL_SUPPLIES` 蹭毒药买家/药品商，语义上略怪；
  新客户能讲圆这个故事（`StoreClientListDict.storeClientDict` 是公开静态字典，可插；还要往 `factionPools` 加权重）。
- **试剂纯度**：化学品产物有 `CATEGORY_CHEMICAL_PURITY` 分级，散装试剂没有。要做得更深就得接这套系统。
