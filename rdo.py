from bbcdito import *
from math import *
def rdo(n_min, n, n_step, h, f):
    C = []
    rdo_f = [0 for _ in range(n)]
    for l in range(n_min, n, n_step):
        print("\n")
        print("# Subtree with Level", l)
        L, rdo_f[l], Cl = bbcdito(l+1, h, f, C, rdo_f)
        if L == []: return False
        else: C = C + Cl

    print("Find Solution [%s] with Objective [%s]"%(L, rdo_f[-1]))
    return L