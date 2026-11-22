import json, sys, time, urllib.request, urllib.parse, os

BASE = "http://127.0.0.1:8188"

def post(path, obj):
    data = json.dumps(obj).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def get(path):
    with urllib.request.urlopen(BASE + path, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def build(prompt, negative, width, height, steps, cfg, shift, seed, prefix, unet, clip, vae, lora):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": unet, "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": clip, "type": "qwen_image"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": vae}},
        "4": {"class_type": "LoraLoaderModelOnly", "inputs": {"model": ["1", 0], "lora_name": lora, "strength_model": 1.0}},
        "5": {"class_type": "ModelSamplingAuraFlow", "inputs": {"model": ["4", 0], "shift": shift}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": ["2", 0]}},
        "8": {"class_type": "EmptySD3LatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
        "9": {"class_type": "KSampler", "inputs": {
            "model": ["5", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["8", 0],
            "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
        }},
        "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["3", 0]}},
        "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": prefix}},
    }

def main():
    cfg_path = sys.argv[1]
    with open(cfg_path, encoding="utf-8") as f:
        c = json.load(f)
    wf = build(**c)
    res = post("/prompt", {"prompt": wf, "client_id": "scav-cover"})
    pid = res["prompt_id"]
    print("prompt_id", pid, flush=True)
    start = time.time()
    while True:
        time.sleep(2)
        try:
            h = get("/history/" + pid)
        except Exception as e:
            print("poll error", e, flush=True)
            continue
        if pid in h:
            item = h[pid]
            print(json.dumps(item.get("status", {}), ensure_ascii=False), flush=True)
            outputs = item.get("outputs", {})
            for node, out in outputs.items():
                for img in out.get("images", []):
                    print("IMAGE", img.get("filename"), img.get("subfolder"), img.get("type"), flush=True)
            return 0
        if time.time() - start > 1800:
            print("timeout", flush=True)
            return 1

if __name__ == "__main__":
    sys.exit(main())
