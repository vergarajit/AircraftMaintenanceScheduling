import argparse
from InstanceGeneration.config import Size

def parse_args():
    parser = argparse.ArgumentParser(description="Analizar soluciones de mantenimiento")
    parser.add_argument("--solver", type=str, required=True, help="Nombre del solver a analizar")
    parser.add_argument("--sizes", type=str, nargs="+", choices=[s.name for s in Size], default=["SMALL"], help="Tamaños a analizar")
    parser.add_argument("--n", type=int, default=None, help="Número máximo de instancias a analizar")
    parser.add_argument("--plot_skills", action="store_true", help="Generar gráficos de skills")
    parser.add_argument("--plot_schedule", action="store_true", help="Generar gráficos de schedule")
    parser.add_argument("--real", action="store_true", help="Analizar instancias reales")
    #parser.add_argument("--n_scenarios", type=int, default=500, help="Número de escenarios Monte Carlo a generar")
    return parser.parse_args()
