import os
import json
import pandas as pd 
from Solvers.registry import SOLVER_REGISTRY
from Solvers.registry import SOLVER_REGISTRY
from Utils.io import make_solution_folder


BASE_DIR = "InstanceGeneration/instances"
RESULTS_DIR = "Results"

REAL_INSTANCES_DIR = "REAL"

os.makedirs(RESULTS_DIR, exist_ok=True)

def run_solver(sizes, n_instances=None, solver_name="MILP", solver_params=None, real=False):
    """
    sizes: lista de Size (SMALL, MEDIUM, LARGE)
    n_instances: máximo número de instancias por tamaño (None = todas)
    solver_name: nombre del solver
    solver_params: diccionario con parámetros específicos del solver (ej: buffer, delta)
    """

    if solver_params is None:
        solver_params = {} 

    if solver_name not in SOLVER_REGISTRY:
        raise ValueError(f"Solver '{solver_name}' no registrado.")

    solver_function = SOLVER_REGISTRY[solver_name]

    for size in sizes:
        
        if real:
            instance_folder = os.path.join(BASE_DIR, size.value, REAL_INSTANCES_DIR)
        else:
            instance_folder = os.path.join(BASE_DIR, size.value)

        solution_folder = make_solution_folder(
            results_dir=RESULTS_DIR,
            solver_name=solver_name,
            size_value=size.value,
            solver_params=solver_params
        )

        os.makedirs(solution_folder, exist_ok=True)

        files = [f for f in os.listdir(instance_folder) if f.endswith(".json")]
        files.sort()

        if n_instances is not None:
            files = files[:n_instances]

        size_results = []

        for file in files:

            instance_path = os.path.join(instance_folder, file)
            with open(instance_path) as f:
                instance = json.load(f) 

            # Aquí se llama al solver con solo los parámetros que le correspondan
            if solver_name == "HEURISTIC":
                (warm_start_dict,elapsed_time, best_value, gap, makespan, task_start_times, unscheduled_tasks, prop_unscheduled) = solver_function(
                    instance, **solver_params
                )
            else: 
                (elapsed_time, best_value, gap, makespan, task_start_times, unscheduled_tasks, prop_unscheduled) = solver_function(
                    instance, **solver_params
                )

            # Guardar SOLO solución estructural
            solution_data = {
                "task_start_times": task_start_times,
                "unscheduled_tasks": unscheduled_tasks,
                "makespan": makespan
            }

            solution_path = os.path.join(solution_folder, file.replace(".json", "_solution.json"))
            os.makedirs(os.path.dirname(solution_path), exist_ok=True)
            
            with open(solution_path, "w") as f:
                json.dump(solution_data, f, indent=4)

            # Guardar métricas agregadas
            size_results.append({
                "file": file,
                "elapsed_time": elapsed_time,
                "objective": best_value,
                "gap": gap,
                "makespan": makespan,
                "unscheduled_tasks": len(unscheduled_tasks) if unscheduled_tasks else 0,
                "prop_unscheduled": prop_unscheduled
            })

            print(f"Resolved {file}")

        # Guardar Excel por tamaño
        df = pd.DataFrame(size_results)

        if real:
            excel_path = os.path.join(solution_folder, f"Statistics_{size.name}_real.xlsx")
        else: 
            excel_path = os.path.join(solution_folder, f"Statistics_{size.name}.xlsx")
        df.to_excel(excel_path, index=False)

        print(f"\nResultados de {size.name} guardados en: {excel_path}")

