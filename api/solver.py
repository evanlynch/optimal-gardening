import os

import numpy as np
import pandas as pd
import pulp

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_data():
    plant_info = pd.read_csv(os.path.join(DATA_DIR, "plant_data.csv"))
    plant_info.index.name = "plant_index"

    family = ["evan", "gina", "liesse", "lizzie", "jack"]
    plant_info["avg_pref"] = np.average(
        plant_info[family], axis=1, weights=[0.5, 0.5, 0, 0, 0]
    )

    bed_info = pd.read_csv(os.path.join(DATA_DIR, "bed_data.csv"))
    bed_info.index.name = "bed_index"

    return plant_info, bed_info


def build_sun_matrix(plant_info, bed_info):
    plant_sun = plant_info.sun.to_numpy()
    bed_sun = bed_info.sun.to_numpy()
    num_plants = len(plant_info)
    num_beds = len(bed_info)

    sun = np.ones(shape=(num_plants, num_beds))
    for p in range(num_plants):
        for b in range(num_beds):
            if plant_sun[p] != bed_sun[b]:
                sun[p, b] = 0
    return sun


def optimize(num_years: int, yummy_weight: float, variety_weight: float) -> dict:
    plant_info, bed_info = load_data()

    plants = plant_info.name.to_numpy()
    plant_index = plant_info.index.to_numpy()
    num_plants = len(plants)
    preferences = plant_info.avg_pref.to_numpy()
    perennials = plant_info[plant_info.perennial == 1].index.to_list()
    problem_plants = plant_info[plant_info.problem_plant == 1].index.to_list()

    beds = bed_info.bed.to_numpy()
    bed_index = bed_info.index.to_numpy()
    num_beds = len(beds)

    year_index = list(range(num_years))

    sun = build_sun_matrix(plant_info, bed_info)
    max_yums = num_beds * num_years * np.max(preferences)

    # Build model
    m = pulp.LpProblem("optimus-veg", pulp.LpMaximize)

    # Decision variables
    x = pulp.LpVariable.dicts(
        "x",
        ((p, b, t) for p in plant_index for b in bed_index for t in year_index),
        cat=pulp.LpBinary,
    )
    y = pulp.LpVariable.dicts("y", plant_index, cat=pulp.LpBinary)

    # Objective
    m += (
        yummy_weight
        * pulp.lpSum(
            preferences[p] * x[p, b, t]
            for p in plant_index
            for b in bed_index
            for t in year_index
        )
        / max_yums
        + variety_weight * pulp.lpSum(y[p] for p in plant_index) / num_plants
    )

    # Constraints
    # One plant per bed per year
    for b in bed_index:
        for t in year_index:
            m += pulp.lpSum(x[p, b, t] for p in plant_index) <= 1

    # Sun compatibility
    for p in plant_index:
        for b in bed_index:
            if sun[p, b] == 0:
                for t in year_index:
                    m += x[p, b, t] == 0

    # Perennials stay in same bed
    for p in plant_index:
        if p in perennials:
            for b in bed_index:
                for t in year_index[1:]:
                    m += x[p, b, t] >= x[p, b, t - 1]

    # Disease rotation
    for p in plant_index:
        if p in problem_plants:
            for b in bed_index:
                for t in year_index[1:]:
                    m += x[p, b, t] <= 1 - x[p, b, t - 1]

    # Relate x to y
    for p in plant_index:
        m += pulp.lpSum(x[p, b, t] for b in bed_index for t in year_index) >= y[p]

    # Solve
    m.solve(pulp.PULP_CBC_CMD(msg=0))

    if m.status != pulp.constants.LpStatusOptimal:
        return {"error": f"Solver did not find optimal solution. Status: {pulp.LpStatus[m.status]}"}

    # Extract solution
    plan = np.zeros(shape=(num_plants, num_beds, num_years))
    for p in plant_index:
        for b in bed_index:
            for t in year_index:
                if pulp.value(x[p, b, t]) > 0.5:
                    plan[p, b, t] = 1

    # Compute scores
    plan_by_plant = plan.sum(axis=(1, 2))
    yummy_score = round(float(np.dot(preferences, plan_by_plant) / max_yums * 100), 1)

    num_planted = int((plan_by_plant > 0).sum())
    variety_score = round(num_planted / num_plants * 100, 1)

    objective = round(pulp.value(m.objective) * 100, 1)

    # Build assignment list
    assignments = []
    for t in year_index:
        for b in bed_index:
            for p in plant_index:
                if plan[p, b, t] == 1:
                    assignments.append(
                        {
                            "year": int(t + 1),
                            "bed": int(beds[b]),
                            "plant": str(plants[p]),
                        }
                    )

    # Build per-year bed plans
    yearly_plans = {}
    for t in year_index:
        bed_plan = {}
        for b in bed_index:
            planted = plant_index[plan[:, b, t] == 1]
            if len(planted) > 0:
                bed_plan[str(int(beds[b]))] = str(plants[planted[0]])
            else:
                bed_plan[str(int(beds[b]))] = None
        yearly_plans[f"year_{int(t + 1)}"] = bed_plan

    return {
        "objective": objective,
        "yummy_score": yummy_score,
        "variety_score": variety_score,
        "num_plants_used": num_planted,
        "total_plants_available": int(num_plants),
        "assignments": assignments,
        "yearly_plans": yearly_plans,
    }
