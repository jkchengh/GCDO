from utils import move


def tos(n):
    n_minus1 = n - 1
    L = list(range(0, n))
    O = [L]
    P = [(0, 0, n_minus1)]
    while P:
        print("\n")
        print("L =", L)
        print("P =", P)
        (i, j, l) = P[-1]
        if j != n_minus1:
            (next_i, next_j)  = (i, j + 1)
        else:
            (next_i, next_j) = (i + 1, i + 2)
        print("(i+, j+): ", "(" + repr(next_i) + " , " + repr(next_j) + ")")
        if next_i < l:
            P[-1] = (next_i, next_j, l)
            L = move(L, next_i, next_j)
            O.append(L)
            P.append((0, 0, next_i))
            print("Move to", L)
        else:
            P.pop()
            if P:
                (parent_i, parent_j, parent_l) = P[-1]
                L = move(L, parent_j, parent_i - 1)
                print("Backtrack to", L, "by taking", "(" + repr(parent_j) + " ," + repr(parent_i - 1) + ")")
    return O