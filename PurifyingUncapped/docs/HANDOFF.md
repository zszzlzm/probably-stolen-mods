# 净化无上限 Mod — 交接资料

> 目标：把「净化水质」基因的 **每晚去除比例上限 95%** 去掉，改为最高 100%。
> 本目录已经放了一份**可编译通过的参考骨架**（`PurifyingUncapped/`），另一个会话可以直接用，也可以按本文重写。

**设计意图（写 mod 描述时可用）**：原版 21 级以后 share 被硬卡在 95%，26 级也要 3–4 晚；玩家只能用「多摆几台水培机」来堆吞吐，实体更多、操作更繁。本 mod 让公式自然涨到 100%，26 级一晚清完（除矿物质），减少机器数量和每晚操作。

---

## 0. TL;DR

- 全游戏只有一处 95% 上限：`PlantWaterQuality.PurifyingShare(int rank)` 里的 `Mathf.Min(0.95f, ...)`。
- 它只有两个调用点：`PlantWaterQuality.Purify`（实际去除）和 `PlantWaterQuality.DescribePurifying`（tooltip 文本）。
- 用 Harmony **Prefix** 把这个静态方法改成 `Mathf.Min(1f, 0.1f * PlantGeneticsHelper.RankScale(rank))`，gameplay 和 tooltip 会一起变。
- 游戏自带的 ModLoader 会自动 `harmony.PatchAll(assembly)`，mod 里**不需要**自己 new Harmony / PatchAll。
- 只改 `PurifyingShare` **不会**改 `PurifyingFloor`：22–25 级重金属仍会卡在 0.01%，26 级才真正 0。详见 §6。

---

## 1. 需求与验收标准

### 必须

1. 26 级净化基因：一晚（一次 `Purify`）把水里**除 `mineral` 外**的所有可过滤液体清到 0。
2. 21 级：去除比例从 95% 变成公式原值 **98%**（tooltip 显示 98%）。
3. 22–25 级：去除比例 **100%**（tooltip 显示 100%）。
4. ≤20 级：行为不变（≤94.57%，tooltip 仍可能四舍五入到 95%）。
5. 不改存档结构；卸载 mod 后存档可正常读。
6. 不改动 `mineral` 的保留规则，也不改「纯度最高可达 x%」的第二个数字（除非另做设计决定，见 §6）。

### 不做

- 不新增物品、不改本地化 CSV、不改水培机/生长速度/每晚一次净化节奏。
- 不动 `PurifyingFloor`、`PurifyingCeilingPercent`、`PlantFilterable`。

---

## 2. 环境事实

| 项 | 值 |
|---|---|
| 游戏 | Probably Stolen（深空当铺：可能是偷的），Steam AppID `4348910` |
| 游戏目录 | `F:\SteamLibrary\steamapps\common\Probably Stolen` |
| 程序集 | `...\Probably Stolen_Data\Managed\Assembly-CSharp.dll` |
| Unity | 2021.3.45f2，Mono |
| Mod 目标框架 | `netstandard2.1` |
| Mod 框架 | 游戏内置 ModLoader（`IMod` + `manifest.xml` + Harmony），不是 BepInEx |
| 游戏版本 | 现有 mod 的 manifest 写 `0.46D`；若游戏已更新，按实际版本改 |
| 可参考的现成 mod | `FilterPrinter/`、`Pharmacy/`（都有 csproj、build/deploy 脚本、manifest） |
| 反编译源码 | `probably_stolen_decomp/`（本次会话用 ilspycmd 生成） |

ModLoader 关键行为（`probably_stolen_decomp/ModLoader.cs` 1586–1663）：

```csharp
Assembly assembly = Assembly.LoadFrom(dllPath);
// 找 IMod 实现
IMod mod = (IMod)Activator.CreateInstance(list[0]);
Harmony harmony = new Harmony("mod." + manifest.ID);
harmony.PatchAll(assembly);   // 自动应用 [HarmonyPatch]
mod.Init(manifest);
mod.OnEnable();
```

所以 mod 程序集里只要有：
- 一个 `IMod` 实现（必需，否则 “No class ... implements IMod” 不加载）；
- 一个或多个 `[HarmonyPatch]` 类（自动应用）。

---

## 3. 代码事实（带行号）

### 3.1 95% 上限的位置

`probably_stolen_decomp/PlantWaterQuality.cs`：

```csharp
public const float PURIFYING_SHARE_PER_CYCLE = 0.1f;   // L6
public const float PURIFYING_MAX_SHARE = 0.95f;        // L8

public static float PurifyingShare(int rank)           // L21
{
    return Mathf.Min(0.95f, 0.1f * PlantGeneticsHelper.RankScale(rank));
}
```

`RankScale`（`PlantGeneticsHelper.cs` L54）：

```csharp
public static float RankScale(int rank)
{
    if (rank <= 0) return 0f;
    return Mathf.Pow(rank, 0.75f);
}
```

### 3.2 调用点只有两处

`grep PurifyingShare` 在整个 `Assembly-CSharp` 只有：

1. `PlantWaterQuality.Purify`（L67）——实际去除：
   ```csharp
   float num = PurifyingShare(rank);
   ...
   int volumeToRemove = Mathf.Max(1000, Mathf.RoundToInt((float)num2 * num)); // L74
   removed += WaterHelper.RemoveContaminantFromContainer(
       container, item.identifier, volumeToRemove, PurifyingFloor(item, rank)); // L75
   ```
2. `PlantWaterQuality.DescribePurifying`（L100）——tooltip：
   ```csharp
   return PlantGeneticsText.EffectPurifying(
       Mathf.RoundToInt(PurifyingShare(rank) * 100f).ToString(),
       PurifyingCeilingPercent(rank).ToString("0.0#"));
   ```

因此 patch `PurifyingShare` 一处，玩法与文本同时生效。

### 3.3 净化是每晚一次

调用链：

`PlayerStore` 夜间结算 → `onCycleEndSlotItemFunc`（`PlayerStore.cs` L1760）
→ `MachineHydroponic.GrowOneCycle`（L115–121）
→ `HydroponicHelper.ContinueGrowing`（L274–290）
→ `RunGrowTickHooks` → `PlantWaterQuality.Purify`

`ContinueGrowing` 里 `progress` 循环只跑营养/污染物伤害，`Purify` 在循环外，因此**一晚只净化一次**，与加工速度无关。

### 3.4 可过滤集合

`PlantWaterQuality.IsPlantFilterable`（L36）：

```csharp
liquid.canBeRemovedByPurifier && liquid.basePurifierRemoveAmount > 0
    && liquid.identifier != "mineral"
```

即除 `water`、`mineral` 外的所有液体（共 34 种，含 27 种 base=12 的液体，以及 debris）。

### 3.5 纯度上限是另一套逻辑

`PurifyingFloor`（L31）与 `PurifyingCeilingPercent`（L88）**不受 95% 上限影响**：

```csharp
public static int PurifyingFloor(Liquid liquid, int rank)
    => liquid.baseMaxPurityFromMachine / Mathf.Max(1, rank);   // 整数除法
```

26 级时 `25 / 26 = 0`，所有 floor 归零，所以 26 级是「能真正 100%」的那一级；25 级重金属仍 `25 / 25 = 1`。

---

## 4. 唯一改动（推荐实现）

`src/PurifyingSharePatch.cs`：

```csharp
using HarmonyLib;
using UnityEngine;

namespace PurifyingUncapped
{
    [HarmonyPatch(typeof(PlantWaterQuality), nameof(PlantWaterQuality.PurifyingShare))]
    internal static class PurifyingSharePatch
    {
        private static bool Prefix(int rank, ref float __result)
        {
            if (rank <= 0)
            {
                __result = 0f;
                return false;
            }

            __result = Mathf.Min(1f, 0.1f * PlantGeneticsHelper.RankScale(rank));
            return false;
        }
    }
}
```

要点：

- 用 **Prefix + `__result` + return false**，直接替换返回值，最稳；
- 保留 `rank <= 0 → 0` 的原行为；
- `Mathf.Min(1f, ...)` 是「把 95% 上限改成 100%」。如果写成 `0.1f * RankScale(rank)`（完全不封顶），26 级 tooltip 会显示 115%，很怪，且 `RemoveContaminantFromContainer` 本来也会把 `newC` clamp 到 0，所以没必要。
- 不要用 transpiler 改 `0.95f` 常量：方法里没有局部常量，改 IL 反而更脆。

`src/PurifyingUncappedMod.cs`：只需一个最小 `IMod` 实现，让 loader 能实例化并打日志。

---

## 5. 改动后的数值（已核对）

`share = min(1, 0.1 × rank^0.75)`，`PurifyingCeilingPercent` 不变。

| 等级 | 原 share / tooltip | 新 share / tooltip | 重金属 floor | 备注 |
|---|---|---|---|---|
| 19 | 91.01% / 91% | 91.01% / 91% | 25/19 = 1 | 不变 |
| 20 | 94.57% / 95% | 94.57% / 95% | 1 | 不变（原代码也没到 95 上限） |
| 21 | 95% / 95% | **98.10% / 98%** | 1 | 小 buff |
| 22 | 95% / 95% | **100% / 100%** | 1 | 一晚清掉除重金属外的所有杂质 |
| 23–25 | 95% / 95% | **100% / 100%** | 1 | 同上；tooltip 上限仍 99.99% |
| 26 | 95% / 95% | **100% / 100%** | **0** | 一晚全清（除 mineral），tooltip 100.0% |

> 注意：rank 20 的 **实际** share 是 94.57%，但 `RoundToInt(94.57)=95`，所以原版 tooltip 在 20 级也显示 95%；不要误以为 20 级被 cap 了。

---

## 6. 重要边界：26 级门槛还在（另一个会话必须知道）

只 patch `PurifyingShare` 时：

- **22–25 级**：`volumeToRemove = c`，但 `RemoveContaminantFromContainer` 的 `minPercentage` 来自 `PurifyingFloor`。重金属 `25/22..25 = 1`，所以重金属会被 clamp 在 `water × 1/10000 = 0.01%`，不会到 0。其它 33 种液体一晚到 0。
- **26 级**：`25/26 = 0`，重金属也能到 0，才真正「除矿物质外全清」。
- **21 级**：share 98%，不是 100%；大容器仍要 2–3 晚，重金属 0.01%。

所以如果用户的实际诉求是「我 21 级就要一晚全清」，那就不是「删 95% 上限」能解决的，需要额外决策：

| 方案 | 改动 | 后果 |
|---|---|---|
| A（本文推荐） | 只把 0.95 改成 1.0 | 21 级 98%，22+ 100%；26 级才全清重金属 |
| B | share 改成 21 级起强制 1.0 | 21 级也 100%，但不再是原公式 |
| C | 同时把 `PurifyingFloor` 改成 0（或除以更大数） | 21 级也能清重金属，但「纯度最高可达」会从 99.99% 变 100%，是更大的平衡改动 |

默认按 **A** 实现；如果用户验收时要求「21 级就 100%」，再上 B/C。交接时先确认这一点。

---

## 7. 项目骨架与构建

本目录已经是可编译骨架：

```
PurifyingUncapped/
  PurifyingUncapped.csproj
  src/
    PurifyingUncappedMod.cs      # IMod 入口
    PurifyingSharePatch.cs       # 唯一 Harmony patch
  mod/
    manifest.xml                 # loader 读取
  scripts/
    build.sh                     # build + deploy
    deploy-when-closed.sh        # 等游戏退出再部署
  build/PurifyingUncappedMod.dll # 已编译验证（0 warning / 0 error）
```

### 7.1 manifest

```xml
<?xml version="1.0" encoding="utf-8"?>
<Mod>
  <ID>harness.purifying-uncapped</ID>
  <Name>净化无上限 / Purifying Uncapped</Name>
  <Author>harness</Author>
  <ModVersion>1.0.0</ModVersion>
  <Description>移除净化水质基因的 95% 去除比例上限，改为最高 100%。/ Removes the 95% per-night removal cap on the Purifying gene, raising it to 100%.</Description>
  <GameVersions><Version>0.46D</Version></GameVersions>
  <Prerequisites />
  <Assemblies><Assembly>PurifyingUncappedMod.dll</Assembly></Assemblies>
  <Capabilities />
</Mod>
```

注意：

- `<Assemblies>` 里的 DLL 名必须和 `AssemblyName` 一致；
- `<Capabilities />` 留空：本 patch 不用文件/网络/反射；
- 中文用 UTF-8；`GameVersions` 按当前游戏版本改；
- 不要尝试 patch `ModLoader`/`ModTrust`/`ModScanner` 等 guard 类型（scanner 会直接拒绝）。

### 7.2 构建

```powershell
dotnet build PurifyingUncapped\PurifyingUncapped.csproj -c Release -o PurifyingUncapped\build
```

或：

```bash
bash PurifyingUncapped/scripts/build.sh
```

`csproj` 里的 `GameManaged` 是硬编码路径；游戏换盘/换目录时改这里。

### 7.3 部署

游戏运行时 DLL 被锁，先退出游戏，再：

```powershell
New-Item -ItemType Directory -Force "F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\PurifyingUncapped" | Out-Null
Copy-Item "PurifyingUncapped\build\PurifyingUncappedMod.dll" "F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\PurifyingUncapped\" -Force
Copy-Item "PurifyingUncapped\mod\manifest.xml" "F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\PurifyingUncapped\" -Force
```

或 `bash PurifyingUncapped/scripts/deploy-when-closed.sh`。

启动游戏 → Mod 菜单 → 启用「净化无上限」。如果是第一次加载本地 mod，按游戏提示信任/启用。

---

## 8. 验证清单

### 8.1 加载

- `Player.log`（`%USERPROFILE%\AppData\LocalLow\...`）里应出现：
  - `[ModLoader] Loading: PurifyingUncappedMod.dll`
  - `[ModLoader]   Harmony: 1 method(s) patched`
  - `[PurifyingUncapped] Initialized: Purifying per-night removal cap 95% -> 100%`
- Mod 列表里显示「净化无上限 / Purifying Uncapped」，启用无报错。

### 8.2 Tooltip

对 21 / 22 / 26 级的净化种子或 DNA 磁盘看说明，第一段应为：

- 21 级：`每晚去除各类污染物中的98%`
- 22–25 级：`每晚去除各类污染物中的100%`
- 26 级：`每晚去除各类污染物中的100%，纯度最高可达100.0%`

第二段（`纯度最高可达`）：

- 21–25 级：`99.99%`（不变，因为 floor 没动）
- 26 级：`100.0%`（不变，因为 26 级 floor 本来就是 0）

### 8.3 实际净化（建议固定测试）

准备：6 L 水罐，装满最脏的 35% gutterflow 水（化学污染物约 1,170,000 µL），水培机里种 26 级净化作物，通电。

> 测试号没有 26 级种子时：用游戏内 DNA 操作台反复叠 `purifying`（该 trait 是 `Unlimited()`），或让测试用的 debug mod 直接生成；`hydroreed_seed` 天生只有 IV 级，不能直接当 26 级样本。

| 等级 | 一晚后的水 |
|---|---|
| 25 | 化学/有机/微生物/物理 = 0；重金属剩 0.01%；mineral 保留 |
| 26 | 除 mineral 外全部 = 0；纯度显示接近 100% |

对照：原版 26 级同一瓶要 4 晚。

### 8.4 回归

- 20 级：tooltip 仍 95%，净化速度和原版一致；
- 21 级：tooltip 98%，6 L 最脏水从 4 晚变 3 晚（小容器可能仍是 3 晚）；
- 普通 95% 纯度的水：26 级仍是一晚（原版 3 晚）；
- 没有矿物质的纯水：不应报错、不应把水清空（`water` 本身不可过滤）；
- 空容器/无净化基因：`rank <= 0` 时 share=0，`Purify` 不动作。

---

## 9. 风险 / 兼容 / 卸载

- **全局生效**：Harmony patch 是全局的，mod 加载后所有 `Purify`/tooltip 调用都会走新值；不写存档，旧存档无需迁移。
- **不写存档**：没有新增 tag/字段，卸载后存档正常。
- **不碰 mineral**：`PlantFilterable` 排除 `mineral`，所以「除矿物质外清干净」仍成立；`HandleNutriment` 仍会按 `mineralUseRate` 消耗一点矿物。
- **不改变「一晚一次」**：不要试图通过改 `PurifyingShare` 让一晚净化多次；频率由 `onCycleEndSlotItemFunc` 决定。
- **游戏更新风险**：如果 `PlantWaterQuality.PurifyingShare` 被重命名/内联/改签名，patch 会失效；用 `nameof` 编译期绑定，更新后重编译即可。若方法被删，ModLoader 会在 `PatchAll` 时抛错并禁用 mod，不会崩存档。
- **兼容性**：与只改物品/配方的 mod 无冲突；与同样 patch `PurifyingShare` 的 mod 冲突（后加载的 prefix 可能覆盖），避免同时装两个。

---

## 10. 参考

- 反编译源码：
  - `probably_stolen_decomp/PlantWaterQuality.cs`（L8、L21–24、L31–34、L56–86、L88–101）
  - `probably_stolen_decomp/PlantGeneticsHelper.cs`（L32、L54）
  - `probably_stolen_decomp/PlantTraitList.cs`（L164–170，`purifying` trait）
  - `probably_stolen_decomp/PlayerStore.cs`（L1760）
  - `probably_stolen_decomp/MachineHydroponic.cs`（L115–121）
  - `probably_stolen_decomp/HydroponicHelper.cs`（L274–290）
  - `probably_stolen_decomp/ModLoader.cs`（L1586–1663）
  - `probably_stolen_decomp/IMod.cs`
- 现成 mod 模板：
  - `FilterPrinter/FilterPrinter.csproj`
  - `FilterPrinter/src/FilterPrinterMod.cs`
  - `FilterPrinter/src/HandleFilterPatch.cs`
  - `FilterPrinter/scripts/build.sh`
  - `Pharmacy/Pharmacy.csproj`

---

## 11. 给下一个会话的 5 步

1. 读本文 §0–§6，确认验收口径是 **A**（21 级 98%、22+ 100%、26 级全清）还是 **B/C**（21 级就要 100%）。
2. 直接用 `PurifyingUncapped/` 骨架；先 `dotnet build` 确认 0 warning / 0 error。
3. 退出游戏，把 `build/PurifyingUncappedMod.dll` + `mod/manifest.xml` 复制到 `F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\PurifyingUncapped\`。
4. 启动游戏，在 Mod 菜单启用，按 §8 的 tooltip + 6 L 水罐测试；对照原版 26 级 4 晚 → 新版 1 晚。
5. 如果用户要发布，补 `preview.png` / `README.txt` / 打包 zip；如果只是自用，§7.3 的部署就够。


---

## 12. 本会话执行结果（2026-11-17）

- 验收口径按 **A** 落地：21 级 98%、22 级起 100%，26 级一晚除 mineral 全清（重金属 floor 仍在 22–25 级生效，未改）。
- 已 `dotnet build`（0 warning / 0 error）并部署到
  `F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\PurifyingUncapped\`
  （`PurifyingUncappedMod.dll` 5120 B + `manifest.xml`）。
- 离线数值核对：`tools/VerifyShare`（net10 控制台，直接反射调用 Prefix，不依赖 Harmony）
  结果与 §5 表格一致，并在末尾自检 rank≤20 不变、rank≥22 为 100%。
  注意：**不要在 .NET 8+ 上直接跑游戏自带的 0Harmony**，它依赖 Mono 的
  `ILGenerator.MarkSequencePoint` 重载，会抛 `MissingMethodException`；要在游戏里验证补丁。
- 实机验证（已启动游戏，看 Player.log）：
  ```
  [ModLoader] Loading: PurifyingUncappedMod.dll
  [ModLoader]   Harmony: 1 method(s) patched
  [净化无上限 / Purifying Uncapped]: Initialized: Purifying per-night removal cap 95% -> 100%
  ```
  随后可用 `scripts/check-log.sh` 复查。
- 与已装 Workshop mod 的冲突检查：`PurifyingShare` 在 Mods/ 与 workshop content 的所有 DLL 里
  只有本 mod 引用（HydroponicSeedPreview / MachineTweaks 都没碰这个函数）。
- 尚未打包发布（无 preview.png / README / zip）；需要上架时再补。

## 13. 发布包（2026-11-17）

- 封面：`scripts/gen_keyart.py`（本地 ComfyUI / Qwen-Image，1280×720）+ `scripts/make_cover.py`
  → `mod/preview.png`（1280×720，625 KB）。
- `packaging/README.txt`、`packaging/workshop_description.txt`（中英双语）。
- `scripts/package.sh` 生成 `dist/`：
  - `PurifyingUncapped-v1.0.0/`（manifest.xml、PurifyingUncappedMod.dll、README.txt、preview.png）
  - `PurifyingUncapped-v1.0.0.zip`
  - `SHA256SUMS.txt`
  - `harness.purifying-uncapped.vdf`（appid 4348910，publishedfileid 0，visibility 2 隐藏）
- DLL 与已部署到 `Mods/PurifyingUncapped/` 的完全一致（sha256 985dada0…）。
- 上传：`steamcmd +login <user> +workshop_build_item <vdf> +quit`；首次上传需在浏览器里接受创意工坊协议，
  确认无误后把 vdf 的 visibility 改成 0 再传一次即公开。
