from fastapi import APIRouter

from app.utils.platform_utils import get_local_subnets

router = APIRouter(prefix="/api/network", tags=["network"])


@router.get("/interfaces")
def list_interfaces():
    subnets = get_local_subnets()
    return {"subnets": subnets}
