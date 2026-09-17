# Enterprise Data Agent -English

**Hybrid Multi-Agent Business Intelligence System**

A self-corrective LangGraph agent that unifies structured database metrics (SQL) and customer feedback (Vector/RAG) into a single natural-language interface.

[![Python](https://img.shields.io/badge/Python-3.14-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)]()
[![Deploy](https://img.shields.io/badge/Deploy-Google%20Cloud%20Run-4285F4)]()

---

## Introduction and Project Motivation

### The Problem

In enterprise companies, data is inherently split in two:

- **Quantitative / structured data** — metrics such as revenue, order count, return rate, and delivery time living in SQL tables.
- **Qualitative / unstructured data** — textual experience data such as customer reviews, complaints, and support records.

Traditional BI (Business Intelligence) tools can only access the first set, so they can only tell you **"what"** happened (e.g., *"revenue dropped 12%"*, *"the return rate increased"*). But they can never explain **"why"** that drop happened — a shipping delay, a damaged package, or a quality issue with the product. These two data worlds usually live in different systems, held by different teams, disconnected from one another.

### The Solution: Enterprise Data Agent

This project is a hybrid system that unites quantitative facts with qualitative context in a **single, intelligent decision-support interface**. When an executive asks:

> *"What are the delivery-related customer complaints in the category that generates the most revenue?"*

or

> *"Is the drop in sales related to general market trends?"*

the system doesn't settle for a single LLM call. It breaks the question into sub-steps when needed (**decompose**), pulls quantitative facts from the relational database (**SQL**), semantically scans customer reviews in the vector database (**RAG**), reaches out to the web for current market dynamics that have no counterpart in the database (**Tavily Web Search**), and turns all the gathered evidence into a coherent, evidence-based executive summary. Throughout the process, every response it produces is verified through hallucination and relevance checks.

---

## Live Links

| Link | Description |
|---|---|
| 🖥️ **[Live Web Cockpit](https://enterprise-data-agent-927895662996.europe-west3.run.app/chat/)** | Executive chat interface — ask questions in natural language and get table/chart responses |
| 📑 **[Live API (Swagger Docs)](https://enterprise-data-agent-927895662996.europe-west3.run.app/docs)** | Interactive OpenAPI documentation for testing the `/api/chat/` endpoint |

---

## Architecture and Technology Stack

| Layer | Technology | Role |
|---|---|---|
| Relational Database | PostgreSQL 16 (Neon DB) | 550k+ rows of structured e-commerce data |
| Vector Database | Qdrant Cloud | 40k+ enriched customer reviews, semantic search |
| Embedding Engine | FastEmbed – `paraphrase-multilingual-MiniLM-L12-v2` | Local, free, multilingual (TR/PT) vectorization |
| Cache & Rate Limiting | Redis (Upstash) | Query cache + SlowAPI request-limiting store |
| External Intelligence | Tavily AI | For up-to-date/external-world questions not covered by the database |
| LLM | Google Gemini 2.5 Flash-lite | SQL generation, routing, synthesis, and grading chains |
| Orchestration | LangGraph (`StateGraph` + `MemorySaver`) | Conditional routing, multi-step decomposition, self-correction |
| Backend | FastAPI + Jinja2 (SSR) | REST API + browser interface |
| Container / Deployment | Docker, Google Cloud Build, Cloud Run | Serverless, scale-to-zero live environment |

---
## Architecture and the LangGraph Loop

The system is a cyclical state machine (`src/graphs/workflow.py`) that subjects each incoming question to intent analysis, builds dependency chains (**Dependency Chaining**) across the SQL/RAG/Web channels, and passes the generated result through hallucination and answer-sufficiency filters.

![LangGraph Workflow](graph.png)

### Decision Flow and Logical Architecture

```mermaid
flowchart TD
    Start(["__start__"]) --> Router{"decided_to_router<br/>(router_chain)"}

    %% Layer 1: Routing and Expert Nodes
    Router -->|MultiStep| Decompose["decompose<br/>(Query Planner)"]
    Router -->|SQL| SQLNode["sql<br/>(sql_grader_node)"]
    Router -->|RAG| RAGNode["rag<br/>(rag_grader_node)"]
    Router -->|websearch| WebNode["websearch<br/>(Tavily AI)"]
    Router -->|out_of_scope| OutNode["out_of_scope"]

    %% Layer 2: Actual State Values Passed to Generation
    Decompose -->|"hybrid_context (sql + rag + web + reasoning)"| GenNode["generation"]
    SQLNode -->|"sql_data + sql_query"| GenNode
    RAGNode -->|"rag_data (verified reviews)"| GenNode
    WebNode -->|"web_data"| GenNode

    OutNode --> EndNode(["__end__"])

    %% Layer 3: Two-Stage Grading and Decision
    GenNode --> Grader{"grader_hallucination_and_answer"}

    Grader -->|"not_supported (retry < 2)"| GenNode
    Grader -->|"not_useful (incomplete answer)"| WebNode
    Grader -->|"useful / give_up"| EndNode

```
### Step-by-Step Workings of the Autonomous Loop

* **1. Dynamic Routing (`decided_to_router`):**
  * The user's question and recent conversation history (`messages[-4:]`) are analyzed via the `router_chain`.
  * The request is conditionally routed to `SQL` for pure table analysis, `RAG` for customer experience, `MultiStep` for complex hybrid analyses, `websearch` for external market/sector intelligence, or `out_of_scope` for anything outside scope.

* **2. Multi-Step Decomposition and Hybrid Orchestration (`decompose_node`):**
  * The `MultiStepDecompose` schema breaks complex questions down into concurrent and sequential subtasks based on their dependencies (`sql_question`, `rag_query`, `web_query`).
  * Quantitative metrics that need to be pulled from the database first are queried via SQL; the resulting data is injected as a dynamic filter into the Olist customer-review scan (Qdrant) and sector research (Tavily) through the `{{context}}` placeholder. All data produced by the node (`sql_data`, `sql_query`, `rag_data`, `web_data`, `reasoning_steps`) is delivered to the `generation` node as a single state package.

* **3. Expert Data Engines (Retrieval Layer):**
  * **`sql` (`sql_chain`):** Checks whether the question can be resolved via the schema (`is_feasible`). It runs a read-only `SELECT` query using sargable filters that preserve B-Tree index performance (`orders.order_purchase_timestamp`), deduplication (`COUNT(DISTINCT)`), and net-revenue rules with `SUM(oi.price)`, producing `sql_data` and `sql_query`.
  * **`rag` (`rag_grader_chain`):** Performs multilingual semantic search with FastEmbed. It tests the Portuguese customer feedback retrieved from Qdrant with a binary validator (`RagGrader`), filtering out only the evidence that directly overlaps with the question as `rag_data`.
  * **`websearch` (`TavilySearch`):** For macroeconomic trends, consumer complaints, and market analyses not found in the internal database, it scans only trusted/authoritative sources:
    * *Consumer & Local Ecosystem:* Şikayetvar, Ekşi Sözlük, DonanımHaber, Webrazzi, BloombergHT
    * *Global Analysis & Market Reports:* McKinsey, Gartner, Forbes, Reuters, Statista
    * The retrieved results are structured with matching source URLs and content and passed into the `web_data` state.

* **4. Synthesis and Reporting (`generation`):**
  * Regardless of which route it came from, all collected datasets (`sql_data`, `rag_data`, `web_data`, `reasoning_steps`) are blended into a single `merged_context` pool and turned into a transparent, evidence-based executive summary for the decision-maker.

* **5. Two-Stage Verification (`grader_hallucination_and_answer`):**
  * **Hallucination Grader:** Every claim in the generated answer is verified against the `merged_context` data. If unsupported or fabricated information is detected (`not_supported`), the answer is regenerated to self-correct in the `generation` node, within a `retry_count < 2` limit; if the limit is exceeded, the process terminates to avoid a lock (`give_up` → `__end__`).
  * **Answer Grader:** Tests whether the hallucination-free answer fully addresses the user's original question. If the answer is insufficient or superficial (`not_useful`), the system automatically falls back to the `websearch` node to gather information from external sources; if it is sufficient (`useful`), the final output is delivered to the user (`__end__`).

---

## Completed Features

- [x] **Data Infrastructure:** PostgreSQL + Qdrant + Redis in isolated Docker services; 550k+ relational rows, 40k+ enriched reviews
- [x] **SQL Analyst Agent:** A node that dynamically reads the schema via `information_schema` and generates/executes read-only queries
- [x] **SQL Security Shield:** Only `SELECT` is allowed — all write commands (`DROP/DELETE/UPDATE/ALTER/TRUNCATE/INSERT`) are blocked instantly
- [x] **B-Tree Indexes:** `idx_orders_customer_id`, `idx_orders_status`, `idx_orders_purchase_timestamp`
- [x] **RAG / Voice of the Customer Agent:** Multilingual semantic search and metadata filtering with FastEmbed + Qdrant
- [x] **Web Search Agent:** Tavily integration for external market/macro trend questions
- [x] **Semantic Router & Multi-Step Decompose:** A history-aware router that splits the question into the relevant routes
- [x] **Autonomous Grading:** Two-layer verification and retry loop with Retrieval Grader, Hallucination Grader, and Answer Grader
- [x] **Multi-Turn Memory:** Context-aware follow-up questions via the `MemorySaver` checkpointer + `session_thread_id` cookie
- [x] **Redis Caching:** Response cache with a 600s TTL keyed on a normalized question hash — zero LLM cost for repeated questions
- [x] **Rate Limiting:** 10 requests per minute per IP with SlowAPI, Redis-backed counter, clean `429` responses
- [x] **Web Interface & BI Visualization:** FastAPI + Jinja2 SSR interface, dynamic tables, and interactive Chart.js charts
- [x] **Full Dockerization:** FastAPI + PostgreSQL + Qdrant + Redis via `docker-compose` with a dedicated bridge network
- [x] **Cloud Migration:** Integration with Neon DB (`sslmode=require`), Qdrant Cloud, and Upstash Redis (`rediss://`)
- [x] **Google Cloud Run Deployment:** Cross-platform build (Cloud Build), `$PORT`-compatible Dockerfile, `europe-west3` region, automatic SSL + scale-to-zero

---

## Screenshots

| Image | Description |
|---|---|
| ![Chat Dashboard](docs/screenshots/chat_dashboard.png) | **Executive Chat & Q&A Interface** — natural-language question entry and live response streaming |
| ![SQL Table Chart](docs/screenshots/sql_table_chart.png) | **SQL Metrics, Markdown Table, and Chart.js** — dynamic table and interactive chart presentation of numeric results |
| ![SQL Query Drawer](docs/screenshots/sql_query_drawer.png) | **Transparent SQL Auditing & Executed Query** — display of the read-only SQL command generated behind the scenes |

---

## Project Structure

```
enterprise-data-agent/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI application (/api/chat/, /chat/)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   └── templates/chat.html  # Jinja2 SSR interface
│   ├── graphs/
│   │   ├── workflow.py          # StateGraph definition (nodes + edges)
│   │   ├── state.py             # GraphState schema
│   │   ├── nodes/                # sql_node, rag_node, decompose, web_search, out_of_scope, generation
│   │   └── chains/               # router, grader, hallucination, answer, generation chains
│   ├── tools/
│   │   ├── db_tools.py           # SQL guardrails + Neon DB connection
│   │   ├── qrant_tools.py        # Qdrant search tools
│   │   └── cache.py              # Redis caching
│   └── ingestion/
│       ├── db_setup.py           # PostgreSQL schema + data loading
│       └── qdrant_setup.py       # Qdrant collection + embedding loading
├── benchmarks/                   # SQL accuracy benchmarks, golden dataset
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── graph.png                     # LangGraph visualization
```

---

## Setup

### Requirements
- Python 3.14+
- Docker & Docker Compose
- Google Gemini API key, Tavily API key

### 1) Clone the repository
```bash
git clone https://github.com/Kambercansahin/Enterprise-Data-Agent.git
cd enterprise-data-agent
```

### 2) Define environment variables

Create `.env` (for database/redis/qdrant) and `src/graphs/.env` (for LLM/tool keys) files at the project root:

```env
# .env — PostgreSQL / Neon DB
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=enterprise
POSTGRES_HOST=...
POSTGRES_PORT=5432
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require   # Neon serverless pooling supported

# .env — Qdrant Cloud
QDRANT_URL=...
QDRANT_API_KEY=...
COLLECTION_NAME=olist_reviews

# .env — Upstash Redis
REDIS_URL=rediss://default:password@host:port   # TLS (rediss://) required
```

```env
# src/graphs/.env — LLM & Tools
GOOGLE_API_KEY=...          # Gemini 2.5 Flash
TAVILY_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=enterprise-data-agent
LANGSMITH_TRACING=true
```

> Note: The project runs on Google Gemini; an OpenAI key is not required.

### 3) Bring it up with Docker Compose
```bash
docker-compose up --build
```
This command starts the `postgres`, `redis`, `qdrant`, and `fast_api` services on a dedicated bridge network (`agent_network`).

### 4) Load the data (initial setup)
```bash
python -m src.ingestion.db_setup
python -m src.ingestion.qdrant_setup
```

### 5) Access the interface
- Web interface: `http://localhost:8080/chat/`
- REST API: `http://localhost:8080/api/chat/`

---

## API Usage

```bash
curl -X POST http://localhost:8080/api/chat/ \
  -H "Content-Type: application/json" \
  -H "X-Thread-ID: demo-thread-1" \
  -d '{"question": "Which product category generates the most revenue?"}'
```

Example response:
```json
{
  "answer": "The highest-revenue category is 'beleza_saude' ...",
  "sql_query": "SELECT ... FROM order_items ...",
  "reasoning_steps": "1) sql_retriever executed 2) generation ...",
  "status": "success"
}
```

You can test the same endpoint directly in the live environment:
```bash
curl -X POST https://enterprise-data-agent-927895662996.europe-west3.run.app/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "Which category has the highest return rate?"}'
```

---

## Deployment to Google Cloud Run

The project has been migrated to a fully serverless architecture with no dependency on any local server: the database runs on **Neon DB**, the vector store on **Qdrant Cloud**, and the cache on **Upstash Redis (`rediss://`)**.

**1) Build the image on Cloud Build for Apple Silicon / ARM64 compatibility:**
```bash
gcloud builds submit --tag europe-west3-docker.pkg.dev/enterprise-data-agent/agent-repo/fastapi-agent:v2
```

**2) Deploy:**
```bash
gcloud run deploy enterprise-data-agent \
  --image europe-west3-docker.pkg.dev/enterprise-data-agent/agent-repo/fastapi-agent:v2 \
  --region europe-west3 \
  --memory 2Gi \
  --env-vars-file env.yaml \
  --allow-unauthenticated
```
---

## Future Roadmap

- [ ] **Multi-Tenant Support:** Allow different businesses to operate with isolated PostgreSQL schemas and Qdrant collections
- [ ] **Advanced RBAC:** Restrict access to financial data based on user and department roles
- [ ] **Proactive Anomaly Detection:** Automated background analyst agents that detect unexpected drops in the database
- [ ] Enterprise access control with authentication (JWT / API Key)

---
## 📄 License

This project was developed for personal research, demonstration, and portfolio purposes.

---
# Enterprise Data Agent -Türkçe


**Multi-Agent İş Zekâsı Sistemi**

Yapısal veritabanı metriklerini (SQL) ve müşteri geri bildirimlerini (Vektör/RAG) tek bir doğal dil arayüzünde birleştiren, kendi kendini denetleyen (self-corrective) bir LangGraph ajanı.

[![Python](https://img.shields.io/badge/Python-3.14-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-1.2-1C3C3C)]()
[![Deploy](https://img.shields.io/badge/Deploy-Google%20Cloud%20Run-4285F4)]()

---

## Giriş ve Projenin Çıkış Amacı

### Problem

Kurumsal şirketlerde veri, doğası gereği ikiye bölünmüş durumdadır:

- **Sayısal / yapısal veri** — SQL tablolarında yaşayan ciro, sipariş adedi, iade oranı, teslimat süresi gibi metrikler.
- **Niteliksel / yapısal olmayan veri** — Müşteri yorumları, şikayetler, destek kayıtları gibi metinsel deneyim verisi.

Geleneksel BI (İş Zekâsı) araçları yalnızca birinci kümeye erişebilir; dolayısıyla yalnızca **"ne olduğunu"** söyleyebilirler (örn. *"ciro %12 düştü"*, *"iade oranı arttı"*). Ancak bu düşüşün **"neden"** yaşandığını — kargonun gecikmesi, paketin hasarlı gelmesi, üründeki bir kalite sorunu — asla açıklayamazlar. Bu iki veri dünyası genellikle farklı sistemlerde, farklı ekiplerin elinde, birbirinden kopuk şekilde yaşar.

### Çözüm: Enterprise Data Agent

Bu proje, sayısal doğrular ile niteliksel bağlamı **tek bir akıllı karar destek arayüzünde** birleştiren hibrit bir sistemdir. Bir yönetici:

> *"En çok ciro getiren kategoride teslimat kaynaklı müşteri şikayetleri nelerdir?"*

veya

> *"Satış düşüşü genel pazar trendleriyle mi ilgili?"*

diye sorduğunda, sistem tek bir LLM çağrısıyla yetinmez. Soruyu gerektiğinde alt adımlara böler (**decompose**), ilişkisel veritabanından sayısal doğruları çeker (**SQL**), vektör veritabanında müşteri yorumlarını anlamsal olarak tarar (**RAG**), veritabanında karşılığı olmayan güncel piyasa dinamikleri için internete çıkar (**Tavily Web Search**) ve topladığı tüm kanıtları tutarlı, kanıta dayalı bir yönetici özetine dönüştürür. Süreç boyunca ürettiği her yanıt, halüsinasyon ve alaka denetiminden geçirilerek doğrulanır.

---

##  Canlı Bağlantılar

| Bağlantı | Açıklama |
|---|---|
| 🖥️ **[Canlı Web Kokpiti](https://enterprise-data-agent-927895662996.europe-west3.run.app/chat/)** | Yönetici sohbet arayüzü — doğal dilde soru sorup tablo/grafik yanıtı alın |
| 📑 **[Canlı API (Swagger Docs)](https://enterprise-data-agent-927895662996.europe-west3.run.app/docs)** | `/api/chat/` uç noktasını interaktif test edebileceğiniz OpenAPI dokümantasyonu |

---

##  Mimari ve Teknoloji Yığını

| Katman | Teknoloji | Rol |
|---|---|---|
| İlişkisel Veritabanı | PostgreSQL 16 (Neon DB) | 550k+ satırlık yapısal e-ticaret verisi |
| Vektör Veritabanı | Qdrant Cloud | 40k+ zenginleştirilmiş müşteri yorumu, anlamsal arama |
| Embedding Motoru | FastEmbed – `paraphrase-multilingual-MiniLM-L12-v2` | Yerel, ücretsiz, çok dilli (TR/PT) vektörleştirme |
| Önbellek & Rate Limit | Redis (Upstash) | Sorgu önbelleği + SlowAPI istek sınırlama deposu |
| Dış İstihbarat | Tavily AI | Veritabanında olmayan güncel/dış dünya soruları |
| LLM | Google Gemini 2.5 Flash-lite | SQL üretimi, yönlendirme, sentez, denetim zincirleri |
| Orkestrasyon | LangGraph (`StateGraph` + `MemorySaver`) | Koşullu yönlendirme, çok adımlı ayrıştırma, self-correction |
| Backend | FastAPI + Jinja2 (SSR) | REST API + tarayıcı arayüzü |
| Konteyner / Dağıtım | Docker, Google Cloud Build, Cloud Run | Sunucusuz, scale-to-zero canlı ortam |

---
## Mimari ve LangGraph Döngüsü

Sistem; gelen soruyu niyet analizine tabi tutan, SQL/RAG/Web kanalları arasında bağımlılık zincirleri (**Dependency Chaining**) kuran ve üretilen sonucu halüsinasyon ile cevap yeterliliği süzgecinden geçiren döngüsel bir durum makinesidir (`src/graphs/workflow.py`).

![LangGraph Workflow](graph.png)

### Karar Akışı ve Mantıksal Mimari

```mermaid
flowchart TD
    Start(["__start__"]) --> Router{"decided_to_router<br/>(router_chain)"}

    %% 1. Katman: Yönlendirme ve Uzman Düğümler
    Router -->|MultiStep| Decompose["decompose<br/>(Query Planner)"]
    Router -->|SQL| SQLNode["sql<br/>(sql_grader_node)"]
    Router -->|RAG| RAGNode["rag<br/>(rag_grader_node)"]
    Router -->|websearch| WebNode["websearch<br/>(Tavily AI)"]
    Router -->|out_of_scope| OutNode["out_of_scope"]

    %% 2. Katman: Generation'a Aktarılan Gerçek State Değerleri
    Decompose -->|"hybrid_context (sql + rag + web + reasoning)"| GenNode["generation"]
    SQLNode -->|"sql_data + sql_query"| GenNode
    RAGNode -->|"rag_data (doğrulanmış yorumlar)"| GenNode
    WebNode -->|"web_data"| GenNode

    OutNode --> EndNode(["__end__"])

    %% 3. Katman: İki Kademeli Denetim ve Karar
    GenNode --> Grader{"grader_hallucination_and_answer"}

    Grader -->|"not_supported (retry < 2)"| GenNode
    Grader -->|"not_useful (eksik yanıt)"| WebNode
    Grader -->|"useful / give_up"| EndNode

```
### Otonom Döngünün Adım Adım İşleyişi

* **1. Dinamik Yönlendirme (`decided_to_router`):**
  * Kullanıcı sorusu ve son konuşma geçmişi (`messages[-4:]`) `router_chain` üzerinden analiz edilir.
  * İstek; salt tablo analizi için `SQL`, müşteri deneyimi için `RAG`, çok adımlı hibrit analizler için `MultiStep`, dış pazar/sektör istihbaratı için `websearch` veya kapsam dışı durumlar için `out_of_scope` rotasına koşullu olarak aktarılır.

* **2. Çok Adımlı Ayrıştırma ve Hibrit Orkestrasyon (`decompose_node`):**
  * `MultiStepDecompose` şeması, karmaşık soruları bağımlılıklarına göre (`sql_question`, `rag_query`, `web_query`) eşzamanlı ve ardışıl alt görevlere ayırır.
  * Veritabanından önce çekilmesi gereken sayısal metrikler SQL ile sorgulanır; elde edilen sonuç `{{context}}` yer tutucusu üzerinden Olist müşteri yorumu taramasına (Qdrant) ve sektör araştırmasına (Tavily) dinamik filtre olarak enjekte edilir. Düğümün ürettiği tüm veriler (`sql_data`, `sql_query`, `rag_data`, `web_data`, `reasoning_steps`) tek bir durum paketi halinde `generation` düğümüne teslim edilir.

* **3. Uzman Veri Motorları (Retrieval Layer):**
  * **`sql` (`sql_chain`):** Soru şema üzerinden çözülebilir mi (`is_feasible`) denetler. B-Tree indeks performansını koruyan sargable filtreler (`orders.order_purchase_timestamp`), tekilleştirme (`COUNT(DISTINCT)`) ve `SUM(oi.price)` net ciro kurallarıyla salt-okunur `SELECT` sorgusu çalıştırarak `sql_data` ve `sql_query` üretir.
  * **`rag` (`rag_grader_chain`):** FastEmbed ile çok dilli anlamsal tarama yapar. Qdrant'tan getirilen Portekizce müşteri geri bildirimlerini ikili doğrulayıcı (`RagGrader`) ile test ederek yalnızca soruyla doğrudan örtüşen kanıtları `rag_data` olarak filtreler.
  * **`websearch` (`TavilySearch`):** Şirket içi veritabanında bulunmayan makro ekonomik trendler, tüketici şikayetleri ve pazar analizleri için sadece güvenilir/yetkili kaynakları tarar:
    * *Tüketici ve Yerel Ekosistem:* Şikayetvar, Ekşi Sözlük, DonanımHaber, Webrazzi, BloombergHT
    * *Global Analiz ve Pazar Raporları:* McKinsey, Gartner, Forbes, Reuters, Statista
    * Çekilen sonuçlar kaynak URL ve içerik eşleşmesiyle yapılandırılarak `web_data` durumuna aktarılır.

* **4. Sentez ve Raporlama (`generation`):**
  * Hangi rotadan gelirse gelsin elde edilen tüm veri kümeleri (`sql_data`, `rag_data`, `web_data`, `reasoning_steps`) tek bir `merged_context` havuzunda harmanlanarak karar vericiye yönelik şeffaf ve kanıta dayalı bir yönetici özetine dönüştürülür.

* **5. Çift Kademeli Doğrulama (`grader_hallucination_and_answer`):**
  * **Hallucination Grader:** Üretilen cevabın her bir iddiası `merged_context` verisiyle doğrulanır. Desteklenmeyen veya uydurulan bilgi saptanırsa (`not_supported`), `retry_count < 2` limiti dahilinde cevap `generation` düğümünde kendi kendini düzeltecek şekilde baştan üretilir; limit aşılırsa kilitlenmeyi önlemek için süreç sonlandırılır (`give_up` $\rightarrow$ `__end__`).
  * **Answer Grader:** Halüsinasyonsuz yanıtın kullanıcının asıl sorusunu eksiksiz karşılayıp karşılamadığı test edilir. Yanıt yetersiz veya yüzeysel kalmışsa (`not_useful`), sistem otomatik olarak dış kaynaklardan bilgi toplamak üzere `websearch` düğümüne fallback yapar; yeterliyse (`useful`) nihai çıktı kullanıcıya sunulur (`__end__`).

---

## Tamamlanan Özellikler

- [x] **Veri Altyapısı:** PostgreSQL + Qdrant + Redis, izole Docker servisleri; 550k+ ilişkisel satır, 40k+ zenginleştirilmiş yorum
- [x] **SQL Analist Ajanı:** Şemayı `information_schema` üzerinden dinamik okuyan, salt-okunur sorgu üreten ve çalıştıran düğüm
- [x] **SQL Güvenlik Kalkanı:** yalnızca `SELECT`, tüm yazma komutları (`DROP/DELETE/UPDATE/ALTER/TRUNCATE/INSERT`) anında engelleniyor
- [x] **B-Tree İndeksleri:** `idx_orders_customer_id`, `idx_orders_status`, `idx_orders_purchase_timestamp`
- [x] **RAG / Müşteri Sesi Ajanı:** FastEmbed + Qdrant ile çok dilli anlamsal arama ve metadata filtreleme
- [x] **Web Arama Ajanı:** Tavily entegrasyonu ile dış pazar/makro trend soruları
- [x] **Semantic Router & Multi-Step Decompose:** Soruyu ilgili rotalara ayıran, geçmişe duyarlı (context-aware) yönlendirici
- [x] **Otonom Denetim (Grading):** Retrieval Grader, Hallucination Grader ve Answer Grader ile çift katmanlı doğrulama + yeniden deneme döngüsü
- [x] **Çok Turlu Bellek (Multi-Turn Memory):** `MemorySaver` checkpointer + `session_thread_id` cookie ile bağlama duyarlı takip soruları
- [x] **Redis Önbellekleme:** Normalize edilmiş soru hash'i ile 600sn TTL'li yanıt önbelleği — tekrarlanan sorularda LLM maliyeti sıfır
- [x] **Rate Limiting:** SlowAPI ile IP başına dakikada 10 istek, Redis destekli sayaç, temiz `429` yanıtı
- [x] **Web Arayüzü & BI Görselleştirme:** FastAPI + Jinja2 SSR arayüz, dinamik tablo ve interaktif Chart.js grafikleri
- [x] **Tam Dockerizasyon:** FastAPI + PostgreSQL + Qdrant + Redis, özel bridge network ile `docker-compose`
- [x] **Bulut Taşıması:** Neon DB (`sslmode=require`), Qdrant Cloud, Upstash Redis (`rediss://`) entegrasyonu
- [x] **Google Cloud Run Dağıtımı:** Cross-platform derleme (Cloud Build), `$PORT` uyumlu Dockerfile, `europe-west3` bölgesi, otomatik SSL + scale-to-zero

---

## Ekran Görüntüleri

| Görsel | Açıklama |
|---|---|
| ![Chat Dashboard](docs/screenshots/chat_dashboard.png) | **Yönetici Sohbet & Soru-Cevap Arayüzü** — Doğal dilde soru girişi ve canlı yanıt akışı |
| ![SQL Table Chart](docs/screenshots/sql_table_chart.png) | **SQL Metrikleri, Markdown Tablo ve Chart.js** — Sayısal sonuçların dinamik tablo ve interaktif grafik sunumu |
| ![SQL Query Drawer](docs/screenshots/sql_query_drawer.png) | **Şeffaf SQL Denetimi & Çalıştırılan Sorgu** — Arka planda üretilen salt-okunur SQL komutunun gösterimi |

---

##  Proje Yapısı

```
enterprise-data-agent/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI uygulaması (/api/chat/, /chat/)
│   │   ├── schemas.py           # Pydantic istek/yanıt şemaları
│   │   └── templates/chat.html  # Jinja2 SSR arayüzü
│   ├── graphs/
│   │   ├── workflow.py          # StateGraph tanımı (düğümler + kenarlar)
│   │   ├── state.py             # GraphState şeması
│   │   ├── nodes/                # sql_node, rag_node, decompose, web_search, out_of_scope, generation
│   │   └── chains/               # router, grader, hallucination, answer, generation zincirleri
│   ├── tools/
│   │   ├── db_tools.py           # SQL guardrails + Neon DB bağlantısı
│   │   ├── qrant_tools.py        # Qdrant arama araçları
│   │   └── cache.py              # Redis önbellekleme
│   └── ingestion/
│       ├── db_setup.py           # PostgreSQL şema + veri yükleme
│       └── qdrant_setup.py       # Qdrant koleksiyon + embedding yükleme
├── benchmarks/                   # SQL doğruluk benchmark'ları, golden dataset
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── graph.png                     # LangGraph görselleştirmesi
```

---

##  Kurulum

### Gereksinimler
- Python 3.14+
- Docker & Docker Compose
- Google Gemini API anahtarı, Tavily API anahtarı

### 1) Depoyu klonla
```bash
git clone https://github.com/Kambercansahin/Enterprise-Data-Agent.git
cd enterprise-data-agent
```

### 2) Ortam değişkenlerini tanımla

Proje kökünde `.env` (veritabanı/redis/qdrant için) ve `src/graphs/.env` (LLM/araç anahtarları için) dosyalarını oluştur:

```env
# .env — PostgreSQL / Neon DB
POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=enterprise
POSTGRES_HOST=...
POSTGRES_PORT=5432
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require   # Neon serverless pooling destekli

# .env — Qdrant Cloud
QDRANT_URL=...
QDRANT_API_KEY=...
COLLECTION_NAME=olist_reviews

# .env — Upstash Redis
REDIS_URL=rediss://default:password@host:port   # TLS (rediss://) zorunlu
```

```env
# src/graphs/.env — LLM & Araçlar
GOOGLE_API_KEY=...          # Gemini 2.5 Flash
TAVILY_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=enterprise-data-agent
LANGSMITH_TRACING=true
```

> Not: Proje Google Gemini üzerinde çalışır; OpenAI anahtarına ihtiyaç yoktur.

### 3) Docker Compose ile ayağa kaldır
```bash
docker-compose up --build
```
Bu komut `postgres`, `redis`, `qdrant` ve `fast_api` servislerini özel bir bridge network (`agent_network`) üzerinde başlatır.

### 4) Veriyi yükle (ilk kurulumda)
```bash
python -m src.ingestion.db_setup
python -m src.ingestion.qdrant_setup
```

### 5) Arayüze eriş
- Web arayüzü: `http://localhost:8080/chat/`
- REST API: `http://localhost:8080/api/chat/`

---

## API Kullanımı

```bash
curl -X POST http://localhost:8080/api/chat/ \
  -H "Content-Type: application/json" \
  -H "X-Thread-ID: demo-thread-1" \
  -d '{"question": "En çok ciro yapan ürün kategorisi hangisi?"}'
```

Örnek yanıt:
```json
{
  "answer": "En çok ciro yapan kategori 'beleza_saude' ...",
  "sql_query": "SELECT ... FROM order_items ...",
  "reasoning_steps": "1) sql_retriever çalıştırıldı 2) generation ...",
  "status": "success"
}
```

Canlı ortamda aynı uç noktayı doğrudan test edebilirsin:
```bash
curl -X POST https://enterprise-data-agent-927895662996.europe-west3.run.app/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"question": "İade oranı en yüksek kategori hangisi?"}'
```

---

##  Google Cloud Run'a Dağıtım

Proje, hiçbir yerel sunucuya bağımlı olmayan tam sunucusuz (serverless) bir mimariye taşındı: veritabanı **Neon DB**, vektör deposu **Qdrant Cloud**, önbellek **Upstash Redis (`rediss://`)** üzerinde çalışıyor.

**1) Apple Silicon / ARM64 uyumluluğu için imajı Cloud Build'de derle:**
```bash
gcloud builds submit --tag europe-west3-docker.pkg.dev/enterprise-data-agent/agent-repo/fastapi-agent:v2
```

**2) Deploy:**
```bash
gcloud run deploy enterprise-data-agent \
  --image europe-west3-docker.pkg.dev/enterprise-data-agent/agent-repo/fastapi-agent:v2 \
  --region europe-west3 \
  --memory 2Gi \
  --env-vars-file env.yaml \
  --allow-unauthenticated
```
---

##  Gelecek Yol Haritası

- [ ] **Multi-Tenant Desteği:** Farklı işletmelerin izole PostgreSQL şemaları ve Qdrant koleksiyonlarıyla çalışması
- [ ] **Gelişmiş RBAC:** Kullanıcı ve departman rollerine göre finansal veri erişim kısıtlaması
- [ ] **Proaktif Anomali Tespiti:** Veritabanında beklenmeyen düşüşleri tespit eden otomatik arka plan analist ajanları
- [ ] Kimlik doğrulama (JWT / API Key) ile kurumsal erişim kontrolü

---
## 📄 Lisans

Bu proje kişisel araştırma, demonstrasyon ve portföy amacıyla geliştirilmiştir.