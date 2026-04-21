#!/usr/bin/env python3
"""
非冗余蛋白质数据集构建工具

基于CAFS (Culling After Full Search) 方法
出自《Protein Supersecondary Structures》第3版 Chapter 6

用法:
    python3 cafs_pipeline.py <sequence_fasta> [options]

依赖:
    pip install mmseqs2 (或使用系统mmseqs)
"""

import os
import sys
import subprocess
import argparse
import tempfile


def run_mmseqs2_cluster(input_fasta, identity=0.3, coverage=0.8, tmp_dir=None):
    """
    使用MMseqs2进行序列聚类
    
    Args:
        input_fasta: 输入FASTA文件
        identity: 最小序列一致性 (0-1)
        coverage: 最小覆盖度 (0-1)
        tmp_dir: 临时目录
    
    Returns:
        代表序列FASTA文件路径
    """
    if tmp_dir is None:
        tmp_dir = tempfile.mkdtemp(prefix='cafs_')
    
    seq_db = os.path.join(tmp_dir, 'seqDB')
    cluster_db = os.path.join(tmp_dir, 'clusterDB')
    rep_db = os.path.join(tmp_dir, 'repDB')
    
    # Step 1: 创建数据库
    subprocess.run(['mmseqs', 'createdb', input_fasta, seq_db], check=True)
    
    # Step 2: 聚类
    subprocess.run([
        'mmseqs', 'cluster', seq_db, cluster_db, tmp_dir,
        '--min-seq-id', str(identity),
        '-c', str(coverage),
        '--cov-mode', '0'
    ], check=True)
    
    # Step 3: 提取代表序列
    subprocess.run([
        'mmseqs', 'createsubdb', cluster_db, seq_db, rep_db
    ], check=True)
    
    # Step 4: 转换为FASTA
    output_fasta = input_fasta.replace('.fasta', '_nr.fasta')
    subprocess.run([
        'mmseqs', 'convert2fasta', rep_db, output_fasta
    ], check=True)
    
    print(f"非冗余数据集: {output_fasta}")
    print(f"一致性阈值: {identity*100}%")
    print(f"覆盖度阈值: {coverage*100}%")
    
    return output_fasta


def run_cdhit_cluster(input_fasta, identity=0.3):
    """
    使用CD-hit进行序列聚类（备选方案）
    
    Args:
        input_fasta: 输入FASTA文件
        identity: 序列一致性阈值
    
    Returns:
        聚类后FASTA文件路径
    """
    output_fasta = input_fasta.replace('.fasta', '_nr.fasta')
    
    # 根据一致性选择word_size
    if identity >= 0.7:
        word_size = 5
    elif identity >= 0.5:
        word_size = 4
    elif identity >= 0.4:
        word_size = 3
    elif identity >= 0.3:
        word_size = 2
    else:
        word_size = 1
    
    subprocess.run([
        'cd-hit',
        '-i', input_fasta,
        '-o', output_fasta,
        '-c', str(identity),
        '-n', str(word_size),
        '-d', '0'  # 保留完整序列名
    ], check=True)
    
    return output_fasta


def count_sequences(fasta_file):
    """统计FASTA文件中的序列数"""
    count = 0
    with open(fasta_file) as f:
        for line in f:
            if line.startswith('>'):
                count += 1
    return count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CAFS非冗余数据集构建工具')
    parser.add_argument('input', help='输入FASTA文件')
    parser.add_argument('-i', '--identity', type=float, default=0.3,
                       help='序列一致性阈值 (default: 0.3)')
    parser.add_argument('-c', '--coverage', type=float, default=0.8,
                       help='覆盖度阈值 (default: 0.8)')
    parser.add_argument('-m', '--method', default='mmseqs',
                       choices=['mmseqs', 'cdhit'],
                       help='聚类方法 (default: mmseqs)')
    
    args = parser.parse_args()
    
    input_count = count_sequences(args.input)
    print(f"输入序列数: {input_count}")
    
    if args.method == 'mmseqs':
        output = run_mmseqs2_cluster(args.input, args.identity, args.coverage)
    else:
        output = run_cdhit_cluster(args.input, args.identity)
    
    output_count = count_sequences(output)
    reduction = (1 - output_count / input_count) * 100 if input_count > 0 else 0
    
    print(f"输出序列数: {output_count}")
    print(f"冗余减少: {reduction:.1f}%")
