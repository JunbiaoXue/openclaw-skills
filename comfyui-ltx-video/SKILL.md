---
name: comfyui-ltx-video
description: ComfyUI LTX 2.3 (Sulphur) 图生视频/文生视频工作流。模型配置、LoRA链、I2V/T2V工作流。
version: 1.0.0
tags: [comfyui, ltx, video-generation, i2v, t2v, sulphur]
---

# ComfyUI LTX 2.3 (Sulphur) 视频生成 Skill

使用 ComfyUI + LTX 2.3 (Sulphur) 模型生成视频的工作流和配置。

## 环境配置

```
ComfyUI版本: v0.21.1
Conda环境: comfyui
GPU: NVIDIA L20 (47GB VRAM)
端口: 8188
```

### 启动命令

```bash
source /home/xjb/miniconda3/etc/profile.d/conda.sh
conda activate comfyui
cd /home/xjb/software/comfyui
python main.py --listen 0.0.0.0 --port 8188 &
```

### 代理设置（下载模型用）

```bash
export http_proxy="http://127.0.0.1:7892"
export https_proxy="http://127.0.0.1:7892"
```

## 模型文件

| 模型 | 路径 | 大小 |
|------|------|------|
| Sulphur主模型 | `models/checkpoints/sulphur_dev_bf16.safetensors` | 30GB |
| Gemma3文本编码器(fp8) | `models/clip/gemma_3_12B_it_fp8_scaled.safetensors` | 9GB |
| Sulphur LoRA | `models/loras/sulphur_final.safetensors` | 9.6GB |
| 蒸馏LoRA | `models/loras/ltx-2.3-22b-distilled-lora-1.1_fro90_ceil72_condsafe.safetensors` | 632MB |
| Upscaler | `models/upscale_models/ltx-2.3-spatial-upscaler-x2-1.0.safetensors` | 950MB |

## 关键配置

### 文本编码器

LTX 2.3 (Sulphur) 使用 **Gemma3** 文本编码器，hidden_size=4096。
- 正确：`gemma_3_12B_it_fp8_scaled.safetensors` (hidden=4096)
- 错误：`gemma_3_12B_it_fp4_mixed.safetensors` (hidden=3840, LTX 2.1专用)

### LoRA链配置

```python
# 双LoRA链 - 按参考工作流
model = LoraLoader(
    lora_name="sulphur_final.safetensors",
    strength_model=1.0, strength_clip=1.0
)
model = LoraLoader(
    lora_name="ltx-2.3-22b-distilled-lora-1.1_fro90_ceil72_condsafe.safetensors",
    strength_model=0.5, strength_clip=0.7
)
```

### 采样器

```
采样器: euler_ancestral_cfg_pp
调度器: ltxv_beta_dist (手动sigmas)
Steps: 20-30
CFG: 3.0-5.0
```

## 工作流

### T2V (文生视频)

```json
KSampler → LTXVDecoder → SaveVideo
```

文件：`scripts/sulphur_test.json`

### I2V (图生视频)

```
LoadImage → LTXVImgToVideoInplace → KSampler → LTXVDecoder → SaveVideo
```

文件：`scripts/sulphur_i2v_baby.json`

## Pitfalls

1. **Gemma3版本不兼容**：LTX 2.1用fp4_mixed(hidden=3840)，2.3用fp8_scaled(hidden=4096)，混用会报错
2. **ComfyUI版本**：v0.10.0不支持hidden_size=4096，必须升级到v0.21.1
3. **M2L vs MML**：PTM编码中M2L是硫氨基酸衍生物，二甲基赖氨酸应使用MLY
4. **LoRA顺序**：sulphur_final在前，distilled在后
5. **外网访问**：下载模型需设置VPN代理(http://127.0.0.1:7892)

## 输出

视频保存在：`/home/xjb/comfyui_outputs/`
