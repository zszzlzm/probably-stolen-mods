# 试剂可售（ChemResale）— 原型 A

> 状态：**游戏内验证通过（2026-11-25 12:54）**，价格与出售均符合预期。本地已部署、已写信任记录。
> **未上传工坊。** 0.1.0 是原型，不具备成品包装（无封面、无 README、无描述）。

## 要验证什么

| 问题 | 预期 | 在哪看 |
|---|---|---|
| 拆包后瓶子有价格了吗 | 250 ml 试剂 ≈ **13**（内容 10 + 瓶基价 3），原来是 ≈6 | 鼠标悬停物品的价值行 |
| 化学买家收吗 | 毒药买家 / 药品商 / Ashish 现在应接受 | 把瓶子放上柜台，客户台词应从“wrong item”变“right item” |
| 净收益 | 买包 50 → 拆出卖 61（**+22%**），落在游戏自身批发差价 15~33% 内 | 结算对话 |

## 实现（3 个文件，约 160 行）

- `src/ReagentPricing.cs` — 判定“试剂瓶”（`LIQUID_CONTAINER_TAG` 且 8 种试剂液体之一），
  按 `WaterFeatureHelper.GetWaterPrice`（40/1000 ml）写 `unitValue`，补 `CHEMICAL_SUPPLIES` 类型，
  并关掉水质评级；给瓶子打一个自己的标记 `CHEM_RESALE_REAGENT_TAG`，供热路径快速识别。
- `src/ChemResalePatches.cs` — 三个 Harmony 钩子：
  1. `WaterFeatureHelper.UpdateWaterFeature` 后置 → 每次加液/倒液/混合都做完整归一化；
  2. `StoreClient.IsClientBuyingThisItem(GameItem, bool)` 前置 → 卖出判定前归一化（旧存档的瓶子靠这里补票）；
  3. `GameItem.GetNegociatedValue` 前置 → 只做“关掉水质评级”这一件廉价操作，保证读价不带 −90%。
- `src/ChemResaleMod.cs` — IMod 入口，只打一行日志。

试剂白名单：`alcohol, methylol, reducing_agent, acid, base, stabilizing_agent, lipobond_agent, chlorine`。
污染物（`chemical_contaminant` 等）故意不在表内，免得脏水被当成化学用品卖。

## 依据（反编译，`probably_stolen_decomp/`）

- 拆包：`MaterialDirectory.cs:94-158`（普通包 50 → 2×迷你酒精 + 亲脂结合剂 + 酸 + 碱；管制包 100）。
- 资格：`StoreClient.cs:449-482`（黑名单 → ALL_TYPE → id 表 → tag 表 → willAcceptItem）。
  化学买家只在 `StoreClientList.cs:185 / 1453 / 3327` 和 `StoreClientListSupplier.cs:181` 挂 `CHEMICAL_SUPPLIES`。
- 价格：`WaterFeatureHelper.cs:369-377`（水费率 40/1000 ml）；`WaterHelper.AddLiquid` → `UpdateWaterFeature`
  不动 `unitValue`，所以瓶装试剂一直是 `FoodItemDirectory.cs:196-205` 的 3。
- 容器基价另加：`WaterHelper.GetContainerPrice`（`LIQUID_CONTAINER_BASE_PRICE_TAG`）。

## 已知副作用 / 待观察

1. `CHEMICAL_SUPPLIES` 类型还被子系统读：`VendingMachineHelper.cs:428`（禁止投放）、
   `ShipSystemDirectory.cs:98`（船舱存放白名单）。前者会让试剂瓶不能塞自动售货机，后者无害。
2. 弹窗文案仍写着“不可交易”（`mech_chemical_supplies_unpack_warning`），装了这个模组后是假话。
   正式版要么覆盖文案（需确认能否改 Unity Localization 表），要么在工坊页说明。
3. 试剂瓶的“水质”特性仍显示“未知液体 (0% 纯度)”——这是原版行为，未处理。
4. 若后续要调价：改 `ReagentPricing.Apply` 里的一行（当前直接用水速率，系数 1.0）。
5. 用试纸测过试剂瓶之后，工具提示仍会显示“未知液体 (90%-)”——`IsFeatureDiscovered` 不看
   `isDisabled`。只影响文案，不影响价格。
6. 原版有个高频循环会不断把 `CATEGORY_WATER_PURITY.isDisabled` 重置成 `false`（第一版实测每秒
   触发一次），所以我们的钩子每次都要再关一次；价格没问题，但 0.1.0 的初版把这件事写进了日志，
   导致日志每秒一行。现在只在“首次归一化 / 价格或类型真的变了”时打日志。
7. `CHEM_RESALE_REAGENT_TAG` 会随物品写进存档。卸载模组后是个无害的未知 tag；重装后立刻恢复作用。
8. 读价路径（`GetNegociatedValue`）只做廉价判断：原版 `GetTagReadonly` 会 `Clone()` 一个
   `TagState`，而 `WaterHelper.GetTotalVolume` 要遍历 36 种液体——所以完整归一化绝不能放进读价路径。

## 坑：非水液体一律被判成“沟渠水 −90%”

`WaterFeatureHelper.GetPurityArrayIndex`（`:451-461`）在纯度不匹配任何档位时**兜底返回 5**，
而 5 是 `GUTTERFLOW_WATER_INDEX`，对应条件 `ItemConditionList.CreateGutterflow()` 的
`modValue = -90`（`:385-395`）。纯度 = 水体积 / 总体积，试剂瓶里水 = 0 → 必然落到兜底。

这条 modValue 是 `ValueStage.Innate`，会乘到基础价值上；容器基价是 `marketScaledValue`，
在乘完之后才相加（`GameItem.ComposeStagedValue`）。所以：

| | 未处理 | 处理之后 |
|---|---|---|
| 内容（250 ml） | 13 × 0.1 = 1.3 | 13 |
| 瓶子基价 | +3 | +3 |
| 成交价 | **≈4** | **≈13** |

原版从没有“可贩卖的非水液体容器”，所以这个兜底从没暴露过；装酸的瓶子是第一个踩进去的。

修法：`ReagentPricing.Apply` 里把 `CATEGORY_WATER_PURITY` 特性 `isDisabled = true`。
`UpdateWaterFeature` 每次都会把它重置为 `IsEmpty`，所以三个钩子（液体变化 / 卖出判定 /
读价 `GetNegociatedValue`）都会重新关一次。

## 构建 / 部署

```bash
bash ChemResale/scripts/build.sh      # 需先关游戏（DLL 被占用）
python tools/trust_local.py --folder "/f/SteamLibrary/steamapps/common/Probably Stolen/Mods/ChemResale" --id harness.chem-resale --dll ChemResaleMod.dll
```

注意：本模组目录只有 `manifest.xml` + DLL，所以 `folderHash` 是空列表的 SHA256
（`e3b0c442…`）——这是**正确值**，不是 bug；加了 `Textures/` 等文件后就会变。
