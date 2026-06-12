import os
import pandas as pd
from collections import defaultdict

from Utils.args import parse_args
from Utils.io import build_plot_directory
from InstanceGeneration.config import Size
from Experiments.experiment_config import EXPERIMENTS
from plot import plot_skill_comparison
from Utils.io import load_all_jsons

BASE_DIR = "analysis_results"
os.makedirs(BASE_DIR, exist_ok=True)

def aggregate_metrics(df):

    grouped = df.groupby(["size", "solver", "config"])

    summary_rows = []
    skill_rows = []

    for (size, solver, config), group in grouped:

        n = len(group)

        # -------- Scalar metrics --------
        mean_unscheduled = group["unscheduled_tasks"].mean()
        mean_prop_unscheduled = group["prop_unscheduled"].mean()

        summary_rows.append({
            "size": size,
            "solver": solver,
            "config": config,
            "mean_unscheduled_tasks": mean_unscheduled,
            "mean_prop_unscheduled": mean_prop_unscheduled
        })

        # -------- Skill metrics --------
        skill_sum = defaultdict(float)
        skill_used_sum = defaultdict(float)

        for _, row in group.iterrows():

            for skill, value in row["avg_skill_prop"].items():
                skill_sum[skill] += float(value)

            for skill, value in row["avg_skill_prop_used"].items():
                skill_used_sum[skill] += float(value)

        for skill in skill_sum.keys():
            skill_rows.append({
                "size": size,
                "solver": solver,
                "config": config,
                "skill": skill,
                "mean_skill_prop": skill_sum[skill] / n,
                "mean_skill_prop_used": skill_used_sum[skill] / n
            })

    summary_df = pd.DataFrame(summary_rows)
    skill_df = pd.DataFrame(skill_rows)

    return summary_df, skill_df

def main(solver_name, size, **kwargs):

    df = load_all_jsons(BASE_DIR, size)

    summary_df, skill_df = aggregate_metrics(df)

    # Build config string safely
    config_str = "".join(f"{k}{v}" for k, v in kwargs.items()) if kwargs else ""
    
    output_dir = build_plot_directory(BASE_DIR, solver_name=solver_name, size=size, **kwargs)
    os.makedirs(output_dir, exist_ok=True) 
    
    # Save aggregated results
    file_path_metrics = os.path.join(output_dir, f"aggregated_metrics_{config_str}.xlsx")
    summary_df.to_excel(file_path_metrics, index=False) 
    
    file_path_skill = os.path.join(output_dir, f"aggregated_skill_usage_{config_str}.xlsx")
    skill_df.to_excel(file_path_skill, index=False)

    # Plot mean_skill_prop
    plot_skill_comparison(skill_df, solver_name, size, metric="mean_skill_prop", **kwargs)

if __name__ == "__main__":
    args = parse_args()
    
    sizes_to_analyze = [Size[s] for s in args.sizes]

    # Iterar sobre todas las configuraciones del solver
    for config in EXPERIMENTS.get(args.solver, [{}]):
        for size in sizes_to_analyze:
            main(solver_name=args.solver, size=size.value, **config)