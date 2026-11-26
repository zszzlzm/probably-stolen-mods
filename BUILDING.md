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
`package.sh` 会沿用 `.vdf` 里已有的 `publishedfileid` 与 `visibility`，所以更新时不会新建条目、
也不会把公开条目改回隐藏。上传步骤见各模组的 `packaging/UPLOAD.md`。

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
关键图是用本地 ComfyUI + Qwen-Image 生成的，仓库里只保留排版后的成品
（`mod/preview.png`），不含生图候选。

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
