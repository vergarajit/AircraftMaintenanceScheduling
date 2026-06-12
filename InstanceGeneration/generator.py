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

        base_path = os.path.dirname(os.path.abspath(__file__))
        CV = f"CV{self.cv}" if self.cv is not None else None
        instance = save_instance(instance, self.config.size.name, self.config.seed, base_path, CV, tipo="instances")

        return instance
