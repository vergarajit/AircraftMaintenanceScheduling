
1. Generar n instancias reales/saa:  

python3 main.py --mode generate --size MEDIUM --n 3 --real (static)
python3 main.py --mode generate --size MEDIUM --n 3 --cv 0.6 --real (dynamic)

python3 main.py --mode generate --size SMALL --n 5 --cv 0.6 --scenarios 2 --type SAA 

2. Resolver instancias sinteticas:
python3 main.py --mode solve --size MEDIUM --n 1 --real --solver MILP 

3. Run pipeline 
python3 run_pipeline.py 

