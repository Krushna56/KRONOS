"""
Robot API Routes
Endpoints for Mini Robot hardware connection and telemetry.
"""

from fastapi import APIRouter, WebSocket
from app.robot.bridge import robot_bridge

router = APIRouter(prefix="/api/robot", tags=["Robot Bridge"])


@router.websocket("/ws")
async def robot_websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket stream for Mini Robot hardware (Mic Audio, Speaker Audio, and Motor Commands).
    """
    await robot_bridge.handle_connection(websocket)


@router.get("/status")
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

@router.post("/action")
async def trigger_robot_action(body: RobotAction):
    """
    Trigger a physical robot motor action (nod, blink, look_left, look_right).
    """
    await robot_bridge.broadcast_speech(f"Action {body.action}", action=body.action)
    return {"status": "ok", "action": body.action}

