"""按文档配方调用本地 Qwen-Image 2.1 —— 本仓库唯一的生图入口。

配方出处：`F:\\随笔集\\完全自由的异世界之旅\\02_文档\\工具与流程\\生图部署方案.md`

三条路线（必须显式声明，不再默默丢掉参考图）：

| route | 用途 | 参考图 | 画布 | 提示词增强器 |
|---|---|---|---|---|
| `"t2i"` | 从零画一张（场景/图标） | 不允许 | 自己给的 `size` | 不适用（增强器要图） |
| `"style"` | 参考图只当风格提示 | 1–4 张，进编码器 | 自己给的 `size` | 默认关，`QWEN_ENHANCE=1` 打开 |
| `"edit"` | 把参考图改造成新图 | 1–4 张，第一张定画布 | 参考图尺寸（文档 §13 细节 1） | **默认开**，`QWEN_ENHANCE=0` 关 |

* 分辨率只用模型档位：封面 **1536×1024**（文档建议日常 1024–1536，原生 2K），
  图标 **1024×1024**。**不要直接要 1280×720** —— 那不是模型档位，而且
  `qwen_img.build_graph` 里 `TextEncodeQwenImage21(resolution=1024)` 是写死的，
  16:9 画布配 1:1 的编码尺度会掉质量。1280×720 是**裁切**产物，交给 `make_cover.py`。
* `steps=25, cfg=1.0, euler/simple`（文档 API 图的默认组合）。
* **生图前必须卸载 27B**：16 GB 卡上二者不能共存。
* `"style"` 路线是官方不保证的用法（`nodes_qwen.py:138-140`：画布尺寸与参考图不一致会让
  「编辑」位移），只适合当风格提示；要严格保持参考图构图就走 `"edit"`。
* `"edit"` 路线走 `tools/qwen_edit.py`：KSampler 的 latent 接编码器第 3 个输出。
* 提示词增强器是官方那个 9B 权重（`qwen3.5_9b_qwen_image_2.1_pe_i2i`，系统提示词
  `04_工具/prompts/edit_enhancer_system.txt`，只吃 `refs[0]` 这一张图）。它是**编辑**
  增强器：让它重写纯文生图的像素约束（9 个格心、≤8 色、1px 描边）只会稀释约束。
* 每次生成都往 `<mod>/refs/gen/manifest.json` 追加一条记录
  （route / prompt / 增强后的全文 / negative / steps / cfg / seed / refs / 输出 sha256），
  这是 `SPRITES.md` §5 与 `ReductionFern/docs/ART_SPEC.md` §7 早就要求的东西。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time

TOOLS = pathlib.Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import qwen_edit  # noqa: E402
import qwen_img  # noqa: E402

# 文档档位：封面 3:2（之后裁成 1280×720），图标 1:1（之后缩到 16/32/48 px）
COVER = (1536, 1024)
ICON = (1024, 1024)
STEPS = 25
CFG = 1.0
ROUTES = ("t2i", "style", "edit")


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _record(manifest: pathlib.Path | None, entry: dict) -> None:
    if manifest is None:
        return
    manifest.parent.mkdir(parents=True, exist_ok=True)
    data = {"entries": []}
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {"entries": []}
    data.setdefault("entries", []).append(entry)
    manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _enhance_enabled(route: str) -> bool:
    flag = os.environ.get("QWEN_ENHANCE", "").strip()
    if flag == "1":
        return True
    if flag == "0":
        return False
    return route == "edit"          # 编辑路线默认走增强器（文档 §13「官方通路」）


def generate(prompt: str, *, out: pathlib.Path, seed: int, size: tuple[int, int] = COVER,
             route: str = "t2i", negative: str | None = None,
             refs: list[pathlib.Path] | None = None, resolution: int = 1024,
             steps: int = STEPS, manifest: pathlib.Path | None = None,
             note: str = "") -> dict:
    """生成一张图。返回生成结果，附带 `prompt_used`、`prompt_enhanced` 与 `route`。"""
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if route not in ROUTES:
        raise ValueError(f"未知 route: {route!r}（可选 {', '.join(ROUTES)}）")
    refs = [pathlib.Path(r) for r in (refs or [])]
    if route == "t2i" and refs:
        raise ValueError(
            "route='t2i' 不接受参考图；要借参考图请用 route='style'（只当风格提示）"
            "或 route='edit'（改造参考图）"
        )
    if route in ("style", "edit") and not refs:
        raise ValueError(f"route={route!r} 需要至少一张参考图")
    for r in refs:
        if not r.exists():
            raise FileNotFoundError(f"参考图不存在: {r}")

    prompt_used = prompt
    enhanced = False
    if refs and _enhance_enabled(route):
        prompt_used = qwen_img.enhance_prompt(prompt, refs)
        enhanced = prompt_used.strip() != prompt.strip()
        print(f"enhanced prompt via 9B PE ({qwen_img.PE_MODEL})", flush=True)

    t0 = time.time()
    if route == "edit":
        # 画布由参考图决定；size 在这个路线里无效
        res = qwen_edit.generate_edit(
            prompt_used, out=out, refs=refs, seed=seed, steps=steps,
            negative=negative, resolution=resolution,
        )
        canvas = res.get("canvas")
    else:
        res = qwen_img.generate(
            prompt_used,
            out=out,
            negative=negative if negative is not None else qwen_img.NEG_DEFAULT,
            width=size[0],
            height=size[1],
            steps=steps,
            seed=seed,
            unload_27b=True,          # 文档硬规则；不要关
            refs=refs or None,        # style 路线才走到这里
        )
        canvas = list(size) if res.get("ok") else None
    res["prompt_used"] = prompt_used
    res["prompt_enhanced"] = prompt_used if enhanced else ""
    res["route"] = route
    res["manifest"] = str(manifest) if manifest else ""

    entry = {
        "out": str(out),
        "ok": bool(res.get("ok")),
        "route": route,
        "server_file": res.get("server_file"),
        "seed": seed,
        "steps": steps,
        "cfg": CFG,
        "size": canvas,
        "resolution": resolution if route == "edit" else None,
        "prompt": prompt,
        "prompt_used": prompt_used,
        "negative": negative if negative is not None else qwen_img.NEG_DEFAULT,
        "refs": [str(r) for r in refs],
        "enhanced": enhanced,
        "model": {
            "unet": qwen_img.UNET,
            "text_encoder": qwen_img.CLIP_NAME,
            "vae": qwen_img.VAE,
            "lora": qwen_img.LORA or None,
            "prompt_enhancer": qwen_img.PE_MODEL if enhanced else None,
        },
        "seconds": res.get("seconds"),
        "sha256": _sha256(out) if res.get("ok") and out.exists() else None,
        "note": note,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(time.time() - t0, 1),
    }
    _record(manifest, entry)
    return res
