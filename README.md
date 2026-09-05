# Enterprise Data Agent: Hibrit Çoklu-Ajan (Multi-Agent) İş Zekâsı Sistemi

## 🎯 Projenin Amacı ve Çözdüğü Problem
Geleneksel İş Zekâsı (BI) araçları veya tekil yapay zekâ botları şirket verilerini analiz ederken iki temel duvara toslar:

1. **Vektör Veritabanları (RAG)** tek başına metin aramakta harikadır ancak *"Son 6 ayın toplam cirosu nedir?"* veya *"En çok satan ilk 3 kategori hangisidir?"* gibi kesin matematiksel/ilişkisel soruları çözemez.
2. **SQL Veritabanları** sayısal ve ilişkisel hesaplamalarda kuruşu kuruşuna doğrudur ancak *"Müşteriler teslimat ambalajı hakkında ne diyor?"* veya *"1 puan veren kullanıcıların asıl kırılma noktası neydi?"* gibi yapısal olmayan metinlerin duygu ve kök neden analizini yapamaz.

**Bu projenin nihai hedefi;** yöneticilerin hem finansal/sayısal metrikleri hem de bu metriklerin arkasındaki müşteri deneyimini tek bir noktadan sorgulayabildiği, kurumsal ölçekte bağımsız servislerle çalışan otonom bir **Hibrit Çoklu-Ajan (Multi-Agent) karar destek mekanizması** inşa etmektir.

---

## 🛠️ Mimari ve Teknolojik Omurga

* **İlişkisel Veri Katmanı (PostgreSQL 16):** 550.000+ satırlık e-ticaret tablosu (siparişler, ödemeler, müşteriler, ürünler). Kesin metrikler ve analitik sorgular için.
* **Vektör Veritabanı Katmanı (Qdrant):** 47.000+ zenginleştirilmiş Portekizce müşteri yorumu. Hızlı semantik arama ve metadata filtreleme için.
* **Embedding Motoru (FastEmbed - BAAI/bge-small-en-v1.5):** Dış API bağımlılığı olmadan yerel donanımda çalışan optimize vektörleştirme.
* **Orkestrasyon ve Karar Mekanizması (LangGraph):** Gelen soruyu anlayan, doğru uzmana yönlendiren ve sonuçları birleştiren durum makinesi.

---

## 📍 Şu Ana Kadar Neler Yapıldı? (Mevcut Durum)

- [x] **Konteyner ve Ağ İzolasyonu:** Docker Compose kullanılarak PostgreSQL, Qdrant ve Redis bağımsız ağ servisleri olarak ayağa kaldırıldı; Python sürecinden ve birbirlerinden izole edildi.
- [x] **Yüksek Hızlı ETL ve Veri PipLine:** Polars motoru ile CSV verileri normalize edildi, tarih tipleri dönüştürüldü ve `execute_values` yöntemiyle 550k+ kayıt ilişkisel kurallarla PostgreSQL'e yüklendi.
- [x] **Vektörleştirme ve Batch Ingestion:** Yorumlar SQL üzerinden metadata (puan, kategori, sipariş ID) ile zenginleştirildi; HTTP payload sınırlarını aşmamak için batch (toplu paket) mimarisiyle Qdrant'a 47.323 adet vektör eksiksiz aktarıldı.
- [x] **Altyapı Doğrulaması:** Qdrant üzerinde hem anlamsal kosinüs araması hem de metadata filtresi (`review_score <= 2`) test edildi; 0.90+ doğruluk skorlarıyla çalıştığı kanıtlandı.

---

## 🚀 Bundan Sonra Neler Yapılacak? (Yol Haritası)

1. **SQL Analist Ajanı (Node 1):** PostgreSQL şemasını otonom inceleyen, gelen iş soruları için güvenli (`SELECT` kısıtlı) SQL üreten ve sonuçları yorumlayan ajan geliştirilecek.
2. **Müşteri Sesi / RAG Ajanı (Node 2):** Müşteri yorumlarını Qdrant üzerinden anlamsal olarak çeken ve şikayet/memnuniyet kök nedenlerini çıkaran uzman ajan yazılacak.
3. **LangGraph Süpervizör & Yönlendirici (Router):** Kullanıcı sorusunu analiz ederek:
   * Sayısal soruları doğrudan SQL Ajanına,
   * Duygu/şikayet sorularını doğrudan RAG Ajanına,
   * *"En çok geciken kategorideki temel müşteri şikayetleri neler?"* gibi karmaşık soruları ise iki ajanı sırayla çalıştırıp çıktıyı birleştirecek **Hibrit Sentez Düğümüne** yönlendirecek.
4. **API ve Test:** Sistemin bir API ucu üzerinden dış dünyaya açılması ve kurumsal senaryolarla uçtan uca test edilmesi sağlanacak.