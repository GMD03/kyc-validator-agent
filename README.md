# 🛡️ Automated KYC Agent (LangGraph + Llama Vision)

An autonomous, multi-agent AI backend designed to orchestrate KYC (Know Your Customer) document verification. Built for Fintech and startup operations, this system uses a local multimodal LLM to extract data from government IDs and strictly validates it against user input using order-agnostic algorithms.

## 🚀 System Architecture

This project moves beyond linear scripts by utilizing a **Stateful, Cyclic LangGraph Architecture**:
1. **Extractor Node:** Uses `Llama 3.2 Vision` via Ollama to perform OCR and structured data extraction from ID images.
2. **Validator Node:** Applies strict Python-based business logic to check for missing fields, standardize varied date formats (e.g., "August 19, 2003" -> `2003-08-19`), and perform order-agnostic name matching.
3. **Database Mock Node:** Simulates an external compliance check (e.g., Ayuda/Fintech blocklists).
4. **Conditional Router:** Features self-correction loops for LLM hallucinations and Human-in-the-Loop (HITL) escalation for suspected fraud.

## 🛠️ Tech Stack
* **Orchestration:** LangGraph, LangChain Core
* **Inference:** Ollama (Llama 3.2 Vision)
* **Validation:** Pydantic
* **API Layer:** FastAPI, Uvicorn

## ⚙️ How to Run Locally

### 1. Prerequisites
* Python 3.10+
* [Ollama](https://ollama.com/) installed and running on your machine.
* Download the Llama Vision model:
  ```bash
  ollama run llama3.2-vision

  