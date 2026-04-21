#!/usr/bin/env python3
"""
ABEGO构象分类工具

将蛋白质主链φ/ψ角转换为ABEGO表示
基于《Protein Supersecondary Structures》第3版 Chapter 6

用法:
    python3 abego_classify.py <pdb_file> [chain_id]
"""

import sys
import math


def phi_psi_to_abego(phi, psi):
    """
    将φ,ψ角转换为ABEGO状态
    
    A = α区域 (右旋α-螺旋)
    B = β区域 (β-折叠)  
    E = 扩展β (左旋β)
    G = 左旋α (左旋α-螺旋)
    O = 其他 (cis peptide等)
    
    Args:
        phi: φ角 (度)
        psi: ψ角 (度)
    
    Returns:
        ABEGO状态字符
    """
    # 归一化到 [-180, 180]
    phi = ((phi + 180) % 360) - 180
    psi = ((psi + 180) % 360) - 180
    
    if -90 < phi < -30 and -90 < psi < -10:
        return 'A'  # α-helix
    elif -180 < phi < -60 and 90 < psi < 180:
        return 'B'  # β-strand
    elif 50 < phi < 90 and -90 < psi < -10:
        return 'G'  # left-handed α
    elif -90 < phi < -30 and 120 < psi < 180:
        return 'E'  # extended β
    else:
        return 'O'  # other


def abego_string(phi_psi_list):
    """
    将φ/ψ角列表转换为ABEGO字符串
    
    Args:
        phi_psi_list: [(phi, psi), ...] 列表
    
    Returns:
        ABEGO字符串
    """
    return ''.join(phi_psi_to_abego(phi, psi) for phi, psi in phi_psi_list)


def classify_pdb(pdb_file, chain_id='A'):
    """
    从PDB文件提取ABEGO分类
    
    需要安装: pip install BioPython
    
    Args:
        pdb_file: PDB文件路径
        chain_id: 链ID
    
    Returns:
        ABEGO字符串和残基信息
    """
    try:
        from Bio.PDB import PDBParser
    except ImportError:
        print("需要安装BioPython: pip install biopython")
        sys.exit(1)
    
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure('protein', pdb_file)
    
    results = []
    for model in structure:
        for chain in model:
            if chain.id != chain_id:
                continue
            
            residues = [r for r in chain if r.has_id('N') and r.has_id('CA') and r.has_id('C')]
            
            for i in range(1, len(residues) - 1):
                prev = residues[i-1]
                curr = residues[i]
                next_res = residues[i+1]
                
                try:
                    # 计算φ和ψ角
                    from Bio.PDB.vectors import calc_dihedral
                    
                    # φ: C(i-1) - N(i) - CA(i) - C(i)
                    phi = math.degrees(calc_dihedral(
                        prev['C'].get_vector(),
                        curr['N'].get_vector(),
                        curr['CA'].get_vector(),
                        curr['C'].get_vector()
                    ))
                    
                    # ψ: N(i) - CA(i) - C(i) - N(i+1)
                    psi = math.degrees(calc_dihedral(
                        curr['N'].get_vector(),
                        curr['CA'].get_vector(),
                        curr['C'].get_vector(),
                        next_res['N'].get_vector()
                    ))
                    
                    abego = phi_psi_to_abego(phi, psi)
                    
                    results.append({
                        'residue': curr.get_resname(),
                        'number': curr.get_id()[1],
                        'phi': phi,
                        'psi': psi,
                        'abego': abego
                    })
                except Exception:
                    results.append({
                        'residue': curr.get_resname(),
                        'number': curr.get_id()[1],
                        'phi': None,
                        'psi': None,
                        'abego': 'O'
                    })
    
    return results


def detect_walker_a(abego_string, sequence):
    """
    在ABEGO字符串中检测Walker-A motif
    
    Walker-A特征构象: EBBGAG 或 BBBGAG
    Walker-A特征序列: GXXXXGK[T/S]
    
    Args:
        abego_string: ABEGO构象字符串
        sequence: 对应氨基酸序列
    
    Returns:
        Walker-A motif列表
    """
    import re
    
    motifs = []
    
    # 构象模式检测
    conf_pattern = re.compile(r'[EB]BBGAG')
    for match in conf_pattern.finditer(abego_string):
        start = match.start()
        end = match.end()
        seq_fragment = sequence[start:end] if start < len(sequence) else ''
        
        # 检查序列模式
        seq_pattern = re.search(r'G.{4}GK[TS]', seq_fragment)
        
        motifs.append({
            'start': start,
            'end': end,
            'abego': match.group(),
            'sequence': seq_fragment,
            'is_canonical_walker_a': seq_pattern is not None
        })
    
    return motifs


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python3 abego_classify.py <pdb_file> [chain_id]")
        print("示例: python3 abego_classify.py protein.pdb A")
        sys.exit(1)
    
    pdb_file = sys.argv[1]
    chain_id = sys.argv[2] if len(sys.argv) > 2 else 'A'
    
    results = classify_pdb(pdb_file, chain_id)
    
    # 输出ABEGO字符串
    abego_str = ''.join(r['abego'] for r in results)
    seq_str = ''.join(r['residue'] for r in results)
    
    print(f"Chain: {chain_id}")
    print(f"Sequence: {seq_str}")
    print(f"ABEGO:    {abego_str}")
    
    # 检测Walker-A
    walker_a = detect_walker_a(abego_str, seq_str)
    if walker_a:
        print(f"\nWalker-A motifs found: {len(walker_a)}")
        for m in walker_a:
            print(f"  Position {m['start']}-{m['end']}: {m['abego']} / {m['sequence']} "
                  f"({'canonical' if m['is_canonical_walker_a'] else 'non-canonical'})")
    else:
        print("\nNo Walker-A motifs detected.")
