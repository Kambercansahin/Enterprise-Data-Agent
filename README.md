# Enterprise Data Agent: Hibrit Çoklu-Ajan (Multi-Agent) İş Zekâsı Sistemi

## 🎯 Projenin Amacı
İş zekâsı süreçlerinde sayısal metrikler (SQL) ile müşteri geri bildirimlerini (Vektör/RAG) tek noktada birleştirmek; yöneticilerin hem finansal verileri hem de bu verilerin arkasındaki niteliksel müşteri deneyimini doğal dille sorgulayabilmesini sağlamak.

---

## 🛠️ Mimari ve Teknolojik Omurga

* **İlişkisel Veritabanı:** PostgreSQL 16 (Yapısal e-ticaret metrikleri)
* **Vektör Veritabanı:** Qdrant (Müşteri yorumları ve anlamsal arama)
* **Embedding Motoru:** FastEmbed (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)
* **Önbellek & Performans:** Redis (Tekrarlanan sorgu önbelleği)
* **Dış İstihbarat:** Tavily AI (Pazar ve trend araştırması)
* **Orkestrasyon:** LangGraph (Koşullu yönlendirme, hata denetimi ve hibrit sentez)
* **Arayüz & Sunucu:** FastAPI + Jinja2 

---

## 📍 Proje Durumu

- [x] **Altyapı & Veri Hattı:** PostgreSQL, Qdrant ve Redis Docker üzerinde izole servisler olarak kuruldu; 550k+ satırlık ilişkisel veri ile 47k+ zenginleştirilmiş müşteri yorumu yüklendi.
- [x] **SQL Analist Ajanı:** Şemayı dinamik okuyup iş sorularına göre güvenli SQL üreten ve çalıştıran düğüm tamamlandı.
- [x] **RAG / Müşteri Sesi Ajanı:** Qdrant üzerinde anlamsal arama ve metadata filtreleriyle duygu/şikayet analizi yapan düğüm kuruldu.
- [x] **Web Arama Ajanı:** Dahili veritabanında bulunmayan dış pazar ve makro trend soruları için Tavily arama entegrasyonu sağlandı.
- [x] **LangGraph Yönlendirici (Router) & Multi-Step:** Sorunun yapısına göre akışı SQL, RAG, WebSearch veya hibrit (Multi-Step Decompose) rotalarına yönlendiren mimari bağlandı.
- [x] **Otonom Denetim (Grading):** Üretilen yanıtın doğruluğunu ve soruya uygunluğunu denetleyen kontrol/yeniden deneme döngüsü uygulandı.
- [x] **Performans (Redis Cache):** Yanıt sürelerini ve API maliyetlerini düşürmek için sorgu bazlı önbellekleme katmanı eklendi.
- [x] **Web Arayüzü & BI Görselleştirme:** FastAPI üzerinde çalışan, SQL metriklerini dinamik tablolara ve interaktif Chart.js grafiklerine dönüştüren responsive arayüz devreye alındı.

---

## 🚀 Yol Haritası (Sıradaki Adımlar)

- [ ] **Sohbet Geçmişi (Multi-Turn Memory):** LangGraph state yapısına checkpointer bağlanarak oturum bazlı (`thread_id`) devam sorularının desteklenmesi.

- [ ] **Yetkilendirme & Güvenlik:** Kurumsal kullanım için kimlik doğrulama (JWT/API Key) ve istek sınırlama (Rate Limiting) katmanı.