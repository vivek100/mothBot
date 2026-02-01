#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""toolCallAgent - Pipecat Diagnostic Agent with Tool Calling

This bot uses a traditional pipeline: Speech-to-Text → LLM (with tools) → Text-to-Speech
- Google STT for speech recognition
- OpenAI LLM (supports cheaper models like gpt-4o-mini) with function calling
- Google TTS for speech synthesis

The agent can:
1. Call individual diagnostic tools (scan_hull, check_oxygen, etc.)
2. Execute multi-step diagnostic plans via the marimo_engine
3. Stream responses in real-time to the frontend
4. Support both voice and text input

Required AI services:
- Google (Speech-to-Text and Text-to-Speech)
- OpenAI (LLM with function calling - supports gpt-4o-mini, gpt-3.5-turbo, etc.)

Run the bot using::

    uv run bot.py
"""

import json
import os

from dotenv import load_dotenv
from loguru import logger
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.processors.frameworks.rtvi import (
    RTVILLMFunctionCallMessage,
    RTVILLMFunctionCallMessageData,
)
from pydantic import BaseModel
from typing import Literal, Any

# Custom RTVI message for function call results
# We use "server-message" type so the client's serverMessage event fires
RTVI_MESSAGE_LABEL = "rtvi-ai"

class FunctionCallResultPayload(BaseModel):
    """Payload for function call result."""
    type: Literal["function-call-result"] = "function-call-result"
    function_name: str
    tool_call_id: str
    args: dict
    result: str  # JSON string of the result

class RTVIServerMessage(BaseModel):
    """Server message wrapper - triggers serverMessage event on client."""
    label: Literal["rtvi-ai"] = RTVI_MESSAGE_LABEL
    type: Literal["server-message"] = "server-message"
    data: FunctionCallResultPayload
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    AssistantTurnStoppedMessage,
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
    UserTurnStoppedMessage,
)
from pipecat.runner.types import DailyRunnerArguments, RunnerArguments, SmallWebRTCRunnerArguments
from pipecat.services.google.stt import GoogleSTTService
from pipecat.services.google.tts import GoogleHttpTTSService  # Use HTTP version for Neural2/Standard voices
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
from pipecat.turns.user_stop.turn_analyzer_user_turn_stop_strategy import (
    TurnAnalyzerUserTurnStopStrategy,
)
from pipecat.turns.user_turn_strategies import UserTurnStrategies
from pipecat_tail.observer import TailObserver
from pipecat_whisker import WhiskerObserver

# Daily transport is optional (not available on Windows)
try:
    from pipecat.transports.daily.transport import DailyParams, DailyTransport
    DAILY_AVAILABLE = True
except Exception:
    # Daily raises Exception, not ImportError
    DAILY_AVAILABLE = False
    DailyParams = None
    DailyTransport = None

# Import our tool definitions and handlers
from tools import SYSTEM_PROMPT, TOOL_DEFINITIONS, execute_tool

load_dotenv(override=True)


def load_google_credentials():
    """Load Google credentials from file path or JSON string."""
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")
    
    # Check if it's a file path
    if os.path.isfile(creds_path):
        with open(creds_path, "r") as f:
            return f.read()
    
    # Otherwise assume it's already JSON content
    return creds_path


async def run_bot(transport: BaseTransport):
    """Main bot logic with tool calling support."""
    logger.info("Starting Diagnostic Agent with tool calling")

    # Load Google credentials (from file or JSON string)
    google_credentials = load_google_credentials()
    logger.info(f"Loaded Google credentials from: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    # Speech-to-Text service (Google)
    stt = GoogleSTTService(
        credentials=google_credentials,
        location=os.getenv("GOOGLE_LOCATION", "us-central1"),
    )

    # Text-to-Speech service (Google HTTP - supports all voice types)
    # GoogleHttpTTSService supports Neural2, Standard, Wavenet voices
    # GoogleTTSService (streaming) only supports Chirp3 HD voices
    voice_id = os.getenv("GOOGLE_VOICE_NAME", "en-US-Neural2-D")
    logger.info(f"Using Google HTTP TTS with voice_id: {voice_id}")
    
    tts = GoogleHttpTTSService(
        credentials=google_credentials,
        location=os.getenv("GOOGLE_LOCATION", "us-central1"),
        voice_id=voice_id,
    )

    # LLM service with tool definitions
    # Supports cheaper models: gpt-4o-mini, gpt-3.5-turbo, etc.
    llm = OpenAILLMService(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),  # Default to cheaper model
        api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    # Tool handlers will be registered after task creation (need access to task.rtvi)

    # Initial messages with system prompt and tool definitions
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
    ]

    # Convert tool definitions to FunctionSchema objects
    function_schemas = []
    for tool_def in TOOL_DEFINITIONS:
        func = tool_def.get("function", {})
        params = func.get("parameters", {})
        function_schemas.append(
            FunctionSchema(
                name=func.get("name", ""),
                description=func.get("description", ""),
                properties=params.get("properties", {}),
                required=params.get("required", []),
            )
        )
    
    # Create ToolsSchema from function schemas
    tools_schema = ToolsSchema(standard_tools=function_schemas)

    # Create context with tools
    context = LLMContext(
        messages=messages,
        tools=tools_schema,
    )
    
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(
            user_turn_strategies=UserTurnStrategies(
                stop=[TurnAnalyzerUserTurnStopStrategy(turn_analyzer=LocalSmartTurnAnalyzerV3())]
            ),
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.2)),
        ),
    )

    # Pipeline - traditional STT → LLM → TTS
    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            enable_rtvi=True,  # Enable RTVI protocol for client communication
        ),
        observers=[
            WhiskerObserver(pipeline),
            TailObserver(),
        ],
    )

    # Create tool handler that notifies RTVI about function calls
    async def create_tool_handler(fn_name: str):
        async def handler(function_name: str, tool_call_id: str, arguments: dict, llm_service, ctx, result_callback):
            logger.info(f"Tool call: {function_name} (id: {tool_call_id}) with args: {arguments}")
            
            # Notify RTVI about the function call so frontend can display it
            try:
                # Create the RTVI message directly
                fn_data = RTVILLMFunctionCallMessageData(
                    function_name=function_name,
                    tool_call_id=tool_call_id,
                    args=arguments,
                )
                message = RTVILLMFunctionCallMessage(data=fn_data)
                await task.rtvi.push_transport_message(message, exclude_none=False)
                logger.info(f"✅ Sent function call event to RTVI: {function_name}")
            except Exception as e:
                logger.warning(f"❌ Failed to send function call to RTVI: {e}")
            
            # Execute the tool
            try:
                result = await execute_tool(function_name, arguments)
                logger.info(f"Tool result: {result[:200]}..." if len(result) > 200 else f"Tool result: {result}")
                
                # Send the result to the frontend via server-message
                try:
                    result_payload = FunctionCallResultPayload(
                        function_name=function_name,
                        tool_call_id=tool_call_id,
                        args=arguments,
                        result=result,
                    )
                    server_message = RTVIServerMessage(data=result_payload)
                    await task.rtvi.push_transport_message(server_message, exclude_none=False)
                    logger.info(f"✅ Sent function call result to RTVI: {function_name}")
                except Exception as e:
                    logger.warning(f"❌ Failed to send function call result to RTVI: {e}")
                
                await result_callback(result)
            except Exception as e:
                error_result = json.dumps({
                    "tool": function_name,
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"Tool error: {e}")
                
                # Send error result to frontend
                try:
                    result_payload = FunctionCallResultPayload(
                        function_name=function_name,
                        tool_call_id=tool_call_id,
                        args=arguments,
                        result=error_result,
                    )
                    server_message = RTVIServerMessage(data=result_payload)
                    await task.rtvi.push_transport_message(server_message, exclude_none=False)
                except Exception:
                    pass
                
                await result_callback(error_result)
        
        return handler

    # Register tools with the LLM (now with RTVI notification)
    tool_names = [
        "scan_hull",
        "check_oxygen",
        "analyze_atmosphere",
        "check_temperature",
        "scan_systems",
        "execute_diagnostic_plan",
        "list_available_plans",
    ]
    
    for tool_name in tool_names:
        handler = await create_tool_handler(tool_name)
        llm.register_function(tool_name, handler)
    
    logger.info(f"Registered {len(tool_names)} tools with RTVI notification")

    @task.event_handler("on_first_participant_joined")
    async def on_first_participant_joined(transport, participant):
        # Send initial greeting when participant joins
        logger.info(f"First participant joined: {participant}")
        # Don't queue frames here - wait for client-ready

    @task.rtvi.event_handler("on_client_ready")
    async def on_client_ready(rtvi):
        # Client is ready, kick off the conversation
        logger.info("Client ready signal received, starting conversation")
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    @user_aggregator.event_handler("on_user_turn_stopped")
    async def on_user_turn_stopped(aggregator, strategy, message: UserTurnStoppedMessage):
        timestamp = f"[{message.timestamp}] " if message.timestamp else ""
        line = f"{timestamp}user: {message.content}"
        logger.info(f"Transcript: {line}")

    @assistant_aggregator.event_handler("on_assistant_turn_stopped")
    async def on_assistant_turn_stopped(aggregator, message: AssistantTurnStoppedMessage):
        timestamp = f"[{message.timestamp}] " if message.timestamp else ""
        line = f"{timestamp}assistant: {message.content}"
        logger.info(f"Transcript: {line}")

    runner = PipelineRunner(handle_sigint=False)

    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point."""

    transport = None

    match runner_args:
        case DailyRunnerArguments():
            if not DAILY_AVAILABLE:
                logger.error("Daily transport is not available on Windows. Please use SmallWebRTC transport instead.")
                return
            transport = DailyTransport(
                runner_args.room_url,
                runner_args.token,
                "Diagnostic Agent",
                params=DailyParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                ),
            )
        case SmallWebRTCRunnerArguments():
            webrtc_connection: SmallWebRTCConnection = runner_args.webrtc_connection

            transport = SmallWebRTCTransport(
                webrtc_connection=webrtc_connection,
                params=TransportParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                ),
            )
        case _:
            logger.error(f"Unsupported runner arguments type: {type(runner_args)}")
            return

    await run_bot(transport)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
