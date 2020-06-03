from gcdo import *
from random import *
from datetime import datetime

from benchmarks.TNCP_h import *

def initial_order_manage(events, idx, group_size):
    group_idx = int(idx / group_size)
    in_group_idx = idx % group_size
    start_idx = (group_idx * 2 * group_size) + in_group_idx
    end_idx = (group_idx * 2 * group_size) + in_group_idx + group_size
    # print(idx, group_idx, in_group_idx, start_idx, end_idx)
    return events[start_idx], events[end_idx]

def generate_TNCP(flow_num = 20, node_num = 3, tc_num = 0, horizon = 3000,
                  edge_loss_lb = 0.08, edge_loss_ub = 0.08,
                  edge_delay_lb = 0.08, edge_delay_ub = 0.08,
                  edge_bw_lb=500, edge_bw_ub=500,
                  flow_loss_lb=0.2, flow_loss_ub=0.6,
                  flow_delay_lb=0.2, flow_delay_ub=0.6,
                  flow_bw_lb=300, flow_bw_ub=600,
                  flow_duration_lb = 20, flow_duration_ub = 80):
    # Flows
    flows = []
    events = list(range(2 * flow_num))
    # shuffle(events)
    seed(datetime.now())
    for i in range(flow_num):
        src = randint(0, node_num - 1)
        rest = list(range(node_num))
        rest.remove(src)
        dst = rest[randint(0, node_num - 2)]

        loss = uniform(flow_loss_lb, flow_loss_ub)
        delay = uniform(flow_delay_lb, flow_delay_ub)
        bw = uniform(flow_bw_lb, flow_bw_ub)
        duration = uniform(flow_duration_lb, flow_duration_ub)

        start, end = initial_order_manage(events, i, 5)
        if i > 0.8 * flow_num: weight = 1e6
        else: weight = 1 # randint(1, 3)
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
        tcs.append([1e6, [[from_event_idx, to_event_idx, 1,]]])


    return [flows, edges, tcs, node_num, horizon]

def print_TNCP(flows, edges, tcs, node_num):
    print("Print Problem Statistics")
    print("Flows:", len(flows))
    [print(flow) for flow in flows]
    print("Edges:", len(edges))
    [[print(edges[i][j]) for i, j in product(range(node_num), range(node_num))]]
    print("Temporal Constraints:", len(tcs))
    [print(tc) for tc in tcs]

# Tests
def solve_TNCP(flows, edges, tcs, PO, node_num, horizon, path = "log", method = "GCDO", timeout = 20):
    flow_num = len(flows)
    events = list(set.union(*[set(flow[1:3]) for flow in flows]))
    event_num = len(events)
    Phi = {"Time": 1e6}
    for flow in flows:
        Phi["F%s_Order" % (flow[0])] = 1e6
        Phi["F%s_State" % (flow[0])] = flow[7]
    for idx in range(len(tcs)):
        Phi["T%s" % (idx)] = tcs[idx][0]

    O = {}
    for flow in flows:
        O["F%s_Order" % (flow[0])] = \
            {"name": "F%s_Order" % (flow[0]),
             "PO": [(flow[2], flow[1])],
             "CS": ["F%s_Order" % (flow[0])],
             "MVS": ["F%s_Order" % (flow[0])],
             "MVC": 1e6}
    for i in range(len(PO)):
        weight, o = PO[i]
        O["O%s" % (i)] = \
            {"name": "O%s" % (i),
             "PO": [(q[1], q[0]) for q in o],
             "CS": ["O%s" % (i)],
             "MVS": ["O%s" % (i)],
             "MVC": weight}

    h = lambda L: make_TNCP_h(L, flows, edges, tcs, PO, node_num, horizon)

    if method == "GCDO": [L, cost] = gcdo(event_num, h, Phi, O, path, timeout)
    elif method == "CDITO": [L, cost] = cdito(event_num, h, Phi, O, path, timeout)


    return [L, cost]






