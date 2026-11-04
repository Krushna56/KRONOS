"""
Robot API Routes
Endpoints for Mini Robot hardware connection and telemetry.
"""

from fastapi import APIRouter, Depends, WebSocket
from app.core.guards import authorize_robot_ws, require_robot_key
from app.robot.bridge import robot_bridge

router = APIRouter(prefix="/api/robot", tags=["Robot Bridge"])


@router.websocket("/ws")
async def robot_websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket stream for Mini Robot hardware (Mic Audio, Speaker Audio, and Motor Commands).
    Requires the shared robot key (X-Robot-Key header or ?key=).
    """
    if not await authorize_robot_ws(websocket):
        return
    await robot_bridge.handle_connection(websocket)


@router.get("/status", dependencies=[Depends(require_robot_key)])
async def robot_status():
    """
    Check if the physical mini robot is connected to the AI Clone brain.
    """
    active = robot_bridge._voice_pipeline._is_running if robot_bridge._voice_pipeline else False
    return {
        "status": "online" if len(robot_bridge.connected_robots) > 0 else "offline",
        "connected_robots": len(robot_bridge.connected_robots),
        "brain_voice_pipeline_active": active
    }


from pydantic import BaseModel

class RobotAction(BaseModel):
    action: str

@router.post("/action", dependencies=[Depends(require_robot_key)])
async def trigger_robot_action(body: RobotAction):
    """
    Trigger a physical robot motor action (nod, blink, look_left, look_right).
    """
    await robot_bridge.broadcast_speech(f"Action {body.action}", action=body.action)
    return {"status": "ok", "action": body.action}

