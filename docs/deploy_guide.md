# GPT-SoVITS 部署安装手册

## 环境要求

| 项目 | 最低要求 |
|------|---------|
| 操作系统 | Linux (x86_64 / ARM64) / macOS / Windows |
| Python | 3.10+ |
| Conda | Miniconda3 或 Anaconda |
| GPU (可选) | NVIDIA GPU + CUDA 12.6/12.8 或 AMD ROCm 6.2 |
| 内存 | 16GB+ 推荐 |
| 磁盘 | 20GB+ 可用空间 |

## 快速安装

### 1. 克隆项目

```bash
git clone https://github.com/brother2050/GPT-SoVITS.git
cd GPT-SoVITS
```

### 2. 创建 Conda 环境

```bash
conda create -n GPTSoVits python=3.10 -y
conda activate GPTSoVits
```

### 3. 运行安装脚本

```bash
bash install.sh --device <设备类型> --source <模型源> [--download-uvr5]
```

**参数说明：**

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--device` | `CU126` | NVIDIA GPU + CUDA 12.6 |
| | `CU128` | NVIDIA GPU + CUDA 12.8 |
| | `ROCM` | AMD GPU + ROCm 6.2 |
| | `MPS` | Apple Silicon (macOS) |
| | `CPU` | 仅 CPU |
| `--source` | `HF` | HuggingFace 官方源 |
| | `HF-Mirror` | HuggingFace 镜像（国内推荐） |
| | `ModelScope` | ModelScope 魔搭社区 |
| `--download-uvr5` | (可选) | 同时下载 UVR5 人声分离模型 |

**示例：**

```bash
# NVIDIA GPU (CUDA 12.8)，使用镜像源，下载 UVR5 模型
bash install.sh --device CU128 --source HF-Mirror --download-uvr5

# CPU 环境，使用 ModelScope 源
bash install.sh --device CPU --source ModelScope
```

### 4. 启动 WebUI

```bash
# 容器/服务器环境需要设置 is_share=True
is_share=True python webui.py

# 本地桌面环境直接启动
python webui.py
```

启动后访问 `http://0.0.0.0:9874`（默认端口）。

---

## TTS API 部署

GPT-SoVITS 提供独立的 TTS HTTP API 服务（`api.py`），可被其他服务调用。

### API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/` | GET / POST | TTS 文本转语音推理 |
| `/change_refer` | GET / POST | 更换默认参考音频 |
| `/set_model` | GET / POST | 切换模型 |
| `/control` | GET / POST | 控制命令 (restart / exit) |

### 启动 API 服务

```bash
# 使用启动脚本（推荐）
bash start_api.sh

# 或手动指定参数
python3 api.py \
  -s "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth" \
  -g "GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt" \
  -dr "参考音频.wav" \
  -dt "参考音频文本。" \
  -dl "zh" \
  -d "cuda" \
  -a "0.0.0.0" \
  -p 9880
```

### API 调用示例

```bash
# GET 方式 - 中文 TTS
curl "http://localhost:9880/?text=你好世界&text_language=zh" -o output.wav

# GET 方式 - 英文 TTS
curl "http://localhost:9880/?text=Hello%20world&text_language=en" -o output.wav

# POST 方式 - 带参数
curl -X POST "http://localhost:9880/" \
  -H "Content-Type: application/json" \
  -d '{"text": "你好世界", "text_language": "zh", "top_k": 20, "temperature": 0.8}' \
  -o output.wav

# 更换参考音频
curl -X POST "http://localhost:9880/change_refer" \
  -H "Content-Type: application/json" \
  -d '{"refer_wav_path": "new_ref.wav", "prompt_text": "新参考文本。", "prompt_language": "zh"}'

# 切换模型
curl -X POST "http://localhost:9880/set_model" \
  -H "Content-Type: application/json" \
  -d '{"gpt_model_path": "path/to/gpt.ckpt", "sovits_model_path": "path/to/sovits.pth"}'
```

### 支持的参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `text` | str | **必填** | 要合成的文本 |
| `text_language` | str | **必填** | 文本语种 (zh/en/ja/ko/yue/auto) |
| `refer_wav_path` | str | 启动参数默认值 | 参考音频路径 |
| `prompt_text` | str | 启动参数默认值 | 参考音频文本 |
| `prompt_language` | str | 启动参数默认值 | 参考音频语种 |
| `top_k` | int | 15 | Top-K 采样 |
| `top_p` | float | 1.0 | Top-P 采样 |
| `temperature` | float | 1.0 | 温度参数 |
| `speed` | float | 1.0 | 语速 |
| `cut_punc` | str | 启动参数 | 文本切分符号 |
| `sample_steps` | int | 32 | VITS 采样步数 |
| `inp_refs` | list | [] | 辅助参考音频列表 |
| `if_sr` | bool | False | 是否超分（仅 V3） |

### 支持的语言

`中文`, `英文`, `日文`, `韩文`, `粤语`, `zh`, `en`, `ja`, `ko`, `yue`, `auto`, `auto_yue`, `中英混合`, `粤英混合`, `日英混合`, `韩英混合`, `多语种混合`, `多语种混合(粤语)`

### 错误响应格式

```json
{"code": 400, "message": "错误描述"}
```

---

## Systemd 服务部署（推荐生产环境）

将 API 注册为系统服务，实现开机自启和自动重启：

```bash
# 1. 复制服务文件
cp gpt-sovits-api.service /etc/systemd/system/

# 2. 编辑服务文件，修改模型路径和参考音频（如需）
vim /etc/systemd/system/gpt-sovits-api.service

# 3. 启动服务
systemctl daemon-reload
systemctl enable gpt-sovits-api
systemctl start gpt-sovits-api

# 4. 查看状态和日志
systemctl status gpt-sovits-api
journalctl -u gpt-sovits-api -f
```

服务文件 `gpt-sovits-api.service` 位于项目根目录。

---

## Docker 部署

### 构建镜像

```bash
docker build -t gpt-sovits-api -f Docker/Dockerfile.api .
```

### Docker Compose 启动

```bash
# 创建参考音频目录
mkdir -p reference_audios
# 放入参考音频文件

# 启动 API 服务
docker compose -f docker-compose.api.yaml up -d

# 查看日志
docker compose -f docker-compose.api.yaml logs -f

# 停止服务
docker compose -f docker-compose.api.yaml down
```

### 手动 Docker 运行

```bash
docker run --gpus all \
  -p 9880:9880 \
  -v $(pwd)/GPT_SoVITS/pretrained_models:/workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models \
  -v $(pwd)/reference_audios:/workspace/GPT-SoVITS/reference_audios \
  --shm-size 8g \
  --restart unless-stopped \
  gpt-sovits-api
```

---

## 版本兼容说明

本项目已锁定以下关键依赖版本，确保稳定运行：

| 包名 | 版本 | 说明 |
|------|------|------|
| `starlette` | `==0.46.0` | 兼容 Gradio 4.x 的 TemplateResponse API |
| `gradio` | `<5` | WebUI 框架 |
| `jinja2` | `>=3.0,<4.0` | 模板引擎 |
| `markupsafe` | `>=2.0` | Jinja2 依赖 |
| `fastapi` | `>=0.115.2` | API 框架 |
| `torch` | (由 --device 决定) | 深度学习框架 |

> **注意：** `starlette>=1.3.0` 修改了 `TemplateResponse` 签名，与 Gradio 4.x 不兼容，会导致 `unhashable type: 'dict'` 错误。本项目锁定 `starlette==0.46.0` 解决此问题。

---

## 常见问题

### 1. `unhashable type: 'dict'` 错误

确保 `starlette==0.46.0`：

```bash
pip install starlette==0.46.0
```

### 2. `When localhost is not accessible, a shareable link must be created`

容器/服务器环境需设置环境变量：

```bash
is_share=True python webui.py
```

### 3. onnxruntime 依赖警告

GPU 环境（x86_64）使用 `onnxruntime-gpu`，`pip check` 提示缺少 `onnxruntime` 是正常的，不影响功能。

### 4. Chrome sandbox 警告

`Running as root without --no-sandbox` 是容器内 Chromium 的正常警告，不影响 WebUI 运行。

### 5. API 返回 `不支持的语言` 错误

检查 `text_language` 和 `prompt_language` 参数，支持的语言见上方"支持的语言"列表。参数大小写不敏感。

## 项目结构

```
GPT-SoVITS/
├── webui.py                  # 主 WebUI 入口
├── api.py                    # API v1 接口（推荐用于生产）
├── api_v2.py                 # API v2 接口（更多高级功能）
├── config.py                 # 全局配置
├── requirements.txt          # Python 依赖（含版本锁定）
├── install.sh                # 一键安装脚本
├── start_api.sh              # API 启动脚本
├── gpt-sovits-api.service    # Systemd 服务文件
├── docker-compose.api.yaml   # API Docker Compose 配置
├── Dockerfile                # WebUI Docker 构建文件
├── Docker/Dockerfile.api     # API Docker 构建文件
├── GPT_SoVITS/               # 核心模块
├── tools/                    # 工具集（UVR5、ASR 等）
└── docs/                     # 文档
```
