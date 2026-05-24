# Dosya Ozeti

## app/main.py
Streamlit uygulamasinin giris noktasi. Sayfa yapisini, navigasyonu ve ekranlar arasi veri akisini yonetir.

## src/data/loader.py
CSV dosyasini okur, farkli kolon adlarini standart isimlere cevirir, tarih ve saat donusumlerini yapar, temiz veri setini ve KPI icin gerekli turetilmis alanlari hazirlar.

## src/models/forecast.py
Gunluk satis toplamlarina gore basit hareketli ortalama yaklasimiyla satis tahmini uretir.

## src/models/campaign.py
Secilen urun, indirim oranı, tarih araligi ve beklenen talep artisina gore kampanya etkisini simule eder.

## src/components/dashboard_view.py
Yonetici Dashboard ekranini olusturur. KPI kartlari, saatlik ve gunluk grafikler, en cok satan urunler ve satis tahmini bu dosyada gosterilir.

## src/components/campaign_view.py
Kampanya simulasyonu ekranini olusturur. Kullanici senaryo girer, gelir etkisini gorur ve kampanyayi aktif olarak kaydedebilir.

## src/components/employee_view.py
Calisan bilgi ekranini olusturur. Yogun saat, aktif kampanya ve top 3 urun bilgisini sade formatta sunar.

## src/utils/constants.py
Uygulama genelinde kullanilan dosya yolu, metin ve varsayilan ayarlari tutar.

## data/raw/coffee_sales_sample.csv
Gercek veri seti gelmeden uygulamanin acilabilmesi icin eklenmis kucuk bir ornek veri dosyasi.
