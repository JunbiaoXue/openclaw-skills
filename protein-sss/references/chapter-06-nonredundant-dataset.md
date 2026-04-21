# Chapter 6: 非冗余数据集构建 (CAFS)

## 概述

CAFS (Culling After Full Search) 方法解决蛋白质结构数据集中的冗余问题。

## 核心问题

> "哪些结构应该被视为近乎相同的？"

即使替换一个氨基酸也可能严重影响蛋白质结构和功能，因此需要精细的去冗余策略。

## CAFS方法流程

```
1. 全量搜索 → 收集所有候选结构
2. 序列聚类 → MMseqs2 / CD-hit
3. 结构验证 → 检查序列相似但结构不同的案例
4. 选择代表 → 考虑分辨率、完整性、构象状态
```

### 详细步骤

```python
def cafs_pipeline(pdb_dir, identity_threshold=0.3):
    """
    CAFS非冗余数据集构建流程
    
    Args:
        pdb_dir: PDB文件目录
        identity_threshold: 序列一致性阈值
    
    Returns:
        非冗余数据集
    """
    # Step 1: 全量搜索
    all_chains = extract_all_chains(pdb_dir)
    
    # Step 2: 序列聚类
    # 使用MMseqs2进行快速聚类
    clusters = mmseqs2_cluster(
        all_chains, 
        min_seq_id=identity_threshold,
        coverage=0.8
    )
    
    # Step 3: 代表序列选择
    representatives = []
    for cluster in clusters:
        # 优先选择:
        # 1. 最高分辨率
        # 2. 最少缺失残基
        # 3. 野生型(非突变体)
        best = select_representative(cluster)
        representatives.append(best)
    
    # Step 4: 结构验证
    # 检查高序列相似但结构不同的案例
    suspicious_pairs = find_structure_divergence(representatives)
    
    # Step 5: 精细化处理
    final_set = resolve_suspicious_pairs(representatives, suspicious_pairs)
    
    return final_set
```

## 推荐阈值

| 用途 | Identity阈值 | 说明 |
|------|-------------|------|
| 高冗余去除 | 90% | 保留同源变异 |
| 中等去冗余 | 40-50% | 同家族代表 |
| 低冗余(推荐) | 25-30% | 折叠级别代表 |
| 超低冗余 | 20% | 超折叠级别 |

## Walker-A Motif 的发现

通过CAFS方法，作者发现了Walker-A motif（GXXXXGK[T/S]）的关键修正：

```
修正1: Walker-A应扩展为 GXXXXGK[TSG]
       - G出现在第8位(核苷酸激酶)

修正2: 非典型序列也能采用Walker-A构象
       - TYPKSGTT (磺基转移酶，缺少保守K)

修正3: Walker-A构象对氨基酸替换的容忍度
       比序列保守性暗示的更高
```

## 实用命令

```bash
# 使用MMseqs2聚类
mmseqs createdb sequences.fasta seqDB
mmseqs cluster seqDB clusterDB tmp --min-seq-id 0.3 -c 0.8
mmseqs createseqdb seqDB clusterDB repDB

# 使用CD-hit聚类
cd-hit -i sequences.fasta -o clustered.fasta -c 0.3 -n 5
```
