#!/usr/bin/env python3
"""
Walker-A Motif 检测工具

检测蛋白质序列中的Walker-A motif (GXXXXGK[T/S])
基于《Protein Supersecondary Structures》第3版 Chapter 6

Walker-A motif 是NTP结合蛋白的标志性序列，
通常位于β-α-β超二级结构的β-α连接处。

用法:
    python3 detect_walker_a.py <fasta_file>
    python3 detect_walker_a.py --sequence "GLYALGKTPRAGVKGKT"
"""

import re
import sys
import argparse


# Walker-A motif 模式
CANONICAL_PATTERN = r'G.{4}GK[TS]'       # 经典 Walker-A
EXTENDED_PATTERN = r'G.{4}GK[TSG]'       # 扩展 Walker-A (含核苷酸激酶)
BROAD_PATTERN = r'G.{3,5}G.K[TS]'        # 宽松模式


def detect_walker_a(sequence, pattern='canonical'):
    """
    检测Walker-A motif
    
    Args:
        sequence: 氨基酸序列(大写)
        pattern: 检测模式
            - 'canonical': GXXXXGK[T/S] (经典)
            - 'extended': GXXXXGK[T/S/G] (扩展)
            - 'broad': GXXX-XXXXG.K[T/S] (宽松)
    
    Returns:
        匹配列表
    """
    patterns = {
        'canonical': CANONICAL_PATTERN,
        'extended': EXTENDED_PATTERN,
        'broad': BROAD_PATTERN
    }
    
    regex = patterns.get(pattern, CANONICAL_PATTERN)
    matches = []
    
    for match in re.finditer(regex, sequence):
        start = match.start()
        end = match.end()
        motif_seq = match.group()
        
        # 分析各位置
        analysis = analyze_walker_a_positions(motif_seq)
        
        matches.append({
            'start': start + 1,  # 1-based
            'end': end,
            'sequence': motif_seq,
            'pattern_type': pattern,
            **analysis
        })
    
    return matches


def analyze_walker_a_positions(motif_seq):
    """
    分析Walker-A motif各位置特征
    
    G X X X X G K T/S
    | | | | | | | |
    1 2 3 4 5 6 7 8
    
    关键位置:
    - G1: 起始甘氨酸 (构象转折)
    - X2-X5: 变异位点 (X3偏好G)
    - G6: 关键甘氨酸 (主链柔性的保证)
    - K7: 保守赖氨酸 (与磷酸基团作用)
    - T/S8: 羟基残基 (与Mg2+配位)
    """
    if len(motif_seq) < 8:
        return {}
    
    return {
        'G1': motif_seq[0],  # 必须为G
        'X2': motif_seq[1],
        'X3': motif_seq[2],  # 偏好G
        'X4': motif_seq[3],
        'X5': motif_seq[4],
        'G6': motif_seq[5],  # 必须为G
        'K7': motif_seq[6],  # 通常为K
        'pos8': motif_seq[7],  # T/S (扩展可为G/E)
        'x3_is_glycine': motif_seq[2] == 'G',
        'is_strict_canonical': (
            motif_seq[0] == 'G' and 
            motif_seq[5] == 'G' and 
            motif_seq[6] == 'K' and 
            motif_seq[7] in 'TS'
        )
    }


def classify_walker_a_type(match_info):
    """
    分类Walker-A motif类型
    
    类型:
    - 'classic': 经典NTPase (GXXXXGK[T/S])
    - 'kinase': 核苷酸激酶 (GXXXXGKG)
    - 'non_canonical': 非典型但构象类似
    """
    seq = match_info['sequence']
    
    if match_info.get('is_strict_canonical'):
        return 'classic'
    elif len(seq) >= 8 and seq[7] == 'G':
        return 'kinase'
    else:
        return 'non_canonical'


def parse_fasta(fasta_file):
    """解析FASTA文件"""
    sequences = {}
    current_id = None
    current_seq = []
    
    with open(fasta_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if current_id:
                    sequences[current_id] = ''.join(current_seq)
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line.upper())
    
    if current_id:
        sequences[current_id] = ''.join(current_seq)
    
    return sequences


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Walker-A Motif检测工具')
    parser.add_argument('input', nargs='?', help='FASTA文件路径')
    parser.add_argument('--sequence', '-s', help='直接输入序列')
    parser.add_argument('--pattern', '-p', default='extended',
                       choices=['canonical', 'extended', 'broad'],
                       help='检测模式 (default: extended)')
    
    args = parser.parse_args()
    
    if args.sequence:
        sequences = {'input': args.sequence.upper()}
    elif args.input:
        sequences = parse_fasta(args.input)
    else:
        parser.print_help()
        sys.exit(1)
    
    total_motifs = 0
    for seq_id, sequence in sequences.items():
        matches = detect_walker_a(sequence, args.pattern)
        total_motifs += len(matches)
        
        if matches:
            print(f"\n{'='*60}")
            print(f"Sequence: {seq_id} (length: {len(sequence)})")
            print(f"Walker-A motifs found: {len(matches)}")
            print(f"{'='*60}")
            
            for m in matches:
                wa_type = classify_walker_a_type(m)
                print(f"\n  Position {m['start']}-{m['end']}: {m['sequence']}")
                print(f"  Type: {wa_type}")
                print(f"  G1={m.get('G1','-')} X2={m.get('X2','-')} "
                      f"X3={m.get('X3','-')} X4={m.get('X4','-')} "
                      f"X5={m.get('X5','-')} G6={m.get('G6','-')} "
                      f"K7={m.get('K7','-')} Pos8={m.get('pos8','-')}")
                if m.get('x3_is_glycine'):
                    print(f"  Note: X3=G (glycine enrichment at position 3)")
        
    if total_motifs == 0:
        print("No Walker-A motifs detected.")
