from gcdito import *
from random import *
from math import *
from gurobi import *
from util.apsp import *
from itertools import product

def generate_TNCP(flow_num = 30, node_num = 15, tc_num = 0,
                  edge_loss_lb = 0.1, edge_loss_ub = 0.3,
                  edge_delay_lb = 0.1, edge_delay_ub = 0.3,
                  edge_bw_lb = 600, edge_bw_ub = 1000,
                  flow_loss_lb = 0.2, flow_loss_ub= 0.6,
                  flow_delay_lb = 0.2, flow_delay_ub = 0.6,
                  flow_bw_lb = 300, flow_bw_ub = 500,
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
        flows.append([i, src, dst, loss, delay, bw, duration])
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

    return [flows, edges, tcs, node_num]

def solve_TNCP(flows, edges, tcs, node_num):
    flow_num = len(flows)
    L = list(range(2 * flow_num))
    P = [(0, 0, 2 * flow_num - 1)]
    Phi = extract_TNCP_Phi(flows, tcs)
    h = lambda L: make_TNCP_h(L, flows, edges, tcs, node_num)

    print("Print Phi")
    for phi in Phi: print(phi)

    L = gcdito(L, P, Phi, h)
    print(L)

def extract_TNCP_Phi(flows, tcs):
    flow_num = len(flows)
    event_num = 2 * flow_num
    eps = 1e-6
    ## initialize distance graphs
    d = [[inf for i in range(event_num)] for j in range(event_num)]
    for i in range(event_num): d[i][i] = 0  # initailize diagonal entry
    for idx in range(flow_num): d[2 * idx + 1][2 * idx] = - flows[idx][-1]  # apply flow duration
    for from_idx, to_idx in tcs: d[to_idx][from_idx] = -eps  # apply precedence temporal constraints
    return orders(d)  # compute all partial orders

def make_TNCP_h(L, flows, edges, tcs, node_num):
    flow_num = len(flows)
    event_num = 2 * flow_num

    # time
    problem = Model("Time")
    problem.setParam(GRB.Param.OutputFlag, 0)
    events = problem.addVars(event_num, vtype = GRB.CONTINUOUS)
    problem.addConstrs(events[2 * idx] + flows[idx][-1] <= events[2 * idx + 1] for idx in range(flow_num))
    problem.addConstrs(events[from_idx] <= events[to_idx] for from_idx, to_idx in tcs)
    problem.addConstrs(events[L[idx]] <= events[L[idx + 1]] for idx in range(event_num - 1))
    problem.optimize()
    if not (problem.status == GRB.OPTIMAL):
        print("Temporally Inconsistent!")
        return (False, [])
    print("Temporally Consistent!")

    # state
    act_indices = []
    for i in range(event_num - 1):
        consistency = True
        # some flows start
        if i % 2 == 0:
            act_indices.append(int(i / 2))
            if not solve_NCP([flows[idx] for idx in act_indices], edges, node_num):
                print("State Inconsistent!")
                return (False, [[(2 * i, 2 * j + 1)] for i, j in product(act_indices, act_indices)])
        # some flows end
        else:
            act_indices.remove(int((i - 1) / 2))
    print("State Consistent!")

    return(True, [])

def solve_NCP(flows, edges, node_num):
    print("Solve NCP with size F", len(flows), 'N', node_num)
    problem = Model("NCP")
    problem.setParam(GRB.Param.OutputFlag, 0)
    vars= {}
    flow_num = len(flows)
    # Initilize Flow Variables
    ## Conditional variables
    for idx in range(flow_num): vars['F%s' % (idx)] = problem.addVar(vtype=GRB.BINARY, name='F%s' % (idx))
    ## Routint variables and BW variables
    for idx, i, j in product(range(flow_num), range(node_num), range(node_num)):
        vars['FR%s(%s,%s)'%(idx, i, j)] = problem.addVar(vtype = GRB.BINARY, name = 'FR%s(%s,%s)'%(idx, i, j))
        vars['FB%s(%s,%s)'%(idx, i, j)] = problem.addVar(vtype = GRB.CONTINUOUS, lb = 0, ub = flows[idx][5],
                                                             name = 'FB%s(%s,%s)'%(idx, i, j))
    ## Loss and Delay Variables
    for idx, i in product(range(flow_num), range(node_num)):
        vars['FL%s(%s)' % (idx, i)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flows[idx][3],
                                                     name='FL%s(%s)' % (idx, i))

        vars['FD%s(%s)' % (idx, i)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flows[idx][4],
                                                     name='FD%s(%s)' % (idx, i))


    # Routing constraints
    for idx in range(flow_num):
        flow = flows[idx]
        src, dst = flow[1:3]
        for node in range(node_num):
            incoming_nodes = [vars['FR%s(%s,%s)'%(idx, i, node)] for i in range(node_num)]
            outcoming_nodes = [vars['FR%s(%s,%s)'%(idx, node, j)] for j in range(node_num)]
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
        bw_flow_vars = [vars['FB%s(%s,%s)'%(idx, i, j)] for idx in range(flow_num)]
        problem.addConstr(LinExpr([1] * flow_num, bw_flow_vars) <= edges[i][j][4])
    ## Bandwidth Consumps if Flows Pass Edges
    for idx, i, j in product(range(flow_num), range(node_num), range(node_num)):
        bw_flow_var = vars['FB%s(%s,%s)'%(idx, i, j)]
        routing_var = vars['FR%s(%s,%s)'%(idx, i, j)]
        problem.addConstr(bw_flow_var + 1e6 * (1 - routing_var) >= flows[idx][5])

    # Loss Constraints
    for idx in range(flow_num): problem.addConstr(vars['FL%s(%s)'%(idx, flows[idx][1])] == 0)
    for idx, i, j in product(range(flow_num), range(node_num), range(node_num)):
        routing_var = vars['FR%s(%s,%s)'%(idx, i, j)]
        loss_from = vars['FL%s(%s)'%(idx, i)]
        loss_to = vars['FL%s(%s)'%(idx, j)]
        problem.addConstr(loss_to - loss_from + 1e6 * (1 - routing_var) >= edges[i][j][2])

    # Delay Constraints
    for idx in range(flow_num): problem.addConstr(vars['FD%s(%s)' % (idx, flows[idx][1])] == 0)
    for idx, i, j in product(range(flow_num), range(node_num), range(node_num)):
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            delay_from = vars['FD%s(%s)' % (idx, i)]
            delay_to = vars['FD%s(%s)' % (idx, j)]
            problem.addConstr(delay_to - delay_from + 1e6 * (1 - routing_var) >= edges[i][j][3])


    # problem.setObjective(LinExpr([1] * flow_num, flow_vars))
    problem.write("debug.lp")
    problem.optimize()

    if problem.status == GRB.OPTIMAL:
        return True
    else: return False

flows, edges, tcs, node_num = generate_TNCP()
solve_TNCP(flows, edges, tcs, node_num)