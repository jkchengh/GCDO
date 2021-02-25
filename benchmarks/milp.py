from gurobi import *
import itertools as it

def milp(flows, edges, tcs, node_num, horizon, path, timeout):
    # [print(flow) for flow in flows]
    M = 1e8
    flow_num = len(flows)
    events = list(set.union(*[set(flow[1:3]) for flow in flows]))
    event_num = len(events)
    # model
    problem = Model("Network")
    problem.setParam(GRB.Param.OutputFlag, 0)
    problem.setParam('TimeLimit', timeout)
    problem.setParam(GRB.Param.IntFeasTol, 1e-9)
    problem._flows = flows
    problem._1stObj = GRB.INFINITY
    problem._1stTime = 0
    problem._incObj = GRB.INFINITY
    problem._incTime = 0

    # variables
    vars = {}
    for flow in flows:
        vars['F%s' % (flow[0])] = problem.addVar(vtype=GRB.BINARY)
    for event in events:
        vars['E%s_Time'%(event)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=horizon)
    for ref in range(event_num):
        vars['R%s_Time'%(ref)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=horizon)
    for flow, s in it.product(flows, range(event_num -1)):
        vars["F%s_on_S%s"%(flow[0], s)] = problem.addVar(vtype=GRB.BINARY)

    # objective
    weights = [flow[9] for flow in flows]
    flow_vars = [vars['F%s' % (flow[0])] for flow in flows]
    problem.addConstr(sum(weights) - LinExpr(weights, flow_vars) <= flow_num)
    problem.setObjective(sum(weights) - LinExpr(weights, flow_vars), GRB.MINIMIZE)

    # constraints
    ## constraints on stage variables
    for flow in flows:
        coeffs = [1] * (event_num - 1)
        stage_vars = [vars["F%s_on_S%s" % (flow[0], s)] for s in range(event_num - 1)]
        problem.addConstr(LinExpr(coeffs, stage_vars) >= 1)
    # temporal constraints
    ## reference points
    for ref in range(event_num-1): problem.addConstr(vars["R%s_Time"%(ref+1)] >= vars["R%s_Time"%(ref)])
    ## reference points and stage variables
    for flow, s in it.product(flows, range(event_num - 1)):
        FonS = vars["F%s_on_S%s"%(flow[0], s)]
        ref_start = vars['R%s_Time'%(s)]
        ref_end = vars['R%s_Time'%(s+1)]
        flow_start = vars['E%s_Time' % (flow[1])]
        flow_end = vars['E%s_Time' % (flow[2])]
        # 1
        tmp_var1 = problem.addVar(vtype=GRB.BINARY)
        tmp_var2 = problem.addVar(vtype=GRB.BINARY)
        problem.addConstr(tmp_var1 + tmp_var2 + FonS >= 1)
        problem.addConstr(flow_start + M * (1-tmp_var1) >= ref_end)
        problem.addConstr(flow_end - M * (1-tmp_var2) <= ref_start)
        # 2
        tmp_var3 = problem.addVar(vtype=GRB.BINARY)
        problem.addConstr(flow_start - M * (1 - FonS) <= ref_end)
        problem.addConstr(ref_start - M * (1 - FonS) <= flow_end)
    ## flow duration
    for flow in flows:
        idx, from_event, to_event = flow[0], flow[1], flow[2]
        problem.addConstr(vars['E%s_Time' % (from_event)] + flow[8] <= vars['E%s_Time' % (to_event)])

    # state constraints
    ## new variables
    for s in range(event_num - 1):
        for flow in flows:
            ## Routint variables and BW variables
            for i, j in it.product(range(node_num), range(node_num)):
                vars['FR%s(%s,%s)_S%s' % (flow[0], i, j, s)] = problem.addVar(vtype=GRB.BINARY)
                vars['FB%s(%s,%s)_S%s' % (flow[0], i, j, s)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[7])
            ## Loss and Delay Variables
            for i in range(node_num):
                vars['FL%s(%s)_S%s' % (flow[0], i, s)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[5])
                vars['FD%s(%s)_S%s' % (flow[0], i, s)] = problem.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=flow[6])

    ## routing constraints
    for s in range(event_num - 1):
        for flow in flows:
            idx, src, dst = flow[0], flow[3], flow[4]
            flow_var = vars['F%s' % (idx)]
            stage_var = vars["F%s_on_S%s"%(flow[0], s)]
            for node in range(node_num):
                incoming_nodes = [vars['FR%s(%s,%s)_S%s' % (idx, i, node, s)] for i in range(node_num)]
                outcoming_nodes = [vars['FR%s(%s,%s)_S%s' % (idx, node, j, s)] for j in range(node_num)]
                if node == src:
                    problem.addConstr(LinExpr([1] * node_num, incoming_nodes) + 1e6 * (2 - flow_var - stage_var) >= 0)
                    problem.addConstr(LinExpr([1] * node_num, incoming_nodes) - 1e6 * (2 - flow_var- stage_var) <= 0)
                    problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) + 1e6 * (2 - flow_var- stage_var) >= 1)
                    problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) - 1e6 * (2 - flow_var- stage_var) <= 1)
                elif node == dst:
                    problem.addConstr(LinExpr([1] * node_num, incoming_nodes) + 1e6 * (2 - flow_var- stage_var) >= 1)
                    problem.addConstr(LinExpr([1] * node_num, incoming_nodes) - 1e6 * (2 - flow_var- stage_var) <= 1)
                    problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) + 1e6 * (2 - flow_var- stage_var) >= 0)
                    problem.addConstr(LinExpr([1] * node_num, outcoming_nodes) - 1e6 * (2 - flow_var- stage_var) <= 0)
                else:
                    problem.addConstr(LinExpr([1] * node_num, incoming_nodes) + 1e6 * (2 - flow_var- stage_var) >=
                                      LinExpr([1] * node_num, outcoming_nodes))
                    problem.addConstr(LinExpr([1] * node_num, incoming_nodes) - 1e6 * (2 - flow_var- stage_var) <=
                                      LinExpr([1] * node_num, outcoming_nodes))

    # Bandwidth Constraints
    ## Bandwidth Consumption = Capacity
    for s in range(event_num - 1):
        for i, j in it.product(range(node_num), range(node_num)):
            bw_flow_vars = [vars['FB%s(%s,%s)_S%s' % (flow[0], i, j, s)] for flow in flows]
            problem.addConstr(LinExpr([1] * flow_num, bw_flow_vars) <= edges[i][j][4])
            ## Bandwidth Consumps if Flows Pass Edges
        for flow in flows:
            for i, j in it.product(range(node_num), range(node_num)):
                idx = flow[0]
                flow_var = vars['F%s' % (idx)]
                stage_var = vars["F%s_on_S%s"%(flow[0], s)]
                routing_var = vars['FR%s(%s,%s)_S%s' % (idx, i, j, s)]
                bw_flow_var = vars['FB%s(%s,%s)_S%s' % (idx, i, j, s)]
                problem.addConstr(bw_flow_var + 1e6 * (3 - flow_var - stage_var - routing_var) >= flow[7])

    # Loss Constraints
    for s in range(event_num - 1):
        for flow in flows:
            problem.addConstr(vars['FL%s(%s)_S%s' % (flow[0], flow[3], s)] == 0)
            for i, j in it.product(range(node_num), range(node_num)):
                idx = flow[0]
                flow_var = vars['F%s' % (idx)]
                stage_var = vars["F%s_on_S%s" % (flow[0], s)]
                routing_var = vars['FR%s(%s,%s)_S%s' % (idx, i, j, s)]
                loss_from = vars['FL%s(%s)_S%s' % (idx, i, s)]
                loss_to = vars['FL%s(%s)_S%s' % (idx, j, s)]
                problem.addConstr(loss_to - loss_from + 1e6 * (3 - flow_var - stage_var - routing_var) >= edges[i][j][2])

    # Delay Constraints
    for s in range(event_num - 1):
        for flow in flows:
            problem.addConstr(vars['FD%s(%s)_S%s' % (flow[0], flow[3], s)] == 0)
            for i, j in it.product(range(node_num), range(node_num)):
                idx = flow[0]
                flow_var = vars['F%s' % (idx)]
                stage_var = vars["F%s_on_S%s" % (flow[0], s)]
                routing_var = vars['FR%s(%s,%s)_S%s' % (idx, i, j, s)]
                delay_from = vars['FD%s(%s)_S%s' % (idx, i, s)]
                delay_to = vars['FD%s(%s)_S%s' % (idx, j, s)]
                problem.addConstr(delay_to - delay_from + 1e6 * (3 - flow_var - stage_var - routing_var) >= edges[i][j][3])

    problem.optimize(cbWrite)
    # for flow in flows: print(flow[0], vars['F%s' % (flow[0])].x)
    print("#flows", len(flows), "t1", problem._1stTime, "g1", problem._1stObj, "t", problem.Runtime, "g", problem._incObj)
    return None, None

def cbWrite(problem, where):
    if where == GRB.Callback.MIPSOL:
        problem._incTime = problem.cbGet(GRB.Callback.RUNTIME)
        problem._incObj = problem.cbGet(GRB.Callback.MIPSOL_OBJ)
        if problem._1stTime == 0:
            problem._1stTime = problem.cbGet(GRB.Callback.RUNTIME)
            problem._1stObj = problem.cbGet(GRB.Callback.MIPSOL_OBJ)