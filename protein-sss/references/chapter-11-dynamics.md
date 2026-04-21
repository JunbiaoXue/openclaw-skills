# Chapter 11: 蛋白质动力学分析

## 概述

从氨基酸序列预测蛋白质动力学性质，基于B因子的傅里叶变换方法。

## 核心方法

### B因子序列表示

```python
def bfactor_to_sequence(bfactors):
    """
    将B因子序列转换为可分析的数值序列
    
    B因子(温度因子)反映原子位置的波动程度
    高B因子 = 高柔性
    低B因子 = 高刚性
    """
    import numpy as np
    
    # 归一化B因子
    mean_b = np.mean(bfactors)
    std_b = np.std(bfactors)
    normalized = (bfactors - mean_b) / std_b
    
    return normalized
```

### 傅里叶变换分析

```python
def fourier_dynamics_analysis(bfactor_sequence):
    """
    傅里叶变换分析蛋白质动力学模式
    
    将B因子序列视为信号，提取周期性模式
    """
    import numpy as np
    from scipy.fft import fft, fftfreq
    
    N = len(bfactor_sequence)
    
    # 傅里叶变换
    yf = fft(bfactor_sequence)
    xf = fftfreq(N, d=1)  # d=1: 每个残基一个采样点
    
    # 功率谱
    power_spectrum = np.abs(yf[:N//2])**2
    frequencies = xf[:N//2]
    
    # 找主频
    dominant_freq_idx = np.argmax(power_spectrum[1:]) + 1
    dominant_period = 1 / frequencies[dominant_freq_idx] if frequencies[dominant_freq_idx] != 0 else float('inf')
    
    return {
        'power_spectrum': power_spectrum,
        'dominant_period': dominant_period,
        'flexibility_profile': bfactor_sequence
    }
```

### 动力学性质预测

```python
def predict_dynamics(sequence):
    """
    从序列预测蛋白质动力学性质
    
    输出:
    - 整体柔性/刚性
    - 柔性区域定位
    - 构象变化倾向
    """
    # 1. 预测平均B因子
    avg_bfactor = predict_avg_bfactor(sequence)
    
    # 2. 预测B因子剖面
    bfactor_profile = predict_bfactor_profile(sequence)
    
    # 3. 傅里叶分析
    dynamics = fourier_dynamics_analysis(bfactor_profile)
    
    # 4. 分类
    if avg_bfactor > high_threshold:
        classification = 'highly_flexible'
    elif avg_bfactor < low_threshold:
        classification = 'rigid'
    else:
        classification = 'moderate'
    
    # 5. 识别有序/无序区域
    disordered_regions = identify_disordered_regions(bfactor_profile)
    
    return {
        'classification': classification,
        'avg_bfactor': avg_bfactor,
        'flexible_regions': disordered_regions,
        'dominant_period': dynamics['dominant_period']
    }
```

## 应用

1. **蛋白质功能预测**: 柔性区域通常是功能位点
2. **别构效应分析**: 动力学传播路径
3. **药物设计**: 靶向柔性vs刚性区域
4. **蛋白质工程**: 调控动力学性质
