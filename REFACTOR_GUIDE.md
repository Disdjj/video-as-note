# Refactor Guide  
video-as-note ‑ 2025-07

---

## 1. Overview – What Changed
| Area | Before | After |
|------|--------|-------|
| AI Layer | LiteLLM + LangChain | **pydantic-ai** (async, typed, native streaming) |
| Streaming | none (polling only) | **Server-Sent Events (SSE)** endpoints, progressive front-end rendering |
| Front-end | Plain HTML + Tailwind | **Vue 3 + Element Plus** SPA (dark-mode, responsive) |
| API | `/api/v1/process`, `/status` | Same plus **`/stream/*`** family and async handlers |
| Dependencies | litellm, langchain | **Removed**, new: pydantic-ai, sse-starlette |
| File structure | mono | added `app/services/ai_service.py`, `app/api/streaming_routes.py`, `static/index_vue.html` |

---

## 2. Key Improvements & New Features
* Real-time document generation – chunks arrive as they are produced.
* Modern UI – theme toggle, progress bar, markdown + mermaid rendering, copy / download buttons.
* Dark/light theme, mobile first, SSR fallback.
* Async AI calls, lower latency, better error surfacing.
* Unified logging & Request-ID middleware preserved.
* Model validation now supports live SSE feedback.

---

## 3. Migrating From the Old System
1. **Install new deps**  
   ```bash
   pip install -r requirements.txt   # or poetry install
   ```
2. Remove any custom code importing `LLMService`; replace with:
   ```python
   from app.services.ai_service import AIService
   ai = AIService()
   ```
3. Update env vars used by LiteLLM (OPENAI_API_KEY etc.) – they are still read by pydantic-ai; no naming changes required.
4. Replace old endpoints in your client:
   * `/api/v1/process` → unchanged (now async)
   * NEW: for streaming use `/api/v1/stream/process` + `/api/v1/stream/<video_id>`
5. Frontend: open `/` (now auto-selects new Vue UI) or specifically `/vue`.

---

## 4. Using the New Streaming Functionality
### a. Quick Start (frontend)
The Vue UI automatically upgrades to streaming when the browser supports `EventSource`.

### b. cURL example
```bash
# 1. Kick off processing
curl -X POST http://localhost:8000/api/v1/stream/process \
     -H "Content-Type: application/json" \
     -d '{"video_id":"dQw4w9WgXcQ","model_name":"gpt-4o","language":"简体中文"}'

# 2. Follow events
curl http://localhost:8000/api/v1/stream/dQw4w9WgXcQ --no-buffer
```
Events are JSON with `type`: `progress`, `content`, `completed`, `error`.

### c. Direct stream without video download
POST `/api/v1/stream/direct-generate` with raw transcript_text for immediate streaming.

---

## 5. Configuring pydantic-ai
pydantic-ai reads the same environment vars as OpenAI SDK:
```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
```
Optional global defaults:
```python
from pydantic_ai import configure_global
configure_global(timeout=60, max_retries=3)
```
No explicit client initialization needed; `AIService` wraps it.

---

## 6. Front-End Improvements & Features
* Vue 3 + Element Plus component library.
* Theme switch (dark/bright) saved via OS preference.
* Live markdown rendering with **highlight.js** and **mermaid** diagrams.
* Form validation, model examples accordion, toast notifications.
* SSE fallback to polling when unsupported.
* Separate routes:
  * `/` auto
  * `/vue` new
  * `/legacy` old Tailwind page

---

## 7. API Changes & New Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/stream/process` | Start async job + enable SSE |
| GET  | `/api/v1/stream/{video_id}` | SSE event stream |
| POST | `/api/v1/stream/direct-generate` | Stream using provided transcript |
| GET  | `/api/v1/stream/status/{video_id}` | Check streaming status (JSON) |
| DELETE | `/api/v1/stream/status/{video_id}` | Clear status |
| POST | `/api/v1/stream/validate-model` | SSE validation of a model |
| Other existing | remain but now **async** and use `AIService` |

Response payloads now follow the new `ProcessingStatus` schema.

---

## 8. Configuration & Setup Steps
1. Clone repo, `cd video-as-note`.
2. Python ≥ 3.12, install deps.
3. Export API keys for chosen LLM.
4. `uvicorn app.main:app --reload` (or `docker-compose up`).
5. Visit `http://localhost:8000/`.

Docker users: new `Dockerfile` unchanged; only dependency layer updated.

---

## 9. Testing & Debugging Tips
* Unit tests updated for `AIService`; run `pytest -vv`.
* SSE debugging: use browser dev-tools “EventStream” or CLI `curl --no-buffer`.
* Enable verbose logging: `LOG_LEVEL=DEBUG uvicorn app.main:app`.
* Mock pydantic-ai by setting `PydanticAI_TEST_MODE=1` (returns canned responses).
* Check `/health` endpoint.

---

## 10. Migration Timeline & Compatibility
| Date | Milestone | Notes |
|------|-----------|-------|
| 2025-07-10 | Code land     | Main branch includes both old & new code. |
| 2025-07-17 | Deprecation   | `LLMService` officially deprecated; security patches only. |
| 2025-08-01 | Removal       | `LLMService` and litellm deps removed from `pyproject`. |
| 2025-08-15 | Legacy UI off | `/legacy` route removed; Vue is default. |
Compatibility: new back-end keeps request/response shapes identical for `/process`, `/status`, so existing integrations keep working until August 1st.

---

### Need Help?
Open an issue or ping @djj-joe on GitHub. Happy streaming!
