from benchmarks.network import *

# only consistency
def gcdo_test1():

    #[i, start, end, src, dst, loss, delay, bw, duration, weight]
    flows = [[0, 0, 4, 0, 1, 0.5, 1, 200, 30, 1e6],
             [1, 1, 2, 0, 1, 3, 1, 360, 30, 5],
             [2, 1, 3, 0, 1, 3, 0.3, 360, 30, 3]]
    # [src, dst, loss, delay, bw]
    edges = [[[0, 0, 0, 0, 10000], [0, 1, 0.1, 0.1, 500], [0, 2, 0.1, 0.5, 500]],
             [[1, 0, 0.1, 0.1, 500], [0, 0, 0, 0, 10000], [1, 2, 0.1, 0.1, 500]],
             [[2, 0, 0.1, 0.5, 500], [2, 1, 1, 0.1, 500], [2, 2, 0, 0, 10000]]]
    tcs = [[1e6, [[2, 3, 20], [3, 2, 20]]]]
    PO = []
    node_num = 3
    horizon = 70
    [L, cost] = solve_TNCP(flows, edges, tcs, PO, node_num, horizon)

# 16 interations
def gcdo_test2():
    #[i, start, end, src, dst, loss, delay, bw, duration, weight]
    flows = [[0, 0, 4, 0, 1, 0.5, 1, 200, 30, 1e6],
             [1, 1, 2, 0, 1, 3, 1, 360, 30, 5],
             [2, 1, 3, 0, 1, 3, 0.3, 360, 30, 3],
             [3, 0, 4, 0, 1, 3, 1, 360, 30, 1e6]]
    # [src, dst, loss, delay, bw]
    edges = [[[0, 0, 0, 0, 10000], [0, 1, 0.1, 0.1, 500], [0, 2, 0.1, 0.5, 500]],
             [[1, 0, 0.1, 0.1, 500], [0, 0, 0, 0, 10000], [1, 2, 0.1, 0.1, 500]],
             [[2, 0, 0.1, 0.5, 500], [2, 1, 1, 0.1, 500], [2, 2, 0, 0, 10000]]]
    tcs = [[1e6, [[2, 3, 20], [3, 2, 20]]],
           [2, [[4, 1, -70]]]]
    PO = [[1e6, [(0, 4)]],
          [1e6, [(1, 4)]],
          [1e6, [(2, 4)]],
          [1e6, [(3, 4)]]]
    node_num = 3
    horizon = 100
    [L, cost] = solve_TNCP(flows, edges, tcs, PO, node_num, horizon)


# simple enumerate all events
def gcdo_test3():
    #[i, start, end, src, dst, loss, delay, bw, duration, weight]
    flows = [[0, 0, 1, 0, 1, 100, 100, 3000, 1, 1e6],
             [1, 2, 3, 0, 1, 100, 100, 3000, 1, 1e6]]
    # [src, dst, loss, delay, bw]
    edges = [[[0, 0, 0, 0, 10000], [0, 1, 0.1, 0.1, 500], [0, 2, 0.1, 0.5, 500]],
             [[1, 0, 0.1, 0.1, 500], [0, 0, 0, 0, 10000], [1, 2, 0.1, 0.1, 500]],
             [[2, 0, 0.1, 0.5, 500], [2, 1, 1, 0.1, 500], [2, 2, 0, 0, 10000]]]
    tcs = []
    PO = []
    node_num = 3
    horizon = 100
    [L, cost] = solve_TNCP(flows, edges, tcs, PO, node_num, horizon)


gcdo_test2()