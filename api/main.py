from fastapi import FastAPI, Query

from api.solver import optimize

app = FastAPI(title="Optimal Gardening API")


@app.post("/optimize")
def run_optimization(
    num_years: int = Query(default=3, ge=1, le=10, description="Planning horizon in years"),
    yummy_weight: float = Query(default=1.0, ge=0, le=1, description="Weight for yummy score"),
    variety_weight: float = Query(default=0.0, ge=0, le=1, description="Weight for variety score"),
):
    result = optimize(num_years, yummy_weight, variety_weight)
    return result
