# 🔬 App Reader — Complete System Flow & Rule Reference

> **App Reader v2.0** — AI Readiness Assessment Platform  
> This document explains the full end-to-end pipeline, all 56 analysis rules, scoring algorithm, and data flow.

---

## 📋 Table of Contents

1. [High-Level Architecture](#1-high-level-architecture)
2. [Step-by-Step Pipeline Flow](#2-step-by-step-pipeline-flow)
3. [All 56 Static Analysis Rules](#3-all-56-static-analysis-rules)
4. [Scoring Algorithm](#4-scoring-algorithm)
5. [Database Structure](#5-database-structure)
6. [Real-Time Progress (SSE)](#6-real-time-progress-sse)
7. [Report Structure](#7-report-structure)
8. [File & Tech Reference](#8-file--tech-reference)

---

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  FRONTEND  (React + Vite)                                           │
│  Splash → Login → Dashboard → Upload → Report → Admin              │
└─────────────────────┬───────────────────────────────────────────────┘
                      │  HTTP / SSE (Server-Sent Events)
┌─────────────────────▼───────────────────────────────────────────────┐
│  BACKEND  (FastAPI + Python 3.12)                                   │
│  /api/auth  /api/assess  /api/report  /api/admin  /api/user         │
└──────┬──────────────────────────────────────┬────────────────────────┘
       │                                      │
┌──────▼──────┐                    ┌──────────▼──────────┐
│  MongoDB     │                    │  /logs/ directory   │
│  (Motor)     │                    │  JSON + TXT reports  │
│  users       │                    └─────────────────────┘
│  assessments │
└─────────────┘
```

---

## 2. Step-by-Step Pipeline Flow

### Step 0 — Authentication
```
User enters email + password
  → POST /api/auth/login
  → Password verified with bcrypt
  → JWT access token issued (expires in settings.ACCESS_TOKEN_EXPIRE)
  → Token stored in localStorage
  → All subsequent requests carry: Authorization: Bearer <token>
```

---

### Step 1 — File Upload
```
User drops ZIP or pastes Git URL
  → POST /api/assess/run  (multipart/form-data)
  → JWT token verified by Depends(get_current_user_id)
  → ZIP saved to temp file on disk (tempfile.NamedTemporaryFile)
```

**Sandbox Security Check** (before anything else):
```python
check_zip_safety(zip_path)
  → Scan ZIP central directory WITHOUT extracting
  → Reject if: path contains "../" or starts with "/"  (path traversal attack)
  → Reject if: file is corrupt/invalid ZIP
  → No file count or size limits — unlimited files accepted
```

**MongoDB placeholder created immediately:**
```json
{
  "user_id": "ObjectId(...)",
  "source_value": "myproject.zip",
  "source_type": "zip",
  "score": 0,
  "status": "Running",
  "created_at": "2026-03-01T00:00:00Z"
}
```

---

### Step 2 — File Ingestion (`file_reader.py`)
```
ZIP extracted to temp directory
  → Walk all directories recursively
  → Skip: node_modules, .git, __pycache__, .venv, dist, build, .next, target
  → Accept: .py .js .ts .jsx .tsx .java .go .rb .php .cs .cpp .c .h .rs
            .json .yaml .yml .toml .ini .cfg .env .md .sh .dockerfile etc.
  → NO file count limit
```

**Smart sampling for huge files:**
```
File size ≤ 85 KB  → Read entire file
File size > 85 KB  → Read first 80,000 chars (head) + last 5,000 chars (tail)
                     Insert separator: "# ... [X total lines — middle section omitted] ..."
```

**Line counting for huge files:**
```python
# Fast binary chunk scan — never loads full file into RAM
count_lines_fast(path) → reads in 64 KB chunks, counts \n bytes
```

Result: list of `{path, content, ext, size_bytes, total_lines, is_sampled}`

---

### Step 3 — Project Classification (`classifier.py`)
```
Input: list of all files
Output: project_info dict
```

Detects:
| Field | How detected |
|---|---|
| `primary_language` | Count files per extension, highest wins |
| `stack` | Keyword scan: FastAPI/Django/Express/Spring/Rails etc. |
| `has_docker` | Dockerfile or docker-compose.yml present |
| `has_cicd` | .github/workflows/ or .gitlab-ci.yml or Jenkinsfile |
| `language_diversity` | Count of distinct code extensions used |
| `total_files` | len(files) |
| `has_tests` | files with test_/spec. patterns |
| `has_env_example` | .env.example present |

---

### Step 4 — Static Analysis — 56 Rules (`static_analyzer.py`)

**This is the heaviest layer — runs FIRST, then other layers run in parallel.**

**Single-pass algorithm:**
```
Pre-compile all 56 rules' regex patterns once at module import → _RULE_BANK

For each FILE in files:
  For each LINE in file content:
    For each of 56 RULES:
      Check positive patterns → record evidence hit
      Check negative patterns → record violation hit

After all files scanned:
  Score each rule based on hits
  Compute category scores
  Check hard blockers
  Build risk register
```

**Why single-pass?**  
Old approach: 56 loops × N files × M lines = O(56×N×M)  
New approach: N files × M lines × 56 checks = O(N×M×56)  
Same math but now each line is in CPU cache when all 56 rules check it → 5-10x faster.

**Real-time per-file ETA:**
```
Every 10 files → emit progress event
ETA = (remaining_files) × (rolling_avg_time_per_file over last 20 files)
msg = "Scanned 142/400 files — ETA 18s"
```

---

### Step 5 — 8 Layers in Parallel (`assessment_engine.py`)

```python
with ThreadPoolExecutor(max_workers=8) as pool:
    futures = {
        pool.submit(build_import_graph, files): "graph",
        pool.submit(compute_ast_metrics, files): "ast",
        pool.submit(check_dependencies, files):  "deps",
        pool.submit(check_test_coverage, files): "tests",
        pool.submit(check_api_quality, files):   "api",
        pool.submit(check_technical_debt, files):"debt",
        pool.submit(check_env_maturity, files):  "env",
        pool.submit(check_observability, files): "obs",
    }
```

All 8 run simultaneously. Total time = slowest single layer, not sum of all.

**Each layer's output:**

| Layer | Key outputs |
|---|---|
| Import Graph | `cohesion_score`, `orphan_files`, `has_circular_imports`, `edge_count` |
| AST Metrics | `ast_score`, `total_functions`, `total_classes`, `comment_density`, `high_complexity_count` |
| Dependencies | `dependency_score`, `unpinned_count`, `deprecated`, `known_risky` |
| Test Coverage | `test_score`, `test_files`, `source_files`, `test_ratio`, `assertion_count` |
| API Quality | `api_score`, `has_versioning`, `has_openapi_docs`, `has_pagination` |
| Tech Debt | `debt_score`, `todos`, `fixmes`, `hacks`, `total_debt_markers` |
| Env Maturity | `env_score`, `has_env_example`, `uses_env_vars`, `has_hardcoded_localhost` |
| Observability | `observability_score`, `has_logging`, `has_health_check`, `has_metrics` |

---

### Step 6 — Score Fusion (`score_engine.py`)

```python
# Weighted average of 9 layer scores
LAYER_WEIGHTS = {
    "static_rules":  30,   # Security rules — most important
    "import_graph":  15,   # Code structure
    "ast_metrics":   10,   # Code complexity
    "dependencies":  10,   # Dependency health
    "test_coverage": 10,   # Testing
    "api_quality":    8,   # API design
    "tech_debt":      7,   # Maintainability
    "env_maturity":   5,   # Configuration
    "observability":  5,   # Monitoring
}

raw_score = sum(layer_score[k] * LAYER_WEIGHTS[k] for k in layers) / 100

# Penalty: too many programming languages = harder to maintain
if language_diversity > 4:
    raw_score -= 5

# Hard blocker cap: critical security issues cap score at 49
has_blockers = bool(static_result.get("blockers", []))
if has_blockers:
    raw_score = min(raw_score, 49)

final_score = clamp(raw_score, 0, 100)
```

**Status assignment:**
```
score ≥ 75  → "Strong"   (AI-ready ✅)
score ≥ 50  → "Moderate" (mostly ready ⚠️)
score ≥ 30  → "Weak"     (needs work 🔴)
score < 30  → "Critical" (major issues ⛔)
```

**Gate checks (5 gates for "80+ AI ready"):**
```
✅ score_ok              score ≥ 80
✅ no_blockers           no hardcoded secrets / no auth / no eval()
✅ has_tests             test:source ratio ≥ 10%
✅ has_auth              JWT/OAuth detected
✅ no_hardcoded_secrets  no secrets in code
```

---

### Step 7 — Report Building (`report_builder.py`)

Assembles the final report JSON:
```json
{
  "score": 73,
  "status": "Moderate",
  "executive_summary": "Your project shows strong security foundations...",
  "layer_scores": { "static_rules": 82, "import_graph": 71, ... },
  "layer_analysis": { "static_rules": { "title": "...", "analysis_text": "...", "data": {...} } },
  "capabilities": { "Has JWT Auth": true, "Has Rate Limiting": false, ... },
  "blockers": [],
  "risks": [ { "rule_id": "R36", "name": "Dependency Pinning", "severity": "high", ... } ],
  "why_not_80": [ "Improve test_coverage (currently 12/100)", "Add unit tests..." ],
  "improvement_diagnostics": [...],
  "risk_register": [...],
  "project_profile": { "primary_language": "Python", "has_docker": true, ... },
  "score_details": { "total_functions": 47, "comment_density": 0.18, ... },
  "gate_checks": { "score_ok": false, "no_blockers": true, ... }
}
```

---

### Step 8 — Database Save + Log File

**MongoDB update:**
```python
await assessment_repo.update_assessment(result_id, {
    **full_report,
    "user_id": ObjectId(user_id),
    "status": "Moderate",
    "score": 73,
    "updated_at": datetime.utcnow()
})
```

**File system save:**
```
/logs/
  └── {assessment_id}/
        ├── report.json      (full report JSON)
        └── summary.txt      (human-readable text summary)
```

---

### Step 9 — SSE Stream Completes

**Final event sent to frontend:**
```json
{"type": "complete", "id": "abc123def456"}
```

Frontend redirects to: `/report/abc123def456`  
Arc reactor animation stops, "Analysis Complete!" screen appears with total time taken.

---

## 3. All 56 Static Analysis Rules

### 🔒 Category 1: Security & Auth (R01–R10)
*Weight: 28% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R01 | JWT / Token Auth | 🔴 Critical | 8 | `jwt.`, `jsonwebtoken`, `PyJWT`, `bearer`, `access_token`, `oauth2`, `HTTPBearer` |
| R02 | Password Hashing | 🔴 Critical | 6 | `bcrypt`, `argon2`, `pbkdf2`, `hashpw` — **Bad:** `md5`, `sha1(` |
| R03 | RBAC / Permissions | 🟠 High | 5 | `role`, `permission`, `is_admin`, `has_permission`, `RoleChecker`, `scope` |
| R04 | Session / Refresh Token | 🟡 Medium | 4 | `refresh_token`, `session`, `cookie`, `httponly`, `revoke`, `blacklist` |
| R05 | Rate Limiting | 🟠 High | 5 | `slowapi`, `ratelimit`, `throttle`, `@limiter`, `express-rate-limit` |
| R06 | CORS Configuration | 🟠 High | 4 | `CORSMiddleware`, `allow_origins`, `@cross_origin` — **Bad:** `allow_origins=["*"]` |
| R07 | SQL Injection Prevention | 🔴 Critical | 7 | `sqlalchemy`, `motor`, `prisma` — **Bad:** `f"SELECT...{user_input}` |
| R08 | CSRF Protection | 🟡 Medium | 3 | `csrf`, `csrftoken`, `samesite`, `SameSite`, `X-CSRF-Token` |
| R09 | Input Validation | 🟠 High | 6 | `pydantic`, `BaseModel`, `Field(`, `zod`, `joi`, `marshmallow`, `@validator` |
| R10 | HTTPS / TLS | 🟠 High | 4 | `ssl_context`, `HTTPSRedirectMiddleware`, `tls`, `certfile`, `SECURE_SSL_REDIRECT` |

---

### 🛡️ Category 2: Data Protection (R11–R18)
*Weight: 16% of static score*

multilodel-detection in code?


| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R11 | No Hardcoded Secrets | 🔴 Critical | 10 | **Negative rule** — detects: `SECRET="abc123"`, `sk-xxxx`, `mongodb+srv://user:pass@`, `Bearer eyJ...` |
| R12 | PII Data Masking | 🟠 High | 5 | `mask`, `redact`, `anonymize`, `pii`, `PII`, `***` |
| R13 | Encryption at Rest | 🟡 Medium | 4 | `cryptography`, `fernet`, `aes`, `AES`, `encrypt`, `Fernet` |
| R14 | Data Retention Policy | 🟢 Low | 2 | `delete_after`, `ttl`, `expires_at`, `retention`, `purge`, `cleanup` |
| R15 | GDPR / Consent | 🟡 Medium | 3 | `gdpr`, `GDPR`, `consent`, `privacy_policy`, `right_to_erasure` |
| R16 | File Upload Validation | 🟠 High | 5 | `content_type`, `mimetype`, `file_size`, `max_size`, `UploadFile`, `multipart` |
| R17 | Output Sanitization (XSS) | 🟠 High | 5 | `bleach`, `DOMPurify`, `markupsafe` — **Bad:** `dangerouslySetInnerHTML`, `innerHTML =` |
| R18 | Secrets Scanning Config | 🟡 Medium | 3 | `gitleaks`, `git-secrets`, `trufflehog`, `detect-secrets`, `.gitleaks.toml` |

---

### 🌐 Category 3: API Quality (R19–R26)
*Weight: 14% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R19 | API Versioning | 🟠 High | 5 | `/v1/`, `/v2/`, `APIVersion`, `api-version`, `/api/v` prefix |
| R20 | OpenAPI / Swagger Docs | 🟡 Medium | 4 | `swagger`, `openapi`, `FastAPI(`, `@ApiProperty`, `@ApiOperation` |
| R21 | Proper HTTP Status Codes | 🟡 Medium | 4 | `status_code=400`, `HTTPException`, `status.HTTP_`, 401/403/404/422/500 |
| R22 | Request Pagination | 🟡 Medium | 3 | `limit`, `offset`, `skip`, `page`, `cursor`, `per_page`, `pageSize` |
| R23 | Error Response Schema | 🟡 Medium | 3 | `error_code`, `ErrorResponse`, `APIError`, `detail.*message` |
| R24 | Async / Non-blocking | 🟡 Medium | 4 | `async def`, `await`, `asyncio`, `httpx.AsyncClient` — **Bad:** `time.sleep(`, `requests.get(` |
| R25 | Request Timeout / Retry | 🟢 Low | 2 | `timeout`, `retry`, `backoff`, `httpx.*timeout` |
| R26 | API Response Caching | 🟢 Low | 2 | `redis`, `cache`, `memcached`, `@cache`, `lru_cache`, `fastapi-cache` |

---

### 🏗️ Category 4: Infrastructure & DevOps (R27–R33)
*Weight: 14% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R27 | Docker / Containerization | 🟠 High | 5 | `FROM \w+`, `EXPOSE`, `docker-compose`, `container_name`, `image:` |
| R28 | CI/CD Pipeline | 🟠 High | 5 | `.github/workflows`, `gitlab-ci`, `Jenkinsfile`, `.circleci`, `on: push` |
| R29 | Environment-based Config | 🟠 High | 5 | `os.environ`, `os.getenv`, `process.env`, `dotenv`, `BaseSettings` |
| R30 | .env.example Template | 🟡 Medium | 3 | `.env.example`, `.env.sample`, `.env.template` |
| R31 | Database Migrations | 🟡 Medium | 3 | `alembic`, `migrate`, `migration`, `flyway`, `liquibase` |
| R32 | Health Check Endpoint | 🟠 High | 4 | `health`, `ping`, `/status`, `readiness`, `liveness`, `heartbeat` |
| R33 | Reverse Proxy Config | 🟢 Low | 2 | `nginx`, `caddy`, `traefik`, `proxy_pass`, `upstream` |

---

### 🧹 Category 5: Code Quality (R34–R40)
*Weight: 10% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R34 | No eval() / exec() | 🔴 Critical | 8 | **Negative rule** — detects: `eval(`, `exec(`, `new Function(`, `execFile(` |
| R35 | Proper Exception Handling | 🟠 High | 5 | `except ValueError`, `except (`, `.catch(err` — **Bad:** `except:`, `catch()` (bare catch) |
| R36 | Dependency Pinning | 🟠 High | 5 | `==1.2.3` — **Bad:** `>=1.0`, `>1.0`, wildcard `*` |
| R37 | Type Annotations | 🟡 Medium | 3 | `-> str`, `Optional[`, `List[`, `Dict[`, TypeScript `interface \w+` |
| R38 | Dead Code Free | 🟢 Low | 2 | **Negative rule** — detects: `# def function_name`, `// function foo` (commented-out code) |
| R39 | Linting / Formatting Config | 🟢 Low | 2 | `.eslintrc`, `pyproject.toml`, `.prettierrc`, `black`, `ruff`, `eslint` |
| R40 | Pre-commit Hooks | 🟢 Low | 2 | `pre-commit`, `husky`, `lint-staged`, `.pre-commit-config.yaml` |

---

### 🤖 Category 6: AI/ML Readiness (R41–R46)
*Weight: 8% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R41 | Async Task Queue | 🟠 High | 6 | `celery`, `arq`, `dramatiq`, `BackgroundTasks`, `asyncio.create_task` |
| R42 | Feature Flag System | 🟡 Medium | 4 | `feature_flag`, `launchdarkly`, `flagsmith`, `unleash`, `ENABLE_AI` |
| R43 | Model Input/Output Logging | 🟠 High | 5 | `model_input`, `model_output`, `langsmith`, `mlflow`, `prompt.*log` |
| R44 | Vector Store / Embeddings | 🟢 Low | 3 | `pinecone`, `weaviate`, `chroma`, `qdrant`, `pgvector`, `embedding`, `faiss` |
| R45 | AI Model Fallback | 🟡 Medium | 4 | `fallback`, `default_response`, `model_fallback`, `retry.*model` |
| R46 | Prompt Injection Prevention | 🔴 Critical | 7 | `sanitize.*prompt` — **Bad:** `user_input.*prompt`, `f"...{user...}"` in prompt |

---

### ⚡ Category 7: Performance (R47–R51)
*Weight: 6% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R47 | Database Index Strategy | 🟠 High | 5 | `create_index`, `Index(`, `index=True`, `createIndex`, `ensureIndex` |
| R48 | Connection Pooling | 🟡 Medium | 4 | `pool`, `max_connections`, `minPoolSize`, `maxPoolSize`, `connection_pool` |
| R49 | Gzip / Compression | 🟢 Low | 2 | `GZipMiddleware`, `gzip`, `brotli`, `compression`, `Content-Encoding` |
| R50 | Lazy Loading / Code Splitting | 🟡 Medium | 3 | `React.lazy`, `lazy(()`, `import(`, `Suspense`, `next/dynamic` |
| R51 | CDN / Static Assets | 🟢 Low | 2 | `cdn`, `cloudfront`, `staticfiles`, `PUBLIC_URL`, `S3_BUCKET` |

---

### 📋 Category 8: Compliance (R52–R56)
*Weight: 4% of static score*

| ID | Rule | Severity | Points | What it detects |
|---|---|---|---|---|
| R52 | Structured Logging | 🟠 High | 5 | `logging.`, `loguru`, `structlog`, `getLogger`, `log.info` — **Bad:** `print(`, `console.log(` |
| R53 | Audit Trail | 🟡 Medium | 4 | `audit`, `audit_log`, `event_log`, `created_by`, `modified_by` |
| R54 | Error Alerting | 🟠 High | 5 | `sentry`, `pagerduty`, `datadog`, `rollbar`, `capture_exception` |
| R55 | Request ID Tracking | 🟡 Medium | 3 | `request_id`, `X-Request-ID`, `trace_id`, `correlation_id` |
| R56 | Graceful Shutdown | 🟡 Medium | 3 | `on_shutdown`, `SIGTERM`, `graceful`, `lifespan` |

---

### ⛔ Hard Blockers (cap score at 49 if ANY triggered)

| Rule | Condition | Why it's a blocker |
|---|---|---|
| R11 | Hardcoded secrets detected | Credentials in source code = instant security breach |
| R34 | eval()/exec() found | Remote code execution vulnerability |
| R01 | No authentication detected | All data is publicly accessible |
| R46 | Raw user input in AI prompts | Prompt injection = data leak / model hijacking |

---

## 4. Scoring Algorithm

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1 (Static Rules) score:                          │
│                                                         │
│  positive_pts = sum of pts for found positive rules     │
│  total_max    = sum of all rule score_pts               │
│  static_score = (positive_pts / total_max) × 100        │
│  penalty      = sum of pts for violated negative rules   │
│  static_score = max(0, static_score - penalty)          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Final Score Fusion:                                    │
│                                                         │
│  weighted = Σ (layer_score[k] × WEIGHT[k]) for k in 9  │
│  raw_score = weighted / 100                             │
│                                                         │
│  if language_diversity > 4: raw_score -= 5              │
│  if has_blockers: raw_score = min(raw_score, 49)        │
│                                                         │
│  final_score = clamp(raw_score, 0, 100)                 │
└─────────────────────────────────────────────────────────┘

Layer Weights:
  static_rules   30%  ████████████████████████████████░░░░░░░░
  import_graph   15%  ████████████████░░░░░░░░░░░░░░░░░░░░░░░░
  ast_metrics    10%  ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  dependencies   10%  ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  test_coverage  10%  ███████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  api_quality     8%  █████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  tech_debt       7%  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  env_maturity    5%  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  observability   5%  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

---

## 5. Database Structure

### `users` collection
```json
{
  "_id": "ObjectId",
  "email": "user@example.com",
  "full_name": "John Doe",
  "password_hash": "$2b$12$...",
  "is_admin": false,
  "created_at": "ISODate",
  "profile_image": null
}
```

### `assessments` collection
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "source_value": "myproject.zip",
  "source_type": "zip",
  "score": 73,
  "status": "Moderate",
  "layer_scores": { "static_rules": 82, "import_graph": 71, ... },
  "blockers": [],
  "risks": [ { "rule_id": "R36", "severity": "high", ... } ],
  "executive_summary": "...",
  "why_not_80": [ "Add unit tests..." ],
  "capabilities": { "Has JWT Auth": true, ... },
  "project_profile": { "primary_language": "Python", ... },
  "score_details": { "total_functions": 47, ... },
  "gate_checks": { "score_ok": false, "no_blockers": true, ... },
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

---

## 6. Real-Time Progress (SSE)

**Connection:** `GET /api/assess/run` returns `text/event-stream`

Events emitted during analysis:
```
data: {"type":"progress","stage":"ingest",  "progress":8,  "message":"Extracting project files ..."}
data: {"type":"progress","stage":"classify","progress":18, "message":"Loaded 342 files — classifying stack ..."}
data: {"type":"progress","stage":"rules",   "progress":22, "message":"Starting 56-rule scan on 342 files ..."}
data: {"type":"progress","stage":"rules",   "progress":28, "message":"Scanned 60/342 files — ETA 42s"}
data: {"type":"progress","stage":"rules",   "progress":34, "message":"Scanned 120/342 files — ETA 28s"}
data: {"type":"progress","stage":"rules",   "progress":40, "message":"Scanned 200/342 files — ETA 15s"}
data: {"type":"progress","stage":"rules",   "progress":42, "message":"Static analysis complete ✓"}
data: {"type":"progress","stage":"graph",   "progress":48, "message":"Import graph built"}
data: {"type":"progress","stage":"ast",     "progress":52, "message":"AST metrics computed"}
data: {"type":"progress","stage":"deps",    "progress":56, "message":"Dependency risk checked"}
data: {"type":"progress","stage":"tests",   "progress":60, "message":"Test coverage measured"}
data: {"type":"progress","stage":"api",     "progress":64, "message":"API quality assessed"}
data: {"type":"progress","stage":"debt",    "progress":68, "message":"Technical debt counted"}
data: {"type":"progress","stage":"env",     "progress":72, "message":"Env maturity evaluated"}
data: {"type":"progress","stage":"obs",     "progress":76, "message":"Observability checked"}
data: {"type":"progress","stage":"score",   "progress":88, "message":"Fusing all 9 layer scores ..."}
data: {"type":"progress","stage":"report",  "progress":94, "message":"Generating detailed report ..."}
data: {"type":"progress","stage":"done",    "progress":100,"message":"Assessment complete — report ready!"}
data: {"type":"complete","id":"abc123def456"}
```

Frontend arc reactor arc angle: `(progress / 100) × 360°`

---

## 7. Report Structure

The report has 5 tabs in the UI:

| Tab | Content |
|---|---|
| **Overview** | Score ring, radar chart, bar chart, capabilities, roadmap to 80+ |
| **9-Layer Analysis** | Expandable cards for each layer with description, verdict, data points |
| **Diagnostics** | Lowest-scoring layers with specific fix suggestions |
| **Risk Register** | All detected risks, sorted critical → high → medium, with remediation steps |
| **Project Profile** | Language, stack, code metrics, test details, dependency health |

**Export options (top-right button):**
- **HTML / PDF** — styled printable report (use Ctrl+P → Save as PDF)
- **JSON** — full raw analysis data  
- **Text** — plain text summary

---

## 8. File & Tech Reference

### Backend Files
| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app, CORS, router registration |
| `app/routers/auth.py` | Login, register, refresh token |
| `app/routers/assess.py` | File upload, SSE stream, ZIP safety check |
| `app/routers/report.py` | Get report, delete, bulk delete, HTML/JSON/text download |
| `app/routers/admin.py` | Stats, user management, assessment listing |
| `app/routers/user.py` | Profile, assessment history |
| `app/core/sandbox.py` | ZIP security check, timeout wrapper |
| `app/core/file_reader.py` | File ingestion, smart head+tail sampling |
| `app/core/classifier.py` | Language/stack detection |
| `app/core/static_analyzer.py` | 56-rule single-pass scanner |
| `app/core/import_graph.py` | Dependency graph, circular import detection |
| `app/core/ast_metrics.py` | Complexity, dead imports, comment density |
| `app/core/dependency_checker.py` | Pinning, deprecated, risky packages |
| `app/core/extra_checks.py` | Tests, API, debt, env, observability layers |
| `app/core/score_engine.py` | Weighted fusion, blocker cap, gate checks |
| `app/core/report_builder.py` | Final report JSON assembly |
| `app/core/assessment_engine.py` | Pipeline orchestrator (parallel execution) |
| `app/core/log_store.py` | Save report to /logs/ directory |
| `app/storage/assessment_repo.py` | MongoDB CRUD for assessments |
| `app/storage/user_repo.py` | MongoDB CRUD for users |

### Frontend Pages
| Page | Route | Purpose |
|---|---|---|
| SplashPage | `/splash` | 3D engine start button, cinematic transition |
| LoginPage | `/login` | JWT login with arc reactor ring |
| RegisterPage | `/register` | Account creation |
| DashboardPage | `/dashboard` | Assessment history, quick actions |
| UploadPage | `/upload` | ZIP/Git upload, arc reactor progress |
| ReportPage | `/report/:id` | Full 5-tab analysis report + export |
| AdminPage | `/admin` | Live user/assessment monitoring |
| ProfilePage | `/profile` | User profile and history |

### Tech Stack
| Layer | Technology |
|---|---|
| Backend | FastAPI, Python 3.12, Uvicorn |
| Database | MongoDB (Motor async driver) |
| Auth | JWT (python-jose), Bcrypt (passlib) |
| Frontend | React 18, Vite, Framer Motion |
| Charts | Recharts (radar, bar, pie, line) |
| HTTP | Axios, httpx |
| Concurrency | asyncio, ThreadPoolExecutor |
| Logs | /logs/ directory (JSON + TXT) |

---
