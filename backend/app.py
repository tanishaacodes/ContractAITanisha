# app.py
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ingest_contracts import ingest_folder
from rag import qa_flow, generate_contract_flow

# -----------------------------------------------------
# FASTAPI APP
# -----------------------------------------------------
app = FastAPI()

# -----------------------------------------------------
# CORS (ALLOW FRONTEND)
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Frontend can call this API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------
# UPLOAD DIR
# -----------------------------------------------------
UPLOAD_DIR = Path("uploaded_contracts")
UPLOAD_DIR.mkdir(exist_ok=True)


# -----------------------------------------------------
# ROUTE: UPLOAD CONTRACTS
# -----------------------------------------------------
@app.post("/upload")
async def upload_contracts(files: list[UploadFile] = File(...)):
    if len(files) > 5:
        return JSONResponse({"error": "You can upload max 5 files."}, status_code=400)

    saved = []
    for f in files:
        dest = UPLOAD_DIR / f.filename
        with open(dest, "wb") as wf:
            shutil.copyfileobj(f.file, wf)
        saved.append(str(dest))

    return {"saved": saved}


# -----------------------------------------------------
# ROUTE: INGEST CONTRACTS
# -----------------------------------------------------
@app.post("/ingest")
async def ingest():
    """
    Converts uploaded files → extracts text → chunks → embeddings → sends to Qdrant.
    """
    count = ingest_folder(str(UPLOAD_DIR))
    return {"status": "success", "vectors_upserted": count}


# -----------------------------------------------------
# ROUTE: Q&A (SHORT ANSWER)
# -----------------------------------------------------
@app.post("/qa")
async def qa(query: str = Form(...)):
    """
    Ask a question based on uploaded contracts.
    Returns short answer (3–5 lines).
    """
    result = qa_flow(query)
    return JSONResponse(content=result)


# -----------------------------------------------------
# ROUTE: GENERATE CONTRACT (FULL CONTRACT)
# -----------------------------------------------------
@app.post("/generate")
async def generate(instruction: str = Form(...)):
    """
    Generate a full legal contract using RAG + LLM.
    """
    result = generate_contract_flow(instruction)
    return JSONResponse(content=result)
