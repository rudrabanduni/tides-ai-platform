\# TIDES AI Platform



\## Current Status



\### Completed



\* GitHub repository connected

\* FastAPI backend running

\* SQLite database configured

\* Alembic migrations working

\* Swagger UI working

\* Authentication fully working

\* Admin bootstrap working

\* Login working

\* JWT authentication working

\* Protected routes working



\### Verified Credentials (Development)



Admin User:



\* Name: Rudra Banduni

\* Email: \[rudra@example.com](mailto:rudra@example.com)

\* Password: TidesAdmin@2026



\### Architecture



Backend:



\* FastAPI

\* SQLAlchemy

\* Alembic

\* SQLite (temporary)

\* Repository-Service pattern



Future AI:



\* LiteLLM gateway

\* Claude as default model

\* Provider-agnostic architecture

\* Easy switching between Claude, GPT, Gemini, etc.



\### Database



Implemented:



\* Users

\* Roles

\* Audit Logs

\* Startup Applications

\* Startup Profiles

\* Startup Profile Versions

\* Founders

\* Company Profiles

\* Documents

\* Document Sources

\* Evaluations

\* Evaluation Scores

\* Evaluation Evidence

\* Recommendation Rules

\* Reviewer Comments

\* Committee Notes

\* Score Overrides



\### Immediate Next Task



Build Startup Intake Pipeline



Goal:



Excel File

↓

Parse Applications

↓

Create StartupApplication records

↓

Create Founder records

↓

Create StartupProfile records

↓

Create StartupProfileVersion records



Endpoint:



POST /api/v1/intake/upload-applications



Expected Excel Columns:



\* Startup Name

\* Founder Name

\* Founder Email

\* Problem Statement

\* Solution

\* Target Market

\* Startup Stage



Requirements:



\* Use openpyxl

\* Add validation

\* Add audit logging

\* Add Swagger documentation

\* Return import summary



\### Future Roadmap



Phase 3:



\* Startup Profile Agent



Phase 4:



\* Founder Assessment Agent

\* Company Assessment Agent

\* Risk Assessment Agent



Phase 5:



\* AI Evaluation Engine



Phase 6:



\* Report Generation



\### Important Notes



\* Authentication is complete and verified.

\* Do not spend time modifying auth.

\* Do not implement AI yet.

\* Build Excel Intake Pipeline first.

\* Platform must support hundreds of startup applications at once.

\* Startup Profile is the canonical source of truth.

\* All future AI outputs must be evidence-backed and auditable.



