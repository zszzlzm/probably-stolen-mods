"""参考图走「编辑图」：拿 TextEncodeQwenImage21 的第 3 个输出当采样起点。

为什么要单独一个文件：官方注释写得很直白（`comfy_extras/nodes_qwen.py:138-140`）

    Empty latent on the first reference image's size, to match with sampling as
    **any other size shifts the edit**.

也就是说「给参考图 + 自己新建一张目标尺寸的空 latent」是错的组合 —— 图会位移。
正确姿势是 KSampler 的 `latent_image` 接编码器第 3 个输出（`["4", 2]`），
画布尺寸由**参考图**决定（`resolution` 只是把参考图缩到约 resolution² 再取整到 32 的倍数）。

本模块不改小说项目那个公用 `qwen_img.py`（那边还在用），只复用它的常量、
`_stage_refs()`、`_post()`、`_wait()` 和 ComfyUI 的输出下载逻辑。

对应文档：`生图部署方案.md` §13「另外两条官方细节」第 1 条。
"""
from __future__ import annotations

import math
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import uuid

QWEN_TOOLS = os.environ.get("QWEN_TOOLS", r"F:\随笔集\完全自由的异世界之旅\04_工具")
if QWEN_TOOLS not in sys.path:
    sys.path.insert(0, QWEN_TOOLS)

import qwen_img  # noqa: E402

MAX_REFS = 4          # 编码器本身支持 16 个槽位，这里沿用 qwen_img.build_graph 的 4 张上限


def resolution_for(width: int, height: int) -> int:
    """想得到 width×height 的画布（保持宽高比），`resolution` 该填多少。

    `resolution` 在节点里是「面积约等于 resolution²」的意思（nodes_qwen.py:156-158），
    所以要 1536×1024 得填 1248，直接填 1536 会得到 1888×1248。
    """
    return max(32, round(math.sqrt(width * height) / 32) * 32)


def canvas_size(ref: pathlib.Path, resolution: int) -> tuple[int, int]:
    """复刻 nodes_qwen.py:155-161：按参考图宽高比，把面积约等于 resolution² 的框取整到 32。"""
    from PIL import Image

    with Image.open(ref) as im:
        w, h = im.size
    if w <= 0 or h <= 0:
        raise ValueError(f"参考图尺寸非法: {ref}")
    if resolution <= 0:
        return max(32, round(w / 32) * 32), max(32, round(h / 32) * 32)
    ratio = w / h
    width = round(math.sqrt(resolution * resolution * ratio) / 32) * 32
    height = round(math.sqrt(resolution * resolution / ratio) / 32) * 32
    return max(32, width), max(32, height)


def build_edit_graph(prompt: str, negative: str, ref_names: list[str], *,
                     steps: int, seed: int, resolution: int = 1024,
                     unet: str | None = None, cfg: float = 1.0,
                     sampler: str = "euler", scheduler: str = "simple",
                     prefix: str = "qwen_edit") -> dict:
    """构造编辑图。ref_names 必须是 ComfyUI `input/` 里的文件名（`_stage_refs` 的产物）。"""
    if not ref_names:
        raise ValueError("编辑图至少要一张参考图")
    ref_names = ref_names[:MAX_REFS]

    g: dict[str, dict] = {
        "1": {"class_type": "UNETLoader",
              "inputs": {"unet_name": unet or qwen_img.UNET, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": qwen_img.CLIP_NAME, "type": "qwen_image", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": qwen_img.VAE}},
        "6": {"class_type": "KSampler",
              "inputs": {"model": ["30", 0] if qwen_img.LORA else ["1", 0],
                         "seed": seed, "steps": steps, "cfg": cfg,
                         "sampler_name": sampler, "scheduler": scheduler,
                         "positive": ["4", 0], "negative": ["4", 1],
                         "latent_image": ["4", 2],          # ← 关键：不是 EmptyLatentImage
                         "denoise": 1.0}},
        "7": {"class_type": "VAEDecode", "inputs": {"samples": ["6", 0], "vae": ["3", 0]}},
        "8": {"class_type": "SaveImage",
              "inputs": {"images": ["7", 0], "filename_prefix": prefix}},
    }
    if qwen_img.LORA:
        g["30"] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"model": ["1", 0], "lora_name": qwen_img.LORA,
                              "strength_model": 1.0}}

    images = {}
    for i, name in enumerate(ref_names, start=1):
        nid = str(20 + i)
        g[nid] = {"class_type": "LoadImage", "inputs": {"image": name}}
        images[f"image_{i}"] = [nid, 0]

    g["4"] = {"class_type": "TextEncodeQwenImage21",
              "inputs": {"clip": ["2", 0], "prompt": prompt, "negative_prompt": negative,
                         "resolution": resolution, "images": images, "vae": ["3", 0]}}
    return g


def _unload_27b() -> None:
    """生图前卸载 27B（文档硬规则）；小说项目那边没装也不影响本仓库。"""
    try:
        from qwen_flag3b import unload_27b  # noqa: PLC0415
        unload_27b()
    except Exception:
        pass


def generate_edit(prompt: str, *, out: pathlib.Path, refs: list[pathlib.Path],
                  seed: int, steps: int = 25, negative: str | None = None,
                  resolution: int = 1024, timeout: float = 900,
                  unet: str | None = None) -> dict:
    """跑一张编辑图，返回与 `qwen_img.generate` 同形的结果（size 是真实画布）。"""
    out = pathlib.Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    refs = [pathlib.Path(r) for r in refs]
    for r in refs:
        if not r.exists():
            return {"ok": False, "error": f"参考图不存在: {r}"}

    width, height = canvas_size(refs[0], resolution)
    t0 = time.time()
    _unload_27b()

    names = qwen_img._stage_refs(refs)
    graph = build_edit_graph(prompt, negative if negative is not None else qwen_img.NEG_DEFAULT,
                             names, steps=steps, seed=seed, resolution=resolution, unet=unet)
    queued = qwen_img._post("/prompt", {"prompt": graph, "client_id": uuid.uuid4().hex})
    pid = (queued or {}).get("prompt_id")
    if not pid:
        return {"ok": False, "error": f"提交失败: {queued}"}

    entry = qwen_img._wait(pid, timeout)
    if not entry:
        return {"ok": False, "error": "超时未完成"}
    status = entry.get("status") or {}
    if status.get("status_str") == "error" or status.get("completed") is False:
        return {"ok": False, "error": f"执行出错: {str(status)[:400]}"}

    files = []
    for node_out in (entry.get("outputs") or {}).values():
        files += node_out.get("images") or []
    if not files:
        return {"ok": False, "error": "没有输出图片"}

    img = files[0]
    query = urllib.parse.urlencode({"filename": img["filename"],
                                    "subfolder": img.get("subfolder", ""),
                                    "type": img.get("type", "output")})
    with urllib.request.urlopen(f"{qwen_img.COMFY}/view?{query}", timeout=60) as r:
        data = r.read()
    out.write_bytes(data)
    return {"ok": True, "path": str(out), "bytes": len(data),
            "server_file": img.get("filename"), "seconds": round(time.time() - t0, 1),
            "size": f"{width}x{height}", "canvas": [width, height],
            "steps": steps, "seed": seed, "resolution": resolution,
            "unet": unet or qwen_img.UNET, "route": "edit"}
