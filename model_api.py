from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer
from google.cloud import storage
import os
import tarfile
import logging


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = FastAPI()
MODEL_BUCKET = os.getenv("MODEL_BUCKET")
MODEL_FILE = 'model.tar.gz'
MODEL_DIR = "artifacts/model"


def download_blob(bucket_name, file_name, destination_path):
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    to_name = os.path.basename(file_name)
    to_path = os.path.join(destination_path, to_name)
    blob.download_to_filename(to_path)
    logger.info(f"Downloaded {blob.name} to {to_path}")

    logger.info(f"Extracting archive ...")
    path = os.path.join(destination_path, file_name)
    with tarfile.open(path, "r:gz") as tar:
        tar.extractall(path=destination_path)


if not os.path.exists(MODEL_DIR):
    logger.info("Model not found locally. Downloading from GCS...")
    download_blob(MODEL_BUCKET, MODEL_FILE, os.path.dirname(MODEL_DIR))

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
        answer = result["answer"]
        score = result["score"]
        response = answer if score > 1e-5 else "Sorry, I couldn't find the answer form the provided context."
        return {"answer": response}
    except Exception as e:
        return {"error": str(e)}
