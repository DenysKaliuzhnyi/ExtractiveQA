from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
from google.cloud import storage
import os


app = FastAPI()
MODEL_BUCKET = os.getenv("MODEL_BUCKET")
MODEL_PATH = os.getenv("MODEL_PATH")
MODEL_DIR = "artifacts/model"

def download_folder(bucket_name, folder_name, destination_dir):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_name)

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for blob in blobs:
        local_file_path = os.path.join(destination_dir, blob.name)
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        blob.download_to_filename(local_file_path)
        print(f"Downloaded {blob.name} to {local_file_path}")


if not os.path.exists(MODEL_DIR):
    print("Model not found locally. Downloading from GCS...")
    download_folder(MODEL_BUCKET, MODEL_PATH, os.path.dirname(MODEL_DIR))

model = AutoModelForQuestionAnswering.from_pretrained(MODEL_DIR)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

class QARequest(BaseModel):
    context: str
    question: str


@app.post("/answer")
def get_answer(request: QARequest):
    try:
        result = qa_pipeline({"question": request.question, "context": request.context})
        return {"answer": result["answer"]}
    except Exception as e:
        return {"error": str(e)}