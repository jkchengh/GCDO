from crdo import *
from random import *
from itertools import product

from benchmarks.network_h import *
from benchmarks.network_f import *

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

        if i <= 0.5 * flow_num: weight = -1e6
        else: weight = - randint(1, flow_num)
        flows.append([i, src, dst, loss, delay, bw, duration, weight])

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
        tcs.append([from_event_idx, to_event_idx])

    print("Print Problem Statistics")
    print("Flows:", len(flows))
    [print(flow) for flow in flows]
    print("Edges:", len(edges))
    [[print(edges[i][j]) for i,j in product(range(node_num), range(node_num))]]
    print("Temporal Constraints:", len(tcs))
    [print(tc) for tc in tcs]

    return [flows, edges, tcs, node_num, horizon]

def solve_TNCP(flows, edges, tcs, node_num, horizon):
    flow_num = len(flows)
    event_num = 2 * flow_num
    h = lambda L: make_TNCP_h(L, flows, edges, tcs, node_num, horizon)
    f = lambda portion, L: make_TNCP_f(portion, L, flows, edges, tcs, node_num, horizon)
    L = crdo(1, event_num, 2, h, f)
    # L = bbo(event_num, h, f, [], [])
    return L

flows, edges, tcs, node_num, horizon = generate_TNCP()

solve_TNCP(flows, edges, tcs, node_num, horizon)