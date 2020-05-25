from gcdo import *
from random import *
from timeit import *
from itertools import product

from benchmarks.TNCP_h import *

def generate_TNCP(flow_num = 20, node_num = 3, tc_num = 0, horizon = 3000,
                  edge_loss_lb = 0.08, edge_loss_ub = 0.08,
                  edge_delay_lb = 0.08, edge_delay_ub = 0.08,
                  edge_bw_lb = 500, edge_bw_ub = 500,
                  flow_loss_lb = 0.2, flow_loss_ub= 0.6,
                  flow_delay_lb = 0.2, flow_delay_ub = 0.6,
                  flow_bw_lb = 300, flow_bw_ub = 600,
                  flow_duration_lb = 20, flow_duration_ub = 80):
    # Flows
    flows = []
    for i in range(flow_num):
        src = randint(0, node_num - 1)
        rest = list(range(node_num))
        rest.remove(src)
        dst = rest[randint(0, node_num - 2)]

        loss = uniform(flow_loss_lb, flow_loss_ub)
        delay = uniform(flow_delay_lb, flow_delay_ub)
        bw = uniform(flow_bw_lb, flow_bw_ub)
        duration = uniform(flow_duration_lb, flow_duration_ub)

        start, end = 2 * i, 2 * i + 1
        if i <= 0.5 * flow_num: weight = 1e6
        else: weight = randint(1, flow_num)
        flows.append([i, start, end, src, dst, loss, delay, bw, duration, weight])

    # Edges
    edges = []
    for src in range(node_num):
        tmp_edges = []
        for dst in range(node_num):
            if src != dst:
                loss = uniform(edge_loss_lb, edge_loss_ub)
                delay = uniform(edge_delay_lb, edge_delay_ub)
                bw = uniform(edge_bw_lb, edge_bw_ub)
            else: loss, delay, bw = 0, 0, 10000
            tmp_edges.append([src, dst, loss, delay, bw])
        edges.append(tmp_edges)

    # Temporal Constraints
    tcs = []
    for i in range(tc_num):
        from_flow_idx = randint(0, flow_num-1)
        from_event_idx = 2 * from_flow_idx + randint(0, 1)
        to_flow_idx = randint(0, flow_num-1)
        to_event_idx = 2 * to_flow_idx + randint(0, 1)
        tcs.append([[from_event_idx, to_event_idx, 1]])

    print("Print Problem Statistics")
    print("Flows:", len(flows))
    [print(flow) for flow in flows]
    print("Edges:", len(edges))
    [[print(edges[i][j]) for i,j in product(range(node_num), range(node_num))]]
    print("Temporal Constraints:", len(tcs))
    [print(tc) for tc in tcs]

    return [flows, edges, tcs, node_num, horizon]

# Tests
def solve_TNCP(flows, edges, tcs, node_num, horizon, alg):
    flow_num = len(flows)
    events = list(set.union(*[set(flow[1:3]) for flow in flows]))
    event_num = len(events)
    Phi = {"Time": 1e6}
    for flow in flows:
        Phi["F%s_Order" % (flow[0])] = 1e6
        Phi["F%s_State" % (flow[0])] = flow[7]
    O = {}
    for flow in flows:
        O["F%s_Order" % (flow[0])] = \
            {"name": "F%s_Order" % (flow[0]),
             "PO": [(flow[2], flow[1])],
             "CS": ["F%s_Order" % (flow[0])],
             "MVS": ["F%s_Order" % (flow[0])],
             "MVC": 1e6}
    h = lambda L: make_TNCP_h(L, flows, edges, tcs, node_num, horizon)
    if alg == 'GCDO': return gcdo(event_num, h, Phi, O)

def benchmark():
    cases = 1
    node_num = 5
    flow_nums = [40]
    f = open("Cases%s_Nodes%s.txt"%(cases, node_num), "a")

    for flow_num in flow_nums:
        f.write("\n#Flows = %s"%(flow_num))
        for case in range(cases):
            flows, edges, tcs, node_num, horizon \
                = generate_TNCP(flow_num = flow_num, node_num = node_num, tc_num = 0, horizon = 3000,
                                  edge_loss_lb = 0.08, edge_loss_ub = 0.08,
                                  edge_delay_lb = 0.08, edge_delay_ub = 0.08,
                                  edge_bw_lb = 500, edge_bw_ub = 500,
                                  flow_loss_lb = 0.2, flow_loss_ub= 0.2,
                                  flow_delay_lb = 0.2, flow_delay_ub = 0.2,
                                  flow_bw_lb = 400, flow_bw_ub = 550,
                                  flow_duration_lb = 20, flow_duration_ub = 80)

            # GCDO
            start = default_timer()
            [L, cost, total_times] = solve_TNCP(flows, edges, tcs, node_num, horizon, 'GCDO')
            f.write("\n[GCDO]  Obj=%s #O=%s Time=%s"%(cost, total_times, default_timer() - start))
    f.close()

def test_case_1():
    #[i, start, end, src, dst, loss, delay, bw, duration, weight]
    flows = [[0, 0, 4, 0, 1, 0.5, 1, 200, 30, 1e6],
             [1, 1, 2, 0, 1, 3, 1, 360, 30, 5],
             [2, 1, 3, 0, 1, 3, 0.3, 360, 30, 3]]
    # [src, dst, loss, delay, bw]
    [0, 1, 0.1, 0.1, 500]
    edges = [[[0, 0, 0, 0, 10000], [0, 1, 0.1, 0.1, 500], [0, 2, 0.1, 0.5, 500]],
             [[1, 0, 0.1, 0.1, 500], [0, 0, 0, 0, 10000], [1, 2, 0.1, 0.1, 500]],
             [[2, 0, 0.1, 0.5, 500], [2, 1, 1, 0.1, 500], [2, 2, 0, 0, 10000]]]
    tcs = [[[2, 3, 20], [3, 2, 20]]]
    node_num = 3
    horizon = 70
    [L, cost, total_times] = solve_TNCP(flows, edges, tcs, node_num, horizon, 'GCDO')


benchmark()