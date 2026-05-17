---
name: lottery-prediction
description: 双色球历史数据分析+预测模型。Transformer模型训练，统计分析，预测号码生成。
version: 1.0.0
tags: [lottery, prediction, machine-learning, transformer, statistics]
---

# 双色球预测 Skill

基于历史数据的双色球统计分析和预测模型。

## 核心流程

### 1. 数据获取

从官方数据源抓取历史开奖数据，保存为CSV格式：
- 双色球：6个红球(1-33) + 1个蓝球(1-16)
- 数据字段：期号、日期、红球1-6、蓝球

### 2. 特征工程

```python
# 基础特征
- 奇偶比、大小比、质数个数
- 和值、跨度、AC值
- 区间分布(1-11, 12-22, 23-33)
- 邻期重号个数、遗漏值

# 时序特征
- 近N期频率统计
- 遗漏期数
- 热号/冷号标识
```

### 3. 模型架构

**推荐：Transformer Encoder**
- 输入：近30期历史数据的特征向量
- 2层Encoder，d_model=64，4头注意力
- 输出：每个号码位置的概率分布

```python
class LotteryTransformer(nn.Module):
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=2):
        super().__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.fc_red = nn.Linear(d_model, 33)   # 红球1-33
        self.fc_blue = nn.Linear(d_model, 16)  # 蓝球1-16
```

### 4. 训练策略

- 训练/测试集按时间顺序分割（早期训练，近期测试）
- Loss：BCEWithLogitsLoss（多标签分类）
- 优化器：Adam, lr=1e-3
- 200-500 epochs

### 5. 预测输出

```python
# 取概率最高的6个红球 + 1个蓝球
red_probs = model.predict(last_30_games)
blue_probs = model.predict_blue(last_30_games)
top_red = sorted(range(33), key=lambda i: red_probs[i], reverse=True)[:6]
top_blue = argmax(blue_probs) + 1
```

## 重要声明

**彩票本质是随机事件，任何模型都无法真正预测。**
- 模型比随机基准高2-5%，属统计噪声范围
- 不构成购买建议，仅供学习和娱乐

## 文件说明

| 文件 | 说明 |
|------|------|
| `scripts/train_final.py` | Transformer模型训练脚本 |
| `scripts/fetch_data.py` | 历史数据抓取脚本 |
| `scripts/README.md` | 项目详细报告 |

## 使用方法

```bash
# 1. 抓取数据
python fetch_data.py

# 2. 训练模型
python train_final.py

# 3. 输出预测号码和概率分析
```
