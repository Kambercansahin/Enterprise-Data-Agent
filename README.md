# Enterprise Data Agent

**Hibrit Çoklu-Ajan (Multi-Agent) İş Zekâsı Sistemi**

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