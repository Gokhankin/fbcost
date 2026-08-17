# Club Adaköy F&B Maliyet Analiz Raporu & Entegrasyon Dokümantasyonu

## 📌 Proje Genel Bilgileri
- **Tesis Adı:** Club Adaköy (Marmaris)
- **Uygulama Adı:** F&B Cost & Consumption Dashboard
- **Sunucu IP Adresi:** `192.168.0.128` (Society Makina)
- **Çalıştığı Port & Servis:** Port `5005` | `fbcost.service` (Systemd User Service)
- **Proje Klasörü:** `/home/society/Masaüstü/fbcost`
- **Canlı SQL Veritabanı:** `192.168.0.41:1433` — `SednaAdakoy`
- **Arşiv SQL Sunucusu:** `10.0.0.11` (`ANTMARINSEDNA2021`, `ANTMARINSEDNA2020` vb.)

---

## 🛠️ Veri Kaynakları ve Entegrasyon Yapısı

### 1. 🟢 Sedna SQL Server'dan %100 Canlı ve Otomatik Çekilenler (`192.168.0.41`):
* **Geceleme ve Pax Sayıları (Misafir Konaklamaları):**
  - `DailyDetail`, `Reservation` ve `Agency` tablolarından seçilen tarihe göre ay başından o güne kadar olan birikimli (**MTD - Month to Date**) konaklamalar canlı hesaplanır.
  - Pansiyon tiplerine göre kırılımlar: **AI** (Her Şey Dahil), **HB** (Yarım Pansiyon), **BB** (Oda Kahvaltı), **Neilson** ve **COMP** (Free/Ücretsiz).
* **Günün Döviz Kurları (EUR & GBP):**
  - `ExchangeRate` tablosundan seçilen tarihteki (veya o tarihe ait en son kaydedilmiş) **EUR** ve **GBP** kurları otomatik çekilir.
* **POS Satış Ciroları:**
  - `PosSummary` ve `Department` tablolarından canlı POS adisyon ciroları çekilir:
    - **Market Satışı (Store - DepartCode: 605)**
    - **Cantina Restaurant (DepartCode: 200)**
    - **Captain Cooks Bar (DepartCode: 300)**
    - **Night Bar (DepartCode: 302)**
    - **Activity Department (DepartCode: 615)**

### 2. 📄 Maliyet Veri Modeli (`fbcost_data.json`):
* **F&B Ambar Tüketim Maliyetleri:** Yiyecek, İçecek ve Alkollü İçecek ambar stok çıkış tutarları, Satış Maliyeti ve Personel Cost.
* **Grup Analizleri:** Ana Grup, Ara Grup ve Alt Grup stok malzeme tüketim tutarları.
* **Detaylı Stok Tüketimi:** 1500+ stok kartının ambar çıkış miktarları ve tutarları.
* **Personel Yemekhane:** Yemekhane deposu malzeme çıkış miktarları ve tutarları.
* **Hariç Tutulan Depolar:** Otele ait olmayan *Demre Malzeme Tüketimi* ve *Marina Sarf Deposu* hesaplamadan ve menüden tamamen çıkartılmıştır.

---

## 🔍 SQL Veritabanı Stok / Sayım Analiz Notları

1. **`192.168.0.41` (Canlı Adaköy SQL) İncelemesi:**
   - `DepotCountValues` (Depo Sayımları), `CostBalance` (Maliyet Bakiyeleri) ve `FbDepotStockDef` (Stok Tanımları) tablolarında **0 KAYIT (Boş)** olduğu tespit edilmiştir.
   - Otelde başından beri stok sayım fişleri Sedna veritabanı yerine resmi Excel F&B Maliyet Analiz Raporları üzerinden yürütüldüğü için stok maliyetleri veri modelinden oranlanmaktadır.

2. **`10.0.0.11` (Arşiv SQL Sunucusu) İncelemesi:**
   - Tüm 7 veritabanı taranmış, `DepotCountValues` ve stok fiş tablolarının tamamının **0 KAYIT (Boş)** olduğu teyit edilmiştir.
   - Bu sunucudaki kayıtlar eski Antalya Marina (2019-2021) ve Andriake Beach Club (2018) tesislerinin arşiv verileridir.

---

## 🎨 Kullanıcı Arayüzü & Mobil Tasarım (UI/UX)

1. **Dinamik Tarih Seçici:**
   - Ekranın sağ üstündeki tarih butonunun **tüm yüzeyi tıklanabilir** durumdadır.
   - Tarih değiştirildiğinde tüm KPI kartları, F&B Maliyet Tablosu, Market Satış Tablosu ve Grafikler anlık olarak yenilenir.

2. **Grafikler (Chart.js Entegrasyonu):**
   - **Net Maliyet Dağılımı (€) Halka Grafiği:** Yiyecek, İçecek ve Alkollü İçecek net euro maliyet oranlarını gösterir.
   - **Oda Gecelemeleri Pasta Grafiği:** AI, HB, BB, Neilson ve Comp konaklama dağılımını gösterir.
   - `Chart.js` kütüphanesi yerel olarak sunucuya indirilmiş (`/static/chart.min.js`), dış CDN bağımlılığı tamamen kaldırılmıştır.

3. **Mobil Ekran (Responsive Block Layout) Optimizasyonu:**
   - Mobil cihazlarda (390px - 768px) tüm **KPI kartları dikey 1fr bloklar halinde** sıralanır; sayfa kayması veya metin taşması engellenmiştir.
   - **Başlık & Denetim Paneli:** Ana başlık, EUR Kuru rozeti ve Tarih Seçici butonları dikeyde ferah ve geniş bloklar halinde sıralanır.
   - **Dokunmatik Tablo Kaydırma:** Geniş tablolar `overflow-x: auto` kapsayıcısına alınmış olup, parmak hareketiyle sağa-sola rahatça kaydırılabilir.

---

*Dokümantasyon Oluşturulma Tarihi: 17 Ağustos 2026*  
*Sistem Durumu: Canlı ve Aktif (`http://192.168.0.128:5005`)*
