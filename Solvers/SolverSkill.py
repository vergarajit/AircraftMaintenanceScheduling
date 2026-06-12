from gurobipy import GRB
import gurobipy as gp
import time

def SolverBySkill(instance, **kwargs):
    start_time = time.time()
    gp.setParam('OutputFlag', 0)

    N        = instance["I"] + instance["O"]
    T        = range(instance["T"])
    M_i      = instance["M_i"]
    epsilon  = 1e-5

    # ── partition tasks by skill ──────────────────────────────────────────────
    tasks_by_skill = {s: [i for i in N if instance["s"][i] == s]
                      for s in instance["S"]}

    # ── accumulators ─────────────────────────────────────────────────────────
    all_start_times  = {}
    all_unscheduled  = []
    total_obj        = 0.0
    global_makespan  = 0.0
    max_gap          = 0.0

    for s, N_s in tasks_by_skill.items():
        if not N_s:
            continue

        m = gp.Model(f'CrewScheduling_s{s}')
        m.setParam('OutputFlag', 0)
       # m.setParam('MIPGap',    0.01)
        m.setParam('Seed',      42)

        # ── variables ────────────────────────────────────────────────────────
        y     = m.addVars(N_s,     vtype=GRB.BINARY,     name="y")
        z     = m.addVars(N_s, T,  vtype=GRB.BINARY,     name="z")
        c_max = m.addVar(           vtype=GRB.CONTINUOUS, lb=0, name="c_max")

        # ── start-once ───────────────────────────────────────────────────────
        for i in N_s:
            m.addConstr(gp.quicksum(z[i, t] for t in T) == y[i],
                        name=f"start_once_{i}")

        # ── workforce capacity (only skill s, so W[h][s] is the RHS) ─────────
        for h in instance["H"]:
            for t in instance["T_h"][str(h)]:
                m.addConstr(
                    gp.quicksum(
                        instance["w"][i] * z[i, tau]
                        for i in N_s
                        for tau in T
                        if tau <= t < tau + M_i[i]
                    ) <= instance["W"][str(h)][s],
                    name=f"cap_h{h}_t{t}"
                )

        # ── time windows (filter each group to tasks in N_s) ─────────────────
        for g, gdata in instance["G"].items():
            a, b = gdata["a"], gdata["b"]
            for i in gdata["tasks"]:
                if i not in N_s:          # ← key: skip tasks not in this skill
                    continue
                c = b - M_i[i] + 1
                for t in T:
                    if t < a or t > c:
                        m.addConstr(z[i, t] == 0,
                                    name=f"tw_{g}_{i}_{t}")

        # ── no overflow beyond T ──────────────────────────────────────────────
        for i in N_s:
            for t in T:
                if t + M_i[i] > instance["T"]:
                    m.addConstr(z[i, t] == 0,
                                name=f"no_overflow_{i}_{t}")

        # ── makespan ─────────────────────────────────────────────────────────
        for i in N_s:
            for t in T:
                m.addConstr(c_max >= (t + M_i[i]) * z[i, t],
                            name=f"makespan_{i}_{t}")

        # ── objective ────────────────────────────────────────────────────────
        m.setObjective(
            gp.quicksum(instance["p"][i] * y[i] for i in N_s)
            - epsilon * gp.quicksum(
               t * instance["w"][i] * z[i, t] for i in N_s for t in T
            ),
            GRB.MAXIMIZE
        )

        m.setParam("Seed", 42)
        m.setParam("MIPGap", 0.01)
        m.optimize()

        # ── harvest results ───────────────────────────────────────────────────
        if m.status == GRB.OPTIMAL:
            total_obj       += m.objVal
            global_makespan  = max(global_makespan, c_max.X)
            max_gap          = max(max_gap, m.MIPGap)

            for i in N_s:
                for t in T:
                    if z[i, t].X > 0.5:
                        all_start_times[i] = t
                        break

            all_unscheduled.extend(i for i in N_s if y[i].X < 0.5)

        elif m.status == GRB.INFEASIBLE:
            print(f"[skill {s}] INFEASIBLE — computing IIS...")
            m.computeIIS()
            m.write(f"model_skill{s}.ilp")
            for c in m.getConstrs():
                if c.IISConstr:
                    print(f"  Infeasible constraint: {c.ConstrName}")
            # propagate failure for this skill
            all_unscheduled.extend(N_s)

        else:
            print(f"[skill {s}] No optimal solution. Status: {m.status}")
            all_unscheduled.extend(N_s)

    # ── aggregate ─────────────────────────────────────────────────────────────
    elapsed_time    = round(time.time() - start_time, 2)
    best_value      = round(total_obj, 2)
    makespan        = round(global_makespan, 2)
    gap             = round(max_gap * 100, 2)
    prop_unscheduled = (
        round(len(all_unscheduled) / len(N) * 100, 2) if N else 0.0
    )
    
    #print(f"Elapsed: {elapsed_time}s | Obj: {best_value} | Gap: {gap}% | Makespan: {makespan}")

    return (elapsed_time, best_value, gap, makespan,
            all_start_times, all_unscheduled, prop_unscheduled)