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
    # print("Conflict:", C)
    return C
