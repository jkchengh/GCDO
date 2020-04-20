
def apsp(d):
    num = len(d[0])
    for k in range(num):
        for i in range(num):
            for j in range(num):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d

def orders(d):
    d = apsp(d)
    orders = []
    num = len(d[0])
    for i in range(num):
        for j in range(num):
            if d[i][j] < 0: orders.append([(j, i)])
    return orders