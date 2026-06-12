import os
import random
import numpy as np 

from Utils.utils import generate_rt, generate_nrt, generar_grupos, generate_arrivals
from Utils.io import save_instance
from InstanceGeneration.config import ExperimentConfig

class InstanceGenerator:

    def __init__(self, config: ExperimentConfig, cv):
        self.config = config
        self.p = config.current

        self.cv = cv 
        self.rng = random.Random(config.seed)
        self.np_rng = np.random.default_rng(config.seed)
  
    def generate(self): 

        # Sample parameters from ranges
        T = self.rng.randint(*self.p.T)
        I_set = self.rng.randint(*self.p.I_set)

        nr_ratio = self.p.nr_ratio
        groups = self.p.groups
        workers = self.p.workers
        skill = self.p.skill

        Slots = T * 4 * 24

        # ----- Global sets -----
        Skills = [f"S{i}" for i in range(1, 11)]
        S = self.rng.sample(Skills, self.rng.randint(skill[0], skill[1]))

        H = list(range(T * 24 // 8))

        I = [f"r{i}" for i in range(1, I_set)]
        O = [f"o{i}" for i in range(1, int(I_set * nr_ratio))]
        N = I + O

        # ----- Durations -----
        d = {}
        for r in I:
            d[r] = generate_rt(self.rng)
        for o in O:
            d[o] = generate_nrt(self.rng)

        # ----- Skills per task -----
        s = {i: self.rng.choice(S) for i in N}

        # ----- Groups -----
        G = generar_grupos(T, groups[0], groups[1])

        regular_groups = [g for g in G if g.startswith("g") and "_" not in g]
        nrt_groups = [g for g in G if g.startswith("g_nrt")]

        task_group = {}

        weights = [self.rng.random() for _ in regular_groups]
        weights_nrt = [self.rng.random() for _ in nrt_groups]

        for r in I:
            task_group[r] = self.rng.choices(regular_groups, weights=weights, k=1)[0]

        for o in O:
            task_group[o] = self.rng.choices(nrt_groups, weights=weights_nrt, k=1)[0]

        for g in G:
            G[g]["tasks"] = [t for t, grp in task_group.items() if grp == g]
            G[g]["a"] = int(G[g]["a"])
            G[g]["b"] = int(G[g]["b"])

        w = {}
        p = {}

        for i in N:
            w[i] = self.rng.randint(1, 4)
            p[i] = 1 if i in O else self.rng.randint(1, 4)

        T_h = {h: [] for h in H}
        T_hours = T * 24

        for t in range(T_hours):
            h = t // 8
            T_h[h].extend([t * 4 + k for k in range(4)])

        M_i = {}
        for i in d:
            dur_slots = ((d[i] / w[i]) * 60) / 15 
            M_i[i] = max(1, int(round(dur_slots)))

        W = {}
        for h in H:
            W[h] = {}
            for sk in S:
                if h % 3 == 0:
                    W[h][sk] = workers[0]
                elif h % 3 == 1:
                    W[h][sk] = workers[1]
                else:
                    W[h][sk] = workers[2]

        G = {g: G[g] for g in G if G[g]["tasks"]}

        a = generate_arrivals(I, O, Slots, self.cv, self.np_rng) 

        instance = {
            "T": Slots,
            "S": S,
            "I": I,
            "O": O,
            "d": d,
            "M_i": M_i,
            "s": s,
            "G": G,
            "w": w,
            "H": H,
            "T_h": T_h,
            "W": W,
            "p": p,
            "a": a
        }

        instance["seed"] = self.config.seed

        return instance

    def generate_nrt_scenario(self, base_instance, scenario_seed):
        """
        Re-run only the NRT-dependent part of instance generation
        with a fresh seed, producing one SAA scenario.
        """
        rng     = random.Random(scenario_seed)
        np_rng  = np.random.default_rng(scenario_seed)

        I_set = self.rng.randint(*self.p.I_set)
        I   = base_instance["I"]
        S       = base_instance["S"]
        T       = base_instance["T"]
        w_base  = base_instance["w"]
        p_base  = base_instance["p"]
        s_base  = base_instance["s"]
        G_base  = base_instance["G"]
        d_base = base_instance["d"]
        M_i_base = base_instance["M_i"]
        a_base = base_instance["a"]

        # --- Exactly your existing NRT logic, just with the new rng ---
        nr_ratio = self.p.nr_ratio
       
        O = [f"o{i}" for i in range(1, int(I_set * nr_ratio))]

        # Durations
        d_omega = {o: generate_nrt(rng) for o in O}

        # Skills, crew demand, priority — re-sampled for arrived tasks
        s_omega = {o: rng.choice(S) for o in O}
        w_omega = {o: rng.randint(1, 4) for o in O}
        p_omega = {o: 1 for o in O}

        # M_i
        M_i_omega = {o: max(1, int(round((d_omega[o] / w_omega[o]) * 60 / 15))) for o in O}

        # Group assignment — re-sampled

        G_omega = {}

        for g in G_base:

            G_omega[g] = {**G_base[g], "tasks": ([] if g.startswith("g_nrt") else list(G_base[g]["tasks"]))}

        nrt_groups = [g for g in G_base if g.startswith("g_nrt")]
        weights_nrt = [rng.random() for _ in nrt_groups]

        for o in O:
            g = rng.choices(nrt_groups, weights=weights_nrt, k=1)[0]
            G_omega[g]["tasks"].append(o)

        # Remove empty groups
        G_omega = {g: data for g, data in G_omega.items() if data["tasks"]}

        # Arrivals
        a_omega = generate_arrivals(I, O, T, self.cv, np_rng)

        return {
            "omega":  None,          # filled in by generate_scenarios
            "S":      S,
            "I":      I,
            "O":      O,
            "d":      {**d_omega, **d_base}, 
            "M_i":    {**M_i_omega,  **M_i_base},
            "s":      {**s_omega,  **s_base}, #mantiene escenario base y copia nuevos de omega 
            "G":      G_omega,
            "w":      {**w_omega,  **w_base}, #mantiene escenario base y copia nuevos de omega 
            "p":      {**p_omega,  **p_base}, #mantiene escenario base y copia nuevos de omega 
            "a":      {**a_omega, **a_base} #mantiene escenario base y copia nuevos de omega 
        }
    
    def generate_scenarios(self, base_instance, Omega):
        """
        Generate Omega SAA scenarios from a base instance.
        Each scenario re-runs generate_nrt_scenario with seed = base_seed + omega.
        """
        scenarios = []
        for omega in range(Omega):
            scenario_seed = self.config.seed + omega
            scenario = self.generate_nrt_scenario(base_instance, scenario_seed)
            scenario["omega"] = omega
            scenario["scenario_seed"] = scenario_seed
            scenarios.append(scenario)
        return scenarios, self.config.seed, scenario_seed
    
    def build_solver_instance(self, base_instance, scenarios, cv, size, scenario_seed):
        """Merge deterministic skeleton with scenario-specific NRT fields."""

        inst = {**base_instance}
        inst["scenarios"] = []
        
        for scenario in scenarios:
            scen_data = {
                "S": scenario["S"], 
                "I": scenario["I"],
                "O": scenario["O"],
                "d": scenario["d"],
                "M_i": {**base_instance["M_i"], **scenario["M_i"]},
                "s": scenario["s"],
                "G": scenario["G"], #scenario["G"],
                "w": scenario["w"],
                "p": scenario["p"],
                "a": scenario["a"]
            }
            inst["scenarios"].append(scen_data)

        base_path = os.path.dirname(os.path.abspath(__file__))
        CV = f"CV{cv}" if cv is not None else None
        instance = save_instance(inst, size, scenario_seed, base_path, CV, tipo="saa_instances")

        return instance