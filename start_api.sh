#!/bin/bash
# GPT-SoVITS API 启动脚本
# 用法: ./start_api.sh [选项]

set -e

# ============ 配置区（按需修改）============
SOVITS_MODEL="GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s2G2333k.pth"
GPT_MODEL="GPT_SoVITS/pretrained_models/gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"
DEFAULT_REF_PATH="参考音频.wav"        # 默认参考音频路径
DEFAULT_REF_TEXT="参考音频文本。"       # 默认参考音频对应文本
DEFAULT_REF_LANG="zh"                  # 默认参考音频语种
DEVICE="cuda"                          # cuda / cpu
BIND_ADDR="0.0.0.0"                   # 监听地址
PORT="9880"                            # 端口
STREAM_MODE="close"                    # close / normal / keepalive
MEDIA_TYPE="wav"                       # wav / ogg / aac
UPLOAD_DIR="./refs"                    # 参考音频上传目录
# ==========================================

# 切换到项目目录
cd "$(dirname "$0")"

# 激活 conda 环境（如果有）
if [ -f "/root/miniconda/envs/GPTSoVits/bin/activate" ]; then
    source /root/miniconda/envs/GPTSoVits/bin/activate
fi

echo "=========================================="
echo "GPT-SoVITS TTS API 启动"
echo "=========================================="
echo "SoVITS 模型: $SOVITS_MODEL"
echo "GPT 模型:    $GPT_MODEL"
echo "设备:        $DEVICE"
echo "监听:        $BIND_ADDR:$PORT"
echo "上传目录:    $UPLOAD_DIR"
echo "=========================================="

export GPT_SOVITS_UPLOAD_DIR="$UPLOAD_DIR"
exec python3 api.py \
    -s "$SOVITS_MODEL" \
    -g "$GPT_MODEL" \
    -dr "$DEFAULT_REF_PATH" \
    -dt "$DEFAULT_REF_TEXT" \
    -dl "$DEFAULT_REF_LANG" \
    -d "$DEVICE" \
    -a "$BIND_ADDR" \
    -p "$PORT" \
    -sm "$STREAM_MODE" \
    -mt "$MEDIA_TYPE"
