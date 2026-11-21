[English](README.md) | Türkçe

# Kafe Karar Destek Sistemi

Karar Destek Sistemleri dersi için geliştirilmiş bir Streamlit prototipi. Kahve dükkânı satış verisini kullanarak "ne oldu"yu gösteren bir dashboard'un ötesine geçer: önümüzdeki günleri tahmin eder, olağandışı gün ve saatleri işaretler, ürünleri davranışlarına göre gruplar, kampanyaları simüle eder ve aksiyon önerir. Arayüz Türkçedir.

Amaç, bir yöneticinin dört soruya veriyle cevap alabilmesi: ne oldu, ne olacak, neden oldu ve ne yapmalıyım?

## Veri

`kds/data/raw/coffee_sales.csv` 1 Mart 2024 ile 23 Mart 2025 arasındaki 3.547 kart ve nakit işlemi içerir: saat, ödeme türü, tutar, ürün adı, günün dilimi ve tarih. Dosya RTF olarak kaydedilmiş; yükleyici, CSV olarak okumadan önce RTF kılıfını ayıklar. Dosya yoksa uygulama küçük `coffee_sales_sample.csv` dosyasına geçer.

## Ekranlar

Kenar çubuğunda beş ekran var:

- **Genel Dashboard:** KPI kartları, saatlik ve günlük satış grafikleri, en çok satan ürünler ve kısa bir satış tahmini.
- **Karar Destek Merkezi:** her biri kendi yöntemini kullanan dört sekme:
  - **Tahminleme:** haftalık mevsimselliği ve sönümlenen bir trendi olan Holt-Winters üstel düzeltme; sonuç, son satışların çevresinde makul bir aralığa kırpılır. Model kurulamazsa hafta günü ortalaması ile son 7 günün karışımına döner.
  - **Anomali Tespiti:** olağandışı gün ve saatleri işaretlemek için günlük ve saatlik satışlarda z-skoru.
  - **Segmentasyon:** ürünler, NumPy ile yazılmış küçük bir K-Means ile davranışlarına göre gruplanır.
  - **Öneri / Aksiyon Motoru:** tahmin, anomali ve segment sonuçlarını birleştirip aksiyon öneren kural tabanlı bir motor.
- **Kampanya Simülatörü:** ürün, indirim, tarih aralığı ve beklenen talep artışını seçip senaryoları karşılaştırır, bir kampanyayı aktif olarak kaydedebilirsiniz.
- **Rapor Ekranı:** seçilen dönem için kısa bir yönetici özeti.
- **Kullanıcı / Çalışan Paneli:** yoğun saat, aktif kampanya ve ilk üç ürünü gösteren bir çalışan ekranı ile giriş ekranı olan bir müşteri ekranı. Buradaki müşteriler gerçek veri değil, `src/data/users.py` içindeki uydurma örnek kullanıcılardır.

## Çalıştırma

```bash
cd kds
pip install -r requirements.txt
streamlit run app/main.py
```

Gereksinimler: Streamlit, pandas, NumPy, Plotly ve statsmodels.

## Yapı

```
kds/
  app/main.py              giriş noktası, gezinme
  src/data/                CSV yükleyici (RTF dosyasını işler), örnek kullanıcılar
  src/models/              tahmin, anomali, segmentasyon, kampanya, öneri
  src/components/          her ekran için bir Streamlit görünümü
  src/utils/constants.py   dosya yolları ve varsayılanlar
  data/raw/                coffee_sales.csv ve küçük bir örnek dosya
  docs/file_summary.md     dosya başına kısa notlar (kısmen eski, aşağıya bakın)
```

## Sınırlar

Bu bir öğrenci prototipidir. Ağır modeller yerine bilinçli olarak açıklanabilir yöntemler seçildi; veritabanı, kimlik doğrulama ve yayına alma yok. Giriş ekranı örnek kullanıcılarla çalışan bir demodur, gerçek kimlik doğrulama değildir. Tahmin, ayrılmış günler üzerinde doğrulanmadı ve tek bir dükkânın bir yıllık verisi, varsaydığı haftalık mevsimsellik için küçük bir temel. `docs/file_summary.md` hâlâ tahmini önceki sürümden kalma basit bir hareketli ortalama olarak anlatıyor; kod yukarıda anlatıldığı gibi Holt-Winters kullanıyor.
