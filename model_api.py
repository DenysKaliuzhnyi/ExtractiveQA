from fastapi import FastAPI
from pydantic import BaseModel
from transformers import pipeline, AutoModelForQuestionAnswering, AutoTokenizer


app = FastAPI()
model_dir = "../transformers/examples/pytorch/question-answering/runs/train_epoch40"
model = AutoModelForQuestionAnswering.from_pretrained(model_dir)
tokenizer = AutoTokenizer.from_pretrained(model_dir)
qa_pipeline = pipeline("question-answering", model=model, tokenizer=tokenizer)

class QARequest(BaseModel):
    context: str
    question: str


@app.post("/answer")
def get_answer(request: QARequest):
    result = qa_pipeline({"question": request.question, "context": request.context})
    return {"answer": result["answer"]}
