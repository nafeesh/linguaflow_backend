import os
import time
import hashlib
import redis
import mlflow
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import requests

load_dotenv()

# --- MLFLOW SETUP (MANUAL LOGGING ONLY) ---
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
mlflow.set_tracking_uri(MLFLOW_URI)

experiment_name = "LinguaFlow-Live-Translations"
max_retries = 15
retry_delay = 2

print(f"Attempting to connect to MLflow at {MLFLOW_URI}...")

# We still need this loop to ensure the Experiment exists before we start.
# Otherwise, the first request might fail or log to 'Default'.
for attempt in range(max_retries):
    try:
        mlflow.set_experiment(experiment_name)
        print(f"✅ Successfully connected to Experiment: {experiment_name}")
        break 
    except Exception as e:
        print(f"⏳ MLflow not ready yet (Attempt {attempt+1}/{max_retries}). Retrying in {retry_delay}s...")
        time.sleep(retry_delay)
else:
    print("❌ Could not connect to MLflow. Logging might fail.")

# ------------------------------------------

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
    redis_client.ping()
except (redis.ConnectionError, TypeError):
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
    target_lang: str = os.getenv("TARGET_LANG", "French")

# --- YOUR MANUAL LOGGING FUNCTION ---
def log_to_mlflow(text, translation, latency):
    try:
        # We explicitly mention the experiment_id to be safe, 
        # though set_experiment above usually handles it.
        with mlflow.start_run(run_name="manual_log"): 
            mlflow.log_param("text", text)
            mlflow.log_metric("latency_ms", latency)
            mlflow.log_param("translation", translation)
    except Exception as e:
        print(f"⚠️ Failed to log to MLflow: {e}")

@app.post("/translate")
async def translate_text(request: TranslationRequest, background_tasks: BackgroundTasks):
    start_time = time.time()
    
    clean_text = request.text.strip().lower()
    text_hash = hashlib.md5(clean_text.encode()).hexdigest()
    cache_key = f"trans:{request.target_lang}:{text_hash}"

    # 1. Check Cache
    if redis_client:
        cached_translation = redis_client.get(cache_key)
        if cached_translation:
            latency = round((time.time() - start_time) * 1000, 2)
            # Log cache hit too!
            background_tasks.add_task(log_to_mlflow, request.text, cached_translation, latency)
            return {
                "original": request.text,
                "translated": cached_translation,
                "latency_ms": latency,
                "source": "cache"
            }

    # 2. API Call
    try:
        response = await chain.ainvoke({
            "language": request.target_lang,
            "text": request.text
        })
        translated_text = response.content
        
        if redis_client:
            redis_client.setex(cache_key, 86400, translated_text)
        
        latency = round((time.time() - start_time) * 1000, 2)

        # 3. Log to MLflow in background
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