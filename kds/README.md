# Kahve Satis Tahmin ve Kampanya Planlama Karar Destek Sistemi

Bu proje, kahve satis verilerini kullanarak analitik dashboard seviyesinden karar destek sistemi seviyesine gecmeyi hedefleyen bir Streamlit prototipidir. Sistem sadece gecmisi gostermekle kalmaz; kisa vadeli tahmin, anomali tespiti, segmentasyon ve aksiyon onerileri de uretir.

## Proje Amaci

Amaç, kahve dukkaninda yonetici ve ekiplerin su sorulara veri ile cevap alabilmesini saglamaktir:

- Ne oldu?
- Ne olacak?
- Neden oldu?
- Ne yapmaliyim?

## Kullanilan Teknolojiler

- Python
- Streamlit
- Pandas
- NumPy
- Plotly

## Temel Ozellikler

- Yonetici dashboard ve KPI analizi
- Holt-Winters Exponential Smoothing ile kisa vadeli satis tahmini
- Z-score tabanli anomali tespiti
- K-Means mantigina dayali urun segmentasyonu
- Kampanya simulasyonu ve senaryo karsilastirmasi
- Kural tabanli onerı / aksiyon motoru
- Donem bazli yonetici raporu
- Calisan bilgi ekrani

## Klasor Yapisi

```text
.
├── app/
│   └── main.py
├── data/
│   └── raw/
│       ├── coffee_sales.csv
│       └── coffee_sales_sample.csv
├── docs/
│   └── file_summary.md
├── src/
│   ├── components/
│   │   ├── anomaly_view.py
│   │   ├── campaign_view.py
│   │   ├── dashboard_view.py
│   │   ├── employee_view.py
│   │   ├── forecast_view.py
│   │   ├── recommendation_view.py
│   │   ├── report_view.py
│   │   └── segment_view.py
│   ├── data/
│   │   └── loader.py
│   ├── models/
│   │   ├── anomaly.py
│   │   ├── campaign.py
│   │   ├── forecast.py
│   │   ├── recommendation.py
│   │   └── segmentation.py
│   └── utils/
│       └── constants.py
├── requirements.txt
└── README.md
```

## Kurulum

1. Proje klasorune gir:

```bash
cd /Users/begumcetin/Documents/Codex/2026-04-21-elimde-karar-destek-sistemleri-dersi-i
```

2. Gerekli kutuphaneleri kur:

```bash
pip install -r requirements.txt
```

## Calistirma

```bash
streamlit run app/main.py
```

## Kullanim

- Sol menuden istedigin sayfayi sec.
- `Yonetici Dashboard` ekrani genel performansi gosterir.
- `Tahminleme` ekrani gelecek gunlerdeki satis egilimini gosterir.
- `Anomali Tespiti` ekrani olagandisi gun ve saatleri isaretler.
- `Segmentasyon` ekrani urunleri benzer davranis gruplarina ayirir.
- `Kampanya Simulasyonu` ekrani gelir etkisini senaryo bazli hesaplar.
- `Oneri / Aksiyon Motoru` ekrani dogrudan yapilabilecek aksiyonlari listeler.
- `Rapor Ekrani` secilen donem icin kisa yonetici ozeti uretir.
- `Calisan Bilgi Ekrani` aktif kampanya ve operasyon bilgisini sade sekilde gosterir.

## Teknik Not

- Tahminleme icin haftalik sezonsalligi dikkate alan Holt-Winters Exponential Smoothing kullanilmistir.
- Anomali tespiti icin z-score tercih edilmistir.
- Segmentasyon icin urun bazli K-Means mantigi uygulanmistir.
- Oneri motoru, tahmin + anomali + segmentasyon sonucuna dayali kural tabanli mantik ile calisir.

## Not

Bu proje ogrenci seviyesinde, savunulabilir ve calisir bir karar destek sistemi prototipi olarak tasarlanmistir. Veritabani, login, deployment ve ileri seviye yapay zeka mimarileri bilerek disarida birakilmistir.
