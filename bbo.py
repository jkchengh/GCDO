from math import *

def parent(L):
    if L == list(range(len(L))): return []
    l = level(L)
    pl = L.index(l)
    return move(L.copy(), pl, l-1)

def level(L):
    for l in range(len(L)):
        if l != L[l]: return l
    return len(L) - 1

def next_child(L, C, h, f, rdo_f, inc_f):
    n = len(L)
    n_minus1 = n - 1
    lp = level(parent(L))
    # print("-- Explore Children along with ", L)
    # print("Parent Level = ", lp)
    # print("Incumbent f = ", inc_f)

    while True:
        # print("\n -- Keep Exploring and Current is ", L)

        consh, Ch = h(L)
        Cm = manifest_conflicts(L, C)
        CL = Cm + Ch
        # print("Conflicts [Cm]:", Cm)
        # print("Conflicts [Ch]:", Ch)
        C = C + Ch
        if consh:
            # calculate objective values
            if rdo_f != []:
                fU = rdo_f[lp - 1]
            else:
                fU = 0
            fA = f("assigned", L)
            fL = fU + fA
            # print("Objective %s = %s + %s" % (fL, fU, fA))
            # return if consistent and better Lren is found
            if fL < inc_f: return L, C

        lc = level(L)
        plc = L.index(lc)
        last = [plc, lc - 1]
        # print("Current Level = ", lc)
        # print("Last Move", lc, "->", plc)
        # initialize resolution
        res = [[plc, plc], [plc, plc+1]]
        if lc < lp and plc < n_minus1:
            res = [[plc, plc], [plc, plc+1]]
        elif lc < lp and plc == n_minus1:
            res = [[plc, lc-1], [lc+1, lc+2]]
        # print("Incumbent Next Move", res)
        # check consistency and extract conflicts


        # compute constituent resolution for every conflict
        for c in CL:
            # print("- Resolve Conflict:", c)
            cons_res = [[plc, lc-1], [lp, lp+1]]
            for (a, b) in c:
                idx_a, idx_b = L.index(a), L.index(b)
                if a < lp:
                    if a <= lc:
                        # print("[Type] Go to Children or Same-Level Sibling")
                        atom_res = [[plc, plc], [idx_a, idx_b]]
                    elif b == lc and (b < a):
                        # print("[Type] Go to Any Other Silbing")
                        atom_res = [[plc, lc-1], [lc+1, lc+2]]
                    else:
                        # print("[Type] Go to Some Other Siblings")
                        atom_res = [[plc, lc-1], [a, idx_b]]
                else:
                    # print("Unresolvable")
                    atom_res= [[plc, lc-1], [lp, lp + 1]]
                # print("Atom Res:", atom_res)
                # break if the conflict is resolved by the incumbent combined resolution
                if closer(atom_res, res):
                    # print("Atom Conflict can be Resolved by Incumbent")
                    cons_res = [[plc, plc], [0, 0]]
                    break
                # update the constituent resolution
                if closer(atom_res, cons_res):
                    # print("Update Constituent Res")
                    cons_res = atom_res
            # print("Constituent Res:", cons_res)
            # break when a unsolvable conflict is detected
            if cons_res == [[plc, lc-1], [lp, lp+1]]:
                # print("* No Children Can Resolve this Conflict")
                return [], C
            # update the combined resolution
            if closer(res, cons_res):
                # print("Update Incumbent Res")
                res = cons_res
            # print("Incumbent Res:", res)
        if res == [[plc, lc-1], [lp, lp+1]]:
            # print("* Exhaust All Children")
            return [], C
        L = move(L, res[0][0], res[0][1])
        L = move(L, res[1][0], res[1][1])

def closer (a, b):
    if a[0] == b[0]: # a[0] and b[0] are smae
        if a[1][0] == b[1][0]: # a[1] and b[1] moves same integer
            if a[1][1] < b[1][1]: return True # a[1] moves to closer position
            else: return False
        elif a[1][0] < b[1][0]: return True # a[1] moves smaller integer
        elif a[1][0] > b[1][0]: return False # b[1] move smaller integer

    elif a[0][1] < b[0][1]: return False # a[0] is backward and b[0] remains
    elif a[0][1] > b[0][1]: return True # a[0] remains and b[0] is backward

def manifest_conflicts(L, C):
    CL = []
    for c in C:
        manifest = True
        for (a, b) in c:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            if idx_a > idx_b:
                manifest = False
                break
        if manifest == True: CL.append(c)
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
    if i != j:
        p = newL.pop(i)
        if j == -1: newL = [p] + newL
        elif i < j: newL.insert(j, p)
        elif i > j: newL.insert(j+1, p)
    return newL

def bbo(n, h, f, C, rdo_f):
    L = list(range(n))
    inc_f, inc_L = f("all", L), L
    # print("Initial Incumbent = ", inc_L)
    L = move(L, 0, 1)
    times = 0
    while L != []:
        if L == list(range(n)): break
        times = times + 1
        fL = f("all", L)
        # print("\n")
        # print("#", times)
        # print("L =", L)
        # print("f = ", fL)
        # Update Incumbent if Better Solution Found
        if fL and fL > inc_f:
            # print("Solution Update!", inc_f, "->", fL)
            inc_f, inc_L = fL, L
        # find next child
        child, newC = next_child(L, C, h, f, rdo_f, inc_f)
        C = C + newC
        # print("Find Child:", child)
        if child == []:
            # print("Backtrack!")
            L = parent(L)
        else:
            L = child

    # print("Find", inc_f, "with", inc_L)
    return [inc_L, inc_f, C, times]


print(move([1, 2, 0, 3 ,4], 2, -1))