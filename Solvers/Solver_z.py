
from gurobipy import GRB
import gurobipy as gp
import time

# Base MILP
def SolverZ(instance, scenarios=None, **kwargs):
    ''' MILP formulation including only variable z_i,t'''

    if scenarios is None:
        
        start_time = time.time()
        gp.setParam('OutputFlag', 0)

        model = gp.Model('ExactCrewScheduling')

        N = instance["I"] + instance["O"]
        T = range(instance["T"])

        # Variables
        y = model.addVars(N, vtype=GRB.BINARY, name="y")
        z = model.addVars(N, T, vtype=GRB.BINARY, name="z")   # initial start slot 
        c_max = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="c_max")

        for i in N:
            model.addConstr(gp.quicksum(z[i, t] for t in T) == y[i], name=f"start_once_{i}")

        M_i = instance["M_i"]
        
        for h in instance["H"]:
            for t in instance["T_h"][str(h)]:
                for s in instance["S"]:
                    model.addConstr(gp.quicksum(instance["w"][i] * z[i, tau] for i in N if instance["s"][i] == s for tau in T
                            if tau <= t < tau + M_i[i]) <= instance["W"][str(h)][s])
        # Time windows
        for g in instance["G"]:
            a = instance["G"][g]["a"]
            b = instance["G"][g]["b"]
            for i in instance["G"][g]["tasks"]: 
                for t in T:
                    c = b - M_i[i] + 1
                    if t < a or t > c:
                        model.addConstr(z[i, t] == 0)
        
        # No overflow beyond T
        for i in N:
            for t in T:
                if t + M_i[i] > instance["T"]:
                    model.addConstr(z[i, t] == 0, name=f"no_overflow_{i}_{t}")
        
        # Define makespan
        for i in N:
            for t in T:
                model.addConstr(c_max >= (t + M_i[i]) * z[i, t], name=f"makespan_{i}_{t}")
        
        # Objective
        epsilon = 1e-5
        model.setObjective(
            gp.quicksum(instance["p"][i] * y[i] for i in N)
            - epsilon * gp.quicksum(
                t * instance["w"][i] * z[i, t] for i in N for t in T
            ),
            GRB.MAXIMIZE
        )

        #model.setParam("MIPGap", 0.01)
        #model.setParam("TimeLimit", 180)
        model.setParam("Seed", 42)
        model.optimize()

        # Measure elapsed time
        elapsed_time = round(time.time() - start_time, 2)

        if model.status == GRB.OPTIMAL:
            best_value = round(model.objVal, 2)
            makespan = round(c_max.X, 2)
            gap = round(model.MIPGap * 100, 2) if model.MIPGap is not None else None

            # Task start times
            task_start_times = {}
            for i in N:
                for t in T:
                    if z[i, t].X > 0.5:
                        task_start_times[i] = t
                        break
        
            # Extract tasks unscheduled
            unscheduled_tasks = [i for i in N if y[i].X < 0.5] 
            # Proportion of tasks unscheduled
            prop_unscheduled = round((len(unscheduled_tasks) / len(N)) * 100, 2) if len(N) > 0 else 0.0

            print(f"Elapsed: {elapsed_time}s | Obj: {best_value} | Gap: {gap}% | Makespan: {makespan}")
            
            return elapsed_time, best_value, gap, makespan, task_start_times, unscheduled_tasks, prop_unscheduled
        
        elif model.status == GRB.INFEASIBLE:
            print("Model is infeasible. Computing IIS...")
            model.computeIIS()
            model.write("model.ilp")
            for c in model.getConstrs():
                if c.IISConstr:
                    print(f"Infeasible constraint: {c.ConstrName}")
            return elapsed_time, None, None, None, None, None, None
        
        else:
            print("No optimal solution found. Status code:", model.status)
            return elapsed_time, None, None, None, None, None, None 
        
    