# 《更好的奥克莫吸注射器 / Luxury Nomore Injector》开发复盘

> 2026-11-22 ~ 11-23 · Probably Stolen 0.46D（Unity 2021.3.45f2 / Mono / netstandard2.1）
> 进度：代码 / 实机验收 / 封面 / 双语描述 / 打包都已完成，条目 3844271622 已上传但仍是隐藏状态。
> 平台通用经验（Hook、打包、SteamCMD、封面流水线）见仓库根 `docs/RETROSPECTIVE.md`，本文只写**这个「一行补丁」的 mod 带来的新东西**。

## 0. 一句话

116 行代码、一个 Harmony postfix，交付物是「一件物品的标签 + 一个数字」。技术含量不在 Harmony，在两件与代码无关的事：**证明补丁真的生效**（第一版打了补丁却静默无效），和**证明 350 这个数字有原版锚点**（否则就是拍脑袋改数值）。

## 1. 交付与验收

| 项 | 状态 | 证据 |
|---|---|---|
| mod 加载 | ✅ | `[ModLoader] Loading: LuxuryNomoreInjectorMod.dll`；`audit: harness.luxury-nomore-injector ... running=True trust=Match caps=none hash=8dd3ce7e…` |
| 补丁挂上 | ✅ | 自定义日志 `Patched MedsItemDirectory.Injector` |
| 类型 + 价格生效 | ✅ | `Applied: pink_alt_injector is now LUXURY_ITEM with value 350`（只在首次命中时打一次） |
| 游戏内 tooltip | ✅ | 用户实机确认「好了，功能正常」（价格与类型都变了） |
| 化工合成产物也是 350 | 🟡 代码路径已核 | `MachineChemFinisher.cs:72` 走 `DirectoryMaster.Item(text)` → 同一个工厂；未逐件实机点过 |
| 旧存档已有注射器 | 🟡 存档实测 | `save_8.es3` 里 `unitValue` 89 处 / `itemTypes` 89 处 → 价格与类型都挂在实例上，老档保持 50 且没有奢侈品类型 |
| 封面 | ✅ | `mod/preview.png` 1280×720 / 718 KB；包内 640×360 / 238 KB |
| 双语描述 | ✅ | `packaging/workshop_description.txt`（中文用户定稿，英文按中文重写，5.8 KB） |
| 打包 | ✅ | `dist/LuxuryNomoreInjector-v1.0.0.zip` 249 KB（包内 4 个文件，preview 640×360 / 238 KB） |
| 上架 | 🟡 已上传隐藏 | 工坊条目 **3844271622**，`visibility 2`；剩「页面粘贴全文描述 + 改公开」两步 |

## 2. 三条平台事实（这个 mod 的全部技术含量）

### 2.1 物品只有一个创建入口：目录工厂

- `MedsItemDirectory.InitDirectory` 里 `Add("pink_alt_injector", () => Injector(InjectorColor.PinkAlt, ...))`（`MedsItemDirectory.cs:27`），而 `Injector(...)`（`:361`）是这件物品唯一的构造点。注意**六种颜色的注射器都走同一个 `Injector`**，所以补丁里必须过滤（这次用 `spritePath`），否则会把别的颜色一起改掉。
- 所有能拿到这件物品的路径最后都过这个工厂：目录生成、化工精制机产物（`MachineChemFinisher.cs:72` 用 `DirectoryMaster.Item(text)`）、李北文的存货（`StoreClientListWanted.cs:1097-1104` → `AddDirectSellingItemToTable(id)` → `DirectoryMaster.Item`，`PlayerStore.cs:2537`）、调试生成器。
- 所以**patch 工厂 = 覆盖全部路径**；patch 某一条"结果"（比如 `DirectoryMaster.Item` 的返回值）就一定漏。
- 工厂是实例方法，`AccessTools.Method(typeof(MedsItemDirectory), "Injector")` 能直接拿到（无重载歧义）。

### 2.2 `Directory<T>.Create` 先造、后命名 → 工厂里 `identifier` 是 null

`Directory.cs:24-38`：

```csharp
T val = factoryDictionary[identifier]();   // 先跑工厂
if (val != null) {
    val.identifier = identifier;           // 才赋值
    val.identifierName = TagSystem.StringToDisplayString(identifier);
}
```

这就是第一版失败的全部原因（见 §4）：postfix 里 `__result.identifier` 还是 `null`。

工厂返回那一刻已经就绪的字段：

| 字段 | 工厂返回时 | 依据 |
|---|---|---|
| `spritePath` | ✅ 已定 | switch 里赋值（`:437`），`SetSpriteAndShape` 在 switch 之后（`:455`） |
| `name` / `unitValue` / 类型 | ✅ 已定 | 工厂内赋值 |
| `identifier` | ❌ null | `Directory.Create` 之后才赋值 |

所以稳定签名是 `spritePath == "injector_pink_alt"`，`identifier` 只作兜底。

### 2.3 `SetGameItemType` 一次调用 = tag + 类型表

`GameItem.cs:2279-2291`：`SetGameItemType(x)` 内部就是 `EnableTag(x)` + `itemTypes.Add(x)`。于是 `IsTag("LUXURY_ITEM")`（`StoreClient.cs:427` 就是这么判的）和 `IsGameItemType` 都会命中，**不需要两种都设**。显示名走 `type_luxury_item` = 奢侈品 / Luxury Item。

### 2.4 「奢侈品」这个类型到底改了哪四件事

| 受影响的系统 | 代码位置 | 实际效果 |
|---|---|---|
| 求购客 | `StoreClientList.cs:154`（上层访客）、`:167`（挑剔顾客 `ulDiscerningShopper`，预算 750+） | `clientBuyingTagList` 含 `LUXURY_ITEM` 的客人开始把它算进可买；这就是描述里「收藏家与上层客人会购买」的依据 |
| 拒收规则 | `StoreClient.cs:425-449` `IsRefusingLuxuryItem` | 「买水」类客人（求购表含 `WATER` 的收废品/水客）**拒收**奢侈品，除非阵营是游客或上层；会触发台词 `dialogue_no_luxury`「我买不起奢侈品。」 |
| 展示柜 | `ShowcaseHelper.cs:92-102` `GetTypeCount`；`:339-357` `GetDiscerningShopperChance` | 摆进展示柜会计入 `LUXURY_ITEM` 计数；但 `MAJOR_TYPES_LIST`（`TypeHelper.cs:24-28`）不含奢侈品、`CreateClientByStockType` 也没有奢侈品分支 → **不会**因为它自动派收藏家，还得有 `UL_DISCERNING_TASTE` 特权 |
| 价格 | `GameItem.cs:419-470` | 与类型无关：`GetValue = (unitValue + 液体等附加) × 状态/折扣系数 × 数量`，所以柜台价略高于 350（液体内容另计） |

写作时的分寸：描述里只写「买奢侈品的客人与收藏家会开始求购它；展示柜的奢侈品统计也把它算进去」——两句都成立；**没有**写成「摆进展示柜就会有收藏家上门」，因为那要靠特权。

## 3. 350 的依据（锚点，不是拍脑袋）

| 参照 | 值 | 位置 |
|---|---|---|
| 奥克莫吸注射器（原版） | `unitValue = 50L`，`MEDICAL` | `MedsItemDirectory.cs:439` |
| 赛纳普斯注射器（原版） | `unitValue = 350L`，`MEDICAL` + `LUXURY_ITEM` | `MedsItemDirectory.cs:345`、`:348` |
| 李北文存货上架 | 8 支，`SetWholesale(50)`（-50%），悬赏 `SetWanted(400)` | `StoreClientListWanted.cs:1080`、`:1097-1104`、`:1078` |

经济账（同样 100 ml 梦帽菇萃取液，99% 纯度）：

| 产物 | 产出 | 收入 | 加 15% 零售加价 |
|---|---|---|---|
| 梦尘（中级违禁品） | 100 ml | 3,636 | 3,939 |
| 奥克莫吸（50 一支） | 15 支（0.6 收率 / 4 ml 一支） | 1,788 | 2,045 |
| 奥克莫吸（350 一支） | 15 支 | 12,516 | —

- 结论：50 的时候，同样原料做奥克莫吸只有梦尘的一半收入、还要多烧 100 ml 还原剂，**没人会做**；350 之后变成梦尘的 3.4 倍。
- 为什么还是选 350：① 工序最长（萃取链 + 还原 + 催化 + 控温 + 蒸发）；② 它是奥克西莫的非成瘾替代品，没有溢价等于惩罚玩家做「对」的选择；③ 350 是原版已有锚点（赛纳普斯同档）；④ 剧情上 8 支从 400 变成 2800（五折 1400）才像一笔「通缉犯卖样品筹钱」的交易，而原版 8×50=400 恰好等于他 400 的悬赏，读起来像白送。
- 留了后手：真要压，150–200 会重新落回梦尘之下；现在这个数写进了工坊描述的「为什么是 350」，等于公开承诺，改价要发更新说明。

## 4. 唯一的真 bug：补丁打了，但没生效

- **现象**：用户实机测试后说「根本没生效啊。你再看看代码」——tooltip 还是 50，也没有奢侈品类型。
- **第一版代码**：postfix 里 `IsTarget` 只比 `__result.identifier == "pink_alt_injector"`。
- **根因**：§2.2 的赋值顺序，工厂返回时 `identifier` 是 `null`，比较永远 false，`return` 掉，什么都不做。
- **为什么日志没抓到**：补丁成功只打了一行 `Patched MedsItemDirectory.Injector`；匹配失败时**一行都不打**。于是"安装成功"和"生效"在日志里长得一模一样，唯一的区别只能靠进游戏看 tooltip。
- **修法**（`src/LuxuryNomoreInjectorMod.cs:107-114`）：`spritePath == "injector_pink_alt"` 优先，`identifier` 兜底；并在首次命中时打一行 `Applied: ...`。
- **教训**：
  1. **补丁必须有正向自证日志**——第一次真正命中时打一行。只有 `patched` 的日志等于没有日志。
  2. 往"工厂"上挂补丁前，先列表：工厂跑完那一刻哪些字段已经就绪（这次是 `spritePath` ✅ / `identifier` ❌）。
  3. 验收动作是「生成一件新物品读 tooltip」，不是「看日志里有没有 patched」。

## 5. 封面：先出画面，后上文字

- 用户明确要求分两步：「先做图片，图片上的文本等一会做」。所以生图阶段只出**纯画面**（画面里绝不允许模型写字），所有文字都在 PIL 排版阶段加。
- 候选一次出 10 张（`refs/gen/keyart_a..j.png`），风格指令围绕「丝绒展示柜 + 笔式自动注射器 + 粉色药窗」，参考图用用户给的 EpiPen 照片（`refs/gen/ref_epipen.png`）。选中丝绒展示柜那张（`keyart_i.png`，即 `keyart.png`）；淘汰的理由集中在三类：笔身被模型写出假文字（如 B）、注射器形态不像自动注射笔、药液画成橙色（药名是粉色系）。
- **文字避让是构图问题，不是排版问题**：9 字标题 96px ≈ 864px 宽，主体必须让出左侧约 1000px。第一版主体偏中，标题压到盒盖亮边，于是重构图两次（zoom 1.06 右移 90、zoom 1.10 右移 160）。
- 这两次重构图当时是临时脚本算的——**已经补成 `make_cover.py` 的 `--zoom/--dx/--dy`**（默认参数不改变现有输出），下一张图不用再手搓中间文件。
- 教训：生图时就把"文字占位"当构图约束（主体偏右下、左上留空），比事后裁切省一整轮。

## 6. 描述：中文定稿 → 英文镜像

结构（中英同构，8 个 `[h2]`）：它做了什么 / 为什么是 350 / 对玩家来说也是亏本买卖 / 注意 / 兼容性 / 安装 / 语言 / 反馈。

- 所有数字都来自反编译或实测：50→350、4 ml 一支、0.6 收率、3,636 / 1,788、8 支 2800 / 五折 1400、悬赏 400。没有一句「大概」。
- 用户改过中文之后，英文是**整段重写**而不是逐句替换——两种语言的句式长度差太多，逐句换会读起来像机翻。
- `[h2]注意[/h2]` 这种标签的闭合位置要先用 `cat -A` 看一眼（这系列工坊描述里 `[/h2]` 的写法不统一），否则改一个字整段就不渲染。
- 自我约束：描述里只写**验证过的机制**。奢侈品那段就是这么写的（见 §2.4 的分寸）。

## 7. 工具与流水线

- `scripts/build.sh`：`dotnet build -c Release -o build` → **先复制 DLL**（游戏运行时会锁，失败即 `exit 1`，别的文件一个都不动）→ 复制 manifest 与 `preview.png` → 校验非空。没有语言包，所以这次自检只有 dll + manifest + 缩略图三项。
- 封面两个脚本：`scripts/make_cover.py`（1280×720，系列版式，支持 `--zoom/--dx/--dy`）、`scripts/make_preview_640.py`（从 `mod/preview.png` 派生包内缩略图，保证两张图永远同源）。
- 部署目录 `Mods/LuxuryNomoreInjector/` 目前只有 `dll + manifest`，**缺 `preview.png`**——对比其它 5 个已发布 mod 的文件夹，每个都有。`build.sh` 已经补上这一步（含重签提示），但还没实际跑；补了之后 `folderHash` 会变（`tools/trust_local.py:53-63` 把除 manifest/dll 之外的所有文件都算进去），必须重跑一次 trust。
- 存档实测（`save_8.es3`）：`unitValue` 89 处、`itemTypes` 89 处、`identifier` 2132 处 → 每件物品实例各存一份价格与类型。所以"老档已有注射器保持原价"这条不是推测。
- 证据链固定为：`Loading` → `Patched` → `Applied` → `audit trust=Match running=True`，四条齐了才算交付。

## 8. 踩坑总表

| 现象 | 根因 | 修法 / 教训 |
|---|---|---|
| 补丁打了但价格没变 | 工厂返回时 `identifier` 还是 null（`Directory.Create` 后赋值） | 改用 `spritePath` 判定；首次命中打 `Applied` 日志 |
| 日志里"看不出有没有生效" | 只在 patch 成功时打日志，匹配失败静默 | 补丁要有"第一次真正命中"的正向日志 |
| 老档里的注射器没变 350 | 价格存在物品实例上（`unitValue`），不是每次读档重建 | 要么接受（写进描述「注意」），要么加读档迁移 |
| 水客/收废品的客人拒收这支药 | `LUXURY_ITEM` 触发 `IsRefusingLuxuryItem`（求购表含 WATER 的客人拒收奢侈品） | 这是标签的真实副作用；主题上说得通，但要在更新说明里提一句 |
| 以为摆进展示柜就会有收藏家 | 展示柜类型统计不含 `LUXURY_ITEM`，那条路要 `UL_DISCERNING_TASTE` 特权 | 描述里只写"统计算进去"，不写"会自动来客" |
| 标题压住盒盖亮边 | 9 字标题 864px，主体偏中 | 重构图（`--zoom/--dx/--dy`）；生图阶段就留文字位 |
| 部署目录缺缩略图 | `build.sh` 只复制 dll + manifest | 打包前补 `preview.png`，并重跑 trust（folderHash 变了） |

## 9. 如果重来

1. **动手前先反编译工厂**，把「工厂返回时哪些字段已就绪」列成表——这次 20 分钟就能避免第一版白写。
2. **每个补丁从第一行代码起就配一条"首次命中"日志**，把"安装成功"和"生效"在日志层面区分开。
3. **改数值前先找原版锚点**（同档物品的价格），把锚点和经济账一起写进描述；没有锚点的价格会被玩家当成作者拍脑袋。
4. **生图就按文字占位构图**：中文标题 9 个字是常态，左侧 1000px 一开始就当禁区。
5. **改类型/标签前，先全库 grep 这个标签被谁读**（`LUXURY_ITEM` 有 20+ 处），把副作用列出来再决定，而不是上线后被玩家发现"我的药卖不出去了"。

## 10. 待办

- **打包**：✅ `scripts/package.sh` 已跑通，产物见 `dist/`（zip 249 KB / 4 个文件 / 包内 preview 640×360）。
- **上架**：条目 **3844271622** 已上传，`visibility 2`。剩两步：在页面粘贴 `dist/workshop_description.txt` 全文；`VIS_OVERRIDE=0 bash scripts/package.sh` 后重传改成公开。
- **可选的旧档迁移**：`onLoaded` 里遍历已存在的 `pink_alt_injector` 实例，补类型 + 改价（一次性，写个标记避免反复）。目前没做，描述里按"接受原价"写的。
- **英文界面验收**：交给玩家反馈（系列约定：无人反馈即视为通过）。
- **源码公开**：六个模组的源码在 https://github.com/zszzlzm/probably-stolen-mods（Apache-2.0），
  本模组在 `LuxuryNomoreInjector/`；release `builds-2026-11-23` 附了安装包。
  想让人接手的话，工坊描述末尾可以加一行仓库链接（需要重传描述）。
