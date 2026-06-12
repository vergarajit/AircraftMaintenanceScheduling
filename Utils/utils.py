import random
import math 

def generate_arrivals(I, O, T, cv, rng):
    """
    Generate arrival times using a Gamma inter-arrival process.

    Parameters
    ----------
    O : list
        List of task IDs
    T : int
        Time horizon
    cv : float
        Coefficient of variation (e.g., 0.1, 0.3, 0.6)
    rng : numpy.random.Generator
        Random number generator (for reproducibility)

    Returns
    -------
    a : dict
        a[i] = arrival time of task i
    """
    # Uniform arrival used at first 
    # a = {}
    #     for i in O:
    #         a[i] = self.rng.randint(0, T)

    # -------- CV generation ------------
     # Caso base: sin CV → uniforme
    if cv is None:
        return {i: 0 for i in O}
    
    T_max = T - 0.2 * T # Task arrive up to 80% of the horizon

    # Target: spread arrivals over horizon
    mean_interarrival = T_max / len(O)

    
    # Gamma parameters from CV
    k = 1 / (cv ** 2)              # shape
    theta = mean_interarrival / k  # scale

    a = {}
    t = 0

    for i in I:
        a[i] = 0

    for i in O:
        # sample inter-arrival time
        delta = rng.gamma(k, theta)

        t += int(delta)

        # clip to horizon
        t = min(t, T_max)

        a[i] = t

    return a

def truncated_normal(mean, std, low, high, rng):
    """Normal truncada simple por rechazo"""
    while True:
        x = rng.gauss(mean, std)
        if low < x < high:
            return x

def generate_rt(rng):
    u = rng.random()

    # 20% < 1 hora — Normal truncada
    if u < 0.20:
        return round(truncated_normal(mean=0.5, std=0.2, low=0.0025, high=1.0, rng=rng), 2)

    # 50% entre 1 y 5 — cola larga, sesgada a 1–2
    elif u < 0.70:
        value = 1 + rng.expovariate(1.3)
        return round(min(value, 5), 2)

    # 20% entre 5 y 10 — cola larga moderada
    elif u < 0.90:
        value = 5 + rng.expovariate(0.6)
        return round(min(value, 10), 2)

    # 9% entre 10 y 50 — cola larga fuerte
    elif u < 0.99:
        value = 10 + rng.expovariate(0.12)
        return round(min(value, 50), 2)

    # 1% entre 50 y 120 — extremos
    else:
        value = 50 + rng.expovariate(0.05)
        return round(min(value, 120), 2)

def generate_nrt(rng):
    u = rng.random()

    # 60% entre 0.1 y 10
    if u < 0.60:
        value = rng.lognormvariate(mu=0.0, sigma=0.9)
        return round(min(max(value, 0.1), 10), 2)

    # 35% entre 10 y 40 — cola larga, sesgada al mínimo
    elif u < 0.95:
        value = 10 + rng.expovariate(0.15)
        return round(min(value, 40), 2)

    # 4% entre 40 y 80
    elif u < 0.99:
        value = 40 + rng.expovariate(0.05)
        return round(min(value, 80), 2)

    # 1% entre 80 y 500
    else:
        value = 80 + rng.expovariate(0.02)
        return round(min(value, 500), 2)
    
def generate_at():
    u = random.random()

    # 60% entre 0.5 y 25 — cola larga suave, sesgada al mínimo
    if u < 0.60:
        value = 0.5 + random.expovariate(0.12)
        return round(min(value, 25), 2)

    # 20% entre 25 y 50 — cola larga moderada
    elif u < 0.80:
        value = 25 + random.expovariate(0.08)
        return round(min(value, 50), 2)

    # 20% entre 50 y 120 — cola larga fuerte
    else:
        value = 50 + random.expovariate(0.04)
        return round(min(value, 120), 2)

def generate_at_nrt():
    u = random.random()

    # 90% entre 0.15 y 30 — cola larga suave, sesgada al mínimo
    if u < 0.90:
        value = 0.15 + random.expovariate(0.10)
        return round(min(value, 30), 2)

    # 10% entre 30 y 130 — cola larga fuerte
    else:
        value = 30 + random.expovariate(0.04)
        return round(min(value, 130), 2)

def generar_grupos(T, G_min, G_max, seed=None):

    if seed is not None:
        random.seed(seed)

    slots_por_dia = 96
    H = T * slots_por_dia

    G = random.randint(G_min, G_max)

    rangos = {
        "corta": (0.05, 0.10),
        "media": (0.10, 0.30),
        "larga": (0.30, 0.70),
        "muy_larga": (0.60, 0.95),
    }

    tipos = ["corta", "media", "larga", "muy_larga"]

    while len(tipos) < G:
        tipos.append(random.choice(list(rangos.keys())))

    random.shuffle(tipos)

    grupos = {}

    for i, tipo in enumerate(tipos, start=1):

        prop_min, prop_max = rangos[tipo]

        dur_min = max(1, math.floor(prop_min * H))
        dur_max = max(dur_min + 1, math.floor(prop_max * H))
        duracion = random.randint(dur_min, dur_max)

        # ---- INICIO SEGÚN TIPO ----
        if tipo == "corta":
            # 50% cortas normales, 50% concentradas al final
            if random.random() < 0.5:
                inicio = random.randint(0, H - duracion)
            else:
                inicio_min = math.floor(0.80 * H)
                inicio_min = min(inicio_min, H - duracion)
                inicio = random.randint(inicio_min, H - duracion)
        else:
            inicio = random.randint(0, H - duracion)

        fin = inicio + duracion

        # --- ESTRUCTURA ORIGINAL ---
        grupos[f"g{i}"] = {"a": inicio, "b": fin}
        grupos[f"g_nrt{i}"] = {"a": inicio, "b": fin}

    return grupos