import os
import time
import hashlib
import redis
import mlflow
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from fastapi import BackgroundTasks

load_dotenv()

# --- MLFLOW CONFIGURATION ---
mlflow.set_experiment("LinguaFlow-Live-Translations")

# ---------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Setup
try:
    redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"), decode_responses=True)
    redis_client.ping() # Check connection
except redis.ConnectionError:
    print("Warning: Redis not connected. Caching disabled.")
    redis_client = None

llm = ChatGroq(
    temperature=0, 
    groq_api_key=os.getenv("GROQ_API_KEY"), 
    model_name=os.getenv("GROQ_MODEL")
)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a skilled translator. Translate into {language}. Return ONLY the text."),
    ("human", "{text}"),
])

chain = prompt | llm

class TranslationRequest(BaseModel):
    text: str
    target_lang: str = os.getenv("TARGET_LANG")


def log_to_mlflow(text, translation, latency):
    # This runs AFTER the response is sent to the user
    with mlflow.start_run():
        mlflow.log_param("text", text)
        mlflow.log_metric("latency", latency)
        mlflow.log_param("translation", translation)

@app.post("/translate")
async def translate_text(request: TranslationRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    clean_text = request.text.strip().lower()
    text_hash = hashlib.md5(clean_text.encode()).hexdigest()
    cache_key = f"trans:{request.target_lang}:{text_hash}"

    # Check Cache
    if redis_client:
        cached_translation = redis_client.get(cache_key)
        if cached_translation:
            latency = round((time.time() - start_time) * 1000, 2)
            background_tasks.add_task(log_to_mlflow, request.text, cached_translation, latency)
            return {
                "original": request.text,
                "translated": cached_translation,
                "latency_ms": latency,
                "source": "cache"
            }

    # API Call
    try:
        # MLflow autolog captures this .ainvoke() automatically!
        response = await chain.ainvoke({
            "language": request.target_lang,
            "text": request.text
        })
        translated_text = response.content
        
        if redis_client:
            redis_client.setex(cache_key, 86400, translated_text)
        
        latency = round((time.time() - start_time) * 1000, 2)

        # Send response immediately, log later
        background_tasks.add_task(log_to_mlflow, request.text, translated_text, latency)

        return {
            "original": request.text,
            "translated": translated_text,
            "latency_ms": latency,
            "source": "api"
        }
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))