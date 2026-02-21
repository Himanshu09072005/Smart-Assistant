# Smart Assistant Chatbot

## Project Overview
Smart Assistant is an AI-powered chatbot built using FastAPI, LangChain, Groq LLM, and MongoDB. It provides intelligent responses and stores conversation history using memory.

## Features
- AI chatbot using Groq LLM
- FastAPI backend
- MongoDB memory storage
- Chat history persistence
- Web-based frontend
- Cloud deployed using Render

## Memory Implementation
Memory is implemented using MongoDB. Each message is stored with:
- user_id
- role (user/assistant)
- message
- timestamp

When a user sends a message, previous conversation history is loaded from MongoDB and passed to the LLM.

## Tech Stack
- Python
- FastAPI
- LangChain
- Groq API
- MongoDB
- HTML/CSS
- Render

## Live API Link
https://smart-assistant-nd1j.onrender.com

## GitHub Repo
https://github.com/Himanshu09072005/Smart-Assistant