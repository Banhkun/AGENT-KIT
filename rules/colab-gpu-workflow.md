# Google Colab GPU Workflow & Architecture

> [!IMPORTANT]
> **DIRECT API INTEGRATION**
> The user configures and runs the Colab notebook environment. The agent communicates directly with the live Colab server via its HTTP/Cloudflare tunnel (calling `/list`, `/cutout-drive`, `/montage-drive`, etc.) to automate asset processing. Do not dump unsolicited Colab notebook code blocks into chat.

## Core Architectural Principle
- **Lightweight Local Footprint**: Do NOT install heavy machine learning libraries (`torch`, `torchvision`, `onnxruntime-gpu`, `rembg`, `opencv-python`, `transformers`, `diffusers`) or create bloated virtual environments on the local Windows drive.
- **Remote Heavy Computing**: All heavy computational tasks run on remote Google Colab GPU runtimes (T4/A100) managed manually by the user.
- **Direct Cloud Storage Integration**: Large asset archives remain in Google Drive (e.g. `/content/drive/MyDrive/...`). Colab mounts Google Drive directly via `drive.mount('/content/drive')`, eliminating local downloads and bypassing anonymous rate limits.

## Colab GPU Setup & ONNX / CUDA Fix
To ensure GPU providers (`CUDAExecutionProvider`, `TensorrtExecutionProvider`) load properly without falling back to CPU:
1. **The Exact Dependency Fix**:
   ```bash
   !pip uninstall -y -q onnxruntime onnxruntime-gpu
   !pip install -q "onnxruntime-gpu[cuda,cudnn]"
   ```
2. **Preload DLLs**: In Python before session or model initialization:
   ```python
   import onnxruntime as ort
   ort.preload_dlls()  # Preloads CUDA/cuDNN before ONNX runtime initializes
   print("Providers:", ort.get_available_providers())
   # Must include: ['TensorrtExecutionProvider', 'CUDAExecutionProvider', 'CPUExecutionProvider']
   ```

## SOTA Neural Matting, MQS & Color Decontamination
*Crucial Rule*: Dirty/dark fringes on white or light backgrounds are primarily caused by **color contamination** — edge pixels carry original backdrop RGB values even when alpha values are mathematically correct. General object models (like `u2net`) yield soft, wide fringes and must be avoided for portrait work.

1. **Model Cascading Chain**:
   - Primary: `birefnet-portrait` (SOTA for human hair & fine edges)
   - Fallback 1: `birefnet-general`
   - Fallback 2: `isnet-general-use`
   - *(Never use `u2net` for human portraits)*

2. **Mask Quality Score (MQS)**:
   - Evaluates raw masks on:
     - **Fringe Width**: ratio of semi-transparent pixels ($15 < \alpha < 240$)
     - **Stray Specks**: disconnected high-alpha clusters outside the main subject
     - **Pinholes**: low-alpha holes inside high-confidence foreground areas
     - **Coverage**: bounding-box proportions and edge contact (penalizing chopped limbs)
   - Models are only replaced if MQS falls below the passing threshold; the highest-scoring mask is selected.

3. **Mask Cleanup & Foreground Color Decontamination**:
   - **Speck Dropping**: Drop small isolated connected components outside main body.
   - **Pinhole Filling**: Morphological closing or flood fill on solid foreground regions.
   - **Faint Alpha Crushing**: Clamp faint grey noise ($\alpha < 10 \to 0$, $\alpha > 245 \to 255$).
   - **Foreground Color Re-estimation (`pymatting`)**: Use `pymatting` (pre-bundled with `rembg`) to re-estimate true foreground RGB values across the transition zone, wiping out backdrop color bleed (e.g. blue stage lighting bleed on hair or white dresses).

## Server & Tunnel Lifecycle
- **Clean Existing Ports**:
   ```bash
   !fuser -k 8000/tcp || true
   !pkill -f cloudflared || true
   ```
- **Cloudflare Tunnel Startup**:
   ```bash
   !wget -q -nc https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
   !dpkg -i cloudflared-linux-amd64.deb > /dev/null 2>&1
   tunnel = subprocess.Popen(["cloudflared", "tunnel", "--url", "http://localhost:8000"], stderr=subprocess.PIPE, text=True)
   ```
   Auto-capture the public URL (`https://*.trycloudflare.com`) from `tunnel.stderr`.

## Standard API Endpoints
- `GET /health`: Returns GPU availability, hardware device name, VRAM, and Drive mount status.
- `POST /exec`: `{"code": "<python_code>"}` -> Dynamic remote Python execution on Colab GPU with captured stdout/stderr.
- `POST /cutout-drive`: `{"path": "<rel_path>"}` -> Runs SOTA model chain + MQS + pymatting decontamination -> returns pristine transparent PNG.
- `POST /montage-drive`: `{"paths": [...], "size": [W, H]}` -> Subject-aware DP seam carving + Laplacian blend -> returns JPEG.

## Local Client Convention
- Maintain client interaction in a lightweight `ColabClient` wrapper (e.g. `scripts/colab_client.py`).
- Read `COLAB_URL` from the environment or configuration file, and update it whenever a new ephemeral tunnel is generated.
