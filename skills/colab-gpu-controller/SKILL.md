---
name: colab-gpu-controller
description: Orchestrates remote Google Colab GPU acceleration (T4/A100) for heavy machine learning, computer vision, audio processing, batch transformations, or remote PyTorch execution from Antigravity via Cloudflare tunnels and Google Drive. Use whenever a task requires GPU compute without installing heavy dependencies locally.
---

# Colab GPU Controller & Remote Execution

This skill provides a generalized pattern to offload GPU-intensive workloads from the local Antigravity environment to a remote Google Colab instance over a secure Cloudflare tunnel.

---

## 1. When to Use This Pattern

Use this workflow when:
- **Local Machine is Resource-Constrained**: The local system lacks an NVIDIA GPU, has limited VRAM, or cannot support heavy CUDA packages (`torch`, `onnxruntime-gpu`, `whisper`, `diffusers`).
- **Heavy Media / Batch Processing**: Tasks such as AI background removal, video frame extraction, speech-to-text, or multi-band image blending.
- **Data Resides on Google Drive**: Large assets are stored in Google Drive and downloading them locally would saturate disk space or trigger Google Drive anonymous rate limits.
- **Rapid Experimentation**: You want to develop and iterate on Python logic inside Antigravity while executing the heavy computations on Colab.

---

## 2. Universal Colab Server Setup

Run these cells in a Google Colab GPU notebook (Runtime > Change runtime type > T4 or A100 GPU).

### Cell 1: Environment & CUDA Runtime Hygiene

```python
# 1. Terminate leftover processes & free ports
!fuser -k 8000/tcp || true
!pkill -f cloudflared || true

# 2. Fix CUDA/cuDNN provider issues for ONNX / PyTorch runtimes
!pip uninstall -y -q onnxruntime onnxruntime-gpu
!pip install -q "onnxruntime-gpu[cuda,cudnn]"
!pip install -q fastapi uvicorn python-multipart nest-asyncio

# 3. Mount Google Drive (if project data is on Drive)
from google.colab import drive
import os
if not os.path.exists('/content/drive/MyDrive'):
    drive.mount('/content/drive')

# 4. Verify GPU availability
import torch, onnxruntime as ort
ort.preload_dlls()  # Crucial: Preload CUDA/cuDNN DLLs before session initialization
print(f"🖥️ PyTorch CUDA Available: {torch.cuda.is_available()} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
print(f"⚡ ONNX Providers: {ort.get_available_providers()}")
```

### Cell 2: Generic FastAPI Remote Controller & Cloudflare Tunnel

```python
import os, io, sys, re, time, threading, subprocess, traceback
import nest_asyncio, uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="Antigravity Colab Remote Controller")

# --- 1. Health & Hardware Status ---
@app.get("/health")
def health():
    import torch, onnxruntime as ort
    has_gpu = torch.cuda.is_available()
    return {
        "status": "online",
        "gpu_available": has_gpu,
        "device_name": torch.cuda.get_device_name(0) if has_gpu else "CPU",
        "onnx_providers": ort.get_available_providers(),
        "drive_mounted": os.path.exists("/content/drive/MyDrive")
    }

# --- 2. Dynamic Remote Code Execution (/exec) ---
# Allows Antigravity to maintain script logic locally and execute on Colab GPU
@app.post("/exec")
async def execute_code(req: Request):
    data = await req.json()
    code_str = data.get("code", "")

    old_stdout, old_stderr = sys.stdout, sys.stderr
    redirected_output = io.StringIO()
    redirected_error = io.StringIO()
    sys.stdout, sys.stderr = redirected_output, redirected_error

    exec_globals = {
        "os": os,
        "sys": sys,
        "io": io,
        "app": app
    }

    try:
        exec(code_str, exec_globals)
        success = True
    except Exception:
        traceback.print_exc(file=redirected_error)
        success = False
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr

    return {
        "success": success,
        "stdout": redirected_output.getvalue(),
        "stderr": redirected_error.getvalue()
    }

# --- 3. Launch Server & Ephemeral Cloudflare Tunnel ---
nest_asyncio.apply()
def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000)

threading.Thread(target=run_server, daemon=True).start()
time.sleep(2)

# Download cloudflared binary
!wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
!dpkg -i cloudflared-linux-amd64.deb > /dev/null 2>&1

tunnel = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:8000"], stderr=subprocess.PIPE, text=True)

while True:
    line = tunnel.stderr.readline()
    match = re.search(r'(https://[a-zA-Z0-9-]+\.trycloudflare\.com)', line)
    if match:
        print("\n" + "="*60)
        print("👉 ANTIGRAVITY CONTROLLER LIVE AT:", match.group(1))
        print("="*60 + "\n")
        break
```

---

## 3. Generalized Local Client (`colab_client.py`)

Keep this lightweight client in your local repository. It has no dependencies beyond the Python standard library.

```python
import urllib.request, urllib.parse, json, os

class ColabClient:
    def __init__(self, base_url=None):
        # Read from environment or default URL
        self.base_url = (base_url or os.environ.get("COLAB_URL", "")).rstrip("/")
        if not self.base_url:
            raise ValueError("COLAB_URL not set. Provide base_url or set COLAB_URL environment variable.")

    def check_health(self):
        req = urllib.request.Request(f"{self.base_url}/health")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def execute_code(self, code_str):
        """Execute arbitrary Python code remotely on the Colab GPU."""
        url = f"{self.base_url}/exec"
        payload = json.dumps({"code": code_str}).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def call_post_json(self, endpoint, data_dict):
        """Call a custom JSON endpoint."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        payload = json.dumps(data_dict).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def download_file(self, endpoint, data_dict, local_save_path):
        """Send a request and stream the binary response to disk."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        payload = json.dumps(data_dict).encode('utf-8')
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        os.makedirs(os.path.dirname(os.path.abspath(local_save_path)), exist_ok=True)
        with urllib.request.urlopen(req) as resp:
            with open(local_save_path, "wb") as f:
                f.write(resp.read())
        return local_save_path
```

---

## 4. Reusable Task Recipes

You can add task-specific endpoints to the FastAPI app or execute them dynamically using `client.execute_code()`.

### Recipe A: Production Neural Matting with SOTA Cascading, MQS & Color Decontamination

Dirty or dark fringes on white/light backgrounds are caused by **color contamination** (edge pixels carry the original stage/backdrop RGB values) and soft alpha falloff from general-purpose models (like `u2net`). 

This 3-pillar pipeline solves it completely:
1. **Cascading Model Chain**: `birefnet-portrait` ➔ `birefnet-general` ➔ `isnet-general-use` (never `u2net`).
2. **Mask Quality Score (MQS)**: Multi-attribute scoring (fringe width, stray specks, pinholes, coverage). The best-scoring mask wins.
3. **Cleanup & Decontamination**: Drop specks, fill pinholes, crush faint grey alpha, and re-estimate edge foreground RGB using `pymatting.estimate_foreground_ml` (bundled with `rembg`).

```python
import io, cv2, numpy as np
from PIL import Image
from fastapi import Request, Response
from rembg import remove, new_session
from pymatting.foreground.estimate_foreground_ml import estimate_foreground_ml

# Pre-warm cascading model sessions on GPU
PROVIDERS = ["CUDAExecutionProvider", "CPUExecutionProvider"]
MODELS = {
    "portrait": new_session("birefnet-portrait", providers=PROVIDERS),
    "general": new_session("birefnet-general", providers=PROVIDERS),
    "isnet": new_session("isnet-general-use", providers=PROVIDERS)
}

def calculate_mqs(alpha_mask: np.ndarray) -> float:
    """
    Mask Quality Score (MQS) [0 - 100]:
    - Fringe Width: penalizes excessive semi-transparent pixels (15 < alpha < 240)
    - Stray Specks: penalizes disconnected high-alpha clusters outside the main mass
    - Pinholes: penalizes holes/cavities inside the core subject
    - Coverage: verifies reasonable bounding box occupancy
    """
    total_pixels = alpha_mask.size
    fg_core = (alpha_mask >= 240).astype(np.uint8)
    fg_any = (alpha_mask >= 15).astype(np.uint8)
    
    total_fg_count = np.count_nonzero(fg_any)
    if total_fg_count == 0 or total_fg_count < (total_pixels * 0.02):
        return 0.0  # Empty or near-empty mask
    
    # 1. Fringe width penalty (ratio of transition pixels to core foreground)
    transition_pixels = np.count_nonzero((alpha_mask > 15) & (alpha_mask < 240))
    fringe_ratio = transition_pixels / max(total_fg_count, 1)
    fringe_score = max(0.0, 1.0 - (fringe_ratio * 2.5))  # Crisper hair/edge = higher score
    
    # 2. Stray specks & Pinholes via Connected Components
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg_any)
    if num_labels <= 1:
        return 0.0
    # Largest component is index 1+ (excluding background index 0)
    areas = stats[1:, cv2.CC_STAT_AREA]
    max_area = np.max(areas)
    stray_area = total_fg_count - max_area
    speck_ratio = stray_area / max(total_fg_count, 1)
    speck_score = max(0.0, 1.0 - (speck_ratio * 4.0))
    
    # 3. Pinholes inside core subject
    contours, _ = cv2.findContours(fg_core, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    internal_holes = sum(1 for c in contours if cv2.contourArea(c) < (max_area * 0.05) and cv2.contourArea(c) > 4)
    pinhole_score = max(0.0, 1.0 - (internal_holes * 0.05))
    
    # 4. Coverage score (reasonable human portrait proportion: 10% - 85% frame)
    coverage_ratio = total_fg_count / total_pixels
    coverage_score = 1.0 if 0.08 <= coverage_ratio <= 0.88 else 0.5
    
    mqs = (fringe_score * 35.0) + (speck_score * 30.0) + (pinhole_score * 20.0) + (coverage_score * 15.0)
    return round(float(mqs), 2)

def decontaminate_and_cleanup(img_rgb: np.ndarray, alpha: np.ndarray) -> Image.Image:
    """
    1. Speck Dropping: Keep main subject & major connected components (>2% of max area).
    2. Pinhole Filling: Morphological closing on core foreground.
    3. Faint Alpha Crushing: Neutralize gray haze (<12 -> 0, >245 -> 255).
    4. pymatting Color Re-estimation: Neutralize stage background RGB bleed along edges.
    """
    # Clean binary components
    fg_bin = (alpha > 15).astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(fg_bin)
    if num_labels > 2:
        max_area = np.max(stats[1:, cv2.CC_STAT_AREA])
        min_keep = max_area * 0.02
        cleaned_mask = np.zeros_like(alpha)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_keep:
                cleaned_mask[labels == i] = alpha[labels == i]
        alpha = cleaned_mask

    # Morphological pinhole closing
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    alpha = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel)

    # Crush faint alpha haze
    alpha[alpha < 12] = 0
    alpha[alpha > 245] = 255

    # pymatting: Re-estimate foreground colors to eliminate dirty backdrop color bleed
    img_float = img_rgb.astype(np.float64) / 255.0
    alpha_float = alpha.astype(np.float64) / 255.0
    
    # Fast multi-level foreground estimation
    foreground_rgb = estimate_foreground_ml(img_float, alpha_float)
    foreground_uint8 = np.clip(foreground_rgb * 255.0, 0, 255).astype(np.uint8)

    # Recombine clean decontaminated RGB + refined alpha
    rgba = np.dstack((foreground_uint8, alpha))
    return Image.fromarray(rgba, "RGBA")

@app.post("/cutout-drive")
async def cutout_drive(req: Request):
    data = await req.json()
    rel_path = data.get("path")
    full_path = os.path.join(ROOT_DIR, rel_path.lstrip("/\\"))
    if not os.path.exists(full_path):
        return JSONResponse(status_code=404, content={"error": f"Not found: {full_path}"})

    pil_img = Image.open(full_path).convert("RGB")
    img_rgb = np.array(pil_img)

    # Cascading Model Chain with MQS
    best_alpha = None
    best_mqs = -1.0
    PASS_MARK = 75.0

    for model_name in ["portrait", "general", "isnet"]:
        sess = MODELS[model_name]
        raw_cutout = remove(pil_img, session=sess, only_mask=True)
        raw_alpha = np.array(raw_cutout)
        
        score = calculate_mqs(raw_alpha)
        if score > best_mqs:
            best_mqs = score
            best_alpha = raw_alpha

        if score >= PASS_MARK:
            break  # Passed threshold, proceed with best model

    # Cleanup & Pymatting Color Decontamination
    clean_rgba = decontaminate_and_cleanup(img_rgb, best_alpha)

    # Auto-crop bounding box with padding
    bbox = clean_rgba.getbbox()
    if bbox:
        pad = 12
        w, h = clean_rgba.size
        clean_rgba = clean_rgba.crop((
            max(0, bbox[0] - pad),
            max(0, bbox[1] - pad),
            min(w, bbox[2] + pad),
            min(h, bbox[3] + pad)
        ))

    buf = io.BytesIO()
    clean_rgba.save(buf, format="PNG")
    return Response(content=buf.getvalue(), media_type="image/png")
```

### Recipe B: Batch Processing Google Drive Files
```python
# Server endpoint to list any Google Drive directory safely
@app.get("/drive/list")
def list_drive(folder_path: str):
    if not os.path.exists(folder_path):
        return {"error": f"Path not found: {folder_path}"}
    items = []
    for entry in sorted(os.listdir(folder_path)):
        full = os.path.join(folder_path, entry)
        items.append({
            "name": entry,
            "is_dir": os.path.isdir(full),
            "size_kb": round(os.path.getsize(full) / 1024, 1) if not os.path.isdir(full) else None
        })
    return {"path": folder_path, "items": items}
```

### Recipe C: Audio / Speech Transcription (Whisper GPU)
```python
# Run via client.execute_code() or define on Colab
code = """
import whisper
model = whisper.load_model("base", device="cuda")
result = model.transcribe("/content/drive/MyDrive/recordings/sample.mp3")
print("TRANSCRIPT:", result["text"])
"""
res = client.execute_code(code)
print(res["stdout"])
```

---

## 5. Operational Best Practices

1. **Avoid Hardcoded Paths**:
   - Google Drive paths containing non-ASCII characters (e.g. Vietnamese accents) may be decomposed (NFD) or composed (NFC). Always use `os.listdir()` to dynamically inspect directories rather than hardcoding complex paths.
2. **Session Reconnects**:
   - Cloudflare ephemeral tunnels generate a new subdomain on each restart. Update `COLAB_URL` locally whenever the Colab session is refreshed.
3. **Execution Safety**:
   - `/exec` executes Python with standard globals. When running multi-line code from Antigravity, catch exceptions and inspect `res["stderr"]`.
4. **Keep Local Machine Pure**:
   - Never run `pip install torch` or heavy wheel builds on the local workspace. All model loading and matrix computing must remain on the Colab GPU.
