import os 
import random 
import numpy as np 
import pandas as pd 

from Utils.io import save_instance
from Utils.utils import generate_arrivals
from InstanceGeneration.config import ExperimentConfig

class MaintenanceInstanceGenerator: 
    def __init__(
        self,
        config: ExperimentConfig,
        tasks_file,
        groups_file,
        cv, 
        num_days=18,
        workers_by_shift=None,
        slot_minutes=15
    ):
        """
        Parameters
        ----------
        tasks_file : str
            Path to tasks.xlsx
        groups_file : str
            Path to milestones_pctg.xlsx
        num_days : int
            Planning horizon in days
        workers_by_shift : dict
            Available workers per shift (e.g., {0:4, 1:4, 2:3})
        slot_minutes : int
            Length of a time slot in minutes
        """
        self.config = config
        self.rng = random.Random(config.seed)
        self.np_rng = np.random.default_rng(config.seed)

        self.df_tasks = pd.read_excel(tasks_file, sheet_name="tasks")
        self.df_groups = pd.read_excel(groups_file, sheet_name="milestones_pctg")
        self.cv = cv 

        self.num_days = num_days
        self.slot_minutes = slot_minutes

        if workers_by_shift is None:
            self.workers_by_shift = {0: 4, 1: 4, 2: 3}
        else:
            self.workers_by_shift = workers_by_shift

        # Derived constants
        self.slots_per_hour = 60 // slot_minutes
        self.T = num_days * 24 * self.slots_per_hour
        self.T_hours = num_days * 24


    def generate(self):
        df_tasks = self.df_tasks
        df_groups = self.df_groups

        # -------------------
        # Task sets
        # -------------------
        df_tasks['hh_nrc'] = pd.to_numeric(df_tasks['hh_nrc'], errors='coerce').fillna(0)
        I = df_tasks["task"].tolist()

        O = []
        for i in I:
            if df_tasks.loc[df_tasks["task"] == i, "hh_nrc"].values[0] > 0:
                O.append(i + "_nr")

        # -------------------
        # Skills
        # -------------------
        Skills = df_tasks["skill_rc"].unique().tolist()
        S = list(set(Skills)) 

        s = {i: df_tasks.loc[df_tasks["task"] == i, "skill_rc"].values[0] for i in I}
        for i in O:
            base = i.replace("_nr", "") 
            s[i] = df_tasks.loc[df_tasks["task"] == base, "skill_nrc"].values[0]

        # -------------------
        # Workers per task
        # -------------------
        w = {i: int(df_tasks.loc[df_tasks["task"] == i, "workers"].values[0]) for i in I}
        for i in O:
            base = i.replace("_nr", "")
            w[i] = int(df_tasks.loc[df_tasks["task"] == base, "workers"].values[0])

        # -------------------
        # Durations (in slots)
        # -------------------
        d = {i: df_tasks.loc[df_tasks["task"] == i, "hh_rc"].values[0] for i in I}
        for i in O:
            base = i.replace("_nr", "")
            d[i] = df_tasks.loc[df_tasks["task"] == base, "hh_nrc"].values[0]

        M_i = {}
        for i in d:
            slots = ((d[i] / w[i]) * 60) / self.slot_minutes
            M_i[i] = max(1, int(round(slots)))

        # -------------------
        # Priorities
        # -------------------
        p = {i: int(df_tasks.loc[df_tasks["task"] == i, "priority"].values[0]) for i in I}
        for i in O:
            base = i.replace("_nr", "")
            p[i] = int(df_tasks.loc[df_tasks["task"] == base, "priority"].values[0])
     
        # -------------------
        # Groups
        # -------------------
        # Routine
        G = {g: {"a": int(df_groups.loc[df_groups["milestone"] == g, "start_milestone_pctg"].values[0] * self.T),
                "b": int(df_groups.loc[df_groups["milestone"] == g, "end_milestone_pctg"].values[0] * self.T), "tasks": []} for g in df_groups["milestone"].tolist()}

        # Non-routine 
        G = {g: {"a": int(df_groups.loc[df_groups["milestone"] == g, "start_milestone_pctg"].values[0] * self.T),
                "b": int(df_groups.loc[df_groups["milestone"] == g, "end_milestone_pctg"].values[0] * self.T), "tasks": []} for g in df_groups["milestone"].tolist()}
        
        for i in I:
            g = df_tasks.loc[df_tasks["task"] == i, "milestone_rc"].values[0]
            if g in G:
                G[g]["tasks"].append(i)


        # Add non-routine tasks
        for i in O:
            base = i.replace("_nr", "")
            g = df_tasks.loc[df_tasks["task"] == base, "milestone_nrc"].values[0]
            if g in G:
                G[g]["tasks"].append(i)
        
        # Remove empty groups
        G = {g: G[g] for g in G if G[g]["tasks"]}
            
            # base = i.replace("_nr", "")
            # row = df_groups.loc[df_groups["milestone"] == g]

            # if row.empty:
            #     raise ValueError(f"Milestone '{g}' no existe en df_groups")

            # G[g] = {
            #     "a": int(row["start_milestone_pctg"].iloc[0] * self.T),
            #     "b": int(row["end_milestone_pctg"].iloc[0] * self.T),
            #     "tasks": []
            # }

        # # -------------------
        # Shifts
        # -------------------
        H = list(range(self.T_hours // 8))

        T_h = {str(h): [] for h in H}
        for t in range(self.T_hours):
            h = t // 8
            T_h[str(h)] += [self.slots_per_hour * t + i for i in range(self.slots_per_hour)]

        # -------------------
        # Workforce capacity
        # -------------------
        at_skill = []
        W = {}
        for h in H:
            W[str(h)] = {}
            for skill in S:
                if skill in at_skill:
                    W[str(h)][skill] = 2
                else:
                    W[str(h)][skill] = self.workers_by_shift.get(h, self.workers_by_shift[max(self.workers_by_shift)])
        
        a = {}
        for i in O:
            a[i] = self.rng.randint(0, self.T)

        a = generate_arrivals(I, O, self.T, self.cv, self.np_rng) 

        instance = {
            "T": self.T,
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

        base_path = os.path.dirname(os.path.abspath(__file__))
        CV = f"CV{self.cv}" if self.cv is not None else None

        instance = save_instance(instance, self.config.size.name, self.config.seed, base_path, CV, tipo="instances", real=True)

        return instance
 