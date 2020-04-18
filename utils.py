def move(L, i, j):
    newL = L.copy()
    p = newL.pop(i)
    if i < j:
        newL.insert(j, p)
    else:
        newL.insert(j+1, p)
    return newL