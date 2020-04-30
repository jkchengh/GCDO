from math import *
from gurobi import *
from itertools import product


def make_TNCP_f(portion, L, flows, edges, tcs, node_num, horizon):

    # find level
    l = level(L)

    # find events
    if portion == "assigned": L = [e for e in L if e > l]
    elif portion == "all": L = L

    events = L
    flows = [flow for flow in flows if (2*flow[0]) in events and (2*flow[0]+1) in events]
    tcs = [tc for tc in tcs if tc[0] in events and tc[1] in events]
    weights = [flow[7] for flow in flows]

    # print("-- Check All Constraints")
    # print("Scoped Flows:", [flow[0] for flow in flows])
    # print("Scoped Events:", events)
    if events == []:
        # print("No Scoped Constraints")
        return 0

    # Model
    problem = Model("TNCP")
    problem.setParam(GRB.Param.OutputFlag, 0)

    # Variables
    vars = {}
    ## Conditional variables
    for flow in flows: vars['F%s' % (flow[0])] = problem.addVar(vtype=GRB.BINARY, name='F%s' % (flow[0]))
    ## Event Variables
    for event in L: vars['E%s' % (event)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=horizon)

    # Set Objective Solve
    problem.setObjective(sum(weights) - LinExpr(weights, [vars['F%s' % (flow[0])] for flow in flows]),
                         GRB.MAXIMIZE)

    # Find Dropped Flows
    dropped_flows = [flow for flow in flows if L.index(2*flow[0]+1) < L.index(2*flow[0])]
    for flow in dropped_flows: problem.addConstr(vars['F%s' % (flow[0])] == 0)
    # print("Dropped:", [flow[0] for flow in dropped_flows])

    # Temporal Constraints
    for flow in flows:
        start_idx, end_idx = 2 * flow[0], 2 * flow[0] + 1
        problem.addConstr(vars['E%s' % (start_idx)] + flow[6]  - 1e6 * (1 - vars['F%s' % (flow[0])])
                          <= vars['E%s' % (end_idx)])
    for from_idx, to_idx in tcs:
        i, j = int(floor(from_idx/2)), int(floor(to_idx/2))
        problem.addConstr(vars['E%s' % (from_idx)] - 1e6 * (2 - vars['F%s' % (i)] - vars['F%s' % (j)])
                          <= vars['E%s' % (to_idx)])
    for idx in range(len(events) - 1):
        problem.addConstr(vars['E%s' % (L[idx])] <= vars['E%s' % (L[idx + 1])])

    # State Constraints
    act_flow_sequence = []
    act_flows = []
    peak = []
    change = 'up'
    for i in range(len(L)):
        event = L[i]
        flow = []
        for f in flows:
            if f[0] == int(floor(event / 2)): flow = f
        # some flows start
        # print("Index[%s]"%(i), "Event[%s]"%(event), "Change[%s]"%(change), "Flow[%s]"%(flow))
        if flow != [] and not flow in dropped_flows:
            if event % 2 == 0:
                if change == 'down': act_flow_sequence.append(peak.copy())
                change = 'up'
                act_flows.append(flow)
            # some flows end
            else:
                if change == 'up': peak = act_flows.copy()
                change = 'down'
                act_flows.remove(flow)
        if i == len(events) - 1 and peak != []:
            act_flow_sequence.append(peak.copy())


    for act_flows in act_flow_sequence:
        add_NCP(problem, vars, act_flows, edges, node_num)

    # for act_flows in act_flow_sequence: print("Flow Main Component Sequence", [flow[0] for flow in act_flows])
    # print("Weights", weights)

    problem.optimize()
    # for flow in flows: print(vars['F%s' % (flow[0])].X, "Flow(%s)"%(flow[0]))
    return problem.objVal

###
def add_NCP(problem, cond_vars, flows, edges, node_num):
    vars = {}

    flow_num = len(flows)
    # Initilize Flow Variables
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
        flow_var = cond_vars['F%s' % (idx)]
        for node in range(node_num):
            incoming_nodes = [vars['FR%s(%s,%s)' % (idx, i, node)] for i in range(node_num)]
            outcoming_nodes = [vars['FR%s(%s,%s)' % (idx, node, j)] for j in range(node_num)]
            if node == src:
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) + 1e6 * (1 - flow_var) >= 0)
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) - 1e6 * (1 - flow_var) <= 0)
                problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) + 1e6 * (1 - flow_var) >= 1)
                problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) - 1e6 * (1 - flow_var) <= 1)
            elif node == dst:
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) + 1e6 * (1 - flow_var) >= 1)
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) - 1e6 * (1 - flow_var) <= 1)
                problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) + 1e6 * (1 - flow_var) >= 0)
                problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) - 1e6 * (1 - flow_var) <= 0)
            else:
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) + 1e6 * (1 - flow_var) >=
                                  LinExpr([1] * node_num, outcoming_nodes))
                problem.addConstr(LinExpr([1] * node_num, incoming_nodes) - 1e6 * (1 - flow_var) <=
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
            flow_var = cond_vars['F%s' % (idx)]
            bw_flow_var = vars['FB%s(%s,%s)' % (idx, i, j)]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            problem.addConstr(bw_flow_var + 1e6 * (2 - flow_var - routing_var) >= flow[5])

    # Loss Constraints
    for flow in flows:
        problem.addConstr(vars['FL%s(%s)' % (flow[0], flow[1])] == 0)
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            flow_var = cond_vars['F%s' % (idx)]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            loss_from = vars['FL%s(%s)' % (idx, i)]
            loss_to = vars['FL%s(%s)' % (idx, j)]
            problem.addConstr(loss_to - loss_from + 1e6 * (2 - flow_var - routing_var) >= edges[i][j][2])

    # Delay Constraints
    for flow in flows:
        problem.addConstr(vars['FD%s(%s)' % (flow[0], flow[1])] == 0)
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            flow_var = cond_vars['F%s' % (idx)]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            delay_from = vars['FD%s(%s)' % (idx, i)]
            delay_to = vars['FD%s(%s)' % (idx, j)]
            problem.addConstr(delay_to - delay_from + 1e6 * (2 - flow_var - routing_var) >= edges[i][j][3])

def level(L):
    for l in range(len(L)):
        if l != L[l]: return l
    return len(L) - 1