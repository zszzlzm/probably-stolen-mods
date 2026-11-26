# Qwen-Image 2.1 使用合规审计

> 审计日期：2026-11-26　范围：本仓库全部模组的发布物（工坊封面 + 游戏内贴图）
> 依据：非法律意见。许可证原文与官方页面为准，本文只做事实核对与风险标注。

## 0. 结论

**按许可证原文，目前发布物里的 AI 素材落在授权范围之外。** 8 个模组里只有 1 个干净：

| 结论 | 模组 |
|---|---|
| ✅ 不涉及该模型 | 试剂可售（封面纯代码绘制，`ChemResale/scripts/make_cover.py`） |
| ⚠️ 封面是模型产物 | 滤芯打印机、下层药房、净化不限、还原蕨、拾荒手记、奢侈品不再注射器、宽客买家 |
| ⚠️ 游戏内贴图也含模型产物 | 还原蕨（5 张）、滤芯打印机（1 张）、下层药房（2 张） |

## 1. 许可证事实

模型卡：<https://huggingface.co/Qwen/Qwen-Image-2.1>，许可标签 **`qwen-research`**（不是 Apache-2.0）。
我们实际下载的转包仓库 <https://huggingface.co/Comfy-Org/Qwen-Image-2.1> 同样是 `qwen-research`。

许可全文：<https://huggingface.co/Qwen/Qwen-Image-2.1/raw/main/LICENSE>
（Qwen RESEARCH LICENSE AGREEMENT，Release Date: September 20, 2026）关键条款：

| 条款 | 原文要点 |
|---|---|
| §1.i | `"Non-Commercial" shall mean for research or evaluation purposes only.` |
| §2.a | 授权仅限 `FOR NON-COMMERCIAL PURPOSES ONLY` |
| §2.b | `You shall not use the Materials for any commercial purpose without obtaining a separate commercial license from us.` |
| §3 | 分发 Materials 需附本协议、改文件要标注、NOTICE 里保留 Qwen 版权声明 |
| §4.b | 若用其产物训练/改进**分发出去的 AI 模型**，须显著标注 "Built with Qwen" |

要点：**"Non-Commercial" 在这里被定义为"仅限研究与评估"**，比通常理解的"不赚钱就行"更窄。
我们没卖钱，但把生成图放进公开发布的工坊条目，很难算"研究或评估"。

我们自己的部署文档当初只记了来源与 SHA256，**没有记许可证**：
`F:\随笔集\完全自由的异世界之旅\02_文档\工具与流程\生图部署方案.md:57`（只写 HF/ModelScope 与校验），
`:231`（提到 Turbo 但没提它的许可）。所以「照那个项目的规定做」并不能自动推导出本仓库合规——
那个项目规定的是**怎么跑模型**（本地 ComfyUI `127.0.0.1:8188` + `qwen_img.py`、int8 三件套、画面里不让模型写字），
而不是**产物能用到哪里**。

同一发行包里的另外两个权重不会改变上述判断：文本编码器 `qwen3vl_8b_int8_convrot`（8.71 GB）与提示词增强器
`qwen3.5_9b_qwen_image_2.1_pe_i2i`（8.82 GB）。它们和 DiT 同属 Qwen-Image 2.1 的发布物，这里按同一个
`qwen-research` 标签保守处理——用增强器改写指令、或用编码器读参考图，都不能把产物挪出 §2.a 的范围。
（这两份权重各自的模型卡没有单独核对过；要精确到文件级，得回 ModelScope 的仓库页看 LICENSE。）

## 2. 使用清单（逐模组）

| 模组 | 工坊封面 | 游戏内贴图 | 产物来源 | 出处记录 |
|---|---|---|---|---|
| 滤芯打印机 | 模型 | `fp_printer.png`（概念图 → 手排） | `qwen_img`（`scripts/gen_keyart.py`、`gen_machine_art.py`） | seed 未记录；概念图在 `refs/gen/machine_s22.png` |
| 下层药房 | 模型 | `calm_agent.png`、`painkiller_pill.png`（形状参考 → 手排） | `qwen_img`（`scripts/gen_keyart.py`、`gen_sprites.py`） | seed 未记录 |
| 净化不限 | 模型 | — | `qwen_img`（`scripts/gen_keyart.py`） | seed 未记录 |
| 还原蕨 | 模型 | 5 张（模型定形 → 像素化） | `qwen_img`（`tools/gen_assets.py`） | **有**：`ART_SPEC.md` 记 seed 102/111/303、steps 30、cfg 1.0 |
| 拾荒手记 | 模型 | — | 自写 ComfyUI 客户端（`scripts/comfy_gen.py`，8188，Qwen-Image 2.1 Turbo + LoRA） | 记了 8 steps / cfg 1 / shift 0.69，seed 未逐张记录 |
| 奢侈品不再注射器 | 模型 | — | 未留脚本（`refs/gen/keyart_a…j.png` 在，命令丢失） | **无** |
| 宽客买家 | 模型 | — | `qwen_img`（`scripts/gen_keyart.py`） | seed 在脚本里（101/202/303/404），未记选中哪张 |
| 试剂可售 | 代码绘制 | — | 无模型 | 不适用 |

`refs/gen/manifest.json`（`SPRITES.md` §5 第 8 条、`ReductionFern/ART_SPEC.md` §7 都规定要写）
**一个都不存在**——可复现性是文档承诺，实际没落地。

## 3. 另外两项缺口

1. **Steam 的 AI 披露**：Valve 2026 年 1 月的澄清是「只对玩家可直接消费的生成内容强制披露」，
   并分 "Pre-generated" / "Live-generated" 两类（[说明](https://www.strayspark.studio/blog/steam-ai-disclosure-examples-indie-developers-2026)）。
   工坊封面是玩家可见内容 → 属于该披露。我们的 8 份工坊描述里**一句都没提**（grep `AI|生成|模型` 无命中）。
2. **"非官方"标识**：8 份描述里也没有 "非官方 / unofficial"。这与模型授权无关，但同属发布合规。

## 4. 可选路径

| 路径 | 做法 | 成本 | 解决什么 |
|---|---|---|---|
| **A. 拿商业许可** | 按 §2.b 联系 `model-business@notice.qwencloud.com` 申请 | 未知（可能要钱/要资质） | 一次性解决许可问题，现有素材全部可留 |
| **B. 换掉模型产物** | 封面改纯代码绘制（照 `ChemResale` 的路子）；贴图手排像素重画 | 中：8 张封面 + 8 张游戏内贴图 | 彻底干净，且风格更统一；不用等外部回复 |
| **C. 只加披露** | 工坊描述加 "封面由 AI 生成" | 低 | **只解决 Steam 政策**，不解决许可证 |
| **D. 停用/下架** | 撤掉含模型产物的条目 | 低但丢内容 | 干净但代价大 |

我的建议：**先按 A 写信问一句**（免费的咨询，几天内能知道要不要钱），同时按 B 准备一条兜底路径
——从试剂可售那次的经验看，纯代码绘制的封面（像素瓶 + 价格签）在工坊里辨识度并不差，
而且和"这是个像素游戏模组"的定位更贴。

## 5. 在拿到许可之前，仓库里该守的规矩

1. **不再用 Qwen-Image 2.1 出一张要发布的新图**（封面、贴图、宣传图都不行）。
2. 新素材要么纯代码绘制，要么手排像素，要么换一个许可明确的模型（用前先把许可写进 `BUILDING.md`）。
3. 每次生图都要落 `refs/gen/manifest.json`：`prompt / negative / steps / cfg / seed / refs / 选中文件`，
   否则连"哪些是模型产物"都说不清——这次的审计就是靠 grep 文档拼出来的。
4. 任何模型产物进发布包之前，在 `packaging/workshop_description.txt` 与 `README.txt` 里写明来源。

## 6. 修复进展（2026-11-26）

按上面 §2 的偏差，脚本与文档已改成文档配方：

| 改动 | 文件 |
|---|---|
| 统一生图入口：尺寸档位、steps 25、强制卸载 27B、自动写 manifest | [tools/qwen_gen.py](tools/qwen_gen.py) |
| 参考图三条路线（`t2i` 拒收参考图、`style` 当风格提示、`edit` 改造参考图），不再静默丢弃 | [tools/qwen_gen.py](tools/qwen_gen.py) |
| 编辑图按文档 §13 细节 1 接 `TextEncodeQwenImage21` 的参考图尺寸 latent | [tools/qwen_edit.py](tools/qwen_edit.py) |
| 9B 提示词增强器接进 `edit` 路线（默认开），改写全文进 manifest | [tools/qwen_gen.py](tools/qwen_gen.py) |
| 等比裁切（3:2 关键图 → 16:9 封面不再被压扁） | [tools/img_fit.py](tools/img_fit.py)、7 个 `scripts/make_cover.py` |
| 裁切几何自检 / 生图接线自检 | [tools/test_img_fit.py](tools/test_img_fit.py)（8 条）、[tools/test_qwen_gen.py](tools/test_qwen_gen.py)（13 条） |
| 各模组生成脚本改用上面的入口并声明 route | `Pharmacy`/`PurifyingUncapped`/`FilterPrinter`/`ScavGame`/`GenerousBuyer` 的 `gen_keyart.py`、`gen_machine_art.py`、`gen_3d_edit.py`、`gen_sprites.py`、`ReductionFern/scripts/gen_assets.py` |
| 配方与坑写进文档 | `BUILDING.md` §6.1、`SPRITES.md` §5 |

没修的（做不到，不是漏了）：

- **已发布的图不重新生成**：重出一轮的收益不确定，等真要改封面时再按新配方来。
- **增强器对已发布图零贡献**：2026-11-26 之前没有任何一次调用（`qwen_gen` 是那天才出现的），
  所以上面 8 个模组的图不受影响；以后再出图才走 `edit` 路线的增强器。
- **老图没有 manifest**：seed/prompt 当时没记，事后补不出真实值，只能标注「来源未知」。
- **奢侈品不再注射器的生图命令已丢失**（`refs/gen/keyart_a..j.png` 还在，脚本没了），这一份的出处只能写"本地生成·参数未知"。
