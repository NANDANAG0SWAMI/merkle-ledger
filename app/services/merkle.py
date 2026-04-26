import hashlib
from typing import List, Tuple

def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def _pair_hash(a: str, b: str) -> str:
    return _hash(a + b)

def build_tree(leaves: List[str]) -> List[List[str]]:
    if not leaves:
        return []
    level = leaves[:]
    if len(level) % 2 == 1:
        level.append(level[-1])
    levels = [level]
    while len(level) > 1:
        level = [_pair_hash(level[i], level[i+1]) for i in range(0, len(level), 2)]
        if len(level) > 1 and len(level) % 2 == 1:
            level.append(level[-1])
        levels.append(level)
    return levels

def merkle_root(leaves: List[str]) -> str:
    levels = build_tree(leaves)
    return levels[-1][0] if levels else ""

def inclusion_proof(leaves: List[str], index: int) -> Tuple[str, List[str]]:
    levels = build_tree(leaves)
    root = levels[-1][0]
    proof = []
    idx = index
    for level in levels[:-1]:
        sibling = idx ^ 1
        if sibling < len(level):
            proof.append(level[sibling])
        idx //= 2
    return root, proof

def verify_proof(leaf: str, proof: List[str], root: str, index: int) -> bool:
    current = leaf
    idx = index
    for sibling in proof:
        if idx % 2 == 0:
            current = _pair_hash(current, sibling)
        else:
            current = _pair_hash(sibling, current)
        idx //= 2
    return current == root