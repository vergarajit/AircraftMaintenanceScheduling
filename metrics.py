from collections import defaultdict
import numpy as np 
import math 



def compute_skill_proportion(instance, task_start_times):
    """
    Compute proportion of used workers per skill per time slot.

    Returns
    -------
    skill_proportion : dict
        {skill: np.array of length T+1 with usage proportion}
    skill_usage : dict 
    {skill: np.array of lenght T+1 with number of workers used}
    """

    T = instance["T"]

    # Available workers per skill per slot
    workers_per_skill = defaultdict(lambda: np.zeros(T + 1))

    for shift_id in instance["H"]:
        shift_id_str = str(shift_id)
        shift_slots = instance["T_h"][shift_id_str]

        for t in shift_slots:
            for skill, n_workers in instance["W"][shift_id_str].items():
                workers_per_skill[skill][t] += n_workers

    # Skill usage per slot
    skill_usage = defaultdict(lambda: np.zeros(T + 1))

    N = instance["I"] + instance["O"]
    for task_id in N:
        if task_id not in task_start_times:
            continue

        start = task_start_times[task_id]
        duration = math.ceil(instance["M_i"][task_id] / instance["w"][task_id])
        skill = instance["s"][task_id]

        for t in range(start, min(start + duration, T + 1)):
            # assuming w[task_id] workers are used
            skill_usage[skill][t] += instance["w"][task_id]

    # Compute proportion used per skill
    skill_proportion = {}

    for skill, available_per_slot in workers_per_skill.items():
        prop = np.zeros(T + 1)
        workers = available_per_slot > 0
        prop[workers] = skill_usage[skill][workers] / available_per_slot[workers]
        skill_proportion[skill] = prop

    avg_skill_proportion = {skill: round((100 * prop.mean()), 2) for skill, prop in skill_proportion.items()}
    avg_skill_proportion_when_used = {}

    for skill, prop in skill_proportion.items():
        prop_workers = prop > 0 
        avg_skill_proportion_when_used[skill] = round((100 * prop[prop_workers].mean()), 2) if prop_workers.any() else 0.0

    skill_usage = dict(skill_usage)

    return skill_usage, skill_proportion, avg_skill_proportion, avg_skill_proportion_when_used
