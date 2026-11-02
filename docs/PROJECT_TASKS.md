# IndexR: Project Tasks

All project tasks grouped by feature, from setup to the final report, followed by the week-wise execution plan for the
August–December 2026 session. Ticket IDs are used in the execution plan and can be assigned to team members in the
logbook.

---

## Part A: Tasks by feature

### 1. Planning and research

- PLN-01 Define the problem statement, motivation, objectives, deliverables and project scope
- PLN-02 Literature survey on lexical retrieval (BM25), dense retrieval and vector search, and neural reranking
- PLN-03 Literature survey on retrieval-augmented generation, LLM query expansion, hallucination and citation quality
- PLN-04 Study scholarly data sources (arXiv, OpenAlex, Semantic Scholar) and the Model Context Protocol; write the research gap analysis
- PLN-05 Feasibility study (technical, economic, operational, schedule) and selection of tools, platforms and external APIs

### 2. Project setup and infrastructure

- SET-01 Set up the Git repository, branch and pull-request workflow, and the Django project with Pipenv and environment-based settings
- SET-02 Configure PostgreSQL and Django REST Framework defaults (authentication, cursor pagination, ordering filter) with shared base models and field-name enums
- SET-03 Set up Redis and the Celery worker with the default task queue
- SET-04 Set up the React + Vite + TypeScript web app with Tailwind CSS, shadcn/ui theming, the API client and TanStack Query
- SET-05 Write the README with backend and frontend setup instructions

### 3. Authentication and accounts

- AUTH-01 Implement the email-based user model with sign-up, email verification, and JWT login, refresh-token rotation, blacklisting and logout
- AUTH-02 Add Google sign-in, connecting and disconnecting a Google account, and guards against losing the last login method or connecting another user's Google account
- AUTH-03 Add profile updates, password change, and setting a first password for Google-only users
- AUTH-04 Build shared permissions (login required, owner checks) and helpers that scope every query to the current user or workspace

### 4. Data models

- MOD-01 Design paper, author, chunk and citation models with ingestion timestamps, derived ingestion status and database constraints
- MOD-02 Design workspace, workspace paper, message and message citation models with database constraints

### 5. Paper fetchers

- FET-01 Build the base fetcher (HTTP client, timeouts, rate-limit retry, date parsing) and the arXiv fetcher
- FET-02 Build the OpenAlex and Semantic Scholar fetchers (abstract rebuilding, open-access PDF links, optional API key)
- FET-03 Build the orchestrator that searches all sources in parallel, de-duplicates by DOI and title, and tolerates a failing source

### 6. Paper storage and ingestion

- ING-01 Store fetched papers and authors without duplicates, filling blank fields and keeping the higher citation count on repeats
- ING-02 Download PDFs safely (size limit, PDF signature check) and convert them to Markdown pages with pymupdf4llm
- ING-03 Split papers into section-aware chunks of at most 1,000 characters with page ranges, dropping references and acknowledgements
- ING-04 Run ingestion as a Celery task queued after a paper is stored, and requeue papers stuck in pending ingestion every hour

### 7. Search and ranking

- SRCH-01 Add a weighted full-text search vector (heading A, text B) with a database trigger and GIN index, and a chunk search query
- SRCH-02 Boost search scores by citation count and recency, add year, venue and citation filters, and expose the chunk search API

### 8. LLM and reranking

- LLM-01 Build a provider-independent LLM service (pydantic-ai) with structured and streamed output and retries on rate limits and server errors
- LLM-02 Implement LLM query expansion into 3–5 keyword queries
- LLM-03 Integrate the Cohere Rerank v3.5 cross-encoder for passages and abstracts

### 9. Discovery, retrieval and answers

- DISC-01 Build the discovery service: expanded queries to all sources, abstract relevance filter, per-question limit, storage and ingestion
- DISC-02 Build the retrieval service (multi-query search, rerank, top 5 passages) with the two-gate rule for triggering discovery
- DISC-03 Build grounded answer generation with numbered passages, [n]-to-chunk citation mapping and an insufficient-context reply

### 10. Ask pipeline and workspaces API

- ASK-01 Build the ask pipeline (expand, search, discover, wait for ingestion, answer) that saves answers with citations and adds cited papers to the workspace
- ASK-02 Expose ask as JSON and streamed (server-sent events) endpoints with status updates and friendly error handling
- ASK-03 Build the workspaces API (CRUD, search, activity annotations) and workspace papers, messages and mentioned papers APIs
- ASK-04 Add the "answer only from these papers" mode and backfill cited papers into existing workspaces

### 11. Web app

- UI-01 Build the app shell (header, breadcrumb, user menu, logo and favicon, light/dark theme, error and not-found pages)
- UI-02 Build login, sign-up and email verification pages with Google sign-in and protected routes
- UI-03 Build the home page listing workspaces grouped by activity, with search and create, rename and delete dialogs
- UI-04 Build the workspace chat with history, composer, streamed answers with live status, markdown rendering, citation chips with passage previews and source lists
- UI-05 Build the papers panel (workspace and mentioned tabs, add-paper search, remove with confirmation, "answer only from these papers" switch, collapsible panel and mobile sheet)
- UI-06 Build the settings page (profile, security and connected accounts, appearance, logout) with mobile tabs

### 12. Private uploads and admin

- UPL-01 Add private paper uploads (owner, content hash, privacy constraints) with an upload service and multipart API
- UPL-02 Enforce paper visibility in search, retrieval, answers and workspace papers
- UPL-03 Add the upload tab to the add-paper dialog and a private badge on papers
- ADM-01 Set up the Django admin for papers, authors, workspaces and access tokens with search, filters and read-only views

### 13. MCP server

- MCP-01 Add personal access tokens (hashed storage, prefix, last used) with an API to create, list and revoke them
- MCP-02 Build the research tools service and MCP tools for paper search, workspaces and workspace papers, acting as the token's user
- MCP-03 Build the MCP ask tool with progress notifications and friendly tool errors
- MCP-04 Run the MCP server over stdio and streamable HTTP with token verification and DNS-rebinding protection
- MCP-05 Build the Settings → Integrations page with token creation, client setup instructions and revocation

### 14. Live tracking

- TRK-01 Add tracking data: topic and paper tracking timestamps, tracking updates with uniqueness constraints and the unseen update count
- TRK-02 Add date-limited search to all fetchers, OpenAlex citing-work lookup and arXiv revision dates
- TRK-03 Build the tracking service for new papers on topics, new citations and new arXiv versions
- TRK-04 Schedule the daily tracking check with Celery beat and add a command to run it on demand
- TRK-05 Build the topics, track/untrack paper and updates APIs, and the MCP tracking tools
- TRK-06 Build the tracking panel, "N updates since date" banner, paper track toggle and home page badge

### 15. Testing and validation

- QA-01 Write unit tests for models, fetchers, extraction, search, retrieval, reranking and answers
- QA-02 Write API tests for scoping, validation and visibility, with query-count tests for every paginated list
- QA-03 Write tests for the ask pipeline, streaming, MCP protocol and authentication, and live tracking
- QA-04 Run browser checks of the UI (desktop and mobile, light and dark) and live runs against the real external services
- QA-05 Measure search and answer latency on the development corpus

### 16. Code review and integration

- REV-01 Define and maintain the code review standards (review rules, regression test for every finding) and the pull-request workflow
- REV-02 Review, comment on, fix and merge pull requests for project setup, authentication and permissions
- REV-03 Review, comment on, fix and merge pull requests for data models, paper fetchers, ingestion and full-text search
- REV-04 Review, comment on, fix and merge pull requests for search boost, reranking, discovery, retrieval and grounded answers
- REV-05 Review, comment on, fix and merge pull requests for the ask pipeline, streaming and the web app
- REV-06 Review, comment on, fix and merge pull requests for private uploads, the admin and the MCP server
- REV-07 Review, comment on, fix and merge pull requests for live tracking and the final test suite

### 17. Documentation and report

- DOC-01 Write the project overview and system design diagrams (architecture, block, data flow, flowcharts, sequence, ER)
- DOC-02 Write the interim project report
- DOC-03 Prepare the presentation and maintain the logbook

---

## Part B: Week-wise execution plan

| Week | Dates (2026) | Milestone | Tickets |
|---|---|---|---|
| 1 | 10 – 15 Aug | Problem identification | PLN-01 |
| 2 | 17 – 21 Aug | Problem identification | PLN-01, SET-01 |
| 3 | 23 – 28 Aug | Literature survey | PLN-02 |
| 4 | 30 Aug – 3 Sep | Literature survey | PLN-03, PLN-04 |
| 5 | 5 – 10 Sep | Feasibility study | PLN-05, SET-02, SET-04, SET-05, REV-01 |
| 6 | 12 – 16 Sep | Feasibility study | AUTH-01, AUTH-02, AUTH-03, AUTH-04, UI-01, UI-02, REV-02 |
| 7 | 18 – 23 Sep | System design | DOC-01, MOD-01, MOD-02, FET-01, FET-02, FET-03, SET-03 |
| 8 | 25 – 29 Sep | System design | ING-01, ING-02, ING-03, ING-04, SRCH-01, LLM-01, REV-03 |
| 9 | 1 – 6 Oct | Design validation | SRCH-02, LLM-02, LLM-03, DISC-01, DISC-02, DISC-03, ASK-03, QA-01, REV-04 |
| 10 | 8 – 12 Oct | Design validation | ASK-01, ASK-02, UI-03, UI-04, UI-05, UI-06, QA-02, REV-05 |
| 11 | 14 – 19 Oct | Report drafting | ASK-04, UPL-01, UPL-02, UPL-03, ADM-01, MCP-01 – MCP-05, REV-06 |
| 12 | 21 – 25 Oct | Report drafting | TRK-01 – TRK-06, QA-03, QA-04, QA-05, DOC-02, REV-07 |
| 13 | 27 Oct – 1 Nov | Presentation and viva | DOC-02, DOC-03 |
| 14 | 3 – 7 Nov | Presentation and viva | DOC-03, internal review by the project committee |
