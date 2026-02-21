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
        ("system", "you are a fitness bot,tell me the ans with respect to the fitness things."),
        ("placeholder", "{history}"),
        ("user","{question}")
    ]
)

llm = ChatGroq(api_key = groq_api_key, model="openai/gpt-oss-20b")
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

