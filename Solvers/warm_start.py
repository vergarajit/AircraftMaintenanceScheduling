import math 
import time

def compute_capacity_utilization(instance):

    N = instance["I"] + instance["O"]

    capacity_total = 0

    for h, slots in instance["T_h"].items():
        for t in slots:
            for s, cap in instance["W"][str(h)].items():
                capacity_total += cap

    demand_total = sum(
        instance["w"][i] * instance["M_i"][i]
        for i in N
    )

    return demand_total / capacity_total

def build_capacity_tracker(instance: dict) -> dict[int, dict[str, float]]:
    """
    Returns capacity[t][s] = available workers for skill s at slot t.

    instance["W"][h][s]      -> worker count for shift h, skill s
    instance["T_h"][str(h)]  -> list of slot indices belonging to shift h
    """
    T = instance["T"]
    capacity: dict[int, dict[str, float]] = {t: {} for t in range(T)}

    for h, slots in instance["T_h"].items():
        workers_per_skill: dict[str, float] = instance["W"][str(h)]
        for t in slots:
            for s, w in workers_per_skill.items():
                # A slot can belong to at most one shift, but initialise
                
                capacity[t][s] = max(capacity[t].get(s, 0), w) # max keeps the highest value if overlap exists

    return capacity 

def remove_task(i, schedule, capacity, instance):

    start = schedule[i]

    skill = instance["s"][i]
    duration = instance["M_i"][i]
    workers = instance["w"][i]

    for tau in range(start, start + duration):
        capacity[tau][skill] += workers

def try_insert(i, capacity, instance, group_window):    
    if i not in group_window:
        return None

    skill = instance["s"][i]
    duration = instance["M_i"][i]
    workers = instance["w"][i]

    a, b = group_window[i]

    last_start = min(
        b - duration + 1,
        instance["T"] - duration
    )

    for t_start in range(a, last_start + 1):

        feasible = all(
            capacity[tau].get(skill, 0) >= workers
            for tau in range(t_start, t_start + duration)
        )

        if feasible:
            return t_start

    return None


def greedy_warm_start(instance, **kwargs):
    """
    Run the greedy heuristic and return the warm start dictionary 
    along with solver-identical performance metrics.
    """
    start_time = time.time()
    
    N   = instance["I"] + instance["O"]   # full task list
    T   = instance["T"]                   # planning horizon length (int)
    p   = instance["p"]                   # priority of each task
    w   = instance["w"]                   # workers required by each task
    s   = instance["s"]                   # skill of each task
    M_i = instance["M_i"] #{i: math.ceil(instance["M_i"][i] / instance["w"][i]) for i in N} # Slots needed per task
   
    # Build a group lookup: task -> (a, b)
    group_window: dict[str, tuple[int, int]] = {}
    for g, gdata in instance["G"].items():
        a, b = gdata["a"], gdata["b"]
        for i in gdata["tasks"]:
            group_window[i] = (a, b)

    # Slot-level remaining capacity
    capacity = build_capacity_tracker(instance)

    # Sort by priority then required workers (descending)
    
   # sorted_tasks = sorted(N, key=lambda i: (p[i], w[i]), reverse=True)
    sorted_tasks = sorted(N, key=lambda i: p[i] / (w[i] * M_i[i]), reverse=True)
    
    # Initialize solution to all-zero
    y_sol: dict[str, int]        = {i: 0 for i in N}
    z_sol: dict[tuple, int]      = {(i, t): 0 for i in N for t in range(T)}

    scheduled:   list[str] = []
    unscheduled: list[str] = []
    schedule = {}

    for i in sorted_tasks:
        skill    = s[i]
        duration = M_i[i]
        workers_needed   = w[i]

        a, b = group_window[i]
        if duration > (b - a + 1): 
            print(
                f"Task {i} infeasible: duration={duration}, "
                f"window=[{a},{b}], size={b-a+1}")
            unscheduled.append(i)
            continue

        if i not in group_window:
            unscheduled.append(i)
            continue

        a, b       = group_window[i]
        last_start = b - duration + 1   
        last_start = min(last_start, T - duration)  

        assigned = False

        for t_start in range(a, last_start + 1):
            active_slots = range(t_start, t_start + duration)

            if all(capacity[tau].get(skill, 0) >= workers_needed for tau in active_slots):
                # Feasible assignment
                y_sol[i] = 1
                z_sol[(i, t_start)] = 1 
                for tau in active_slots:
                    capacity[tau][skill] -= workers_needed  

                scheduled.append(i)
                schedule[i] = t_start
                assigned = True
                break

        if not assigned:
            unscheduled.append(i)

   # Metrics computation 
    elapsed_time = round(time.time() - start_time, 2)
    epsilon = 1e-5

    objective = 0
    for t, start in schedule.items():
        objective += p[t] - epsilon * start * w[t]

    best_value = round(objective, 2)

    if schedule:
        makespan = max(start + M_i[i] for i, start in schedule.items())
    else:
        makespan = 0.0

    gap = None
    prop_unscheduled = round((len(unscheduled) / len(N)) * 100, 2) if len(N) > 0 else 0.0

    warm_start_dict = {"y": y_sol, "z": z_sol}
    task_start_times = schedule

    tasks_in_groups = set()
  
    for g, gdata in instance["G"].items():
        tasks_in_groups.update(gdata["tasks"])

    print("Total tasks:", len(N))
    print("Tasks in groups:", len(tasks_in_groups))
    no_gruop_tasks = set(N) - tasks_in_groups
    print("Tasks not in groups:", len(set(N) - tasks_in_groups))
    #Sprint("Tasks not in groups (IDs):", no_gruop_tasks)


    return warm_start_dict, elapsed_time, best_value, gap, makespan, task_start_times, unscheduled, prop_unscheduled

