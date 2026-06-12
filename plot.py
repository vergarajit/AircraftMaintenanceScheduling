import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import plotly.express as px
import os

from Utils.io import build_plot_directory

BASE_DIR = "analysis_results"

def plot_skill_comparison(skill_df, solver_name, size, metric="mean_skill_prop_used", **kwargs):
    # Construir carpeta  
    output_dir = build_plot_directory(base_dir=BASE_DIR, solver_name=solver_name, size=size, plot_type="skill", **kwargs)
    os.makedirs(output_dir, exist_ok=True)  # crear carpeta si no existe
    
    config_str = "".join(f"{k}{v}" for k, v in kwargs.items()) if kwargs else "" # This retunrs the buffer size 10, 20, 30
    file_name = f"plot_skill_usage_{size}_{config_str}.png"

    plt.close('all') 

    size_value = size.value if hasattr(size, "value") else size
    df_size = skill_df[skill_df["size"].str.upper() == size_value.upper()]

    # df_size = skill_df[skill_df["size"] == size]
    # df_size = skill_df[skill_df["size"].str.upper() == size.upper()]

    plt.figure(figsize=(12, 6))

    for (solver, config), group in df_size.groupby(["solver", "config"]):
        
        label = f"{solver}-{config}"
        plt.plot(group["skill"], group[metric], marker="o", label=label)

    plt.xlabel("Skill")
    plt.ylabel(f"Avg. Skill Utilization")
    #plt.title(f"Skill Comparison - {size}")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    # Guardar plot en la carpeta correcta
    plt.savefig(os.path.join(output_dir, file_name))
    plt.close()

def plot_skill_proportions(skills_proportion, solver_name, size, output_dir="analysis_results/plots", instance_name=None, selected_skills=None, hide_zero_skills=False, **kwargs):
    """
    Plot skill utilization percentages over the planning horizon.

    Parameters
    ----------
    skills_proportion : dict
        {skill: np.array of proportions in [0, 1]}
    selected_skills : list or set, optional
        Skills to plot. If None, plot all skills.
    hide_zero_skills : bool, default False
        If True, skip skills that are zero everywhere.
    """
     # Construir carpeta 
    output_dir = build_plot_directory(base_dir="analysis_results/plots", solver_name = solver_name, size=size, plot_type="skill", **kwargs)
    os.makedirs(output_dir, exist_ok=True)  # crear carpeta si no existe
    
    plt.close('all')

    # Filter skills if needed
    skills = skills_proportion
    if selected_skills is not None:
        skills = {
            k: v for k, v in skills_proportion.items()
            if k in selected_skills
        }

    # x-axis
    x = np.arange(len(next(iter(skills.values()))))

    plt.figure(figsize=(12, 6))

    for skill, values in skills.items():
        if hide_zero_skills and not np.any(values > 0):
            continue

        plt.plot(x, values * 100, label=skill) # Values * 100 for %

    plt.xlabel("Planning Horizon")
    plt.ylabel("Percentage (%)")
    plt.legend()
    plt.tight_layout()
    # Guardar plot en la carpeta correcta
    plt.savefig(os.path.join(output_dir, instance_name))
    plt.close()

def plot_scheduling_plan(instance, task_start_times, solver_name, size, output_dir="analysis_results/plots", instance_name=None, **kwargs):
    """
    Plots a Gantt-like schedule for tasks colored by group and skill.

    Parameters
    ----------
    instance : dict
        Instancia cargada.
    task_start_times : dict
        {task_id: start_slot}
    output_dir : str
        Carpeta donde guardar el HTML
    filename : str or None
        Nombre del archivo. Si None, se genera automáticamente.
    instance_name : str
        Nombre de la instancia, para generar el nombre del archivo
    size : Size
        Tamaño de la instancia
    kwargs : dict
        Otros parámetros, ej. buffer, gamma
    """

    output_dir = build_plot_directory(base_dir="analysis_results/plots", solver_name = solver_name, size=size, plot_type="schedule", **kwargs)

    os.makedirs(output_dir, exist_ok=True)
    
    # Mapea tareas a grupos
    task_to_group = {}
    for group_name, gdata in instance["G"].items():
        for task in gdata["tasks"]:
            task_to_group[task] = group_name

    # Preparar DataFrame
    rows = []
    for task, start in task_start_times.items():
        duration = instance["d"][task]
        finish = start + duration
        rows.append({
            "Task": task,
            "Start": start,
            "Finish": finish,
            "Duration": duration,
            "Group": task_to_group.get(task, "Unassigned"),
            "Skill": instance["s"].get(task),
            "Workers": instance["w"].get(task)
        })

    df = pd.DataFrame(rows)
    df["SlotStart"] = df["Start"]
    df["SlotEnd"] = df["Finish"] - df["Start"]

    fig = px.bar(
        df,
        x="SlotEnd",
        y="Skill",
        base="SlotStart",
        orientation="h",
        color="Group",
        hover_data={
            "Task": True,
            "Group": True,
            "SlotStart": True,
            "SlotEnd": True,
            "Skill": True,
            "Workers": True
        }
    )

    fig.update_yaxes(autorange="reversed", title="Skill")
    fig.update_xaxes(range=[0, instance["T"]], tickmode="linear", tick0=0, dtick=50, title="Time slots")
    fig.update_layout(legend_title="Group")

    # Nombre base
    instance_name = instance_name or "instance"

    # Asegurar extensión
    if not instance_name.endswith(".html"):
        instance_name += ".html"

    output_path = os.path.join(output_dir, instance_name)
    fig.write_html(output_path, config={"scrollZoom": True, "displayModeBar": True})
    print(f"Schedule plot saved: {output_path}")