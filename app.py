import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pymongo import MongoClient
from datetime import datetime,UTC
import certifi
from langchain_core.messages import HumanMessage, AIMessage
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
mongo_uri = os.getenv("MONGODB_URI")

client = MongoClient(
    mongo_uri,
    tls=True,
    tlsCAFile=certifi.where()
)
db = client["CHATBOT"]
collection = db["users"]

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class ChatRequest(BaseModel):
    user_id : str
    question : str

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
    allow_credentials = True
)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are Smart Assistant, a highly intelligent, professional, and helpful AI assistant with persistent memory.

You can remember previous conversations and use that context to provide better, more personalized responses.

CORE BEHAVIOR:
- Answer any type of question: programming, business, studies, health, finance, productivity, or general knowledge.
- Use conversation history to maintain context and continuity.
- Provide clear, structured, and practical responses.
- Be professional, intelligent, and helpful.

SPECIAL INSTRUCTIONS:
- If user asks coding question, provide code example.
- If user asks plan, provide step-by-step plan.
- If user asks explanation, explain simply first, then deeply.
- If user asks comparison, provide structured comparison.
- If user asks for advice, provide actionable steps.

MEMORY USAGE RULES:
- Use previous conversation history when relevant.
- If the user refers to something mentioned earlier, use memory to respond correctly.
- Do NOT repeat information unnecessarily.
- Maintain conversation continuity naturally.

RESPONSE QUALITY RULES:
- Give direct answers first.
- Structure responses using headings, steps, or bullet points when helpful.
- Be concise but informative.
- Avoid unnecessary questions.
- Only ask clarification questions if truly needed.

FORMAT RULES:
For "plans" → Provide complete plan immediately.
For "technical questions" → Explain + Example.
For "advice" → Provide actionable steps.
For "general questions" → Provide clear explanation.

PERSONALITY:
- Professional
- Intelligent
- Helpful
- Calm
- Confident

Your goal is to behave like a production-level AI assistant similar to ChatGPT."""
        ),
        ("placeholder", "{history}"),
        ("user", "{question}")
    ]
)

llm = ChatGroq(
    api_key=groq_api_key,
    model="llama-3.1-70b-versatile",
    temperature=0.3,
    max_tokens=1024,
    top_p=0.9
)
chain = prompt | llm


def load_history(user_id):

    messages = []

    chats = collection.find(
        {"user_id": user_id}
    ).sort("timestamp", 1)

    for chat in chats:

        if chat["role"] == "user":
            messages.append(HumanMessage(content=chat["message"]))

        elif chat["role"] == "assistant":
            messages.append(AIMessage(content=chat["message"]))

    return messages

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/chat")
def chat(request : ChatRequest):
    history = load_history(request.user_id)
    response = chain.invoke({
        "history": history,
        "question": request.question
    })
    collection.insert_one({
        "user_id": request.user_id,
        "role": "user",
        "message": request.question,
        "timestamp": datetime.now(UTC)
    })

    collection.insert_one({
        "user_id": request.user_id,
        "role": "assistant",
        "message": response.content,
        "timestamp": datetime.now(UTC)
    })

    return {"response" : response.content}

