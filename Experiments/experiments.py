import os 
from InstanceGeneration.config import ExperimentConfig, params_dict
from InstanceGeneration.generator import InstanceGenerator
from InstanceGeneration.maintenance_generator import MaintenanceInstanceGenerator


# ----- Configuración de experimentos -----
OUTPUT_DIR = "instances"  # carpeta base de instancias

def run_generation(sizes, n_instances, cv, real=False):

    for size in sizes:
        for seed in range(n_instances):

            config = ExperimentConfig(size=size, seed=seed, params=params_dict, output_dir=OUTPUT_DIR)
            
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))

            base_path = os.path.join(BASE_DIR, "..", "InstanceGeneration", OUTPUT_DIR, size.value, "REAL", f"instance_{seed}.xlsx")
            base_path = os.path.abspath(base_path)

            milestones_path = os.path.join(BASE_DIR, "..", "InstanceGeneration", OUTPUT_DIR, size.value, "REAL", "milestones_pctg.xlsx")
            milestones_path = os.path.abspath(milestones_path)
           
            if real:
                generator = MaintenanceInstanceGenerator(config, base_path, milestones_path, cv)
            else:
                generator = InstanceGenerator(config, cv)

            generator.generate()

