---
name: protein-sss
description: 蛋白质超二级结构（Supersecondary Structure）分析方法。触发词：二级结构预测、Walker-A motif、ABEGO构象、卷曲螺旋设计、突变效应预测、非冗余数据集、AlphaFold局限。基于Springer《Protein Supersecondary Structures》第三版提炼。
license: MIT
---

# 蛋白质超二级结构分析 Skill

## 触发条件

### ✅ 自动激活场景
- 蛋白质二级/超二级结构预测与分析
- Walker-A / NTPase motif 检测
- ABEGO构象分类与Ramachandran分析
- 突变效应与蛋白质稳定性预测
- 非冗余蛋白质数据集构建（CAFS）
- 卷曲螺旋（coiled coil）设计与分析
- AlphaFold局限性讨论与传统方法补充
- β-sandwich / β-α-β motif分析

### ❌ 不触发场景
- 简单PDB查询或分子可视化（常识操作）
- 仅需要AlphaFold预测（有独立流程）
- 小分子药物设计或基因序列分析

---

## 核心方法

### 方法1: ABEGO构象分类

将蛋白质主链φ/ψ角转换为5种离散状态：

| 状态 | 构象 | φ范围 | ψ范围 | 典型结构 |
|------|------|-------|-------|----------|
| **A** | α-螺旋 | -90°~-30° | -90°~-10° | 右手α-螺旋 |
| **B** | β-折叠 | -180°~-60° | 90°~180° | β-链 |
| **E** | 扩展β | -90°~-30° | 120°~180° | 左手β |
| **G** | 左旋α | 50°~90° | -90°~-10° | 左手α-螺旋 |
| **O** | 其他 | 其他 | 其他 | cis肽键等 |

**应用**：Walker-A motif典型构象为 `EBBGAGAA` 或 `BBBGAGAA`

**脚本**：`scripts/abego_classify.py`

---

### 方法2: Walker-A Motif检测

**序列模式**：`GXXXXGK[T/S]`

**检测流程**：
1. 序列模式匹配 → 候选位点
2. 结构预测（如有结构）→ ABEGO构象分析
3. 构象验证 → 是否形成"nest"（anion-hole）

**扩展模式**：
- `GXXXXGK[TSG]` - 包含核苷酸激酶
- `GXXXXG.X` - 非典型序列也能采用Walker-A构象

**脚本**：`scripts/detect_walker_a.py`

---

### 方法3: CAFS非冗余数据集构建

**Culling After Full Search** 方法：

```
1. 全量搜索 → 收集所有候选
2. 序列聚类 → MMseqs2 / CD-hit
3. 结构验证 → 检查序列相似但结构不同的案例
4. 选择代表 → 优先高分辨率、少缺失、野生型
```

**推荐阈值**：

| 用途 | Identity阈值 |
|------|-------------|
| 高冗余去除 | 90% |
| 中等去冗余 | 40-50% |
| 低冗余（推荐） | 25-30% |

**脚本**：`scripts/cafs_pipeline.py`

---

### 方法4: 突变效应预测

**三种方法组合**：

| 方法 | 适用场景 | 工具 |
|------|----------|------|
| Rosetta能量分析 | 有结构，需精确ΔΔG | Rosetta ddg_monomer |
| 接触分析 | 快速筛选，理解机制 | HBPlus + 自定义脚本 |
| AlphaFold2建模 | 无结构，关注全局变化 | ColabFold/本地AF2 |

**Rosetta能量项**：
- `fa_atr` - 范德华吸引
- `fa_rep` - 范德华排斥
- `fa_elec` - 静电
- `fa_sol` - 溶剂化

---

### 方法5: 卷曲螺旋设计

**Heptad重复规则**：

```
位置:  a  b  c  d  e  f  g
       ↓        ↓
     疏水     疏水
     
a位: L, I, V, F (大疏水)
d位: L, I, V, F (大疏水，dimer偏好N)
e-g位: 极性/带电 (静电相互作用)
```

**设计流程**：
1. DeepCoil预测卷曲螺旋倾向
2. AGGRESCAN/TANGO评估聚集风险
3. 确定骞聚态（二聚/三聚/四聚）
4. 序列设计 + 分子动力学验证

---

### 方法6: AlphaFold局限与补充

| AlphaFold局限 | 传统方法补充 | 章节 |
|---------------|-------------|------|
| 可解释性缺失 | 物理化学原理（UNRES/Rosetta） | Preface, Ch14 |
| 仅36%高置信 | 多预测器ensemble验证 | Preface |
| 从头设计挑战 | 能量函数理性设计 | Ch9 |
| 静态结构 | MD模拟、SSSCPreds动力学 | Ch5, Ch11 |

**混合策略**：AlphaFold初预测 → 传统方法精细化 → 实验验证

---

## 快速参考

### 二级结构评估指标

| 指标 | 定义 | 典型值 | 使用场景 |
|------|------|--------|----------|
| **Q3** | 3-state正确率 | 82-86% | SS预测评估 |
| **Q8** | 8-state正确率 | 70-76% | 精细SS评估 |
| **SOV** | 段级重叠评分 | 70-85% | 段边界重要时 |
| **MCC** | Matthews相关系数 | -1~+1 | 不平衡分类 |

### 交叉验证选择

| 数据量 | 推荐方法 |
|--------|----------|
| 大(>1000) | 十折交叉验证 |
| 中(100-1000) | 五折交叉验证 |
| 小(<100) | 留一交叉验证 |

---

## 工具清单

### 核心工具（通过验证）

| 工具 | 用途 | 可用性 |
|------|------|--------|
| **DeepCoil** | 卷曲螺旋预测 | Web: toolkit.tuebingen.mpg.de |
| **AGGRESCAN** | 聚集倾向 | Web: bioinf.uab.es/aggrescan |
| **TANGO** | 聚集预测 | Web: tango.crg.es |
| **MMseqs2** | 序列聚类 | GitHub |
| **CD-hit** | 序列聚类 | GitHub |
| **HBPlus** | 氢键分析 | 本地安装 |

### 进化信息工具

| 工具 | 产出 | 使用率 |
|------|------|--------|
| **PSI-BLAST** | PSSM | 35/45工具使用 |
| **HHblits** | HMM profile | 37/45工具使用 |

### 参考工具（按需使用）

- DSSP/STRIDE：二级结构注释
- SOCKET：Knobs-into-holes分析
- PROMOTIF：结构motif识别

---

## 脚本

| 脚本 | 功能 |
|------|------|
| `scripts/abego_classify.py` | PDB→ABEGO字符串+Walker-A检测 |
| `scripts/detect_walker_a.py` | 序列Walker-A motif检测 |
| `scripts/cafs_pipeline.py` | 非冗余数据集构建流程 |

---

## 详细参考

| 文档 | 内容 |
|------|------|
| `references/abego-guide.md` | ABEGO详细说明 |
| `references/walker-a-analysis.md` | Walker-A完整流程 |
| `references/coiled-coil-design.md` | 卷曲螺旋设计 |
| `references/evaluation-metrics.md` | 评估指标详解 |
| `references/alphafold-limitations.md` | AlphaFold局限清单 |

---

## 来源

- **书籍**：Protein Supersecondary Structures: Methods and Protocols (3rd Ed), Springer 2025
- **系列**：Methods in Molecular Biology, Vol. 2870
- **Editor**：Alexander E. Kister

---

## 何时使用本Skill

```
用户问题涉及蛋白质结构方法选择？
→ 激活本Skill
→ 提供方法对比+工具推荐+代码示例
→ 指出常见陷阱+最佳实践
```

**本Skill不做**：简单PDB操作、通用分子可视化、仅AlphaFold预测
