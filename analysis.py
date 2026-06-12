import os
import pandas as pd
from Utils.args import parse_args
from metrics import compute_skill_proportion 
from plot import plot_skill_proportions, plot_scheduling_plan
from InstanceGeneration.config import Size
from Experiments.experiment_config import EXPERIMENTS
from Utils.io import load_instance, load_solution

# BASE_DIR = "InstanceGeneration/instances"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESULTS_DIR = "Results"
ANALYSIS_DIR = "analysis_results"
os.makedirs(ANALYSIS_DIR, exist_ok=True)


def analyze_results(solver_name, sizes, n_instances=None, plot_skills=False, plot_schedule=False, real=False, **kwargs):
    """Analiza resultados para un solver y tamaños dados, usando parámetros dinámicos"""
    for size in sizes:
        # Dentro de analyze_results o antes de llamar a plot
        if solver_name in ["MILP_BUFFER"]: 
            # Carpeta base + tamaño + parámetros (buffer o gamma)
            config_str = "".join(f"{k}{v}" for k, v in kwargs.items()) if kwargs else "default"
            output_dir = os.path.join(ANALYSIS_DIR, "plots", solver_name, size.value, config_str)
        else:
            config_str = "" 
            # Para MILP simple o sin parámetros
            output_dir = os.path.join(ANALYSIS_DIR, "plots", solver_name, size.value)

        # Asegurarse de que exista
        os.makedirs(output_dir, exist_ok=True)

        # instance_folder = os.path.join(BASE_DIR, size.value)
        if real: 
            instance_folder = os.path.join(BASE_DIR, "InstanceGeneration", "instances", size.value.upper(), "REAL")
        else:
            instance_folder = os.path.join(BASE_DIR, "InstanceGeneration", "instances", size.value.upper()) 

        files = sorted(f for f in os.listdir(instance_folder) if f.endswith(".json"))
        print(instance_folder)
        if n_instances:
            files = files[:n_instances]

        all_results = []

        for file in files:
            print(file)
            instance = load_instance(instance_folder, file)
            solution = load_solution(RESULTS_DIR, solver_name, size, file, **kwargs)

            task_start_times = solution.get("task_start_times", {})
            unscheduled_tasks = solution.get("unscheduled_tasks", [])

            # Calcular métricas
            skill_usage, skill_proportion, avg_skill_prop, avg_skill_prop_used = compute_skill_proportion(instance, task_start_times)
            
            total_tasks = len(instance["I"]) + len(instance["O"])
            prop_unscheduled = round(len(unscheduled_tasks) / total_tasks * 100, 4)

            # Guardar métricas agregadas
            all_results.append({
                "size": size.name,
                "instance": file,  # o file.replace(".xlsx","") si prefieres
                "solver": solver_name,
                "config": config_str,
                "unscheduled_tasks": len(unscheduled_tasks),
                "prop_unscheduled": prop_unscheduled,
                "avg_skill_prop": avg_skill_prop,
                "avg_skill_prop_used": avg_skill_prop_used
            })

            if plot_skills:
                plot_skill_proportions(skill_proportion, solver_name=solver_name, size=size, output_dir=output_dir, instance_name=file.replace(".json", ""), selected_skills=None, hide_zero_skills=True, **kwargs)

            if plot_schedule:
                plot_scheduling_plan(instance, task_start_times, solver_name=solver_name, size=size, output_dir=output_dir, instance_name=file.replace(".json", ""), **kwargs)

        # Guardar Excel resumen por tamaño y configuración
        # config_str = "".join(f"{k}{v}" for k, v in kwargs.items()) if kwargs else "default"
        # ----- Guardar Excel -----
        df = pd.DataFrame(all_results)
        excel_path = os.path.join(ANALYSIS_DIR, f"{size.value}_{solver_name}_{config_str}metrics.xlsx")
        df.to_excel(excel_path, index=False)

        # ----- Guardar JSON -----
        json_path = os.path.join(ANALYSIS_DIR, f"{size.value}_{solver_name}_{config_str}metrics.json")
        df.to_json(json_path, orient="records", indent=4)

        print(f"Análisis de {size.value} guardado en {excel_path}")


if __name__ == "__main__":
    args = parse_args()
    sizes_to_analyze = [Size[s] for s in args.sizes]

    # Iterar sobre todas las configuraciones del solver
    for config in EXPERIMENTS.get(args.solver, [{}]):
        print(f"Analizando solver {args.solver} con configuración {config}")
        analyze_results(
            solver_name=args.solver,
            sizes=sizes_to_analyze,
            n_instances=args.n,
            plot_skills=args.plot_skills,
            plot_schedule=args.plot_schedule,
            real=args.real,
            **config
        )
