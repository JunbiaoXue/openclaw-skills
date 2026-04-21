# Chapter 5: 突变效应预测

## 概述

使用深度神经网络预测突变对蛋白质二级和超二级结构的影响。

## 四态构象编码

| 编码 | 构象 | 描述 |
|------|------|------|
| B | β-sheet | β-折叠 |
| H | α-helix | α-螺旋 |
| O | other | 卷曲/转角 |
| D | disordered | 无序状态 |

## 预测方法

### 输入
- 野生型序列
- 突变位点与类型
- 进化信息(PSSM)

### 输出
- 突变后每个残基的构象状态概率
- 构象变化的残基定位
- 稳定性影响评分

### 网络架构
```
序列编码 → Embedding层 → 多层Transformer → 
突变注意力层 → 构象预测头 → B/H/O/D概率
```

## 应用案例

### 1. 流感病毒血凝素突变追踪
```python
def track_hemagglutinin_mutations(wt_sequence, mutations):
    """
    追踪血凝素突变对构象的影响
    
    关键位点:
    - 受体结合位点(RBS)突变
    - 抗原漂移位点
    - 裂解位点附近突变
    """
    results = []
    for mut in mutations:
        pos, wt_aa, mut_aa = parse_mutation(mut)
        
        # 预测构象变化
        wt_conf = predict_conformation(wt_sequence, pos)
        mut_sequence = apply_mutation(wt_sequence, mut)
        mut_conf = predict_conformation(mut_sequence, pos)
        
        # 计算构象变化
        delta = calculate_conformational_change(wt_conf, mut_conf)
        
        results.append({
            'mutation': mut,
            'wt_conformation': wt_conf,
            'mut_conformation': mut_conf,
            'delta_score': delta,
            'impact': 'high' if delta > threshold else 'low'
        })
    
    return results
```

### 2. 抗体稳定性评估
```python
def assess_antibody_stability(vh_sequence, vl_sequence, mutations):
    """
    评估抗体突变对稳定性的影响
    
    重点关注:
    - 框架区(FW)突变 → 结构稳定性
    - CDR区突变 → 结合特异性
    - 界面残基突变 → VH-VL相互作用
    """
    stability_scores = []
    for mut in mutations:
        # 预测各区域构象变化
        conf_change = predict_mutation_effect(mut)
        
        # 区分影响类型
        if is_framework_mutation(mut):
            impact_type = 'structural_stability'
        elif is_cdr_mutation(mut):
            impact_type = 'binding_affinity'
        elif is_interface_mutation(mut):
            impact_type = 'domain_interaction'
        
        stability_scores.append({
            'mutation': mut,
            'conformational_change': conf_change,
            'impact_type': impact_type
        })
    
    return stability_scores
```

## 灵敏度

- 可检测**单点突变**引起的构象变化
- 对关键功能位点的突变尤其敏感
- 适用于快速筛选有害突变
