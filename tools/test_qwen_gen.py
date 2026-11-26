"""离线自检：生图路线的接线对不对（不用 ComfyUI、不出图）。

    python tools/test_qwen_gen.py

查三件事：
1. 编辑图确实把 KSampler 的 latent 接到 `TextEncodeQwenImage21` 的第 3 个输出，
   而且图里没有 `EmptyLatentImage`（文档 §13 细节 1 的反例）；
2. `canvas_size()` 与 `nodes_qwen.py:155-161` 的取整一致；
3. 仓库里没有「传了 refs 却没声明 route」的调用点 —— 以前那样写会静默丢掉参考图。
"""
from __future__ import annotations

import ast
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

checks = 0


def check(cond: bool, label: str) -> None:
    global checks
    checks += 1
    if not cond:
        raise AssertionError(label)
    print(f"  ok  {label}")


def test_edit_graph() -> None:
    import qwen_edit

    g = qwen_edit.build_edit_graph("改一下", "别糊", ["a.png", "b.png"],
                                   steps=25, seed=7, resolution=1024)
    kinds = {n["class_type"] for n in g.values()}
    check("EmptyLatentImage" not in kinds, "编辑图里没有 EmptyLatentImage")
    check(g["6"]["inputs"]["latent_image"] == ["4", 2], "KSampler.latent_image → 编码器第 3 个输出")
    check(g["6"]["inputs"]["positive"] == ["4", 0] and g["6"]["inputs"]["negative"] == ["4", 1],
          "正负条件都接编码器")
    enc = g["4"]["inputs"]
    check(sorted(enc["images"]) == ["image_1", "image_2"], "两张参考图都进编码器")
    check(enc["vae"] == ["3", 0], "编码器拿到 VAE（参考图要编码成 latent）")
    check(enc["resolution"] == 1024, "resolution 透传")


def test_canvas_size() -> None:
    from PIL import Image
    import tempfile
    import qwen_edit

    with tempfile.TemporaryDirectory() as td:
        square = pathlib.Path(td) / "sq.png"
        Image.new("RGB", (512, 512)).save(square)
        check(qwen_edit.canvas_size(square, 1024) == (1024, 1024), "512² → 1024²")
        wide = pathlib.Path(td) / "wide.png"
        Image.new("RGB", (1536, 1024)).save(wide)
        res = qwen_edit.resolution_for(1536, 1024)
        check(res == 1248, f"1536×1024 对应的 resolution 是 {res}（不是 1536）")
        check(qwen_edit.canvas_size(wide, res) == (1536, 1024), "1536×1024 参考图 → 同尺寸画布")
        # 取整必须落在 32 的倍数上
        w, h = qwen_edit.canvas_size(wide, 1024)
        check(w % 32 == 0 and h % 32 == 0, f"画布取整到 32 的倍数（{w}×{h}）")


def test_routes() -> None:
    import qwen_gen

    tmp = pathlib.Path(__file__).resolve().parents[0] / "__route_probe.png"
    try:
        qwen_gen.generate("x", out=tmp, seed=1, route="t2i", refs=[ROOT / "README.md"])
    except ValueError as exc:
        check("route='t2i'" in str(exc), "t2i + refs 直接报错，不再静默丢弃")
    else:
        raise AssertionError("t2i + refs 居然没报错")
    try:
        qwen_gen.generate("x", out=tmp, seed=1, route="style", refs=[])
    except ValueError as exc:
        check("需要至少一张参考图" in str(exc), "style 没给图也报错")
    else:
        raise AssertionError("style 没给图居然没报错")


def test_call_sites() -> None:
    """AST 扫所有脚本：只要传了 refs= 就必须写 route=。"""
    offenders = []
    for path in sorted(ROOT.glob("*/scripts/*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:                       # noqa: PERF203
            offenders.append(f"{path.relative_to(ROOT)}: 语法错误 {exc}")
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name != "generate":
                continue
            kwargs = {k.arg for k in node.keywords if k.arg}
            if "refs" in kwargs and "route" not in kwargs:
                offenders.append(f"{path.relative_to(ROOT)}:{node.lineno} 传了 refs 却没有 route")
    check(not offenders, "所有 generate(refs=…) 都声明了 route" + ("" if not offenders else f" —— {offenders}"))


def main() -> int:
    print("编辑图接线")
    test_edit_graph()
    print("画布尺寸")
    test_canvas_size()
    print("路线守卫")
    test_routes()
    print("调用点")
    test_call_sites()
    print(f"\n{checks} checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
