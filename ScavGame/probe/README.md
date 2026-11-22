# M0 探针：ScavProbe

> 目的：在正式做网格/文字层之前，验证 5 件事是否可用。
> 这是**临时探针**，验证完就删，不要当正式 mod 发布。

## 怎么装

已部署到：

```text
F:\SteamLibrary\steamapps\common\Probably Stolen\Mods\ScavProbe\
  ScavProbe.dll
  manifest.xml
  Sounds\probe_beep.wav
```

重新构建/部署：

```bash
cd ScavGame/probe
bash scripts/build.sh
```

进游戏 →「模组」列表 → 启用 **Scav M0 Probe** → 完全退出再启动（游戏内启用通常要重启）。

## 怎么打开

到夜晚去**垃圾场**：

- 如果地点面板是 `CustomUI` 生成的，会多一个「M0 探针」按钮。
- **无论哪种面板**，点原版「拾荒」按钮也会打开探针（`DumpingGroundLocation.OnScavenge` 和 `MapUIManager.ScavengeButtonClick` 都打了前缀），并**跳过原版拾荒**。

> 注意：探针启用时，原版「拾荒」按钮不再执行原版结算。这是 M0 的预期行为。

## 五个检查项

### 1. 生命周期

窗口顶部状态行应显示：

```text
[M0] arrived=True  grid=True  items=N  pixel=closed
```

- 进垃圾场：`arrived=True`。
- 离开垃圾场：窗口自动关闭；重新进入再点按钮能开。
- 读档：`OnGameLoadedInit` 会重置，窗口关闭。

### 2. 物品入包 + 最简揭示

点「生成测试物品 + 最简揭示」：

- 背包里出现一件**废金属**（`scrap_metal`）。
- 物品上盖一层深色矩形，约 0.55 秒后淡出，露出原图。
- 状态行 `items` 增加，`target=True`。

要看的点：

- `GameItemElement.handler.rectTransform` 是否拿得到（`target=True`）。
- 覆盖层是否只盖住物品本身、不挡鼠标（`raycastTarget=false`）。
- 物品被移走/拖走时覆盖层会不会残留（M0 不处理，记录现象即可）。

### 3. 受伤遮罩

点「受伤遮罩」：

- 物品区盖一层暗红（`#792025`，alpha 125）。
- 中间一个白色十字（横 96×7、竖 7×96）。
- 约 0.08 秒后开始淡出，0.28 秒消失。

要看的点：

- 遮罩是否只盖物品区、不盖整个屏幕。
- 是否被网格的 Mask 裁掉（应该被裁，符合预期）。
- 淡出是否跟手（`Time.unscaledTime`）。

### 4. 自带音效

点「播放自带音效」：

- 一声 880Hz、0.15 秒的短音。
- 状态行 `PlaySound probe_beep = True`。

要看的点：

- mod 的 `Sounds/` 是否被自动加载。
- 音量是否和原版音效在同一档。

### 5. PixelWindow 层级

点「PixelWindow 开关」：

- 弹出一个原生 4×4 空库存窗口。
- 再点一次关闭。

要看的点：

- 原生 `PixelWindow` 与 `CustomUI` 探针窗口谁在上、谁能拖、点得到谁。
- 关窗后有没有残留。
- 网格/背包布局有没有被挤乱。

## 日志

`Player.log`：

```text
%LOCALAPPDATA%Low\Questing Goose Studio\Probably Stolen\Player.log
```

搜 `[ScavProbe]`：

```text
[ScavProbe] Init harness.scav-probe
[ScavProbe] enabled
[ScavProbe] arrive dumping_ground dumping=True
[ScavProbe] leave dumping_ground
```

有异常会带 `Debug.LogException` 的堆栈；把 `[ScavProbe]` 前后 50 行贴回来即可。

## 验证完之后

- 关掉 mod，或直接删 `Mods/ScavProbe`。
- 这版的 `OnScavenge` 前缀会拦原版拾荒，别带着它继续正常玩。
- 结果用来决定：网格用 `CustomUI` 还是原生 `PixelWindow`；揭示做多复杂；遮罩/音效是否保留。
