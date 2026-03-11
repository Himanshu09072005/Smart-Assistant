import os
import certifi
import pytz
import uuid

from dotenv import load_dotenv
from datetime import datetime, UTC

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

from pymongo import MongoClient

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage


load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")
mongo_uri = os.getenv("MONGODB_URI")

client = MongoClient(
    mongo_uri,
    tls=True,
    tlsCAFile=certifi.where()
)

db = client["CHATBOT"]
collection = db["messages"]


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    question: str


class NewChat(BaseModel):
    user_id: str


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful AI assistant."),
        ("placeholder", "{history}"),
        ("user", "{question}")
    ]
)


llm = ChatGroq(
    api_key=groq_api_key,
    model="llama-3.3-70b-versatile"
)

chain = prompt | llm


def load_history(user_id, conversation_id):

    chats = list(
        collection.find({
            "user_id": user_id,
            "conversation_id": conversation_id
        }).sort("timestamp", 1)
    )

    history = []

    for chat in chats:

        if chat["role"] == "user":
            history.append(HumanMessage(content=chat["message"]))

        if chat["role"] == "assistant":
            history.append(AIMessage(content=chat["message"]))

    return history


@app.post("/chat")

def chat(req: ChatRequest):

    history = load_history(req.user_id, req.conversation_id)

    response = chain.invoke({
        "history": history,
        "question": req.question
    })

    reply = response.content

    collection.insert_one({
        "user_id": req.user_id,
        "conversation_id": req.conversation_id,
        "role": "user",
        "message": req.question,
        "timestamp": datetime.now(UTC)
    })

    collection.insert_one({
        "user_id": req.user_id,
        "conversation_id": req.conversation_id,
        "role": "assistant",
        "message": reply,
        "timestamp": datetime.now(UTC)
    })

    return {"response": reply}


@app.post("/new_chat")

def new_chat(req: NewChat):

    conversation_id = str(uuid.uuid4())

    return {"conversation_id": conversation_id}


@app.get("/chat_list/{user_id}")

def chat_list(user_id: str):

    chats = collection.distinct(
        "conversation_id",
        {"user_id": user_id}
    )

    return {"chats": chats}


@app.get("/chat_history/{conversation_id}")

def chat_history(conversation_id: str):

    chats = list(
        collection.find({"conversation_id": conversation_id})
        .sort("timestamp", 1)
    )

    result = []

    for chat in chats:

        result.append({
            "role": chat["role"],
            "message": chat["message"]
        })

    return {"history": result}
