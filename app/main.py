from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.sqlite.aio import AsyncSQLiteSaver
from app.graph import build_graph
from app.schemas import AgentRequest
import json, uuid

agent_graph = None # Global variable to hold the compiled graph

@asynccontextmanager
async def lifespan(app: FastAPI): #lifespan function to initialize the graph before the server starts
    global agent_graph # Declare that we are using the global variable
    async with AsyncSQLiteSaver.from_conn_string("checkpoints.db") as saver: # Create an async SQLite saver for state persistence
        agent_graph = build_graph(saver) # Build and compile the graph, storing it in the global variable
        yield # Yield control back to FastAPI to start the server

app = FastAPI(title="Agent Signal", lifespan=lifespan) # Create FastAPI app with the custom lifespan

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.1"}

@app.post("/agent/run")
async def run_agent(req: AgentRequest):
    session_id = req.session_id or str(uuid.uuid4()) # Use provided session_id or generate a new one
    config = {"configurable": {"thread_id": session_id}} # Create config with the session_id as thread_id
    result = await agent_graph.ainvoke(
        {"messages": [("user", req.prompt)], "session_id": session_id, "safety_flagged": False}, # Initial state with user message and session info
        config=config, # Pass the config to the graph invocation

    )
    return {
        "session_id": session_id,
        "response": result["messages"][-1].content, # Return the content of the last message as the response
        "safety_flagged": result["safety_flagged"] # Include the safety flag status in the response 
    }

@app.post("/agent/stream")
async def stream_agent(req: AgentRequest):
    session_id = req.session_id or str(uuid.uuid4()) # Use provided session_id or generate a new one
    config = {"configurable": {"thread_id": session_id}} # Create config with the session_id as thread_id

    async def event_generator():
        async for event in agent_graph.astream_events(
            {"messages": [("user", req.prompt)], "session_id": session_id, "safety_flagged": False}, # Initial state with user message and session info
            config=config, version="v2" # Use v2 for more detailed event streaming
        ):
            if event["event"] == "on_chat_model_stream":
                token = event["data"]["chunk"].content # extract the streamed token from the event data
                if token:
                    yield f"data: {json.dumps({'token': token})}\n\n" # Stream the token as a Server-Sent Event (SSE)
        yield f"data: {json.dumps({'status': 'done'})}\n\n" # Indicate the end of the stream
    return StreamingResponse(event_generator(), media_type="text/event-stream") # Return the streaming response with the correct media type
