import os
import certifi
import pytz

from dotenv import load_dotenv
from datetime import datetime, UTC

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel

from pymongo import MongoClient

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage


load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
mongo_uri = os.getenv("MONGODB_URI")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY is missing in .env file")

if not mongo_uri:
    raise ValueError("MONGODB_URI is missing in .env file")


client = MongoClient(
    mongo_uri,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=5000
)

db = client["CHATBOT"]
collection = db["users"]

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

class ChatRequest(BaseModel):
    user_id: str
    question: str


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are Smart Assistant, a highly intelligent, professional, and helpful AI assistant with persistent memory.

Current date and time: {current_time}

IMPORTANT:
- You MUST use this current date and time when answering questions about today's date, day, or time.
- India follows IST (Asia/Kolkata) unless otherwise specified.

CORE BEHAVIOR:
- Answer any type of question: programming, business, studies, health, finance, productivity, or general knowledge.
- Use conversation history to maintain context and continuity.
- Provide clear, structured, and practical responses.
- Be professional, intelligent, and helpful.

SPECIAL INSTRUCTIONS:
- If user asks coding question, provide working code example.
- If user asks plan, provide step-by-step plan.
- If user asks explanation, explain simply first, then deeply.
- If user asks comparison, provide structured comparison.
- If user asks for advice, provide actionable steps.

MEMORY USAGE RULES:
- Use previous conversation history when relevant.
- Maintain conversation continuity naturally.
- Do NOT repeat unnecessary information.

RESPONSE QUALITY RULES:
- Give direct answers first.
- Structure responses using headings, bullet points, or steps.
- Be concise but informative.
- Avoid unnecessary clarifying questions.

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
    model="llama-3.3-70b-versatile",
    temperature=0.3
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
def chat(request: ChatRequest):

    try:

        if not request.question.strip():
            return {"response": "Please enter a valid question."}

        history = load_history(request.user_id)

        ist = pytz.timezone("Asia/Kolkata")
        current_time = datetime.now(ist).strftime(
            "%A, %d %B %Y, %I:%M %p IST"
        )

        response = chain.invoke({
            "history": history,
            "question": request.question,
            "current_time": current_time
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

        return {"response": response.content}

    except Exception as e:

        print("ERROR:", e)

        return {
            "response": "Sorry, something went wrong. Please try again."
        }