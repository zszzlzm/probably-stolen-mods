# 构建与打包 / Building

所有模组都是 `netstandard2.1` 类库，用 `dotnet build` 编译，Harmony 在运行时由游戏自带的
`0Harmony.dll` 提供——**不需要**在仓库里放任何游戏 DLL。

## 1. 前置

| 需要 | 说明 |
|---|---|
| .NET SDK 8 或更新 | `dotnet --version` 能跑就行（目标是 netstandard2.1，不挑 SDK 版本） |
| 游戏本体 0.46D | 编译时要引用 `Probably Stolen_Data/Managed/` 里的 `Assembly-CSharp.dll`、`0Harmony.dll`、`UnityEngine.CoreModule.dll` |
| 可选：Python 3 + Pillow / numpy | 只有重新生成封面、或跑校验脚本时才需要 |

## 2. 编译

每个 `.csproj` 里游戏路径是一个可覆盖的属性 `GameManaged`，默认值是开发者机器上的路径。
在自己的机器上编译时覆盖它：

```bash
dotnet build LuxuryNomoreInjector/LuxuryNomoreInjector.csproj -c Release -o /tmp/out \
  -p:GameManaged="C:/Program Files (x86)/Steam/steamapps/common/Probably Stolen/Probably Stolen_Data/Managed"
```

Windows 的默认 Steam 库一般在
`C:\Program Files (x86)\Steam\steamapps\common\Probably Stolen\Probably Stolen_Data\Managed`。

> 注意：`Assembly-CSharp.dll` 属于游戏本体，**不要**把它提交到仓库、也不要随模组分发。

## 3. 部署到本地游戏

每个模组都有 `scripts/build.sh`，做三件事：编译 → 复制 DLL 到 `Mods/<模组>/` → 复制 manifest。

```bash
bash LuxuryNomoreInjector/scripts/build.sh
```

- 脚本里的游戏目录可以用环境变量覆盖（每个模组变量名不同，见脚本顶部，例如
  `LUXURY_INJECTOR_GAME_DIR`）。
- **先复制 DLL 再动别的文件**：游戏运行时 DLL 会被锁，复制失败就整体退出，
  避免留下"语言包/贴图换了、DLL 没换"的半套状态。
- 部署目录里要保留 `preview.png`（游戏内模组列表的缩略图读它）。

## 4. 打包成工坊条目

```bash
bash LuxuryNomoreInjector/scripts/package.sh
```

产物在 `dist/`：干净的模组文件夹、zip、`SHA256SUMS.txt`、给 SteamCMD 用的 `.vdf`。
`package.sh` 会沿用 `.vdf` 里已有的 `publishedfileid` 与 `visibility`，所以更新时不会新建条目、也不会把公开条目改回隐藏。
上传步骤见各模组的 `packaging/UPLOAD.md`。

**描述字段**：把 `packaging/workshop_description.txt` 全文写进 vdf 的 `description`，上传时自动更新页面，
不用手动粘贴。两个硬限制：

| 限制 | 后果 | 处理 |
|---|---|---|
| 描述 **> 8000 字节**（UTF-8，中文约 2600 字） | SteamCMD 内容与预览都传完，最后一步报 `Failed to update workshop item (Invalid Parameter)` | `package.sh` 打包时按字节检查并直接失败 |
| 值里有 ASCII 双引号 | KeyValues 没有转义，整份 vdf 解析失败 | 源文件只许用「」，`package.sh` 同样会拦 |

**可见性**：`.vdf` 里记的是**首次发布**时的值。如果之后在网页上把条目改成了公开，
仓库里的 vdf 仍写着 `visibility 2`，直接打包上传会把公开条目改回隐藏——
这种情况要 `VIS_OVERRIDE=0` 打包，或者手动改 vdf 里的数字。

### 4.1 模组设置项用什么控件

`ModHelper.GetConfig(id).Define(...)` 的控件由类型和参数决定（`ModConfigWindow.cs:99-117`）：

| 声明 | 控件 | 看得见当前值吗 |
|---|---|---|
| `bool` | 开关 | 是 |
| `int` + `min`/`max` | **滑条**（`AddSlider`） | **否**——只有一条滑轨，标签只在开窗时生成一次 |
| `int` / `float` 不带范围 | 输入框 | 是（可编辑） |
| `string` + `choices` | **下拉框**（`AddDropdown`） | 是，永远显示当前选中项 |

所以离散档位（1–10 倍、几档耗电）一律用 `string` + `choices`；连续数值用输入框。
滤芯打印机的 `print_power` 当年用了滑条，玩家反馈「拖完不知道设了多少」，就是这张表的第一行。

## 5. 本地信任（改完代码不出现「未审核」）

游戏会把每个模组的指纹（manifest 哈希 + DLL 哈希 + 整包文件哈希）记在存档里。
改了 DLL 之后，如果不想每次都进游戏手动「审核并启用」，可以在**游戏关闭**时用：

```bash
python tools/trust_local.py --folder "<游戏>/Mods/LuxuryNomoreInjector" \
    --id harness.luxury-nomore-injector --dll LuxuryNomoreInjectorMod.dll
```

它会按游戏的算法重算指纹、写进存档的 `modTrust`，并删掉 `modTrustMac` 让它重算。
存档目录默认取自 `%LOCALAPPDATA%Low`，也可以用 `--save-dir` 指定。

## 6. 封面

```bash
python LuxuryNomoreInjector/scripts/make_cover.py                       # 1280×720 + 640×360
python LuxuryNomoreInjector/scripts/make_cover.py art.png out.png --zoom=1.1 --dx=160
```

`--zoom/--dx/--dy` 用来重新构图（裁一刀再缩回 1280×720），只有部分模组的脚本带这三个参数。

封面统一版式：左侧压暗 + 中文标题 + 英文副标题 + 三条要点 + 卖点 + 页脚。
早期封面（试剂可售以外）用的是本地 ComfyUI + Qwen-Image 2.1 生成的关键图，仓库里只保留排版后的成品
（`mod/preview.png`），不含生图候选。

> **硬规则（2026-11-26 起）：不要再用 Qwen-Image 2.1 出任何要发布的图。**
> 该模型是 `qwen-research` 许可而非 Apache-2.0，许可证把 "Non-Commercial" 定义为
> "for research or evaluation purposes only"（§1.i、§2.a），公开发布的工坊素材落在授权之外。
> 详见 [AI_ART_LICENSE_AUDIT.md](AI_ART_LICENSE_AUDIT.md)；新封面照 `ChemResale/scripts/make_cover.py`
> 的路子纯代码绘制，或手排像素，或换一个许可已核实并写进本文件的模型。

### 6.1 生图配方（拿到许可后照这个跑）

配方出处：`F:\随笔集\完全自由的异世界之旅\02_文档\工具与流程\生图部署方案.md`。
唯一入口是 [tools/qwen_gen.py](tools/qwen_gen.py)，它替各模组把当年踩歪的四条固定住：

| 项 | 规定 | 以前错在哪 |
|---|---|---|
| 尺寸 | 封面 `COVER = 1536×1024`、图标 `ICON = 1024×1024` | 直接向模型要 1280×720：不是模型档位，而 `TextEncodeQwenImage21` 的 `resolution` 写死 1024，16:9 配 1:1 编码尺度 |
| 裁切 | 1280×720 由 [tools/img_fit.py](tools/img_fit.py) 的 `cover_fit` **等比裁切**产生 | `make_cover.py` 直接 `resize((1280,720))`，3:2 会被横向压扁 ~18% |
| 采样 | `steps=25, cfg=1.0, euler/simple` | 一律 30 步，且没有档位依据 |
| 显存 | **生成前卸载 27B**（wrapper 强制 `unload_27b=True`） | 5 个脚本传了 `False`，把文档的硬规则关掉了 |
| 参考图 | 必须显式声明 `route`：`"t2i"` 不收参考图、`"style"` 只当风格提示、`"edit"` 改造参考图（画布由参考图定） | 传了 `refs` 却不声明路线时被静默丢弃，而提示词里还写着「与参考图里的…同一种美术风格」——模型根本没看见那张图 |
| 出处 | 自动写 `refs/gen/manifest.json`：route/prompt/增强后全文/negative/steps/seed/尺寸/模型/输出 sha256 | 一张都没记，事后分不清哪些是模型产物 |

**三条路线**（`qwen_gen.generate(route=...)`）：

| route | 用途 | 参考图 | 画布 | 增强器 |
|---|---|---|---|---|
| `"t2i"` | 从零画（场景、图标） | 给了就报错 | `size` | 不适用 |
| `"style"` | 参考图只当风格提示 | 1–4 张进编码器 | `size` | 默认关，`QWEN_ENHANCE=1` 开 |
| `"edit"` | 改造参考图（立体化、换场景） | 1–4 张，第一张定画布 | 参考图尺寸 | **默认开**，`QWEN_ENHANCE=0` 关 |

`"style"` 是官方不保证的用法：`nodes_qwen.py:138-140` 说画布尺寸与参考图不一致会让「编辑」位移，
只适合当风格提示；要严格保持构图必须走 `"edit"`，它把 KSampler 的 latent 接到
`TextEncodeQwenImage21` 的第 3 个输出（[tools/qwen_edit.py](tools/qwen_edit.py)），不是自建空 latent。

**提示词增强器**：官方 9B 权重 `qwen3.5_9b_qwen_image_2.1_pe_i2i`（8.82 GB），系统提示词
`04_工具/prompts/edit_enhancer_system.txt`（10,571 字符），只吃 `refs[0]` 这一张图。它是**编辑**
增强器：会把一句糙指令扩写成三百字、逐条「保留 X 不变」的改造指令。对像素图那套硬约束
（9 个格心不透明、≤8 色、1px 描边）反而是稀释，所以图标继续手写提示词，只让 `"edit"` 路线用。
2026-11-26 之前它一次都没被调用过——已上架的图全部是手写提示词直出。

**画布**：`resolution` 是「面积约等于 resolution²」（`nodes_qwen.py:156-158`）。要 1536×1024
得填 1248（`qwen_edit.resolution_for(1536, 1024)`），填 1536 会得到 1888×1248。

用法（在模组目录里）：

```bash
python scripts/gen_keyart.py 7        # 内部调 qwen_gen.generate(...) → refs/gen/keyart.png (1536×1024)
python scripts/make_cover.py          # cover_fit 裁成 1280×720 + 排字 → mod/preview.png
python tools/test_img_fit.py          # 裁切几何自检（改 img_fit 后必跑）
python tools/test_qwen_gen.py         # 生图接线自检：编辑图 latent、画布取整、route 守卫
```

Turbo LoRA 那条路 `qwen_img.py` 没有包装，仍用 `ScavGame/scripts/comfy_gen.py`；
但 **步数必须跟着 LoRA 走（5–8 步、cfg 1）**，不能套 25 步，草稿定稿后回到 `qwen_gen` 复现一张。

## 7. 提交前

- 不要提交 `build/`、`obj/`、`dist/`、`refs/`（已在 `.gitignore` 里）。
- 不要提交任何反编译出来的游戏源码。
- 改了 `manifest.xml` 的版本号记得同步 `packaging/README.txt` 与工坊描述的版本行。

## 8. 网络（GitHub / 工坊）

这台机器的出口是「半墙」：同一个地址有时候通、有时候不通，属于中国互联网长城的预期表现，
不是谁的配置错，也不该在这上面花时间做工程化绕行。

判断顺序：

| 症状 | 含义 | 处理 |
|---|---|---|
| `Failed to connect ... over proxy 127.0.0.1 after 0 ms` | shell 里带着 `http_proxy`，但代理客户端没开 | `env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY` + `git -c http.proxy= -c https.proxy=` 直连 |
| `Failed to connect to github.com:443 after 21 s` / `Connection was reset` | 链路当时的解析或出口不通 | 直连重试 2~3 次，间隔十几秒；通常有一次会过 |
| 同时 `api.github.com` 正常、`github.com` 不通 | 两个域名不是同一条路，不代表整体断网 | 同上，别据此判断「网没问题」 |

重试几次仍失败就**停下来问用户**（他会检查代理是否开启、地址是否正确），不要自己改 hosts、
不要写临时代理、不要动系统网络配置——试过，收益为零，还会留下需要收尾的东西。

SteamCMD 上传不受这个影响（它不走 shell 的 `http_proxy`），所以「推不上 GitHub」和
「传不了工坊」是两件独立的事。

## 9. 脚本怎么调用（shell 环境）

这个工作区里所有 `scripts/*.sh`、`tools/*.sh` 都是 **bash 脚本**，但 agent 侧能用的
「bash」工具在不同插件配置下指向不同的 shell，写法必须跟着变：

| 情况 | `bash` 工具实际执行的 | 怎么跑 `.sh` |
|---|---|---|
| 装了 dsh-ops（`ops_bash`） | 真 bash（git-bash） | `bash scripts/package.sh` 直接可用 |
| 只有内置工具（当前） | **PowerShell 7**（`bash.exe` 是 WSL 启动器，不是 git-bash） | `& "C:\Program Files\Git\bin\bash.exe" -lc 'cd /c/... && bash scripts/package.sh'` |

踩过的具体差异：

- `bash` 工具在 PowerShell 下**不认 `/c/...` 这种 MSYS 路径**，`cd /c/...` 会报「找不到路径」；
  要么写 `C:\...`，要么把整段命令交给 git-bash 执行。
- `git-bash` 里的 `python3` 指向 Windows 应用商店的占位程序（退出码 49），仍然必须用
  `tools/find-python.sh` 解析（它优先用 DSH 运行时自带的解释器）。
- PowerShell 下 `&&` 可用（7.x），但 `head`/`tail`/`uname`/`sed`/`awk` 都没有；要这些就走 git-bash。

**判断方法**：`$PSVersionTable.PSVersion` 有输出 = 当前是 PowerShell；`uname -s` 输出 `MINGW64_NT-*` = 真 bash。
- `Compress-Archive` 在 PowerShell 5.1 里是**自动加载模块**。如果父进程是 pwsh 7 / git-bash，
  `PSModulePath` 会带上 PS7 的模块目录，5.1 于是报「command was found in the module
  'Microsoft.PowerShell.Archive', but the module could not be loaded」。同一个脚本在普通
  终端里却正常——所以打包脚本**不再用 PowerShell 压缩**，统一走 `tools/make_zip.sh`
  （python `shutil.make_archive`，顶层目录名与旧 zip 一致）。

## 10. PowerShell 7.7 复核（哪些坑已消失）

同一份探针 [tools/ps_probe.ps1](tools/ps_probe.ps1) 在 7.7 和系统自带的 5.1 下各跑一次：

    pwsh -NoProfile -File tools/ps_probe.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/ps_probe.ps1

| 项 | Windows PowerShell 5.1 | PowerShell 7.7 | 结论 |
|---|---|---|---|
| `&&` / `\|\|` | 语法错误 | 可用（本仓库文档里的链式命令就是 7.x 的写法） | ✅ 已修好 |
| `curl` | **是 `Invoke-WebRequest` 的别名**，`-s` / `-X POST` / `-o` 全不认 | 真 `curl.exe`（8.22.0），参数与 bash 一致 | ✅ 已修好，Steam API 查询可以直接写 |
| 读无 BOM 的 UTF-8 中文文件 | 按 ANSI 解码 → 乱码（实测 `试剂可售` → `璇曞墏鍙敭`） | 默认 UTF-8 → 正确 | ✅ 已修好 |
| `$OutputEncoding` | `us-ascii`（管道交给外部程序时非 ASCII 会丢） | `utf-8` | ✅ 已修好 |
| 执行策略 | `Restricted`：本地 `.ps1` 直接拒跑 | `RemoteSigned`：本地脚本可跑 | ✅ 已修好 |
| `Compress-Archive` | 自动加载模块；父进程把 PS7 的 `PSModulePath` 传下来时加载失败 | 内置可用 | ✅ 已修好（打包脚本仍用 `tools/make_zip.sh`，不想依赖 shell） |
| 按名字调用当前目录里的程序 | 不搜 cwd | 不搜 cwd | ❌ 未变，仍需 `.\` 或全路径 |
| `/c/...` 这种 MSYS 路径 | 不认 | 不认 | ❌ 未变（这是路径格式，不是 PowerShell 的问题） |
| 脚本文件的编码 | 无 BOM 的 UTF-8 中文注释会让解析错位（行号、语法都可能乱） | 无 BOM 也能正确解析 | ✅ 已修好，但**要兼容 5.1 就得存 BOM** |

结论：凡是「PowerShell 怪癖」类的坑，7.7 基本都消掉了；剩下两条跟我们自己的路径写法有关，跟版本无关。
平时仍然可以放心用 `curl`、`&&`、直接 `Get-Content` 读 UTF-8；只有 `steamcmd` 这种不在 PATH 的程序继续写全路径。
