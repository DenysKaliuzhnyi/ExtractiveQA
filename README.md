## ExtractiveQA
This project implements an extractive question-answering system in a Telegram bot. The project leverages Google Cloud 
Run for scalable containerized deployment, GCP cloudbuild configuration for CI/CD, Google Cloud Storage for model 
hosting, and Google Cloud Secret Manager for secure configuration. The system is built using Python, FastAPI, 
Hugging Face Transformers, and Telegram Bot API.

---
### Project Overview

* **Telegram Bot** (`bot.py`): Accepts user queries in the format `Context | Question` and forwards them to the model API service.
* **QA model FastAPI Service** (`model_api.py`): Hosts a Transformer-based question-answering model and processes queries.
* **Cloud Build Configuration** (`cloudbuild.yaml`): Automates building, pushing, and deploying the services to Google Cloud Run.
* **Docker Compose Configuration** (`docker-compose.yaml`): Launches app locally.

---

### Key Features

* **Extractive QA**: Uses a fine-tuned Transformer model to extract answers from provided contexts.
* **Scalable Cloud Deployment**: Deploys services on Google Cloud Run for automatic scaling.
* **CI/CD**: Automatic deployment with cloudbuild configration that is triggered on push to the GitHub repository.
* **Model Hosting**: Downloads and initializes a pre-trained QA model from Google Cloud Storage.
* **Secure Secrets Management**: Uses Google Cloud Secret Manager to store sensitive credentials like the Telegram bot token.
* **Bot UI**: Provides a simple Telegram bot interface for users to interact with the QA system.
---

### Usage

1.	**Start the Bot**: Interact with the [@ExtractiveQAbot](https://t.me/ExtractiveQAbot) bot by sending messages in the format:
```plaintext
Context | Question
```
Example:
```plaintext
The Transformers library provides NLP tools. | What does it provide?
```
2. **Get the Answer**: The bot forwards you the answer by the QA model.

---


### Model

This repo does not include the code for model fine-tuning part, though below I include general considerations and steps to reproduce results.


**Considerations**.  
According to [paperswithcode.com](https://paperswithcode.com/sota/question-answering-on-squad20), 
the current open-source SOTA benchmark on SQuAD2.0 dataset is 
[Retro-Reader](https://paperswithcode.com/paper/retrospective-reader-for-machine-reading#code) model providing 90.578 
EM and 92.978 F1 scores. The other top-performing models include derivatives form BERT (e.g., 
[ALBERT](https://paperswithcode.com/paper/albert-a-lite-bert-for-self-supervised), 
[RoBERTa](https://paperswithcode.com/paper/roberta-a-robustly-optimized-bert-pretraining), etc.) and ELECTRA. 

For this project the selection criteria was to use a small model that can be trained on a local machine (M1 MackBook air). 
So I ended up using BERT-Tiny - the smallest from the family. Initial model's weights were not pre-trained for the extractive QA, 
so some task-specific layers were fine-tuned from scratch. The main goal of this project were not to use the most accurate 
model but to conduct the training process. Indeed, taking some out-of-the-box models would provide better results 
compared to the model I fine-tuned.

**Tools**.  
For model fine-tuning I used Transformers library from Hugging Face, which hosts [prajjwal1/bert-tiny](https://huggingface.co/prajjwal1/bert-tiny) 
model, [SQuAD2.0](https://huggingface.co/datasets/rajpurkar/squad_v2) dataset, and provides [run_qa.py](https://github.com/huggingface/transformers/blob/main/examples/pytorch/question-answering/run_qa.py) script for training and evaluation. I fine-tuned model on the dataset for 
40 epochs, which took around 11 hours on my local machine and achieved 39.48 EM and 44.31 F1 scores on the evaluation set. 
I enabled integration with Weights & Biases for logging training metrics.

**Training**.  
Below here are steps to reproduce the training process.
```bash
git clone https://github.com/huggingface/transformers.git
cd transformers/examples/pytorch/question-answering
pip install torch transformers datasets accelerate evaluate
wandb login
python3 run_qa.py   \
  --model_name_or_path prajjwal1/bert-tiny   \
  --dataset_name squad_v2   \
  --do_train    \
  --do_eval  \
  --per_device_train_batch_size 12   \
  --learning_rate 3e-5  \
  --num_train_epochs 40   \
  --max_seq_length 384   \
  --doc_stride 128 \
  --output_dir runs/train_squadV2_epoch40 \
  --overwrite_output_dir   \
  --report_to wandb \
  --save_steps 5000 \
  --version_2_with_negative
```
After training, model files are saved to a local directory and W&B. They can be archived as `model.tar.gz` and placed on
GCS for deployment.

**Results**.  
Below there is a training summery from logs and Weights & Biases.

```plaintext  
***** train metrics *****
  epoch                    =        40.0
  total_flos               =   4490144GF
  train_loss               =      1.5059
  train_runtime            = 11:06:58.82
  train_samples            =      131754
  train_samples_per_second =     131.692
  train_steps_per_second   =      10.975
  
***** eval metrics *****
  epoch                   =       40.0
  eval_HasAns_exact       =    31.3765
  eval_HasAns_f1          =    41.0357
  eval_HasAns_total       =       5928
  eval_NoAns_exact        =    47.5694
  eval_NoAns_f1           =    47.5694
  eval_NoAns_total        =       5945
  eval_best_exact         =    50.1221
  eval_best_exact_thresh  =        0.0
  eval_best_f1            =    50.1221
  eval_best_f1_thresh     =        0.0
  eval_exact              =    39.4845
  eval_f1                 =    44.3072
  eval_runtime            = 0:01:28.40
  eval_samples            =      12134
  eval_samples_per_second =    137.252
  eval_steps_per_second   =     17.159
  eval_total              =      11873
```
![training_loss.png](artifacts%2Ftraining_loss.png)

---

### Setup Instructions
Below here are setup instructions to launch bot locally and/or deploy it to Google Cloud Run.

#### 1. Prerequisites
* Python 3.12
* Google Cloud SDK
* Docker installed locally
* A Google Cloud project with:
  * Cloud Run enabled 
  * Secret Manager API enabled and `BOT_TOKEN` stored as a secret
  * Cloud Storage bucket created for the QA model and the `model.tar.gz` uploaded

---

#### 2. Local Deployment

Edit the `docker-compose.yaml` file to update env variables.
Then launch the services with:
```bash
docker-compose up --build
```

---

#### 3. Deployment to Google Cloud Run
Authenticate with Google Cloud SDK.  
```bash
gcloud auth login
```
Edit the `cloudbuild.yaml` file to update substitutions. Then run the following command:
```bash
gcloud builds submit --config=cloudbuild.yaml
```

---

### Future Work
There are many ways to extend and improve this project:
* **Fine-tuning**: Fine-tune and deploy bigger, more capable QA model.
* **Model registry CI/CD**: Implement a CI/CD pipeline between model training and deployment (e.g., automatic upload to GCS from W&B).
* **Add monitoring to bot**: Monitor performance of the system with extra tools, add alerts.
* **Simplify local build**: Allow local deployment without GCP.