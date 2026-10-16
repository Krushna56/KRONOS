"""
Mini Robot Hardware Bridge
Coordinates communication between the physical Mini Robot (Raspberry Pi/ESP32/Mini PC)
and the AI Clone Brain over low-latency WebSockets.
"""

import json
import base64
import logging
from typing import Dict, Optional, Set
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect

from app.persona.clone_engine import clone_engine
from app.voice.tts.engine import get_tts_engine
from app.voice.pipeline import VoicePipeline

logger = logging.getLogger(__name__)


class RobotBridge:
    """
    Manages active robot connections, hardware telemetry, audio streams, and physical actions.
    """

    def __init__(self):
        self.connected_robots: Set[WebSocket] = set()
        self.tts = get_tts_engine()
        self._voice_pipeline: Optional[VoicePipeline] = None

    @property
    def voice_pipeline(self) -> VoicePipeline:
        if self._voice_pipeline is None:
            self._voice_pipeline = VoicePipeline(
                on_transcript=self._on_robot_speech_transcribed,
                use_microphone=False
            )
            self._voice_pipeline.start()
        return self._voice_pipeline

    def _on_robot_speech_transcribed(self, transcript: str):
        """
        When the robot's microphone stream detects and transcribes user speech.
        """
        import asyncio
        logger.info(f"🤖 [Robot Speech In]: \"{transcript}\"")
        # Run response generation and stream back to robot
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._process_and_reply(transcript))
        except RuntimeError:
            pass

    async def _process_and_reply(self, transcript: str):
        reply = await clone_engine.generate_reply(
            incoming_message=transcript,
            channel="voice"
        )
        logger.info(f"🤖 [Robot Reply Out]: \"{reply}\"")
        await self.broadcast_speech(reply)

    async def handle_connection(self, websocket: WebSocket):
        """
        Accepts and maintains live WebSocket connection with the mini robot.
        """
        await websocket.accept()
        self.connected_robots.add(websocket)
        logger.info(f"🤖 Mini Robot connected. Total robots active: {len(self.connected_robots)}")

        try:
            # Send initial greeting/handshake
            await websocket.send_json({
                "type": "handshake",
                "status": "connected",
                "message": "AI Clone Brain connected to Mini Robot"
            })

            while True:
                message_text = await websocket.receive_text()
                try:
                    payload = json.loads(message_text)
                    msg_type = payload.get("type")

                    if msg_type == "audio_chunk":
                        # Base64 encoded PCM audio chunk from robot's microphone
                        raw_b64 = payload.get("data", "")
                        if raw_b64:
                            pcm_bytes = base64.b64decode(raw_b64)
                            # Convert 16-bit PCM bytes back to float32 numpy array
                            audio_np = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32767.0
                            self.voice_pipeline.feed_audio(audio_np)

                    elif msg_type == "command_text":
                        # Direct text command from robot screen or button
                        user_text = payload.get("text", "")
                        if user_text:
                            await self._process_and_reply(user_text)

                    elif msg_type == "telemetry":
                        battery = payload.get("battery", 100)
                        logger.debug(f"Robot Telemetry - Battery: {battery}%")

                except json.JSONDecodeError:
                    pass

        except WebSocketDisconnect:
            logger.info("🤖 Mini Robot disconnected")
        finally:
            self.connected_robots.discard(websocket)

    async def broadcast_speech(self, text: str, action: str = "nod"):
        """
        Synthesizes speech and sends both audio and physical action instructions to the robot.
        """
        pcm_bytes = self.tts.synthesize_pcm(text)
        b64_audio = base64.b64encode(pcm_bytes).decode("utf-8") if pcm_bytes else ""

        message = {
            "type": "speak",
            "text": text,
            "audio_base64": b64_audio,
            "action": action  # Physical robot action: "nod", "blink", "shake_head"
        }

        dead_connections = []
        for ws in self.connected_robots:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)

        for ws in dead_connections:
            self.connected_robots.discard(ws)


robot_bridge = RobotBridge()
