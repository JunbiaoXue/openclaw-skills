# Chapter 1: 二级与超二级结构预测综述

## 概述

本章综述2018年以来发布的45个SS预测器和32个SSS预测器。

## SS预测器分类

### 输入特征（5大类）

| 输入类型 | 描述 | 使用率 |
|----------|------|--------|
| 原始序列 | 直接输入氨基酸序列 | 常用 |
| One-hot编码 | 20维向量表示氨基酸 | 常用 |
| PSSM | PSI-BLAST/MMseqs2生成 | **35/45工具使用** |
| 理化性质 | 疏水性、体积、极化率 | 辅助 |
| HMM Profile | HHblits生成 | 常用 |

> **关键发现**: 37/45工具使用至少一种进化信息(PSSM/HMM)，PSSM是最受欢迎的输入

### 模型架构趋势

```
2018-2020: CNN + BiLSTM 为主
2021-2022: Transformer兴起
2022-2024: 大语言模型(ESM/ProtTrans)作为特征提取器
```

### 现代预测器推荐

| 工具 | 架构 | Q3准确率 | 输出 | 可用性 |
|------|------|----------|------|--------|
| SPOT-1D-LM | Transformer+LM | ~85% | 3&8-state | GitHub |
| NetSurfP-3.0 | Transformer | ~84% | 3&8-state | Web |
| OPUS-TASS | Transformer | ~84% | 3&8-state | GitHub |
| PHAT | FFNN | ~82% | 3&8-state | GitHub |

## SSS预测器分类

### 主要预测目标

1. **Coiled coil预测**: 多螺旋缠绕结构
2. **β-hairpin预测**: 反平行β-链对
3. **β-α-β motif预测**: 最常见的SSS单元

### 评估指标

- **Q3/Q8 accuracy**: 正确预测残基比例
- **SOV (Segment Overlap)**: 段级重叠评分，更关注连续片段
- **MCC**: 平衡各类别的性能

## 实用建议

1. **选择工具**: 优先使用集成多种进化信息的预测器
2. **共识策略**: 结合多个预测器结果提升准确率
3. **后处理**: 使用Viterbi解码确保SS段连续性

## 代码示例

```python
# 使用PSIPRED进行二级结构预测
# 安装: conda install -c bioconda psipred

# 1. 生成PSSM
# psiblast -query input.fasta -db uniref90 -evalue 0.001 -num_iterations 3 -out_ascii_pssm pssm.txt

# 2. 运行PSIPRED
# psipred pssm.txt output.ss2 output.horiz

# 3. 解析结果
def parse_psipred(ss2_file):
    """解析PSIPRED .ss2输出"""
    results = []
    with open(ss2_file) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 6:
                    results.append({
                        'residue': int(parts[0]),
                        'aa': parts[1],
                        'ss': parts[2],
                        'prob_H': float(parts[3]),
                        'prob_E': float(parts[4]),
                        'prob_C': float(parts[5])
                    })
    return results
```
