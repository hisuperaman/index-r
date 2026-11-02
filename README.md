# IndexR

A vectorless research intelligence platform: it discovers research papers for your question, answers with section- and page-level citations, and tracks what changes in your topic. See the [project overview](docs/PROJECT_OVERVIEW.md) for how it works.

## Project Setup

### Backend Setup

1. Clone the repository and navigate to the project root:

```bash
git clone https://github.com/hisuperaman/index-r.git
cd index-r
```

2. Install dependencies and create a virtual environment using Pipenv:

```bash
pipenv install
pipenv shell
```

3. Create a .env file in the root directory with the following template:

```bash
ALLOWED_HOSTS=*
SECRET_KEY=YOUR_SECRET_KEY_HERE
RDS_HOSTNAME=localhost
RDS_DB_NAME=indexr
RDS_USERNAME=
RDS_PASSWORD=
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=YOUR_EMAIL_ADDRESS
EMAIL_HOST_PASSWORD=YOUR_EMAIL_PASSWORD
REDIS_HOST=localhost
REDIS_PORT=6379
# '<provider>:<model>', plus that provider's key: ANTHROPIC_API_KEY, OPENAI_API_KEY or GOOGLE_API_KEY
LLM=anthropic:claude-sonnet-5-5
ANTHROPIC_API_KEY=
COHERE_API_KEY=
# Optional, but without it Semantic Scholar rate-limits searches heavily
SEMANTIC_SCHOLAR_API_KEY=
# Where MCP clients reach the server, and where `manage.py mcp --http` listens
MCP_PUBLIC_URL=http://localhost:8100/mcp
MCP_HOST=127.0.0.1
MCP_PORT=8100
# Hour (UTC) of the daily live-tracking check
TRACKING_CHECK_HOUR=6
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Start the backend server:

```bash
python manage.py runserver
```

7. Start Redis, then the Celery worker, which ingests papers in the background (it uses Redis database 0 as its
   broker):

```bash
celery -A server worker --queues=default --pool=threads --concurrency=4 --loglevel=INFO
```

   Also start Celery beat, which runs the daily live-tracking check (at `TRACKING_CHECK_HOUR` UTC, default 6) and
   requeues papers whose ingestion got stuck:

```bash
celery -A server beat --loglevel=INFO
```

   To run the tracking check right away instead of waiting for the schedule:

```bash
python manage.py check_tracking
```

8. Optionally, run the MCP server so AI assistants (Claude Desktop, Claude Code, IDEs) can use IndexR. Create an access
   token in Settings → Integrations, which also shows the setup for each client. Remote clients connect over HTTP:

```bash
python manage.py mcp --http
```

   Or run it locally over stdio, acting as the token's user:

```bash
INDEXR_ACCESS_TOKEN=ixr_... python manage.py mcp
```

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd webapp
```

2. Install dependencies:

```bash
yarn install
```

3. Create a .env file in the /webapp directory with the following template:

```bash
VITE_APP_GOOGLE_CLIENT_ID=
```

4. Start the frontend server:

```bash
yarn run dev
```

### Adding UI Components

This project uses **shadcn/ui**. Add UI components using the shadcn CLI.

```bash
yarn shadcn add <component>
```

For example, to add the `button` component:

```bash
yarn shadcn add button
```
