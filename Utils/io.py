import os
import json 
import pandas as pd 

def load_all_jsons(base_dir, size):
    records = []
    size = size.lower()  # por si pasan "MEDIUM" o "Medium"

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".json") and file.lower().startswith(f"{size}_"):
                with open(os.path.join(root, file), "r") as f:
                    data = json.load(f)

                    if isinstance(data, list):
                        records.extend(data)
                    else:
                        records.append(data)

    return pd.DataFrame(records)

# def save_instance(data, size_name, seed, base_path, cv, tipo="instances", real=False):
#     """
#     Guarda instancias o realizaciones de escenarios de duración.
#     """
#     # Carpeta según tipo
#     # Si es Enum, convertir a string
#     if hasattr(size_name, "name"):
#         size_name = size_name.name 

#     folder = os.path.join(base_path, tipo, size_name, cv)
#     os.makedirs(folder, exist_ok=True)

#     # Nombre del archivo
#     if real: 
#         filename = f"real_instance_{seed}.json"
#         file_path = os.path.join(folder, "REAL", filename)
#     else: 
#         filename = f"instance_seed{seed}.json"
#         file_path = os.path.join(folder, filename)

#     os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
#     # Guardar JSON
#     with open(file_path, "w") as f:
#         json.dump(data, f, indent=4)


def save_instance(data, size_name, seed, base_path, cv=None, tipo="instances", real=False):
    """
    Guarda instancias o realizaciones de escenarios de duración.
    """
    # Si es Enum, convertir a string
    if hasattr(size_name, "name"):
        size_name = size_name.name 

    # Construir ruta dinámicamente (sin if extra)
    parts = [base_path, tipo, size_name, cv]
    folder = os.path.join(*[p for p in parts if p is not None])

    # Nombre del archivo
    filename = f"real_instance_{seed}.json" if real else f"instance_seed{seed}.json"

    # Si es real, agregar subcarpeta "REAL"
    if real:
        folder = os.path.join(folder, "REAL")

    os.makedirs(folder, exist_ok=True)

    file_path = os.path.join(folder, filename)

    # Guardar JSON
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def build_plot_directory(base_dir, solver_name, size=None, plot_type=None, **kwargs):
    """
    Construye la ruta:
    base/solver/[size]/[config]/plot_type

    - size es opcional
    - config (kwargs) es opcional
    """
    path_parts = [base_dir, solver_name]

    # Agregar size solo si existe
    if size is not None:
        path_parts.append(getattr(size, "value", size))

    # Agregar configuración si hay parámetros extra
    if kwargs:
        config_str = "_".join(f"{k}{v}" for k, v in sorted(kwargs.items()))
        path_parts.append(config_str)

    # Agregar tipo de plot
    if plot_type is not None:
        path_parts.append(plot_type)

    final_path = os.path.join(*path_parts)
    os.makedirs(final_path, exist_ok=True)

    return final_path

def make_solution_folder(results_dir, solver_name, size_value, solver_params=None):
    """
    Devuelve la carpeta donde guardar los resultados, considerando
    size y parámetros del solver.
    """
    if solver_params is None:
        solver_params = {}

    # Carpeta base por tamaño
    folder = os.path.join(results_dir, solver_name, size_value)

    # Solo añadir subcarpeta si hay parámetros experimentales distintos de 0 o None
    param_string = "_".join(
        f"{k}{int(v*100) if isinstance(v, float) else v}" 
        for k, v in solver_params.items() 
        if v not in [0, None]
    )

    if param_string:
        folder = os.path.join(folder, param_string)

    os.makedirs(folder, exist_ok=True)
    return folder

def load_instance(BASE_DIR, file):
    path = os.path.join(BASE_DIR, file)
    with open(path) as f:
        return json.load(f)

def load_solution(RESULTS_DIR, solver_name, size, file, **kwargs):
    """Carga la solución según el solver y sus parámetros (buffer, gamma, etc.)"""
    path_parts = [RESULTS_DIR, solver_name, size.value]

    # Agrega parámetros si existen
    for key in ["buffer", "gamma"]:
        if kwargs.get(key) is not None:
            path_parts.append(f"{key}{kwargs[key]}")

    file_path = os.path.join(*path_parts, file.replace(".json", "_solution.json"))
    #print(f"Printing file path for MILP_BUFFFER {file_path}")
    with open(file_path) as f:
        return json.load(f)
    