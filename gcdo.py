import networkx as nx

def parent(L):
    if L == list(range(len(L))): return []
    l = level(L)
    pl = L.index(l)
    return move(L.copy(), pl, l-1)

def level(L):
    for l in range(len(L)):
        if l != L[l]: return l
    return len(L) - 1

def first_resolving_move(o, L):
    print("# - Search Resolving Move for [%s]"%(o))
    n = len(L)
    nminus1 = n - 1
    l = level(L)
    (i, j) = (nminus1, nminus1 + 1)
    for (a, b) in o:
        (idx_a, idx_b) = (L.index(a), L.index(b))
        # update the move
        if (a <= l) and (n * idx_a + idx_b) < (n * i + j):
            (i, j) = (idx_a, idx_b)
    if L[i] > l:
        print("# - [Fail] Find Move (%s -> %s)"%(nminus1, nminus1+1))
        return (nminus1, nminus1 + 1)
    else:
        print("# - [Succeed] Find Move (%s -> %s)"%(i, j))
        return (i, j)

def first_reducing_move(reducing_moves, reduction, n):
    print("# - Search Reducing Move for Reduction %s"%(reduction))
    for move in reducing_moves: print("# -- Reducing [%s] through (%s -> %s)"%(move[1], move[0][0], move[0][1]))
    nminus1 = n - 1
    for i in range(len(reducing_moves)):
        reduction = reduction - reducing_moves[i][1]
        if reduction < 0:
            print("# - [Succeed] Find Move (%s -> %s)" % (reducing_moves[i][0][0], reducing_moves[i][0][1]))
            return reducing_moves[i][0]
    print("# - [Fail] Find Move (%s -> %s)" % (nminus1, nminus1 + 1))
    return (nminus1, nminus1 + 1)

def manifest_orderings(L, Phi, O):

    # find manifested orderings
    # print("- # Search Manifested Orderings")
    # for o in O.values(): print("--",o["name"])
    OL = []
    for o in O.values():
        manifest = True
        PO = o["PO"]
        for (a, b) in PO:
            (idx_a, idx_b) = (L.index(a), L.index(b))
            if idx_a > idx_b:
                manifest = False
                break
        if manifest == True: OL.append(o)
    # print("- All Manifested Ordering:")
    # print("--", [o["name"] for o in OL])
    # find disjoint manifested orderings
    G = nx.Graph()
    G.add_nodes_from(list(range(len(OL))))
    for i in range(len(OL)):
        for j in range(i):
            oi, oj = OL[i], OL[j]
            disjoint = True
            for phi in set.intersection(set(oi["CS"]), set(oj["CS"])):
                if Phi[phi] < 1e6:
                    disjoint = False
                    break
            if disjoint: G.add_edge(i, j)
    inc_clique, inc_cost = [], 0
    for clique in nx.find_cliques(G):
        cost = sum([OL[i]["MVC"] for i in clique])
        if cost > inc_cost: inc_clique, inc_cost = [OL[i] for i in clique], cost

    dOL = {}
    for o in inc_clique: dOL[o["name"]] = o

    # print("- Disjoint Manifested Ordering:")
    # print("--", [o["name"] for o in inc_clique])

    return dOL

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

def gcdo(n, h, Phi, O):
    nminus1 = n - 1
    (L, i, j) = (list(range(n)), 0, 0)
    (inc_L, inc_cost) = ([], 1e6)
    times = 0
    while L != []:
        print("\n")
        print("#", times)
        print("L = %s, Status: (%s -> %s)"%(L, i, j))
        times = times + 1
        OL = manifest_orderings(L, Phi, O)
        costL = sum([o["MVC"] for o in OL.values()])
        print("* [Estimation] Cost = ", costL)
        print("* [Estimation] Disjoint Manifested Ordering:", [o["name"] for o in OL.values()])

        # Solve for True Cost if the Estimation is Very Low
        if costL <= inc_cost:
            costL, OL = h(L)
            O.update(OL)
            print("* [True] Cost = ", costL)
            print("* [True] Disjoint Manifested Ordering:", [o["name"] for o in OL.values()])
            OL = manifest_orderings(L, Phi, O)
            print("* [Refine] Cost = ", sum([o["MVC"] for o in OL.values()]))
            print("* [Refine] Disjoint Manifested Ordering:", [o["name"] for o in OL.values()])


        # Update Incumbent if Better Solution Found
        if costL < inc_cost:
            print("* Solution Update!", inc_cost, "->", costL)
            inc_L, inc_cost = L, costL
        if inc_cost <= 1e-3:
            print("* Optimal Solution Returned!", inc_cost, "->", costL)
            return [inc_L, inc_cost, times]
        reduction = costL - inc_cost
        print("* Desired Reduction = %s"%(reduction))
        l = level(L)
        # Standard Next Move
        # Same-cluster Sibling
        if nminus1 * i + j == nminus1 * l: next_i, next_j = L.index(l), L.index(l)+1
        # Child with the same cluster
        elif (j < nminus1): (next_i, next_j) = (i, j + 1)
        # Child in the next cluster
        else: (next_i, next_j) = (i + 1, i + 2)
        print("# Standard Next Move (%s -> %s)"%(next_i, next_j))
        # Find Reducing Move
        reducing_moves = [((next_i, next_j), 1e6)] + \
                         [(first_resolving_move(o["PO"], L), o["MVC"]) for o in OL.values()]
        reducing_moves.sort(key=lambda e: n * e[0][0] + e[0][1])
        next_i, next_j = first_reducing_move(reducing_moves, reduction+1e6, n)
        if L[next_i] <= l:
            i, j = 0, 0
            print("# Apply (%s -> %s)"%(next_i, next_j))
            L = move(L, next_i, next_j)
        else:
            i, j = l, nminus1
            L = parent(L)
            print("# Backtrack")

    print("* Incumbent Solution Returned!", inc_cost, "->", costL)
    return [inc_L, inc_cost, times]

