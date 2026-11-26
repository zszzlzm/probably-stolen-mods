# 目录与命名规范（本仓库）

> 借 `F:\随笔集\完全自由的异世界之旅\02_文档\工具与流程\文件与命名规范.md` 的三条总原则，
> 按"这是一个代码仓而不是内容仓"调整后的版本。**新建目录、搬文件之前先看这里；
> 结构改了必须同时改这份文档。**
> 2026-11-26 立。

## 1. 三条总原则

1. **一个任务的产物放同一个目录**：一个模组的源码、运行时资源、脚本、发布文本都待在 `<模组名>/` 下，不散到仓库根。
2. **草稿和定稿分开**：`refs/`（生图候选、参考照片、中间稿）可随时清空；`mod/` 是定稿，只带发布所需的文件；
   `dist/`、`build/`、`obj/` 是产物，不进 git。
3. **名字要稳定**：目录用产品名（工坊条目、游戏 `Mods/` 子目录都按这个名字对），文件名不用空格、不用日期、
   不用模型名；版本用 `_v{N}`，来源写进 `manifest.json` / `metainfo`。

与小说项目不同的地方：**模组目录不改成中文编号目录**。`FilterPrinter/`、`ScavGame/` 这些名字同时是
Steam 工坊条目的标识和本机部署目录名，改名的收益远小于要同步的 csproj / VDF / 脚本 / 文档链接成本。

## 2. 一级目录

| 目录 | 放什么 | 不许放什么 |
|---|---|---|
| `<模组名>/` ×8 | 每个模组一个，见 §3 | 跨模组共用脚本 |
| `docs/` | 项目级文档：构建、贴图、复盘、合规审计、本文件 | 模组专属文档（放 `<模组名>/docs/`） |
| `tools/` | 跨模组共用脚本（`trust_local.py`、`make_zip.sh`、`qwen_gen.py`…） | 某个模组专用的脚本 |
| `research/` | 本机抓取的资料、日志、临时实验（gitignore） | 任何发布物 |
| `tmp/` | 一次性草稿（gitignore） | 要长期留的东西 |
| `probably_stolen_decomp/` | 游戏反编译源码（gitignore，**版权不属于我们，永远不提交**） | 任何被引用的代码 |

根目录只留 `README.md`、`LICENSE`、`NOTICE`、`.gitignore`。

## 3. 模组目录（统一结构）

```text
<模组名>/
├─ src/                   C# 源码（默认 glob src/**/*.cs）
├─ mod/                   运行时资源 = 定稿区：manifest.xml、preview.png、Textures/、Sounds/、Localization/
├─ scripts/               Python / bash：构建、部署、打包、生图、封面
├─ packaging/             给人看/给工坊用的文本：README.txt、workshop_description.txt、UPLOAD.md
├─ docs/                  该模组的文档：PLAN、HANDOFF、RETROSPECTIVE、ART_SPEC、spec/、content/
├─ tools/                 （可选）非 Python 的辅助工程，如 C# 验证器、AutoHotkey 脚本
├─ refs/                  草稿区：生图候选、参考图、模型输出（gitignore）
├─ build/ obj/            dotnet 产物（gitignore）
└─ dist/                  打包产物、VDF（gitignore）
```

级别规则：

- **顶层 csproj**：`<模组名>/<AssemblyName>.csproj`，与 `src/` 平级。不要再把整个工程塞进 `mod/`。
- **`mod/` 只放发布要用的东西**：`packaging/` 里的说明、`.bak`、草稿都不要进 `mod/`。
- **`docs/spec/`**：设计规格文档（原 `ScavGame/docs/spec/`）；**`docs/content/`**：内容与文案设计（原 `ScavGame/docs/content/*.md`）。
- **辅助子项目**（不参与发布，保留自己的结构）：
  - `ScavGame/probe/`：验证用的探针模组（csc 项目 + 自己的 `src/mod/scripts`），只在排查游戏行为时用；
  - `PurifyingUncapped/tools/VerifyShare/`：C# 校验器；
  - `ScavGame/tools/`：AutoHotkey 调试脚本（`ahk-v2.zip`、`AutoHotkey/` 已在 `.gitignore`）。
  这三个不要按发布结构改造，也不要打进 `dist/`。

## 4. 文件命名

| 类型 | 规则 | 例 |
|---|---|---|
| 构建/打包/生图脚本 | 小写下划线，动词开头 | `build.sh`、`package.sh`、`gen_keyart.py`、`make_cover.py` |
| 模组文档 | 大写下划线（沿用已有） | `PLAN.md`、`HANDOFF.md`、`RETROSPECTIVE.md` |
| 贴图 | 与游戏内 sprite key 同名 | `mod/Textures/Items/fp_printer.png` |
| 生图产物 | `<用途>_s<seed>.png` 或 `<用途>_<字母>.png` | `keyart_s772.png`、`machine_s22.png` |
| 发布包 | `<模组名>-v<版本>.zip` | `Pharmacy-v1.0.2.zip` |
| 版本号 | `_v{N}`，不写日期 | `镜头表_v2` 式的写法 |

**禁止**：文件名带空格、带日期（`2026-11-25-xxx`）、带模型名（`qwen_xxx.png`——脚本名 `qwen_gen.py` 是工具名，不算）；
`mod/` 里出现 `.bak`、`.bak2`、`newloot.txt` 这类工作文件。

## 5. 草稿与定稿

| 区域 | 规则 |
|---|---|
| `refs/` | 草稿：可以覆盖、可以清空、不进 git |
| `refs/gen/manifest.json` | 每次生图由 `tools/qwen_gen.py` 追加：prompt / steps / seed / 尺寸 / 模型 / 输出 sha256 |
| `mod/` | 定稿：只有发布需要的文件；改它 = 改发布物，改完要重跑 `tools/trust_local.py` |

## 6. 改动流程

1. **先改本文件**，再动文件系统；
2. 用 `git mv` 搬（保留历史），不要 `mv` + 重新 `git add`；
3. 同步更新：`README.md` 的模组表、`docs/BUILDING.md` 里的路径示例、各模组 `packaging/UPLOAD.md` 的命令；
4. 验证：`dotnet build` 每个改过的模组 + `python tools/test_img_fit.py` + 全仓库 grep 一遍旧路径；
5. 提交时**只 add 相关路径**，不要 `git add -A`（工作区里有实验文件时会一起扫进去）。
