# Chapter 13: 卷曲螺旋(Coiled Coil)设计

## 概述

卷曲螺旋是最常见的超二级结构之一，由多条α-螺旋缠绕形成超螺旋束。

## 基础原理

### Heptad重复 (7残基周期)

```
位置:  a  b  c  d  e  f  g
       ↓        ↓
     疏水     疏水
     核心a-d-a-d packing

a位: 大疏水残基 (L, I, V, F)
d位: 大疏水残基 (L, I, V, F)
b,c,e,f,g位: 极性/带电残基
```

### 骞聚状态决定因素

| 骞聚态 | a位偏好 | d位偏好 | 交叉角 |
|--------|---------|---------|--------|
| 二聚体 | L, I | L, N | ~20° |
| 三聚体 | I, V | L, I | ~20° |
| 四聚体 | L, I | L, I | ~20° |

### Crick参数

```
- 超螺旋半径 (superhelical radius)
- 超螺距 (superhelical pitch)  
- 相位角 (phase angle)
- 残基/圈 (residues/turn)
```

## 设计流程

### 1. 序列设计

```python
def design_coiled_coil(oligomer_state='dimer', length=28):
    """
    设计卷曲螺旋序列
    
    Args:
        oligomer_state: 二聚/三聚/四聚
        length: 序列长度(建议7的倍数)
    
    Returns:
        设计的氨基酸序列
    """
    # 定义各位置偏好
    heptad_preferences = {
        'dimer': {
            'a': ['L', 'I', 'V'],  # 疏水核心
            'b': ['E', 'K', 'Q'],  # 极性
            'c': ['E', 'K', 'Q'],  # 极性
            'd': ['L', 'N', 'Q'],  # 疏水核心(dimer特异)
            'e': ['E', 'K'],       # 静电相互作用(e-g')
            'f': ['E', 'K', 'Q'],  # 极性
            'g': ['E', 'K'],       # 静电相互作用(g-e')
        }
    }
    
    positions = 'abcdefg'
    sequence = ''
    for i in range(length):
        pos = positions[i % 7]
        prefs = heptad_preferences[oligomer_state][pos]
        # 根据偏好选择残基
        sequence += select_residue(prefs, pos, i)
    
    return sequence
```

### 2. 结构验证

```python
def validate_coiled_coil(pdb_file):
    """
    验证卷曲螺旋结构质量
    
    检查项:
    1. 螺旋度(helicity)
    2. 超螺旋参数
    3. 疏水核心堆积
    4. 链间盐桥
    """
    structure = load_structure(pdb_file)
    
    # 检查螺旋度
    helicity = calculate_helicity(structure)
    
    # 检查knobs-into-holes堆积
    kih_score = analyze_knobs_into_holes(structure)
    
    # 检查heptad重复
    heptad_reg = check_heptad_register(structure)
    
    return {
        'helicity': helicity,
        'kih_score': kih_score,
        'heptad_register': heptad_reg,
        'quality': 'good' if helicity > 0.9 and kih_score > 0.8 else 'needs_refinement'
    }
```

### 3. 功能化设计

卷曲螺旋可用于：
- **药物载体**: 精确靶向递送
- **抗体结合模块**: 构建双特异性抗体
- **纳米材料**: 自组装纳米结构
- **信号通路调控**: 模拟蛋白-蛋白相互作用

## 工具推荐

| 工具 | 功能 | 链接 |
|------|------|------|
| SOCKET | 检测coiled coil | CC+ database |
| COILS | 序列预测coiled coil | ExPASy |
| LOGICOIL | 骞聚态预测 | Web server |
| CCBuilder | 结构建模 | GitHub |

## 注意事项

1. **静电互补**: e位和g位的盐桥对稳定性至关重要
2. **螺旋倾斜**: 正确的交叉角确保疏水核心闭合
3. **异源骞聚**: 可设计特异性链配对(a-a', d-d'互补)
4. **长度效应**: 至少3-4个heptad重复才稳定
