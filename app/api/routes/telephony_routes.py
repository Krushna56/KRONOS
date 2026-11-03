"""
Telephony API Routes
Webhooks and WebSocket endpoints for Inbound Phone Call handling.
Supports both Twilio carrier-grade speech Gather loops (Polly.Aditi)
and bidirectional real-time audio WebSocket streams.
"""

import os
from fastapi import APIRouter, Request, Response, WebSocket
from app.tasks.telephony.call_agent import telephony_agent
from app.persona.clone_engine import clone_engine
from app.core.logger import logger

router = APIRouter(prefix="/api/telephony", tags=["Telephony"])


@router.post("/incoming")
async def incoming_call_webhook(request: Request):
    """
    Twilio Webhook: Called immediately when a phone number receives an inbound call.
    Greets caller in Krushna's AI Clone persona and activates interactive speech gathering.
    """
    form_data = await request.form()
    caller = form_data.get("From", "Unknown Caller")
    call_sid = form_data.get("CallSid", "")
    host = request.headers.get("host", "localhost:8000")

    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    is_secure = "https" in str(request.url) or forwarded_proto == "https" or "ngrok" in host
    ws_protocol = "wss" if is_secure else "ws"
    stream_url = f"{ws_protocol}://{host}/api/telephony/stream"

    logger.info(f"📞 [INCOMING CALL] from {caller} (CallSid: {call_sid})")

    # Interactive TwiML: Greets caller and listens to speech
    twiml_response = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="/api/telephony/gather" method="POST" speechTimeout="auto" language="en-IN">
        <Say voice="Polly.Aditi">Haan bhai, hello! Main Krushna ka AI assistant hu. Krushna abhi thoda busy hai, bolo kya kaam tha?</Say>
    </Gather>
    <Say voice="Polly.Aditi">Awaaz nahi aayi bhai. Aap Krushna ko direct message drop kar dena. Bye!</Say>
</Response>"""

    return Response(content=twiml_response, media_type="application/xml")


@router.post("/gather")
async def telephony_gather(request: Request):
    """
    Twilio Speech Callback: Receives caller's transcribed words,
    generates a real-time persona response from clone_engine, and speaks it back.
    """
    form = await request.form()
    caller = form.get("From", "Caller")
    call_sid = form.get("CallSid", "")
    speech_result = form.get("SpeechResult", "").strip()

    logger.info(f"📞 [CALL INBOUND] from {caller} (CallSid: {call_sid}): \"{speech_result}\"")

    if not speech_result:
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="/api/telephony/gather" method="POST" speechTimeout="auto" language="en-IN">
        <Say voice="Polly.Aditi">Bolo bhai, sun raha hu. Krushna ki jagah main help kar sakta hu.</Say>
    </Gather>
    <Say voice="Polly.Aditi">Koi awaaz nahi aayi bhai. Baad me connect karte hain, bye!</Say>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Generate reply matching Krushna's authentic clone persona
    reply = await clone_engine.generate_reply(
        incoming_message=speech_result,
        channel="call",
        caller_name=caller
    )

    logger.info(f"🤖 [CALL CLONE REPLY] to {caller}: \"{reply}\"")

    # Sanitize XML special characters for TwiML
    clean_reply = reply.replace("&", "and").replace("<", "").replace(">", "").replace('"', "'")

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">{clean_reply}</Say>
    <Gather input="speech" action="/api/telephony/gather" method="POST" speechTimeout="auto" language="en-IN">
    </Gather>
    <Say voice="Polly.Aditi">Thik hai bhai, agar kuch aur nahi hai toh main Krushna ko bata dunga. Take care!</Say>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


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
