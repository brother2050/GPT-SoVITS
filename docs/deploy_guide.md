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

## 容器部署

### Docker

```bash
# 构建镜像
docker build -t gpt-sovits .

# 运行容器
docker run --gpus all -p 9874:9874 gpt-sovits
```

### 容器内直接安装

```bash
# 容器环境中启动需设置 is_share=True
conda activate GPTSoVits
is_share=True python webui.py
```

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

## 项目结构

```
GPT-SoVITS/
├── webui.py              # 主 WebUI 入口
├── api_v2.py             # API v2 接口
├── config.py             # 全局配置
├── requirements.txt      # Python 依赖（含版本锁定）
├── install.sh            # 一键安装脚本
├── Dockerfile            # Docker 构建文件
├── GPT_SoVITS/           # 核心模块
├── tools/                # 工具集（UVR5、ASR 等）
└── docs/                 # 文档
```
