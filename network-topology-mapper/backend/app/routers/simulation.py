from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.graph.failure_simulator import failure_simulator
from app.services.graph.spof_detector import spof_detector
from app.services.graph.resilience_scorer import resilience_scorer

router = APIRouter(prefix="/api", tags=["simulation"])


class FailureRequest(BaseModel):
    remove_nodes: list[str] = []
    remove_edges: list[list[str]] = []


@router.post("/simulate/failure")
def simulate_failure(request: FailureRequest):
    remove_edges = [tuple(e) for e in request.remove_edges] if request.remove_edges else None
    result = failure_simulator.simulate_failure(
        remove_nodes=request.remove_nodes or None,
        remove_edges=remove_edges,
    )
    return result


@router.get("/simulate/spof")
def get_spofs():
    spofs = spof_detector.find_spofs()
    bridges = spof_detector.find_bridges()
    centrality = spof_detector.get_betweenness_centrality()

    return {
        "spofs": spofs,
        "bridges": bridges,
        "top_centrality": centrality,
    }


@router.get("/simulate/resilience")
def get_resilience():
    return resilience_scorer.calculate_global_resilience()
