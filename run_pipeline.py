import subprocess
import logging
from datetime import datetime
import os

# Crear carpeta logs
os.makedirs("logs", exist_ok=True)

# Nombre de archivo con timestamp
log_filename = f"logs/pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  
    ]
)

def run_command(cmd):
    logging.info(f"Running: {cmd}")

    result = subprocess.run(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    logging.info(result.stdout)

    if result.stderr:
        logging.error(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")

def main():
    SIZE = "MEDIUM"
    N = 2
    SOLVER = "HEURISTIC"

    # Step 1: Generate
    run_command(f"python3 main.py --mode generate --size {SIZE} --n {N} --real")

    # Step 2: Solve
    run_command(f"python3 main.py --mode solve --size {SIZE} --n {N} --solver {SOLVER} --type DETERMINISTIC --real")

    # Step 3: Analyze
    #run_command(f"python3 analysis.py --solver {SOLVER} --sizes {SIZE} --n {N} --real") 
    run_command(f"python3 analysis.py --solver {SOLVER} --sizes {SIZE} --n {N} --plot_skills --plot_schedule --real") # to generate plots

    # Step 4: Metrics
    run_command(f"python3 aggregated_metrics.py --solver {SOLVER} --sizes {SIZE} --n {N}")

    logging.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()