# Probably Stolen 模组源码 / Mod Sources

《Probably Stolen》（0.46D，Unity 2021.3.45f2 / Mono / netstandard2.1）的八个模组源码。
每个模组都对应一个创意工坊条目，源码放在这里，方便后来的人改数值、修 bug、或者接着往下做。

Source for eight mods for **Probably Stolen** 0.46D. Reusable under [Apache-2.0](LICENSE).

## 模组列表

| 模组 | 工坊 ID | 版本 | 做什么 | 目录 |
|---|---|---|---|---|
| 滤芯打印机 / Filter Cartridge Printer | [3840097356](https://steamcommunity.com/sharedfiles/filedetails/?id=3840097356) | 1.1.1 | 一台新机器：往滤芯里灌任意截留物质，打印一次 120 电；自带机身贴图 | [`FilterPrinter/`](FilterPrinter/) |
| 下层药房 / Lower-District Pharmacy | [3840842240](https://steamcommunity.com/sharedfiles/filedetails/?id=3840842240) | 1.0.2 | 化学精制机两条配方：澄心剂（价值 12）、消痛片（价值 20） | [`Pharmacy/`](Pharmacy/) |
| 净化无上限 / Purifying Uncapped | [3841246322](https://steamcommunity.com/sharedfiles/filedetails/?id=3841246322) | 1.0.0 | 一个 Prefix，把净化上限从 95% 提到 100% | [`PurifyingUncapped/`](PurifyingUncapped/) |
| 拾荒手记 / Scavenger's Notes | [3841523504](https://steamcommunity.com/sharedfiles/filedetails/?id=3841523504) | 0.3.0 | 6×4 拾荒小游戏：线索、手电、放大镜 | [`ScavGame/`](ScavGame/) |
| 还原剂蕨 / Reduction Fern | [3844217940](https://steamcommunity.com/sharedfiles/filedetails/?id=3844217940) | 0.1.0 | 新作物还原蕨：种出来、割下来、搅碎就是还原剂 | [`ReductionFern/`](ReductionFern/) |
| 更好的奥克莫吸注射器 / Luxury Nomore Injector | [3844271622](https://steamcommunity.com/sharedfiles/filedetails/?id=3844271622) | 1.0.0 | 给奥克莫吸注射器加「奢侈品」类型，基础价值 50 → 350 | [`LuxuryNomoreInjector/`](LuxuryNomoreInjector/) |
| 删除种类多样 / No More Variety | [3845143246](https://steamcommunity.com/sharedfiles/filedetails/?id=3845143246) | 1.0.0 | 「种类多样」去掉「每种只买一件」，规则改名为「慷慨」，+15% 柜台加成保留 | [`GenerousBuyer/`](GenerousBuyer/) |
| 试剂可售 / Reagent Resale | [3845593063](https://steamcommunity.com/sharedfiles/filedetails/?id=3845593063) | 1.0.0 | 拆包后的化学试剂按水价计价、可作为化学用品出售，并修掉原版把非水液体判成「沟渠水 −90%」的兜底 | [`ChemResale/`](ChemResale/) |

## 玩家：怎么装

1. 从创意工坊订阅（推荐），或者下载 Releases 里的 zip；
2. 手动装的话，把 zip 里的整个模组文件夹解压到 `<游戏目录>/Mods/`，
   路径形如 `Mods/LuxuryNomoreInjector/`，里面有 `manifest.xml`；
3. 启动游戏 →「模组」菜单 → 找到模组 → 审核并启用 → 可能需要重启一次。

每个模组目录里的 `packaging/README.txt` 是该模组的玩家说明（安装、数值、注意事项）。

## 改代码的人：从这里开始

- 构建、部署、打包的完整步骤见 **[BUILDING.md](BUILDING.md)**。
- 要做物品/机器贴图，先读 **[SPRITES.md](SPRITES.md)**：三条画法路线、尺寸与占格规则、原版色板、
  验收清单，以及还原蕨和滤芯打印机踩过的坑。
- 每个模组都有一份 `RETROSPECTIVE.md`，写的是**为什么这么做**：踩过的坑、反编译出来的平台事实、
  哪些数值有原版锚点。改之前建议先读，能省掉一整轮试错。
- 根目录的 [`RETROSPECTIVE.md`](RETROSPECTIVE.md) 是跨模组的平台经验（Hook、存档信任、SteamCMD、封面流水线）。

## 接手 / Contributing

- Bug、数值调整、新想法都欢迎开 issue 或直接提 PR；单个模组的改动不需要碰其它模组。
- 如果我不再维护，而你想长期接手某个模组（包括工坊条目），开个 issue 说一声——
  可以把仓库转成共同维护者，或者把该模组的开发指引整理给你。
- 提交前请读 `BUILDING.md` 最后一节：不要提交 `build/`、`obj/`、`dist/`、`refs/`，
  以及任何反编译出来的游戏源码。

## 仓库结构

```
<每个模组>/
  src/             C# 源码
  mod/             manifest.xml + 运行时资源（打包进工坊条目的东西）
  scripts/         build.sh（构建+部署）、package.sh（打包+vdf）、make_cover.py（封面排版）
  packaging/       README.txt（玩家说明）、UPLOAD.md（上传步骤）、workshop_description.txt
  RETROSPECTIVE.md 这个模组的开发复盘
tools/             本地工具（写模组信任记录）
SPRITES.md         像素贴图手册（尺寸/占格/色板/画法/验收，跨模组）
BUILDING.md        构建、部署、打包步骤
```

## 许可证与免责

- 源码：[Apache-2.0](LICENSE)。你可以修改、再发布、甚至拿去上架自己的工坊条目，保留版权与许可声明即可。
- **仓库里不包含任何游戏本体资源**：没有 `Assembly-CSharp.dll`、没有图集、没有游戏内文本。
  构建时引用的是你自己机器上已经安装的游戏（见 [BUILDING.md](BUILDING.md)）。
- 与 Questing Goose Studio 无关，非官方内容。
