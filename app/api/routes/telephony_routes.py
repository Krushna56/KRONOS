"""
Telephony API Routes
Webhooks and WebSocket endpoints for Inbound Phone Call handling.
"""

import os
from fastapi import APIRouter, Request, Response, WebSocket
from app.telephony.call_agent import telephony_agent
from app.core.logger import logger

router = APIRouter(prefix="/api/telephony", tags=["Telephony"])


@router.post("/incoming")
async def incoming_call_webhook(request: Request):
    """
    Twilio Webhook: Called immediately when a phone number receives an inbound call.
    Returns TwiML that connects the caller's audio stream directly to our AI Clone WebSocket.
    """
    form_data = await request.form()
    caller = form_data.get("From", "Unknown Caller")
    call_sid = form_data.get("CallSid", "")
    host = request.headers.get("host", "localhost:8000")

    ws_protocol = "wss" if "https" in str(request.url) else "ws"
    stream_url = f"{ws_protocol}://{host}/api/telephony/stream"

    logger.info(f"📞 Incoming call received from {caller} (CallSid: {call_sid}). Routing to {stream_url}")

    # TwiML response telling Twilio to open bidirectional media stream to our AI Clone Brain
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">Connecting you to Krushna's AI Assistant.</Say>
    <Connect>
        <Stream url="{stream_url}">
            <Parameter name="caller" value="{caller}" />
            <Parameter name="callSid" value="{call_sid}" />
        </Stream>
    </Connect>
</Response>"""

    return Response(content=twiml_response, media_type="application/xml")


@router.websocket("/stream")
async def telephony_media_stream(websocket: WebSocket):
    """
    Bidirectional WebSocket stream connected directly to Twilio Media Streams.
    """
    await telephony_agent.handle_media_stream(websocket)


@router.get("/active-calls")
async def get_active_calls():
    """
    Get list of active ongoing phone calls and turn count.
    """
    calls = []
    for sid, session in telephony_agent.active_calls.items():
        calls.append({
            "call_sid": sid,
            "caller": session.caller_number,
            "turns": len(session.history),
            "history": session.history
        })
    return {"active_calls_count": len(calls), "calls": calls}
