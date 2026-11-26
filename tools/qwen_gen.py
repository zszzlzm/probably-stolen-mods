"""按文档配方调用本地 Qwen-Image 2.1 —— 本仓库唯一的生图入口。

配方出处：`F:\\随笔集\\完全自由的异世界之旅\\02_文档\\工具与流程\\生图部署方案.md`

* 分辨率只用模型档位：封面 **1536×1024**（文档建议日常 1024–1536，原生 2K）、
  图标 **1024×1024**。**不要直接要 1280×720** —— 那不是模型档位，而且
  `qwen_img.build_graph` 里 `TextEncodeQwenImage21(resolution=1024)` 是写死的，
  16:9 画布配 1:1 的编码尺度会掉质量。1280×720 是**裁切**产物，交给 `make_cover.py`。
* `steps=25, cfg=1.0, euler/simple`（文档 API 图的默认组合）。
* **生图前必须卸载 27B**（`unload_27b=True`）：16GB 卡上二者不能共存。
* 参考图**不进 T2I**：文档 §13 的用法是「9B 增强器先改写指令」，或走编辑路
  （本仓库没有编辑图）。想用参考图就设 `QWEN_ENHANCE=1`，这里会先调
  `qwen_img.enhance_prompt` 再生成；否则给个提示、丢掉 refs。
* 每次生成都往 `<mod>/refs/gen/manifest.json` 追加一条记录
  （prompt / negative / steps / cfg / seed / refs / 输出 sha256），
  这是 `SPRITES.md` §5 与 `ReductionFern/ART_SPEC.md` §7 早就要求的东西。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time

QWEN_TOOLS = os.environ.get("QWEN_TOOLS", r"F:\随笔集\完全自由的异世界之旅\04_工具")
if QWEN_TOOLS not in sys.path:
    sys.path.insert(0, QWEN_TOOLS)

import qwen_img  # noqa: E402

# 文档档位：封面 3:2（之后裁成 1280×720），图标 1:1（之后缩到 16/32/48 px）
COVER = (1536, 1024)
ICON = (1024, 1024)
STEPS = 25
CFG = 1.0


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


def generate(prompt: str, *, out: pathlib.Path, seed: int, size: tuple[int, int] = COVER,
             negative: str | None = None, refs: list[pathlib.Path] | None = None,
             steps: int = STEPS, manifest: pathlib.Path | None = None,
             note: str = "") -> dict:
    """生成一张图。返回 qwen_img.generate 的结果，附带 `prompt_used` 与 `manifest`。"""
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    prompt_used = prompt
    refs_used: list[str] = []
    if refs:
        refs_used = [str(pathlib.Path(r)) for r in refs]
        if os.environ.get("QWEN_ENHANCE") == "1":
            prompt_used = qwen_img.enhance_prompt(prompt, [pathlib.Path(r) for r in refs])
            print("enhanced prompt via 9B PE (documented §13 route)", flush=True)
        else:
            print("note: refs 不传给 T2I（文档 §13）；要借用参考图请设 QWEN_ENHANCE=1", flush=True)

    t0 = time.time()
    res = qwen_img.generate(
        prompt_used,
        out=out,
        negative=negative if negative is not None else qwen_img.NEG_DEFAULT,
        width=size[0],
        height=size[1],
        steps=steps,
        seed=seed,
        unload_27b=True,          # 文档硬规则；不要关
    )
    res["prompt_used"] = prompt_used
    res["manifest"] = str(manifest) if manifest else ""

    entry = {
        "out": str(out),
        "ok": bool(res.get("ok")),
        "seed": seed,
        "steps": steps,
        "cfg": CFG,
        "size": list(size),
        "prompt": prompt_used,
        "negative": negative if negative is not None else qwen_img.NEG_DEFAULT,
        "refs": refs_used,
        "enhanced": prompt_used != prompt,
        "model": {
            "unet": qwen_img.UNET,
            "text_encoder": qwen_img.CLIP_NAME,
            "vae": qwen_img.VAE,
            "lora": qwen_img.LORA or None,
        },
        "seconds": res.get("seconds"),
        "sha256": _sha256(out) if res.get("ok") and out.exists() else None,
        "note": note,
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "elapsed_s": round(time.time() - t0, 1),
    }
    _record(manifest, entry)
    return res
