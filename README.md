# CareerLens – AI-Powered Skill Gap Analyzer

An intelligent, full-stack **Skill Gap Analyzer** that compares resumes against standardised occupational skill requirements from the **ESCO taxonomy**.

## 🎯 Quick Links

- 📚 [Full Documentation](./DOCUMENTATION.md)
- 🚀 [Deployment Guide](./DEPLOYMENT.md)
- 🤖 [n8n Workflows](./workflows/README.md)
- 📋 [Project Report](./careerlens-backend/REPORT.md)

## 🌟 Features

✅ **Resume Analysis** - Compare resumes against 3,007 ESCO occupations  
✅ **Skill Gap Detection** - Identify missing skills with confidence scores  
✅ **Learning Roadmap** - Get personalized development paths  
✅ **ML Fit Scoring** - Predict recruiter fit probability  
✅ **Batch Processing** - Automate resume analysis with n8n  
✅ **Real-time Notifications** - Alert recruiters of high-fit candidates  
✅ **API-First Design** - RESTful endpoints with auto-generated docs  

## 🚀 Quick Start (30 seconds)

### With Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/your-org/careerlens.git
cd careerlens

# 2. Setup and start
chmod +x quickstart.sh
./quickstart.sh

# 3. Open browser
open http://localhost:3000
```

### Manual Setup (Local Development)

```bash
# Backend
cd careerlens-backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (in new terminal)
cd careerlens-frontend
npm install
npm run dev
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                    │
│                  (http://localhost:3000)                    │
└────────────┬────────────────────────────────────────────────┘
             │ HTTP/JSON
┌────────────▼────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.13)                  │
│                (http://localhost:8000)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /analyze           - Hybrid ESCO/O*NET analysis     │  │
│  │  /ml-fit/score      - ML-based recruiter fit        │  │
│  │  /roadmap           - Learning path generation      │  │
│  │  /resumes           - Resume management             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────────────┐
│           MySQL Database + ESCO/O*NET Data                  │
│         (Occupations, Skills, Relations)                    │
└─────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│            n8n Workflow Automation (Optional)               │
│     (Batch processing, notifications, scheduling)          │
└─────────────────────────────────────────────────────────────┘
```

## 📚 API Endpoints

### Resume Analysis
```bash
# Single resume analysis
POST /analyze
{
  "resume_text": "...",
  "target_role": "software developer"
}

# Hybrid ESCO + O*NET analysis
POST /analyze/hybrid
{
  "resume_text": "...",
  "target_role": "software developer"
}

# API Docs
GET /docs  # Swagger UI
GET /openapi.json
```

### ML Fit Scoring
```bash
# Single candidate prediction
POST /ml-fit/score
{
  "candidate_id": "candidate_123",
  "analysis_result": {...}
}

# Batch predictions
POST /ml-fit/score-batch
{
  "candidates": [
    {"candidate_id": "c1", "analysis_result": {...}},
    {"candidate_id": "c2", "analysis_result": {...}}
  ]
}

# Model metadata
GET /ml-fit/model/metadata
```

## 🗄️ Database

**Schema:**
- `occupations` - 3,007 ESCO occupations
- `skills` - 13,896 ESCO skills
- `occupation_skill_relations` - 123,788 mappings
- `resumes` - User resume storage
- `analysis_results` - Analysis history
- `users` - User accounts

**ER Diagram:**
```
occupations 1──*── occupation_skill_relations ──*─ skills
                        │
                        │
                        ▼
                resumes 1──* analysis_results
                │
                └── users
```

## 🤖 Automation with n8n

Pre-built workflows for:
1. **Batch Resume Analysis** - Process multiple resumes daily
2. **Recruiter Notifications** - Alert on high-fit candidates
3. **Scheduled Reports** - Generate weekly analysis summaries

See [workflows/README.md](./workflows/README.md) for setup.

## 📊 Scoring Algorithm

### Three-Tier Classification
- **Core Skills** (Essential) - 40% weight
- **Secondary Skills** (Important) - 35% weight
- **Bonus Skills** (Nice-to-have) - 25% weight

### Confidence Engine
Combines:
- Frequency signals (skill mention count)
- Context signals (skill relevance)
- Morphological variants (algorithm-wise matching)

### ML Fit Model
- **Type:** Logistic Regression or Random Forest
- **Features:** Scores, confidence, skill counts
- **Output:** Fit probability 0-1 + feature importance

See [DOCUMENTATION.md](./DOCUMENTATION.md#8-scoring-algorithm--deep-dive) for details.

## 🧪 Testing

### Run Tests
```bash
# Backend tests
cd careerlens-backend
pytest tests/ -v

# Frontend tests
cd careerlens-frontend
npm test

# Integration tests
curl http://localhost:8000/docs  # Check API
curl http://localhost:3000       # Check frontend
```

### Test Data
- Sample resumes: `Datasets/Resume.csv`
- ESCO data: `Datasets/ESCO csv/`
- Test scripts: `careerlens-backend/scripts/test_*.py`

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Clean up volumes (⚠️ removes database)
docker-compose down -v

# Start specific service
docker-compose up -d backend

# Execute command in container
docker-compose exec backend bash
```

## 📦 Deployment

### Quickstart Options
1. **Docker Compose** - Local development (recommended)
2. **AWS ECS** - Scalable production deployment
3. **DigitalOcean App Platform** - Simple managed hosting
4. **Kubernetes** - Enterprise-grade orchestration

See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

## 🔐 Security

- ✅ Environment variables for secrets (`.env` not in git)
- ✅ CORS configured for frontend origin
- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Rate limiting on API endpoints

## 📈 Performance

- ⚡ Analysis: ~500ms per resume
- ⚡ Batch processing: 1000 resumes/hour
- ⚡ Database queries: <100ms (indexed)
- ⚡ Frontend load time: <2s

## 🐛 Known Limitations

1. **Resume Parsing** - Text extraction from PDFs may lose formatting
2. **Skill Matching** - Acronyms not always recognized
3. **Role Resolution** - Similar role names may conflict
4. **ML Model** - Requires historical data for training (see `scripts/train_ml_fit_model.py`)

## 🔮 Future Enhancements

- [ ] Multi-language support (ESCO has 27 languages)
- [ ] Video resume analysis
- [ ] Real-time collaboration (multiple recruiters)
- [ ] Advanced ML models (BERT-based skill extraction)
- [ ] Mobile app (React Native)
- [ ] Blockchain credentials validation

## 📞 Support

- 📚 [API Documentation](http://localhost:8000/docs)
- 🐙 [GitHub Issues](https://github.com/your-org/careerlens/issues)
- 💬 [Discussion Forum](https://github.com/your-org/careerlens/discussions)

## 📄 License

MIT License - See [LICENSE](./LICENSE) for details

## 👨‍💻 Author

**Mitesh Rao** - Capstone Project  
*Tech Stack:* Python 3.13 · FastAPI · React 19 · MySQL · ESCO Dataset

---

**Last Updated:** March 2026  
**Version:** v2.0.0
