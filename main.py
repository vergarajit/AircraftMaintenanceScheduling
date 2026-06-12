import argparse
from Experiments.experiments import run_generation
from Experiments.saa_experiments import run_generation as run_saa_generation
from Solvers.run_solver import run_solver
#from Solvers.run_solver_saa import run_solver_saa
from InstanceGeneration.config import Size
from Experiments.experiment_config import EXPERIMENTS

def parse_sizes(size_list):
    return [Size[s] for s in size_list]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--mode",
        choices=["generate", "solve"],
        required=True
    )

    parser.add_argument(
        "--size",
        nargs="+",  # permite uno o varios
        choices=["SMALL", "MEDIUM", "LARGE"],
        required=True
    )

    parser.add_argument(
    "--n",
    type=int,
    required=True,
    help="Número de instancias (seeds) a generar o resolver"
    )

    parser.add_argument(
    "--real",
    action="store_true",
    help="Generar instancias reales"
    )

    parser.add_argument(
    "--cv",
    type=float,
    help="Arrival rates"
    )

    parser.add_argument(
    "--solver",
    choices=["MILP", "MILP_BUFFER", "MILP_SAA", "MILP_Z", "MILP_SKILLS", "HEURISTIC"],
    required=False,
    default="MILP", 
    help="Tipo de solver a utilizar"
    )

    parser.add_argument(
    "--type",
    choices=["SAA", "DETERMINISTIC"],
    required=False,
    default="DETERMINISTIC", 
    help="Tipo de instancia a generar"
    )

    parser.add_argument(
    "--scenarios",
    type=int, 
    required=False,
    default=100, 
    help="Número de escenarios a generar"
    )

    args = parser.parse_args()

    sizes = parse_sizes(args.size) 

    if args.mode == "generate":

        if args.type == "DETERMINISTIC":
            run_generation(
                sizes=sizes, n_instances=args.n, cv=args.cv, real=args.real)
        
        else:
            run_saa_generation(
                sizes=sizes, n_instances=args.n, cv=args.cv, num_scenarios=args.scenarios, real=args.real)
        
    elif args.mode == "solve":
        
        if args.type == "DETERMINISTIC": 
            # Si se especifica un solver, filtramos solo ese
            solvers_to_run = [args.solver] if args.solver else EXPERIMENTS.keys()

            for solver_name in solvers_to_run:
                param_list = EXPERIMENTS[solver_name]
                for solver_params in param_list:
                    run_solver(
                        sizes=sizes, n_instances=args.n, solver_name=solver_name, solver_params=solver_params, real=args.real)
        else:
            # Si se especifica un solver, filtramos solo ese
            solvers_to_run = [args.solver] if args.solver else EXPERIMENTS.keys()

            for solver_name in solvers_to_run:
                param_list = EXPERIMENTS[solver_name]
                for solver_params in param_list:
                    
                    run_solver_saa(sizes=sizes, n_instances=args.n, solver_name=solver_name, solver_params=solver_params, cv= args.cv, real=args.real)
