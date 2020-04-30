from bbo import *

def crdo(n_min, n, n_step, h, f):
    C = []
    rdo_f = [0 for _ in range(n)]
    for l in range(n_min, n, n_step):
        # print("\n")
        # print("# Subtree with Level", l)
        total_times = 0
        L, fl, Cl, times = bbo(l+1, h, f, C, rdo_f)
        rdo_f[l:l + n_step] = [fl] * n_step
        total_times = total_times + 1
        if fl <= -1e6:
            # print("No Solution")
            return [False, -1e6, total_times]
        else: C = C + Cl

    # print("Find Solution [%s] with Objective [%s]"%(L, rdo_f[-1]))
    return [L, rdo_f[-1], total_times]