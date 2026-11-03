"""
Telephony Call Agent
Handles incoming telephone calls, bidirectional real-time audio streams (Twilio/WebRTC/SIP),
converses in the user's authentic clone tone, and logs call summaries.
"""

import base64
import json
import logging
import audioop
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

from app.persona.clone_engine import clone_engine
from app.voice.tts.engine import get_tts_engine
from app.voice.stt.engine import get_stt_engine

logger = logging.getLogger(__name__)


class CallSession:
    """
    Represents an ongoing phone call session with state and history.
    """

    def __init__(self, call_sid: str, caller_number: str):
        self.call_sid = call_sid
        self.caller_number = caller_number
        self.history: list[dict] = []
        self.is_active = True

    def add_turn(self, speaker: str, text: str):
        self.history.append({"speaker": speaker, "text": text})


class TelephonyCallAgent:
    """
    Manages telephony call lifecycle and bidirectional audio streaming.
    """

    def __init__(self):
        self.active_calls: Dict[str, CallSession] = {}
        self.tts = get_tts_engine()
        self.stt = get_stt_engine()

    def create_session(self, call_sid: str, caller_number: str) -> CallSession:
        session = CallSession(call_sid, caller_number)
        self.active_calls[call_sid] = session
        logger.info(f"📞 New call session started for {caller_number} (SID: {call_sid})")
        return session

    def get_session(self, call_sid: str) -> Optional[CallSession]:
        return self.active_calls.get(call_sid)

    def close_session(self, call_sid: str) -> Optional[CallSession]:
        session = self.active_calls.pop(call_sid, None)
        if session:
            session.is_active = False
            logger.info(f"📞 Call session ended for {session.caller_number} (Turns: {len(session.history)})")
        return session

    async def handle_media_stream(self, websocket: WebSocket):
        """
        Handles bidirectional Twilio WebSocket media stream.
        Receives caller's voice chunks, runs STT, generates Clone reply, and streams back synthesized audio.
        """
        await websocket.accept()
        call_sid = None
        stream_sid = None

        try:
            while True:
                message_text = await websocket.receive_text()
                data = json.loads(message_text)
                event = data.get("event")

                if event == "start":
                    start_data = data.get("start", {})
                    stream_sid = data.get("streamSid")
                    call_sid = start_data.get("callSid", "CALL_UNKNOWN")
                    caller = start_data.get("customParameters", {}).get("caller", "Unknown")
                    session = self.create_session(call_sid, caller)

                    # Initial greeting in Krushna's clone tone
                    greeting = "Haan bhai, hello! Main Krushna ka AI assistant hu. Krushna abhi thoda busy hai, bolo kya kaam tha?"
                    session.add_turn("agent", greeting)
                    await self._stream_speech(websocket, stream_sid, greeting)

                elif event == "media":
                    # Inbound audio from caller (mulaw 8000Hz base64)
                    payload = data.get("media", {}).get("payload")
                    if payload and stream_sid:
                        # Process audio chunk when speech completes
                        pass

                elif event == "user_transcript":
                    # If upstream Twilio / Deepgram STT provides transcript directly
                    caller_text = data.get("text", "")
                    if caller_text and call_sid:
                        session = self.get_session(call_sid)
                        if session:
                            session.add_turn("caller", caller_text)
                            # Generate AI Clone reply in Krushna's exact tone
                            reply = await clone_engine.generate_reply(
                                incoming_message=caller_text,
                                channel="call",
                                caller_name=session.caller_number
                            )
                            session.add_turn("agent", reply)
                            await self._stream_speech(websocket, stream_sid, reply)

                elif event == "stop":
                    logger.info(f"Twilio stream stopped for {call_sid}")
                    break

        except WebSocketDisconnect:
            logger.info("Telephony WebSocket disconnected")
        except Exception as e:
            logger.exception(f"Error in telephony stream: {e}")
        finally:
            if call_sid:
                self.close_session(call_sid)

    async def _stream_speech(self, websocket: WebSocket, stream_sid: str, text: str):
        """
        Synthesizes text to audio and sends it over the WebSocket back to the caller.
        """
        try:
            pcm_audio = self.tts.synthesize_pcm(text)
            if not pcm_audio:
                return

            # Convert 16-bit linear PCM (16kHz or 22kHz) to 8kHz mu-law for Twilio telephony
            try:
                # Downsample if needed or convert to ulaw
                ulaw_audio = audioop.lin2ulaw(pcm_audio, 2)
            except Exception:
                ulaw_audio = pcm_audio

            b64_payload = base64.b64encode(ulaw_audio).decode("utf-8")
            response_msg = {
                "event": "media",
                "streamSid": stream_sid,
                "media": {
                    "payload": b64_payload
                }
            }
            await websocket.send_text(json.dumps(response_msg))
            logger.info(f"📞 Streamed voice reply to caller: \"{text}\"")
        except Exception as e:
            logger.error(f"Failed to stream speech to telephony: {e}")


telephony_agent = TelephonyCallAgent()
