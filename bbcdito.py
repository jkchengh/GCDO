from math import *

def next_move(L, C, i, j, l):
    n = len(L)
    n_minus1 = n - 1
    # compute the constituent resolution for search status
    # as the incumbent combined resolution

    if (n_minus1 * i + j >= n_minus1 * l):
        idx_l = L.index(l)
        (next_i, next_j) = (idx_l, idx_l + 1)
    elif (j < n_minus1):
        (next_i, next_j) = (i, j + 1)
    else:
        (next_i, next_j) = (i + 1, i + 2)
    # print("Constituent Resolution", next_i, "->", next_j, "for statuts (", i, j, l, ")")
    # compute constituent resolution for every conflict
    for c in C:
        (cons_i, cons_j) = (n_minus1, n_minus1 + 1)
        for (a, b) in c:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            # break if the conflict is resolved by the incumbent combined resolution
            if (a <= l) and (n * idx_a + idx_b) <= (n * next_i + next_j):
                (cons_i, cons_j) = (0, 0)
                break
            # update the constituent resolution
            if (a <= l) and (n * idx_a + idx_b) < (n * cons_i + cons_j):
                (cons_i, cons_j) = (idx_a, idx_b)
        # print("Constituent Resolution", cons_i, "->", cons_j, "for conflict", c)
        # break when a unsolvable conflict is detected
        if cons_i > l: return (n_minus1, n_minus1 + 1)
        # update the combined resolution
        if (n * next_i + next_j) < (n * cons_i + cons_j):
            (next_i, next_j) = (cons_i, cons_j)
    # print("Combined Resolution:", next_i, "->", next_j)
    return (next_i, next_j)

def manifest_conflicts(L, C):
    CL = []
    for c in C:
        manifest = True
        for (a, b) in c:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            if idx_a > idx_b:
                manifest = False
                break
        if manifest == True: C.append(c)
        # print("Conflict:", c, "for ", phi)
    # print("Conflict:", C)
    return CL

def negate(C):
    Phi = []
    for c in C:
        phi = []
        for (a, b) in c:
            phi.append((b, a))
        Phi.append(phi)
    return Phi

def move(L, i, j):
    newL = L.copy()
    p = newL.pop(i)
    if i < j:
        newL.insert(j, p)
    else:
        newL.insert(j+1, p)
    return newL

def bbcdito(L, P, h, f, C, rdo_f):
    n_minus1 = len(L) - 1
    times = 0
    inc_f, inc_L = - inf, []
    while P:
        times = times + 1
        print("\n")
        print("#", times)
        print("L =", L)
        print("P =", P)
        CL = manifest_conflicts(L, C)
        h_consistent, Ch = h(L)
        if CL == [] and h_consistent:
            print("Solution Found")
            # Update Incumbent if Better Solution Found
            fL = f('all', L)
            print("Objective = ", fL)
            if fL > inc_f: inc_f, inc_L = fL, L
        (i, j, l) = P[-1]
        print("Conflicts [CL]:", CL)
        print("Conflicts [Ch]:", Ch)
        (next_i, next_j) = next_move(L, Ch+CL, i, j, l)

        print("Combined Resolution:", next_i, "->", next_j)
        if next_i < l:
            L = move(L, next_i, next_j)
            P[-1] = (next_i, next_j, l)
            P.append((0, 0, next_i))
            print("[Type 1] Move to", L)
        else:
            P.pop()
            if P:
                (parent_i, parent_j, parent_l) = P[-1]
                L = move(L, parent_j, parent_i - 1)
                print("Backtrack to", L, "by taking", "(" + repr(parent_j) + " ," + repr(parent_i - 1) + ")")
                if l < next_i < n_minus1:
                    print("[Type 2] Update Parent's Status for Moving to a Sibling")
                    P[-1] = (parent_i, next_j - 1, parent_l)
                if next_i == n_minus1:
                    print("[Type 3] Update Parent's Status for Pruning")
                    P[-1] = (parent_i + 1, parent_i + 1, parent_l)

    return [inc_L, inc_f, C]
