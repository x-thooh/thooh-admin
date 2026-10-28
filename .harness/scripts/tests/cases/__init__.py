"""反向语料：一个域一个文件，`reverse.py` 按文件名发现它们。

约束（由 `reverse.py` 的 coverage() 机器判）：文件名 = scope 的 NAME，每个文件都要导出
`NAME` 与 `cases()`；造不出样本的 code 在本文件写 `UNCOVERED = ((code, 理由),)`，不许留空。
"""
