# from Solvers.Solver import Solver as milp
# from Solvers.Solver_z import SolverZ as milp_z
# from Solvers.SolverSkill import SolverBySkill as milp_skill
# from Solvers.SolverBuffer import SolverBuffer as milp_buffer
# from Solvers.SolverSAA import SolverSAA as milp_saa 

from Solvers.warm_start import greedy_warm_start as heuristic

SOLVER_REGISTRY = {
    "HEURISTIC": heuristic, 
    # "MILP": milp,
    # "MILP_Z": milp_z,
    # "MILP_SKILLS": milp_skill,
    # "MILP_BUFFER": milp_buffer,
    # "MILP_SAA": milp_saa
} 
