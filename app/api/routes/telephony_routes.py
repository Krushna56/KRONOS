"""
Telephony API Routes
Webhooks and WebSocket endpoints for Inbound Phone Call handling.
Supports both Twilio carrier-grade speech Gather loops (Polly.Aditi)
and bidirectional real-time audio WebSocket streams.
Includes auto-setup: ngrok tunnel + Twilio webhook configuration.
"""

import os
import uuid
from fastapi import APIRouter, Request, Response, WebSocket
from app.tasks.telephony.call_agent import telephony_agent
from app.persona.clone_engine import clone_engine
from app.core.logger import logger
from app.core.config import settings

router = APIRouter(prefix="/api/telephony", tags=["Telephony"])

# ── Module-level state for ngrok tunnel URL ──
_ngrok_public_url: str | None = None


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
        <Say voice="Polly.Aditi">Good day. This is KRONOS, Krushna's AI executive assistant. Krushna is presently occupied, sir. How may I assist you?</Say>
    </Gather>
    <Say voice="Polly.Aditi">I could not detect any input, sir. Please drop Krushna a message directly. Goodbye.</Say>
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
        <Say voice="Polly.Aditi">I am listening, sir. Krushna is unavailable at the moment, but I can certainly help.</Say>
    </Gather>
    <Say voice="Polly.Aditi">No input detected, sir. Please reach out to Krushna directly. Goodbye.</Say>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Immediate Stop / Hangup Command Interceptor
    stop_phrases = [
        "stop talking", "stop", "shut up", "be quiet", "quiet", "silence",
        "chup", "chup ho ja", "chup raho", "shant", "shant ho ja", "shant raho",
        "bas karo", "bolna band", "ruk ja", "ruko", "hold on", "pause",
        "hang up", "cut the call", "call kato", "phone kato", "bye", "goodbye", "alvida", "tata"
    ]
    s_lower = speech_result.lower().strip()
    if any(phrase in s_lower for phrase in stop_phrases):
        logger.info(f"🛑 [STOP COMMAND] Caller requested stop/hangup: \"{speech_result}\"")
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi">Understood, sir. Ending the call now. Have a good day.</Say>
    <Hangup/>
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
    <Say voice="Polly.Aditi">Very well, sir. If there is nothing else, I shall inform Krushna. Take care.</Say>
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


# ── Telephony Setup: ngrok tunnel + Twilio webhook auto-config ──

@router.get("/setup")
async def telephony_setup():
    """
    One-click setup:
    1. Starts an ngrok tunnel to expose localhost:8000
    2. Configures Twilio phone number webhook to point to the ngrok URL
    Returns the public URL and status.
    """
    global _ngrok_public_url

    # Validate Twilio credentials
    sid = settings.TWILIO_ACCOUNT_SID.strip()
    token = settings.TWILIO_AUTH_TOKEN.strip()
    phone = settings.TWILIO_PHONE_NUMBER.strip()

    errors = []
    if not sid or not sid.startswith("AC"):
        errors.append("TWILIO_ACCOUNT_SID must start with 'AC'. Get it from https://console.twilio.com/")
    if not token or len(token) < 20:
        errors.append("TWILIO_AUTH_TOKEN looks invalid. Get it from https://console.twilio.com/")
    if not phone or not phone.startswith("+"):
        errors.append("TWILIO_PHONE_NUMBER must be in E.164 format, e.g. +18562299971")

    if errors:
        return {"status": "error", "message": "Twilio credentials are not configured correctly.", "errors": errors}

    # Step 1: Start ngrok tunnel
    try:
        from pyngrok import ngrok
        # Kill any existing tunnels first
        tunnels = ngrok.get_tunnels()
        for t in tunnels:
            ngrok.disconnect(t.public_url)

        tunnel = ngrok.connect(8000, "http")
        _ngrok_public_url = tunnel.public_url
        logger.info(f"🌐 ngrok tunnel started: {_ngrok_public_url}")
    except ImportError:
        return {"status": "error", "message": "pyngrok is not installed. Run: pip install pyngrok"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to start ngrok tunnel: {str(e)}"}

    # Step 2: Configure Twilio webhook
    webhook_url = f"{_ngrok_public_url}/api/telephony/incoming"
    try:
        from twilio.rest import Client
        client = Client(sid, token)

        # Find the phone number SID
        numbers = client.incoming_phone_numbers.list(phone_number=phone)
        if not numbers:
            return {
                "status": "error",
                "ngrok_url": _ngrok_public_url,
                "message": f"Phone number {phone} not found in your Twilio account. Check TWILIO_PHONE_NUMBER in .env"
            }

        number = numbers[0]
        number.update(
            voice_url=webhook_url,
            voice_method="POST",
            status_callback=f"{_ngrok_public_url}/api/telephony/status-callback",
            status_callback_method="POST"
        )

        logger.info(f"✅ Twilio webhook configured: {webhook_url} for {phone}")
        return {
            "status": "success",
            "ngrok_url": _ngrok_public_url,
            "webhook_url": webhook_url,
            "phone_number": phone,
            "message": f"KRONOS telephony is LIVE. Call {phone} to test."
        }
    except ImportError:
        # twilio not installed — return manual instructions
        return {
            "status": "partial",
            "ngrok_url": _ngrok_public_url,
            "webhook_url": webhook_url,
            "message": "ngrok tunnel is running. Twilio SDK not installed — manually set your Twilio Voice webhook to the webhook_url above."
        }
    except Exception as e:
        return {
            "status": "partial",
            "ngrok_url": _ngrok_public_url,
            "webhook_url": webhook_url,
            "message": f"ngrok running but Twilio config failed: {str(e)}. Manually set Voice webhook to the webhook_url."
        }


@router.post("/make-call")
async def make_outbound_call(request: Request):
    """
    Make an outbound call from KRONOS to a given phone number.
    Body: {"to": "+919876543210", "message": "optional greeting"}
    """
    sid = settings.TWILIO_ACCOUNT_SID.strip()
    token = settings.TWILIO_AUTH_TOKEN.strip()
    phone = settings.TWILIO_PHONE_NUMBER.strip()

    if not sid.startswith("AC"):
        return {"status": "error", "message": "Twilio credentials not configured. Visit /api/telephony/setup first."}

    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON body. Send {\"to\": \"+919876543210\"}"}

    to_number = body.get("to", "").strip()
    custom_msg = body.get("message", "Good day, sir. This is KRONOS, Krushna's AI executive assistant, reaching out on his behalf.")

    if not to_number or not to_number.startswith("+"):
        return {"status": "error", "message": "Provide 'to' in E.164 format, e.g. +919876543210"}

    try:
        from twilio.rest import Client
        client = Client(sid, token)

        # Build TwiML for the outbound call
        twiml_str = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="speech" action="/api/telephony/gather" method="POST" speechTimeout="auto" language="en-IN">
        <Say voice="Polly.Aditi">{custom_msg}</Say>
    </Gather>
    <Say voice="Polly.Aditi">No response detected. Goodbye, sir.</Say>
</Response>"""

        # Determine URL for TwiML
        if _ngrok_public_url:
            call = client.calls.create(
                to=to_number,
                from_=phone,
                url=f"{_ngrok_public_url}/api/telephony/incoming"
            )
        else:
            # Use inline TwiML
            from twilio.twiml.voice_response import VoiceResponse
            call = client.calls.create(
                to=to_number,
                from_=phone,
                twiml=twiml_str
            )

        logger.info(f"📞 [OUTBOUND CALL] to {to_number}, CallSid: {call.sid}")
        return {"status": "success", "call_sid": call.sid, "to": to_number, "message": "Call initiated, sir."}

    except ImportError:
        return {"status": "error", "message": "twilio package not installed. Run: pip install twilio"}
    except Exception as e:
        return {"status": "error", "message": f"Call failed: {str(e)}"}


@router.post("/status-callback")
async def call_status_callback(request: Request):
    """
    Twilio Status Callback: logs call events (ringing, answered, completed).
    """
    form = await request.form()
    call_sid = form.get("CallSid", "")
    call_status = form.get("CallStatus", "")
    caller = form.get("From", "")
    duration = form.get("CallDuration", "0")

    logger.info(f"📞 [CALL STATUS] {call_sid}: {call_status} (from: {caller}, duration: {duration}s)")
    return Response(content="", status_code=204)


@router.get("/tunnel-status")
async def get_tunnel_status():
    """Check if ngrok tunnel is active."""
    return {
        "tunnel_active": _ngrok_public_url is not None,
        "public_url": _ngrok_public_url,
        "call_link": f"{_ngrok_public_url}/call" if _ngrok_public_url else "/call",
        "twilio_configured": settings.TWILIO_ACCOUNT_SID.startswith("AC") if settings.TWILIO_ACCOUNT_SID else False,
        "phone_number": settings.TWILIO_PHONE_NUMBER
    }


# ── Free Browser-Based Web Call Automation (No Twilio Required) ──

@router.post("/start-tunnel")
async def start_free_tunnel():
    """Start ngrok tunnel without requiring Twilio so the /call link can be shared externally."""
    global _ngrok_public_url
    try:
        from pyngrok import ngrok
        for t in ngrok.get_tunnels():
            ngrok.disconnect(t.public_url)
        tunnel = ngrok.connect(8000, "http")
        _ngrok_public_url = tunnel.public_url
        logger.info(f"🌐 Free Web Call tunnel started: {_ngrok_public_url}/call")
        return {
            "status": "success",
            "public_url": _ngrok_public_url,
            "call_link": f"{_ngrok_public_url}/call",
        }
    except ImportError:
        return {"status": "error", "message": "pyngrok is not installed. Run: pip install pyngrok"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to start ngrok tunnel: {str(e)}"}


@router.post("/web-call/start")
async def web_call_start(request: Request):
    """Start a free browser-based AI call session (no Twilio needed)."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    caller_name = str(body.get("caller_name", "Web Caller")).strip() or "Web Caller"
    call_sid = f"WEB_{uuid.uuid4().hex[:10]}"
    session = telephony_agent.create_session(call_sid, caller_name)

    greeting = (
        "Good day. This is KRONOS, Krushna's AI executive assistant. "
        "Krushna is presently occupied, sir. How may I assist you?"
    )
    session.add_turn("agent", greeting)
    return {"status": "connected", "call_sid": call_sid, "greeting": greeting}


@router.post("/web-call/turn")
async def web_call_turn(request: Request):
    """Process one conversational turn from a browser caller."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "error", "reply": "I could not parse your request, sir.", "ended": False}

    call_sid = str(body.get("call_sid", "")).strip()
    caller_text = str(body.get("text", "")).strip()

    session = telephony_agent.get_session(call_sid) if call_sid else None
    if not session:
        return {"status": "ended", "reply": "Call session has ended, sir.", "ended": True}

    if not caller_text:
        return {"status": "ok", "reply": "I am listening, sir. Please go ahead.", "ended": False}

    session.add_turn("caller", caller_text)

    stop_phrases = [
        "hang up", "cut the call", "call kato", "phone kato",
        "bye", "goodbye", "alvida", "tata", "end call"
    ]
    if any(phrase in caller_text.lower() for phrase in stop_phrases):
        farewell = "Understood, sir. Ending the call now. Have a good day."
        session.add_turn("agent", farewell)
        telephony_agent.close_session(call_sid)
        return {"status": "ended", "reply": farewell, "ended": True}

    reply = await clone_engine.generate_reply(
        incoming_message=caller_text,
        channel="call",
        caller_name=session.caller_number
    )
    session.add_turn("agent", reply)
    return {"status": "ok", "reply": reply, "ended": False}


@router.post("/web-call/end")
async def web_call_end(request: Request):
    """Close an active browser call session."""
    try:
        body = await request.json()
    except Exception:
        body = {}

    call_sid = str(body.get("call_sid", "")).strip()
    if call_sid:
        telephony_agent.close_session(call_sid)
    return {"status": "closed"}
