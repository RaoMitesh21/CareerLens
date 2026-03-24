# CareerLens – AI-Powered Skill Gap Analyzer (Backend)

## Tech Stack
- **Backend:** FastAPI (Python)
- **Database:** MySQL
- **ORM:** SQLAlchemy

## Quick Start
```bash
cd careerlens-backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open: http://127.0.0.1:8000/docs to see the API docs.

## Migration and Validation Commands

### 1) Apply startup migrations (automatic)
Migrations run automatically when the API starts.

```bash
cd careerlens-backend
uvicorn app.main:app --reload
```

### 2) Upload and process a PDF resume

The API supports server-side PDF upload and text extraction:

```bash
# Using curl to upload a PDF resume
curl -X POST http://127.0.0.1:8000/resumes/upload-pdf \
  -F "user_id=1" \
  -F "file=@/path/to/resume.pdf"

# Response:
# {
#   "id": 42,
#   "user_id": 1,
#   "filename": "resume.pdf",
#   "created_at": "2026-03-24T10:30:00"
# }

# Then retrieve the extracted text:
curl http://127.0.0.1:8000/resumes/42
```

Features:
- Server-side PDF text extraction using pdfplumber
- Automatic validation (PDF format, file size, minimum text content)
- Stores extracted text in resume records for analysis

### 3) Hybrid vs ESCO evaluation on CSV resumes

```bash
cd careerlens-backend
python3 -m scripts.evaluate_hybrid \
	--input-csv ../Datasets/Resume.csv \
	--target-role "software developer" \
	--resume-col "Resume_str" \
	--name-col "Name" \
	--output-csv ./reports/hybrid_eval_output.csv \
	--output-report ./reports/hybrid_eval_summary.txt \
	--top-k 3 \
	--top-movers 10
```

### 4) API smoke tests (includes hybrid endpoints)

```bash
cd careerlens-backend
python3 -m scripts.test_api
```
