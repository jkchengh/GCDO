from benchmarks.network import *
from multiprocessing import Process
import os
import sys
import matplotlib.pyplot as plt

def benchmark(cases, node_nums, flow_nums):
    horizon = 3000
    for idx in range(len(flow_nums)):
        node_num = node_nums[idx]
        flow_num = flow_nums[idx]
        for case in range(cases):

            flows, edges, tcs, node_num, horizon \
                = generate_TNCP(flow_num = flow_num, node_num = node_num, tc_num = 0, horizon = horizon,
                                  edge_loss_lb = 0.1, edge_loss_ub = 0.1,
                                  edge_delay_lb = 0.1, edge_delay_ub = 0.1,
                                  edge_bw_lb = 500, edge_bw_ub = 500,
                                  flow_loss_lb = 0.15, flow_loss_ub= 0.15,
                                  flow_delay_lb = 0.15, flow_delay_ub = 0.15,
                                  flow_bw_lb = 400 , flow_bw_ub = 500,
                                  flow_duration_lb = 20, flow_duration_ub = 20)
            sys.stdout = open(os.devnull, 'w')
            # GCDO
            # sys.stdout = open("N%sF%s[%s].log" % (node_num, flow_num, case), 'w')
            # print_TNCP(flows, edges, tcs, node_num)
            csv_path = os.path.abspath("results/[GCDO]N%sF%s#%s.csv" % (node_num, flow_num, case))
            f = open(csv_path, "w+")
            f.close
            solve_TNCP(flows, edges, tcs, [], node_num, horizon, csv_path, "GCDO", timeout = 30)

            # CDITO
            csv_path = os.path.abspath("results/[CDITO]N%sF%s#%s.csv" % (node_num, flow_num, case))
            f = open(csv_path, "w+")
            f.close
            solve_TNCP(flows, edges, tcs, [], node_num, horizon, csv_path, "CDITO", timeout = 30)



cases = 50
node_nums = [3]
flow_nums = [20]


def process_simulation_results(cases, node_nums, flow_nums):
    for idx in range(len(flow_nums)):
        node_num = node_nums[idx]
        flow_num = flow_nums[idx]
        for alg in ["GCDO", "CDITO"]:
            first_time = 0
            first_cost = 0
            returned_cost = 0
            optimal_num = 0
            unsolve_num, subopt_num, optimal_num = 0, 0, 0
            iters_for_unsolve = 0
            itersh_for_unsolve = 0
            iters_for_subopt = 0
            itersh_for_subopt = 0
            iters_for_optimal = 0
            itersh_for_optimal = 0
            for case in range(cases):
                path = os.path.abspath("results/[%s]N%sF%s#%s.csv" % (alg, node_num, flow_num, case))
                times, costs, statuses, iters, itersh = [], [], [], [], []
                with open(path, newline='') as csvfile:
                    contents = csv.reader(csvfile)
                    for line in contents:
                        times.append(float(line[0]))
                        statuses.append(line[1])
                        costs.append(float(line[2]))
                        iters.append(float(line[3]))
                        itersh.append(float(line[4]))
                if costs[-1] >= 1e6:
                    unsolve_num = unsolve_num + 1
                    iters_for_unsolve = iters_for_unsolve + iters[-1]
                    itersh_for_unsolve = itersh_for_unsolve + itersh[-1]
                elif costs[-1] < 1e6:
                    first_time = first_time + times[0]
                    first_cost = first_cost + costs[0]
                    returned_cost = returned_cost + costs[-1]
                    if statuses[-1] == 'timeout':
                        subopt_num = subopt_num + 1
                        iters_for_subopt = iters_for_subopt + iters[-1]
                        itersh_for_subopt = itersh_for_subopt + itersh[-1]
                    elif statuses[-1] == 'optimal':
                        optimal_num = optimal_num + 1
                        iters_for_optimal = iters_for_optimal + iters[-1]
                        itersh_for_optimal = itersh_for_optimal + itersh[-1]

            print("[%s] #N=%s #F=%s p(solve)=%.3f t1=%.3f, g1=%.3f, g=%.3f, p(h)=%.3f"
                  % (alg, node_num, flow_num,
                     (cases - unsolve_num) / cases,
                     first_time / (cases - unsolve_num),
                     first_cost / (cases - unsolve_num),
                     returned_cost / (cases - unsolve_num),
                     (itersh_for_subopt + itersh_for_subopt + itersh_for_optimal)
                     / (iters_for_subopt + iters_for_subopt + iters_for_optimal)))
            # print("[%s] p(suboptimal)=%.3f #times=%.3f #timesh=%.3f"
            #       % (alg,
            #          subopt_num / cases,
            #          iters_for_subopt / subopt_num,
            #          itersh_for_subopt / subopt_num))


# benchmark(cases, node_nums, flow_nums)
process_simulation_results(cases, node_nums, flow_nums)