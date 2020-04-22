from math import *
from gurobi import *
from itertools import product

def make_TNCP_h(L, flows, edges, tcs, node_num, horizon):
    event_num = len(L)
    flow_num = floor(event_num/2)
    flows = [flows[idx] for idx in range(flow_num) if flows[idx][7] == -1e6]
    events = [2 * flow[0] for flow in flows] + [2 * flow[0] + 1 for flow in flows]
    tcs = [tcs[i] for i in range(len(tcs))
           if tcs[i][0] in events and tcs[i][1] in events]
    event_num = len(events)
    print("-- Check Mandatory Constraints")
    print("Mandatory Flows:", [flow[0] for flow in flows])
    print("Mandatory Events:", events)
    if events == []:
        # print("No Mandatory Constraints")
        return [True, []]

    # Partial orders
    Phi = extract_TNCP_Phi(events, flows, tcs)
    # print("Print Phi")
    # for phi in Phi: print(phi)
    C = phi_conflicts(L, Phi)
    if C != []:
        print("Ordering Inconsistent!")
        return [False, C]
    print("Ordering Consistent!")

    # Time
    if not solve_Time(L, events, flows, tcs, horizon):
        print("Temporally Consistent!")
        return [False, []]
    print("Temporally Consistent!")

    # State
    act_flows = []
    for i in range(event_num):
        # some flows start
        event = L[i]
        flow = []
        for f in flows:
            if f[0] == int(floor(event / 2)): flow = f
        if flow != []:
            if event % 2 == 0:
                act_flows.append(flow)
                if not solve_NCP(act_flows, edges, node_num):
                    print("State Inconsistent!")
                    conflicts = []
                    for flow_i, flow_j in product(act_flows, act_flows):
                        conflicts.append([(2 * flow_i[0], 2 * flow_j[0] + 1)])
                    return (False, conflicts)
            # some flows end
            else: act_flows.remove(flow)
    print("State Consistent!")

    return [True, []]

def extract_TNCP_Phi(events, flows, tcs):
    event_num = len(events)
    eps = 1e-6
    ## initialize distance graphs
    d = [[inf for i in range(event_num)] for j in range(event_num)]
    for i in range(event_num): d[i][i] = 0  # initailize diagonal entry
    for flow in flows:
        d[events.index(2 * flow[0] + 1)][events.index(2 * flow[0])] = - flow[6]  # apply flow duration
    for from_idx, to_idx in tcs: d[to_idx][from_idx] = -eps  # apply precedence temporal constraints
    # compute all partial orders
    d = apsp(d)
    orders = []
    num = len(d[0])
    for i in range(num):
        for j in range(num):
            if d[i][j] < 0: orders.append([(events[j], events[i])])
    return orders

def apsp(d):
    num = len(d[0])
    for k in range(num):
        for i in range(num):
            for j in range(num):
                d[i][j] = min(d[i][j], d[i][k] + d[k][j])
    return d


def solve_Time(L, events, flows, tcs, horizon):
    # time
    event_num = len(events)
    problem = Model("Time")
    problem.setParam(GRB.Param.OutputFlag, 0)
    ## Event Variables
    vars = {}
    for event in L: vars['E%s' % (event)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=horizon)
    # Temporal Constraints
    for flow in flows:
        start_idx, end_idx = 2 * flow[0], 2 * flow[0] + 1
        problem.addConstr(vars['E%s' % (start_idx)] + flow[6] <= vars['E%s' % (end_idx)])
    for from_idx, to_idx in tcs:
        problem.addConstr(vars['E%s' % (from_idx)] <= vars['E%s' % (to_idx)])
    for idx in range(event_num - 1):
        problem.addConstr(vars['E%s' % (L[idx])] <= vars['E%s' % (L[idx + 1])])


    problem.optimize()

    if (problem.status == GRB.OPTIMAL): return True
    else: return False

def solve_NCP(flows, edges, node_num):
    # print("Solve NCP with size F", len(flows), 'N', node_num)
    problem = Model("NCP")
    problem.setParam(GRB.Param.OutputFlag, 0)
    vars= {}
    flow_num = len(flows)
    # Initilize Flow Variables
    ## Conditional variables
    for flow in flows: vars['F%s' % (flow[0])] = problem.addVar(vtype=GRB.BINARY, name='F%s' % (flow[0]))
    for flow in flows:
        ## Routint variables and BW variables
        for i, j in product(range(node_num), range(node_num)):
            vars['FR%s(%s,%s)' % (flow[0], i, j)] = problem.addVar(vtype=GRB.BINARY)
            vars['FB%s(%s,%s)' % (flow[0], i, j)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[5])
        ## Loss and Delay Variables
        for i in range(node_num):
            vars['FL%s(%s)' % (flow[0], i)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[3])
            vars['FD%s(%s)' % (flow[0], i)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[4])

    # Routing constraints
    for flow in flows:
        idx, src, dst = flow[0:3]
        flow_var = vars['F%s' % (idx)]
        for node in range(node_num):
            incoming_nodes = [vars['FR%s(%s,%s)' % (idx, i, node)] for i in range(node_num)]
            outcoming_nodes = [vars['FR%s(%s,%s)' % (idx, node, j)] for j in range(node_num)]
            if node == src:
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) == 0)
                problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) == 1)
            elif node == dst:
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) == 1)
                problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) == 0)
            else:
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) ==
                                  LinExpr([1] * node_num, outcoming_nodes))

    # Bandwidth Constraints
    ## Bandwidth Consumption = Capacity
    for i, j in product(range(node_num), range(node_num)):
        bw_flow_vars = [vars['FB%s(%s,%s)' % (flow[0], i, j)] for flow in flows]
        problem.addConstr(LinExpr([1] * flow_num, bw_flow_vars) <= edges[i][j][4])
    ## Bandwidth Consumps if Flows Pass Edges
    for flow in flows:
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            bw_flow_var = vars['FB%s(%s,%s)' % (idx, i, j)]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            problem.addConstr(bw_flow_var + 1e6 * (1 - routing_var) >= flow[5])

    # Loss Constraints
    for flow in flows:
        problem.addConstr(vars['FL%s(%s)' % (flow[0], flow[1])] == 0)
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            loss_from = vars['FL%s(%s)' % (idx, i)]
            loss_to = vars['FL%s(%s)' % (idx, j)]
            problem.addConstr(loss_to - loss_from + 1e6 * (1 - routing_var) >= edges[i][j][2])

    # Delay Constraints
    for flow in flows:
        problem.addConstr(vars['FD%s(%s)' % (flow[0], flow[1])] == 0)
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            delay_from = vars['FD%s(%s)' % (idx, i)]
            delay_to = vars['FD%s(%s)' % (idx, j)]
            problem.addConstr(delay_to - delay_from + 1e6 * (1 - routing_var) >= edges[i][j][3])

    problem.write("debug.lp")
    problem.optimize()

    if problem.status == GRB.OPTIMAL: return True
    else: return False

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
