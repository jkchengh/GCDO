from utils import move


def next_move(L, C, i, j, l):
    n = len(L)
    n_minus1 = n - 1
    # compute the constituent kernel for search status
    # as the incumbent combined kenerl

    if (n_minus1 * i + j >= n_minus1 * l):
        idx_l = L.index(l)
        (next_i, next_j) = (idx_l, idx_l + 1)
    elif (j < n_minus1):
        (next_i, next_j) = (i, j + 1)
    else:
        (next_i, next_j) = (i + 1, i + 2)
    print("Constituent Kernel", next_i, "->", next_j, "for statuts (", i, j, l, ")")
    # compute constituent kernel for every conflict
    for c in C:
        (cons_i, cons_j) = (n_minus1, n_minus1 + 1)
        for (a, b) in c:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            # break if the conflict is resolved by the incumbent combined kernel
            if (a <= l) and (n * idx_a + idx_b) <= (n * next_i + next_j):
                (cons_i, cons_j) = (0, 0)
                break
            # update the constituent kernel
            if (a <= l) and (n * idx_a + idx_b) < (n * cons_i + cons_j):
                (cons_i, cons_j) = (idx_a, idx_b)
        print("Constituent Kernel", cons_i, "->", cons_j, "for conflict", c)
        # break when a unsolvable conflict is detected
        if cons_i > l: return (n_minus1, n_minus1 + 1)
        # update the combined kernel
        if (n * next_i + next_j) < (n * cons_i + cons_j):
            (next_i, next_j) = (cons_i, cons_j)
    # print("Combined Kernel:", next_i, "->", next_j)
    return (next_i, next_j)


def phi_consistent(L, Phi):
    for phi in Phi:
        phi_consistent = False
        for (a, b) in phi:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            if idx_a < idx_b:
                phi_consistent = True
                break
        if not phi_consistent:
            # print("Inconsistent! Violate ", phi)
            return False
    # print("Phi Consistent!")
    return True


def phi_conflicts(L, Phi):
    C = []
    for phi in Phi:
        c = []
        for (a, b) in phi:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            c.append((b, a))
            if idx_a < idx_b:
                c = []
                break
        # print("Conflict:", c, "for ", phi)
        if c: C.append(c)
    print("Conflict:", C)
    return C


def conflicts2clauses(C):
    Phi = []
    for c in C:
        phi = []
        for (a, b) in c:
            phi.append((b, a))
        Phi.append(phi)
    return Phi


def cdito(L, P, Phi, h):
    n_minus1 = len(L) - 1
    times = 0
    while P and times < 100:
        times = times + 1
        print("\n")
        print("#", times)
        print("L =", L)
        print("P =", P)
        # print("Phi = ", Phi)
        if phi_consistent(L, Phi):
            (h_consistent, Ch) = h(L)
            if h_consistent:
                print("Solution Found")
                return L
            else:
                Phi = Phi + conflicts2clauses(Ch)
        (i, j, l) = P[-1]
        C = phi_conflicts(L, Phi)
        (next_i, next_j) = next_move(L, C, i, j, l)
        print("Combined Kernel:", next_i, "->", next_j)
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
    print("No Solution!")
    return []