from math import *
from gurobi import *
from itertools import product

def make_TNCP_h(L, flows, edges, tcs, PO, node_num, horizon):
    O = {}
    # # TODO: Test Only
    # if L == [1, 2, 3, 0, 4]:
    #     O["Time%s" % (L)] = {"name": "Time%s" % (L),
    #                          "PO": [(2, 0), (3, 0)],
    #                          "CS": ["Time", "T0", "T1"],
    #                          "MVS": ["T1"],
    #                          "MVC": 1}
    #     return 1, O
    # Partial Orders
    O.update(extractO_order(L, flows, PO))
    cost = sum([o["MVC"] for o in O.values()])
    if cost >= 1e6: return cost, O
    # Time
    O.update(extractO_time(L, flows, tcs, horizon))
    cost = sum([o["MVC"] for o in O.values()])
    if cost >= 1e6: return cost, O
    # State
    O.update(extractO_state(L, flows, edges, node_num))
    return sum([o["MVC"] for o in O.values()]), O

def extractO_order(L, flows, PO):
    O = {}
    for flow in flows:
        idx = flow[0]
        from_event, to_event = flow[1], flow[2]
        from_idx, to_idx = L.index(from_event), L.index(to_event)
        constraint_name = "F%s_Order"%(idx)
        if from_idx > to_idx:
            print("- Violate %s"%(constraint_name))
            O[constraint_name] = {"name": constraint_name,
                                   "PO":[(to_idx, from_idx)],
                                   "CS": [constraint_name],
                                   "MVS": [constraint_name],
                                   "MVC": 1e6}
    for i in range(len(PO)):
        weight, o = PO[i]
        hold = False
        for left, right in o:
            if L.index(left) < L.index(right): hold = True
        constraint_name = "O%s"%(i)
        if not hold: O[constraint_name] = {"name": constraint_name,
                                           "PO": [(q[1], q[0]) for q in o],
                                           "CS": [constraint_name],
                                           "MVS": [constraint_name],
                                           "MVC": weight}

    return O

def extractO_time(L, flows, tcs, horizon):
    events = list(range(len(L)))
    problem = Model("Time")
    problem.setParam(GRB.Param.OutputFlag, 0)
    ## Event Variables
    vars = {}
    for event in events:
        vars['E%s' % (event)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=horizon)
    # Temporal Constraints
    for flow in flows:
        idx, from_event, to_event = flow[0], flow[1], flow[2]
        problem.addConstr(vars['E%s' % (from_event)] + flow[8] <= vars['E%s' % (to_event)])

    for idx in range(len(L) - 1):
        problem.addConstr(vars['E%s' % (L[idx])] <= vars['E%s' % (L[idx + 1])])

    tc_vars, weights, indices = [], [], []
    for dtc_idx in range(len(tcs)):
        weight, dtc = tcs[dtc_idx]
        if weight < 1e6:
            tc_var = problem.addVar(vtype=GRB.BINARY)
            tc_vars.append(tc_var)
            weights.append(weight)
            indices.append(dtc_idx)
            flags = problem.addVars(len(dtc), vtype=GRB.BINARY)
            problem.addConstr(flags.sum() >= 1)
            for tc_idx in range(len(dtc)):
                from_idx, to_idx, lb = dtc[tc_idx]
                problem.addConstr(vars['E%s' % (from_idx)] + lb
                                  - 1e6 * (1 - flags[tc_idx])
                                  - 1e6 * (1 - tc_var)
                                  <= vars['E%s' % (to_idx)])
        else:
            flags = problem.addVars(len(dtc), vtype = GRB.BINARY)
            problem.addConstr(flags.sum() >= 1)
            for tc_idx in range(len(dtc)):
                from_idx, to_idx, lb = dtc[tc_idx]
                problem.addConstr(vars['E%s' % (from_idx)] + lb - 1e6 * (1 - flags[tc_idx])
                                  <= vars['E%s' % (to_idx)])
    problem.setObjective(sum(weights) - LinExpr(weights, tc_vars), GRB.MINIMIZE)
    problem.optimize()
    if (problem.status == GRB.OPTIMAL):
        if problem.objVal > 1e-3:
            print("- Temporal Suboptimal")
            CS = ["Time"] + ["T%s" % (indices[idx]) for idx in range(len(indices))]
            MVS = ["T%s" % (indices[idx]) for idx in range(len(indices)) if tc_vars[idx].x < 1e-3]
            return {"Time%s" % (L): {"name": "Time%s" % (L),
                                     "PO": [(L[idx], L[idx + 1]) for idx in range(len(L) - 1)],
                                     "CS": CS,
                                     "MVS": MVS,
                                     "MVC": problem.objVal}}
        else:
            print("- Temporal Optimal")
            return {}
    else:
        print("- Temporal Inconsistent")
        return {"Time%s"%(L): {"name": "Time%s"%(L),
                               "PO":[(L[idx], L[idx+1]) for idx in range(len(L) - 1)],
                               "CS": ["Time"],
                               "MVS": ["Time"],
                               "MVC": 1e6}}

def extractO_state(L, flows, edges, node_num):
    O = {}

    NCP_sequence = [[] for i in range(len(L))]
    # initialize all redundant NCPs
    act_flows = [flow for flow in flows if L.index(flow[1]) < L.index(flow[2])]
    for flow in act_flows:
        start_event, end_event = flow[1], flow[2]
        start_idx, end_idx = L.index(start_event), L.index(end_event)
        for i in range(start_idx, end_idx): NCP_sequence[i].append(flow[0])
    # filter left side
    tmp_sequence = []
    for i in range(len(NCP_sequence)+1):
        if i == 0: left = set()
        else: left = set(NCP_sequence[i-1])
        if i == len(NCP_sequence): right = set()
        else: right = set(NCP_sequence[i])
        if not left.issubset(right) and left != set(): tmp_sequence.append(left)
    NCP_sequence, tmp_sequence = tmp_sequence, []
    # filter right side
    for i in range(len(NCP_sequence)+1):
        if i == 0: left = set()
        else: left = set(NCP_sequence[i-1])
        if i == len(NCP_sequence): right = set()
        else: right = set(NCP_sequence[i])
        if not right.issubset(left) and right!=set(): tmp_sequence.append(right)
    NCP_sequence = tmp_sequence
    print(NCP_sequence)

    # group flows into constraint set
    NCP_groups, NCP_group = [], [NCP_sequence[0]]
    for i in range(len(NCP_sequence)-1):
        last_NCP, NCP = NCP_sequence[i], NCP_sequence[i+1]
        disjoint = True
        for flow_idx in set.intersection(last_NCP, NCP):
            if flows[flow_idx][9] < 1e6:
                disjoint = False
                break
        if disjoint:
            NCP_groups.append(NCP_group.copy())
            NCP_group = [NCP]
        else:
            NCP_group.append(NCP)
    if NCP_group != []: NCP_groups.append(NCP_group.copy())

    # solve NCP group
    for NCP_group in NCP_groups:
        problem = Model("NCP")
        problem.setParam(GRB.Param.OutputFlag, 0)
        ## Conditional variables
        cond_vars = {}
        flow_indices = set.union(*NCP_group)
        for idx in flow_indices:
            cond_vars['F%s' % (idx)] = problem.addVar(vtype=GRB.BINARY, name='F%s' % (idx))
        ## Set Objective Solve
        weights = [flows[idx][9] for idx in flow_indices]
        flow_vars = [cond_vars['F%s' % (idx)] for idx in flow_indices]
        problem.setObjective(sum(weights) - LinExpr(weights, flow_vars), GRB.MINIMIZE)
        ## Add constraints
        for NCP in NCP_group:
            NCP_flows = [flows[idx] for idx in NCP]
            add_NCP(problem, cond_vars, NCP_flows, edges, node_num)
        ## Optimize
        problem.optimize()
        PO = set()
        for NCP in NCP_group:
            for i, j in product(NCP, NCP):
                PO = set.union(PO, {(flows[i][1], flows[j][2])})
        CS = ["F%s_State"%(idx) for idx in NCP]
        MVS = ["F%s_State"%(idx) for idx in NCP if cond_vars['F%s'%(idx)].x < 1e-3]
        print("- NCP[%s]: PO=%s, CS=%s, MVS=%s, Cost=%s"
              %(sorted(NCP), list(PO), CS, MVS, problem.objVal))
        if problem.objVal >= 1e-3:
            O["State%s"%(sorted(list(NCP)))] = {"name": "State%s"%(sorted(list(NCP))),
                                                "PO": list(PO), "CS": CS, "MVS": MVS, "MVC": problem.objVal}
    return O

def add_NCP(problem, cond_vars, flows, edges, node_num):
    vars = {}

    flow_num = len(flows)
    # Initilize Flow Variables
    for flow in flows:
        ## Routint variables and BW variables
        for i, j in product(range(node_num), range(node_num)):
            vars['FR%s(%s,%s)' % (flow[0], i, j)] = problem.addVar(vtype=GRB.BINARY)
            vars['FB%s(%s,%s)' % (flow[0], i, j)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[7])
        ## Loss and Delay Variables
        for i in range(node_num):
            vars['FL%s(%s)' % (flow[0], i)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[5])
            vars['FD%s(%s)' % (flow[0], i)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[6])

    # Routing constraints
    for flow in flows:
        idx, src, dst = flow[0], flow[3], flow[4]
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
            problem.addConstr(bw_flow_var + 1e6 * (2 - flow_var - routing_var) >= flow[7])

    # Loss Constraints
    for flow in flows:
        problem.addConstr(vars['FL%s(%s)' % (flow[0], flow[3])] == 0)
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            flow_var = cond_vars['F%s' % (idx)]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            loss_from = vars['FL%s(%s)' % (idx, i)]
            loss_to = vars['FL%s(%s)' % (idx, j)]
            problem.addConstr(loss_to - loss_from + 1e6 * (2 - flow_var - routing_var) >= edges[i][j][2])

    # Delay Constraints
    for flow in flows:
        problem.addConstr(vars['FD%s(%s)' % (flow[0], flow[3])] == 0)
        for i, j in product(range(node_num), range(node_num)):
            idx = flow[0]
            flow_var = cond_vars['F%s' % (idx)]
            routing_var = vars['FR%s(%s,%s)' % (idx, i, j)]
            delay_from = vars['FD%s(%s)' % (idx, i)]
            delay_to = vars['FD%s(%s)' % (idx, j)]
            problem.addConstr(delay_to - delay_from + 1e6 * (2 - flow_var - routing_var) >= edges[i][j][3])
