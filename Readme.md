# LanNGraph Prototype - Minimum Viable Safety Agent

## Goal

Running agent i can hit with a curl or simple UI, deployed somewhere accessible. Nothing more.

## What's In

- Single-agent graph - 3 nodes
- 1 tool(web search or echo)
- FastAPI with `/run` + `/stream` endpoints
- SQLite checkpointer(not yet Postgres setup)
- Railway deploy
- .env config
- LangSmith free tracing

## Stage-0 structure

safety-agent-v0/
├── app/
│   ├── main.py          # FastAPI app + lifespan
│   ├── graph.py         # LangGraph StateGraph (3 nodes)
│   ├── state.py         # AgentState TypedDict
│   ├── tools.py         # 1 tool (Tavily search)
│   └── schemas.py       # Pydantic request/response
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
