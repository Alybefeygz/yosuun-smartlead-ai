# Yosuun SmartLead AI — Faz Bazlı Uygulama Planı

Bu plan, `project_documents.md` içindeki teknik sözleşmeyi uygulanabilir geliştirme fazlarına dönüştürür. Amaç; Python, Flask, Jinja, vanilla JavaScript, CSS, SQLite, Groq ve Render kullanarak test edilebilir, güvenli ve uçtan uca çalışan bir MVP teslim etmektir.

> **19 Eylül 2026 revizyonu:** Kullanıcı arayüzlerinde Wix kullanma zorunluluğu kaldırıldı. Bu plandaki Flask/Jinja tabanlı UI kararları, `project_documents.md` içindeki Wix'e özel maddelerin yerine geçer. Diğer backend, veri, güvenlik ve deployment kuralları geçerliliğini korur. MVP'de ayrı bir cross-origin istemci kalmadığı için mevcut Flask-Cors bağımlılığı ve `CORS_ORIGINS` ayarı Faz 7'de kontrollü olarak kaldırılacaktır.

## 1. Proje hedefi

Uygulama iki temel kullanıcı akışı sunacaktır:

1. Ziyaretçi, Flask tarafından sunulan karşılama sayfasında Yosuun AI Asistan ile sohbet eder ve iletişim bilgilerini bırakır.
2. Yosuun ekibi, aynı uygulamadaki ayrı yönetim ekranında kaydedilen lead'leri en yeniden eskiye doğru görür.

Temel veri akışı:

```text
Browser / -> Flask template + static assets
         -> Flask API -> Groq
         \-> Flask API -> SQLite

Browser /dashboard -> Flask template + static assets
                   -> Flask API -> SQLite
```

## 2. Değiştirilemez teknik kurallar

- Backend Python ve Flask ile geliştirilecek.
- Veritabanı olarak SQLite kullanılacak.
- AI sağlayıcısı Groq, model olarak developer planda canlı bağlantısı doğrulanan `openai/gpt-oss-20b` kullanılacak.
- Kullanıcı arayüzleri Flask Jinja template, semantik HTML, vanilla JavaScript ve CSS ile hazırlanacak.
- Frontend için ayrı bir framework veya ayrı deployment kullanılmayacak.
- Uygulamanın tamamı tek Render Web Service olarak yayınlanacak.
- SQL ifadeleri yalnızca `app/database.py` içinde bulunacak.
- Groq HTTP çağrıları yalnızca `app/services/ai_service.py` içinde bulunacak.
- Route fonksiyonları sadece parse, validate, delegate ve response mapping yapacak.
- Yapılandırma değerlerinin tek kaynağı `config.py` olacak.
- Secret değerler environment variable olarak saklanacak; `.env` repoya eklenmeyecek.
- SQL sorgularında `?` placeholder kullanılacak.
- Uygulama `create_app()` application factory ile oluşturulacak.
- Template dosyalarında inline JavaScript veya inline CSS bulunmayacak.
- HTTP istekleri yalnızca ortak frontend API client modülünden yapılacak.
- Sayfa scriptleri DOM ve kullanıcı etkileşiminden; API client yalnızca HTTP sözleşmesinden sorumlu olacak.
- Aynı origin kullanıldığı için frontend isteklerinde sabit domain yerine göreli `/api/*` yolları kullanılacak.
- MVP'de cross-origin API erişimi sunulmayacak; ileride gerçek bir tüketici ihtiyacı doğarsa CORS ayrı bir güvenlik kararı ve testleriyle yeniden eklenecek.
- Fonksiyonlar tek sorumluluklu, kısa ve açık isimli olacak; tekrar eden DOM ve hata işlemleri ortak yardımcılara alınacak.
- Bir fazın test kapısı geçilmeden sonraki faza başlanmayacak.

## 3. Hedef dosya yapısı

```text
.
├── app/
│   ├── __init__.py
│   ├── database.py
│   ├── routes.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── ai_service.py
│   ├── templates/
│   │   ├── index.html
│   │   └── dashboard.html
│   └── static/
│       ├── css/
│       │   └── main.css
│       ├── images/
│       │   └── favicon.svg
│       └── js/
│           ├── api-client.js
│           ├── home.js
│           └── dashboard.js
├── tests/
│   ├── conftest.py
│   ├── test_ai_service.py
│   ├── test_config.py
│   ├── test_database.py
│   ├── test_routes.py
│   └── test_templates.py
├── .env.example
├── .gitignore
├── config.py
├── pytest.ini
├── requirements.txt
├── run.py
└── README.md
```

## Faz 0 — Hazırlık ve kapsamı sabitleme

**Amaç:** Geliştirme ortamını hazırlamak ve proje sınırlarını netleştirmek.

**Durum:** Yerel hazırlık tamamlandı. Harici hesap erişimleri kullanıcı tarafından doğrulanmayı bekliyor.

### Yapılacaklar

- [x] Python 3.9+ sürümünü doğrula.
- [x] Proje için sanal ortam oluştur.
- [x] Git deposunu başlat ve `main` branch'ini kullan.
- [ ] GitHub, Render ve Groq hesap erişimlerini doğrula.
- [x] MVP kapsamını ve kapsam dışı maddeleri ekip için sabitle.
- [x] Gerçek API anahtarlarının belgelere veya commit'lere yazılmayacağını doğrula.

### Kapsam dışı

- Kullanıcı hesabı ve tam yetkilendirme sistemi
- CRM pipeline ve otomatik e-posta akışları
- PostgreSQL, Redis, Celery veya mikroservis mimarisi
- RAG, vector database veya uzun süreli sohbet hafızası

### Test kapısı

```bash
python --version
git --version
```

**Tamamlanma kriteri:** Yerel ortam hazır, hesap erişimleri mevcut ve kapsam onaylıdır.

## Faz 1 — Proje iskeleti ve yapılandırma

**Amaç:** Uygulamanın klasör yapısını ve environment tabanlı ayarları kurmak.

**Durum:** Tamamlandı ve otomatik testlerle doğrulandı.

### Oluşturulacak dosyalar

- `config.py`
- `.env.example`
- `.gitignore`
- `requirements.txt`
- `app/__init__.py`
- `app/services/__init__.py`
- `run.py`

### Yapılacaklar

- [x] Flask, Flask-Cors, python-dotenv, requests, gunicorn ve pytest bağımlılıklarını tanımla.
- [x] `Config`, `DevelopmentConfig` ve `ProductionConfig` sınıflarını oluştur.
- [x] `SECRET_KEY`, `DATABASE_URL`, `GROQ_API_KEY`, `AI_PROVIDER`, `BUSINESS_CONTEXT` ve `CORS_ORIGINS` ayarlarını tanımla.
- [x] `CORS_ORIGINS` değerini tek yerde normalize et.
- [x] `.env.example` içine yalnızca örnek/boş değerler ekle.
- [x] `.env`, sanal ortam, Python cache ve runtime SQLite dosyalarını `.gitignore` kapsamına al.
- [x] `run.py` dosyasını sadece uygulama giriş noktası olacak şekilde hazırla.

### Test kapısı

```bash
python -m pip install -r requirements.txt
python -c "from config import Config; print(bool(Config.DATABASE_URL))"
```

**Tamamlanma kriteri:** Ayarlar import ediliyor, secret değerler kodda bulunmuyor ve temiz ortamda bağımlılıklar kurulabiliyor.

## Faz 2 — SQLite veri katmanı

**Amaç:** Lead verisini kalıcı ve test edilebilir biçimde yönetmek.

**Durum:** Tamamlandı; geçici SQLite dosyası kullanan entegrasyon testleriyle doğrulandı.

### Değişecek dosyalar

- `app/database.py`
- `tests/test_database.py`
- `tests/conftest.py`

### Veri modeli

```sql
CREATE TABLE IF NOT EXISTS leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isim TEXT NOT NULL,
    telefon TEXT NOT NULL,
    mesaj TEXT,
    tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Yapılacaklar

- [x] Request/application context ile çalışan `get_db()` fonksiyonunu yaz.
- [x] Bağlantıda `sqlite3.Row` kullan.
- [x] Bağlantı kapatma işlemini Flask teardown mekanizmasına bağla.
- [x] Tabloyu idempotent oluşturan `init_db(app)` fonksiyonunu yaz.
- [x] Parametreli sorgu kullanan `lead_ekle(isim, telefon, mesaj)` fonksiyonunu yaz.
- [x] Kayıtları `tarih DESC, id DESC` sırasında getiren `tum_leadler()` fonksiyonunu yaz.
- [x] Üst katmana cursor yerine dict/list döndür.
- [x] Testlerde geçici bir SQLite dosyası kullan.

### Test kapısı

```bash
pytest -q tests/test_database.py
```

### Doğrulanacak senaryolar

- [x] Tablo birden fazla kez hatasız oluşturuluyor.
- [x] Lead eklendiğinde kimlik üretiliyor.
- [x] Tüm zorunlu alanlar saklanıyor.
- [x] Liste en yeni kayıttan başlıyor.
- [x] SQL sorgularında string interpolation bulunmuyor.

**Tamamlanma kriteri:** Veri katmanı testleri geçiyor ve uygulamanın başka hiçbir dosyasında SQL bulunmuyor.

## Faz 3 — AI servis katmanı

**Amaç:** Groq entegrasyonunu Flask ve veri katmanından bağımsız kurmak.

**Durum:** Tamamlandı; provider başarı, hata ve demo yolları mock testlerle doğrulandı.

### Değişecek dosyalar

- `app/services/ai_service.py`
- `tests/test_ai_service.py`

### Yapılacaklar

- [x] `AIServiceError` exception tipini oluştur.
- [x] `AIService` sınıfını ve `yanit_uret(mesaj, gecmis)` metodunu yaz.
- [x] Mesaj dizisini system prompt, doğrulanmış geçmiş ve yeni kullanıcı mesajı sırasında kur.
- [x] Frontend'den gelen `system` rolünü kabul etme.
- [x] Geçmiş mesaj sayısına veya karakter miktarına limit uygula.
- [x] Groq isteğinde finite timeout kullan.
- [x] Non-2xx, timeout ve bozuk provider cevabını `AIServiceError` olarak normalize et.
- [x] API anahtarı olmadığında kontrollü demo cevabı döndür.
- [x] Kullanıcıya provider response body, stack trace veya API anahtarı sızdırma.

### Test kapısı

```bash
pytest -q tests/test_ai_service.py
```

### Doğrulanacak senaryolar

- [x] System prompt her zaman ilk sırada.
- [x] Yeni kullanıcı mesajı her zaman son sırada.
- [x] Geçersiz geçmiş rolleri reddediliyor.
- [x] Başarılı provider cevabı string olarak dönüyor.
- [x] Timeout ve HTTP hataları tek tip exception'a dönüşüyor.
- [x] API anahtarı yokken uygulama çökmüyor.

**Tamamlanma kriteri:** Groq sınırı mock testlerle doğrulanmış ve tüm provider mantığı tek dosyada izole edilmiştir.

## Faz 4 — REST API ve doğrulama

**Amaç:** Browser arayüzü ile backend arasındaki sabit API sözleşmesini gerçekleştirmek.

**Durum:** Tamamlandı; API sözleşmesi, validasyon ve güvenli hata yolları entegrasyon testleriyle doğrulandı.

### Değişecek dosyalar

- `app/routes.py`
- `tests/test_routes.py`

### Endpoint'ler

| Method | Yol | Başarı | Amaç |
|---|---|---:|---|
| `GET` | `/` | 200 | Basit karşılama sayfası |
| `GET` | `/dashboard` | 200 | Basit dashboard template'i |
| `POST` | `/api/sohbet` | 200 | AI cevabı üretme |
| `POST` | `/api/leads` | 201 | Lead kaydetme |
| `GET` | `/api/leads` | 200 | Lead'leri listeleme |

### Yapılacaklar

- [x] Route'ları Flask Blueprint ile tanımla.
- [x] JSON body'nin obje olduğunu kontrol et.
- [x] `mesaj`, `isim` ve `telefon` alanlarını trim edip server tarafında doğrula.
- [x] Alanlara makul uzunluk limitleri uygula.
- [x] `tarih` ve `id` değerlerini client'tan alma.
- [x] AI hatalarını güvenli JSON ile `503` durumuna map et.
- [x] Veritabanı hatalarını güvenli JSON ile `500` durumuna map et.
- [x] Her API cevabında `basari` alanını bulundur.
- [x] Raw exception metnini response içine koyma.

### API alan adları

- Sohbet isteği: `mesaj`, `gecmis`
- Sohbet cevabı: `basari`, `cevap`
- Lead isteği: `isim`, `telefon`, `mesaj`
- Lead listesi: `basari`, `leads`
- Lead kaydı: `id`, `isim`, `telefon`, `mesaj`, `tarih`

### Test kapısı

```bash
pytest -q tests/test_routes.py
```

### Doğrulanacak senaryolar

- [x] Boş sohbet mesajı `400` döndürüyor.
- [x] Mock AI başarısı `200` ve `cevap` döndürüyor.
- [x] AI servis hatası `503` döndürüyor.
- [x] Geçerli lead `201` ile kaydediliyor.
- [x] Eksik isim veya telefon `400` döndürüyor.
- [x] Lead listesi `200` ve JSON dizi döndürüyor.

**Tamamlanma kriteri:** API sözleşmesi testlerle sabitlenmiş ve route katmanında SQL/provider mantığı bulunmamaktadır.

## Faz 5 — Application factory, CORS ve backend entegrasyonu

**Amaç:** Tüm backend bileşenlerini tek composition root altında birleştirmek.

**Durum:** Tamamlandı; factory, health, CORS, logging ve yerel process smoke testi başarılı.

### Değişecek dosyalar

- `app/__init__.py`
- `run.py`
- `app/templates/index.html`
- `app/templates/dashboard.html`
- `tests/conftest.py`

### Yapılacaklar

- [x] `create_app(config_name=None)` factory fonksiyonunu tamamla.
- [x] Config yükleme, CORS, DB init ve Blueprint registration işlemlerini burada birleştir.
- [x] `GET /health` endpoint'ini ekle.
- [x] CORS'u yalnızca `/api/*` için ve allowlist origin'lerle etkinleştir.
- [x] `run.py` dosyasında `app = create_app()` nesnesini sun.
- [x] Local geliştirme için `__main__` guard ekle.
- [x] `/` ve `/dashboard` için minimal fallback template'leri ekle.
- [x] Startup ve exception loglarını secret/telefon sızdırmayacak biçimde yapılandır.

### Test kapısı

```bash
pytest -q
python run.py
curl http://127.0.0.1:5000/health
```

Beklenen health cevabı:

```json
{"basari": true, "durum": "aktif"}
```

**Tamamlanma kriteri:** Tüm otomatik testler geçiyor, backend yerelde açılıyor ve health endpoint'i `200` döndürüyor.

## Faz 6 — Gerçek Groq bağlantısı ve backend QA

**Amaç:** Mock dışında gerçek AI entegrasyonunu ve tüm hata yollarını doğrulamak.

**Durum:** Kısmen tamamlandı; API anahtarı ve `openai/gpt-oss-20b` ile gerçek Groq bağlantısı doğrulandı ve kalıcı model konfigürasyonu güncellendi. Yalnızca davranış kabul kontrolleri açık.

### Yapılacaklar

- [x] Yerel `.env` içine gerçek Groq anahtarını ekle; bu dosyayı commit etme.
- [x] `GROQ_MODEL` varsayılanını ve `.env.example` değerini `openai/gpt-oss-20b` olarak güncelle.
- [ ] Türkçe ve Yosuun bağlamına uygun cevap alındığını doğrula.
- [ ] Asistanın bilmediği bir özelliği kesin bilgi gibi sunmadığını kontrol et.
- [ ] Hassas bilgi talep etmediğini kontrol et.
- [x] Yanlış API anahtarı, timeout ve provider kesintisi senaryolarını dene.
- [x] Sohbet geçmişi limitinin uygulandığını doğrula.
- [x] Loglarda secret veya tam telefon bulunmadığını incele.

### Manuel smoke test

```bash
curl -X POST http://127.0.0.1:5000/api/sohbet \
  -H "Content-Type: application/json" \
  -d '{"mesaj":"Yosuun stok yönetiminde nasıl yardımcı olur?","gecmis":[]}'

curl -X POST http://127.0.0.1:5000/api/leads \
  -H "Content-Type: application/json" \
  -d '{"isim":"Test Kullanıcı","telefon":"05550000000","mesaj":"Demo lead"}'

curl http://127.0.0.1:5000/api/leads
```

**Tamamlanma kriteri:** Chat, lead kaydı ve lead listeleme yerelde uçtan uca çalışıyor; hata cevapları güvenlidir.

## Faz 7 — Flask B2C ziyaretçi arayüzü

**Amaç:** Ziyaretçinin aynı Flask uygulaması üzerinden AI ile konuşmasını ve lead bırakmasını sağlamak.

**Durum:** Tamamlandı; B2C arayüzü, sohbet, lead formu, responsive tasarım, erişilebilirlik durumları ve template testleri uygulandı.

### Değişecek dosyalar

- `app/templates/index.html`
- `app/static/css/main.css`
- `app/static/images/favicon.svg`
- `app/static/js/api-client.js`
- `app/static/js/home.js`
- `app/__init__.py`
- `config.py`
- `.env.example`
- `requirements.txt`
- `tests/test_config.py`
- `tests/test_routes.py`
- `tests/test_templates.py`

### HTML sözleşmesi

| Bileşen | HTML ID |
|---|---|
| Mesaj input | `messageInput` |
| Sor butonu | `askButton` |
| AI cevap alanı | `answerText` |
| İsim input | `nameInput` |
| Telefon input | `phoneInput` |
| Lead mesajı | `leadMessageInput` |
| Kaydet butonu | `saveLeadButton` |
| Durum metni | `statusText` |

### Clean Code sorumlulukları

- `index.html`: Yalnızca semantik sayfa yapısı, erişilebilir label'lar ve asset referansları.
- `main.css`: Renkler, responsive yerleşim, component durumları ve tasarım token'ları.
- `api-client.js`: `sohbetGonder()` ve `leadKaydet()` dahil tüm HTTP istekleri ve normalize edilmiş frontend hataları.
- `home.js`: DOM olayları, form validasyonu, sohbet geçmişi ve loading/success/error durumları.
- Template içinde iş mantığı, inline event handler, inline JavaScript veya inline CSS bulunmayacak.

### Yapılacaklar

- [x] Minimal fallback `index.html` dosyasını gerçek B2C arayüzüyle değiştir.
- [x] Semantik `header`, `main`, `section`, `form`, `label` ve `button` yapısı kullan.
- [x] Z-pattern karşılama düzenini ve Yosuun renklerini uygula: `#78F666`, siyah ve beyaz.
- [x] Renk, boşluk, radius ve typography değerlerini CSS custom property olarak tek yerde tanımla.
- [x] Mobil-first responsive yerleşim uygula.
- [x] `api-client.js` içinde göreli `POST /api/sohbet` entegrasyonunu yaz.
- [x] Yalnızca `user` ve `assistant` rollerinden oluşan sınırlı sohbet geçmişi gönder.
- [x] Lead formunu `POST /api/leads` endpoint'ine bağla.
- [x] Browser validasyonunu backend limitleriyle uyumlu tut; backend validasyonunu tek güvenlik kaynağı olarak koru.
- [x] Loading, success, empty ve error durumlarını ayrı fonksiyonlarla yönet.
- [x] İstek sırasında butonları disable ederek yinelenen tıklamaları engelle; `finally` bloğunda geri aç.
- [x] Başarılı lead kaydından sonra formu temizle ve erişilebilir geri bildirim göster.
- [x] Durum alanlarına uygun `aria-live` kullan; form alanlarını label ile eşle.
- [x] Klavye kullanımını, focus görünümünü ve renk kontrastını kontrol et.
- [x] Template contract ve static asset cevapları için Flask testleri ekle.
- [x] Ayrı cross-origin istemci kalmadığı için Flask-Cors bağımlılığını, `CORS_ORIGINS` config'ini ve bunlara özel testleri birlikte kaldır.
- [x] Aynı-origin olmayan isteklerin uygulama tarafından özel olarak yetkilendirilmediğini doğrula.

### Test kapısı

- [x] `/` gerekli HTML elementleri ve static asset referanslarıyla `200` döndürüyor.
- [x] Boş mesaj istemci tarafında gönderilmiyor.
- [x] AI cevabı arayüzde gösteriliyor.
- [x] Backend hatasında teknik detay içermeyen anlaşılır mesaj gösteriliyor.
- [x] Eksik isim/telefon ile lead gönderilmiyor.
- [x] Geçerli lead backend'e kaydediliyor ve form temizleniyor.
- [x] Dar ve geniş ekranlarda yatay taşma oluşmuyor.
- [x] `pytest -q` tamamen geçiyor.

**Tamamlanma kriteri:** `/` sayfasında sohbet ve lead formu aynı-origin Flask API ile masaüstü ve mobilde uçtan uca çalışıyor; HTML, CSS, HTTP ve DOM sorumlulukları ayrı dosyalarda tutuluyor.

## Faz 8 — Flask B2B lead yönetim paneli

**Amaç:** Kaydedilen lead'leri aynı Flask uygulaması içinde okunabilir ve responsive bir operasyon ekranında göstermek.

**Durum:** Tamamlandı; responsive dashboard, güvenli lead render akışı, yenileme ve tüm ekran durumları uygulandı.

### Değişecek dosyalar

- `app/templates/dashboard.html`
- `app/static/css/main.css`
- `app/static/js/api-client.js`
- `app/static/js/dashboard.js`
- `tests/test_templates.py`

### HTML sözleşmesi

| Bileşen | HTML ID |
|---|---|
| Lead tablosu/liste kapsayıcısı | `leadList` |
| Yenile butonu | `refreshButton` |
| Durum metni | `dashboardStatus` |
| Satır template'i | `leadRowTemplate` |

### Clean Code sorumlulukları

- `dashboard.html`: Semantik başlık, kontrol alanı, tablo/liste iskeleti ve boş durum alanı.
- `api-client.js`: Yalnızca `leadleriGetir()` HTTP fonksiyonu ve ortak response/error normalizasyonu.
- `dashboard.js`: Veriyi DOM'a güvenli biçimde basma, tarih formatlama, loading/empty/error durumları ve yenileme olayı.
- Kullanıcı verileri `innerHTML` ile birleştirilmeyecek; `textContent` kullanılarak XSS riski azaltılacak.

### Yapılacaklar

- [x] Minimal fallback `dashboard.html` dosyasını gerçek yönetim ekranıyla değiştir.
- [x] F-pattern yerleşimli, semantik ve responsive dashboard tasarla.
- [x] `api-client.js` içinde göreli `GET /api/leads` entegrasyonunu yaz.
- [x] Lead listesini `id` değerini DOM kimliği olarak kullanmadan güvenli satırlara dönüştür.
- [x] Kullanıcı alanlarını yalnızca `textContent` ile render et.
- [x] Loading, boş liste ve hata durumlarını ayrı ayrı göster.
- [x] Manuel yenile butonunu uygula ve istek sırasında disable et.
- [x] Tarihi `Intl.DateTimeFormat("tr-TR")` ile okunabilir yerel formata çevir.
- [x] Mobilde tablo yerine okunabilir kart veya yatay taşmasız liste düzeni kullan.
- [x] Template contract ve static asset testlerini ekle.

### Güvenlik notu

MVP API sözleşmesinde `GET /api/leads` için backend auth zorunlu tutulmamıştır. Aynı-origin UI bu açığı tek başına kapatmaz. Gerçek kişisel veriyle production kullanımından önce `/dashboard` ve `GET /api/leads` kimlik doğrulama ve yetkilendirme ile korunmalıdır.

### Test kapısı

- [x] `/dashboard` gerekli HTML elementleri ve static asset referanslarıyla `200` döndürüyor.
- [x] Yeni eklenen lead panelde ilk sırada görünüyor.
- [x] Kullanıcı girdileri HTML olarak yorumlanmadan gösteriliyor.
- [x] Boş ve hata durumları doğru görünüyor.
- [x] Yenile butonu listeyi tekrar getiriyor ve yinelenen isteği engelliyor.
- [x] Mobil ve masaüstü yerleşimleri kullanılabilir durumda.
- [x] `pytest -q` tamamen geçiyor.

**Tamamlanma kriteri:** `/dashboard` sayfası backend'deki lead'leri hatasız, güvenli ve en yeni kayıt önce olacak şekilde gösteriyor; dashboard kodu HTTP ve DOM sorumluluklarını ayırıyor.

## Faz 9 — GitHub ve Render deployment

**Amaç:** HTML, CSS, JavaScript, API, AI servisi ve SQLite veri katmanını içeren tek Flask uygulamasını canlı ortama almak.

### Yapılacaklar

- [ ] Kodun public GitHub reposuna gönderilmeye hazır olduğunu kontrol et.
- [ ] `.env` ve runtime SQLite dosyasının Git indexinde olmadığını doğrula.
- [ ] Render Web Service oluştur.
- [ ] Build command olarak `pip install -r requirements.txt` ayarla.
- [ ] Start command olarak `gunicorn run:app` kullan.
- [ ] Render environment variable'larını tanımla.
- [ ] Frontend'in tüm API çağrılarında göreli `/api/*` yolları kullandığını ve hardcoded domain bulunmadığını doğrula.
- [ ] Flask-Cors ve `CORS_ORIGINS` kalıntısı bulunmadığını doğrula.
- [ ] Render health check'i `/health` olarak ayarla.
- [ ] Canlı HTML sayfalarını, static asset'leri ve API endpoint'lerini test et.
- [ ] Canlı B2C sohbet ve lead formunu browser üzerinden test et.
- [ ] Canlı B2B dashboard'u browser üzerinden test et.

### Render environment variable'ları

```text
FLASK_ENV=production
SECRET_KEY=<guclu-ve-gizli-deger>
GROQ_API_KEY=<gercek-anahtar>
AI_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=<sqlite-dosya-yolu>
```

Flask tarafından sunulan first-party UI aynı-origin çalıştığı için production ortamında `CORS_ORIGINS` tanımlanmaz.

### Test kapısı

- [ ] Canlı `/health` `200` döndürüyor.
- [ ] Canlı `/` ve `/dashboard` sayfaları `200` döndürüyor; CSS ve JavaScript asset'leri yükleniyor.
- [ ] Canlı sohbet Groq cevabı döndürüyor.
- [ ] Canlı lead kaydı dashboard'da görünüyor.
- [ ] Render loglarında secret veya hassas veri bulunmuyor.

### Kritik persistence kontrolü

Bir test lead'i oluştur, Render servisini yeniden başlat ve kaydı tekrar sorgula. Veri kayboluyorsa:

1. Uygun Render persistent disk/volume seçeneğini yapılandır.
2. Bu seçenek kullanılamıyorsa demo verisinin ephemeral olduğunu README'de açıkça belirt.

**Tamamlanma kriteri:** Tek Render servisi HTML, static asset, API, Groq ve SQLite akışlarını production ortamında uçtan uca sunuyor.

## Faz 10 — Dokümantasyon, güvenlik kontrolü ve teslim

**Amaç:** Projeyi başka bir geliştiricinin kurabileceği, değerlendirebileceği ve sunabileceği duruma getirmek.

### README içeriği

- [ ] Proje özeti ve kullanıcı problemi
- [ ] Mimari ve dosya sorumlulukları
- [ ] Teknoloji yığını
- [ ] Yerel kurulum ve çalıştırma adımları
- [ ] Environment variable tablosu
- [ ] API endpoint ve örnek request/response'lar
- [ ] Frontend dosya sorumlulukları ve UI geliştirme adımları
- [ ] Render deployment bilgileri
- [ ] Test komutları
- [ ] Güvenlik kararları
- [ ] Bilinen sınırlamalar
- [ ] GitHub ve Render demo bağlantıları

### Son kalite kontrolü

- [ ] `pytest -q` tamamen geçiyor.
- [ ] Temiz bir sanal ortamda `requirements.txt` kurulabiliyor.
- [ ] `database.py` dışında SQL bulunmuyor.
- [ ] `ai_service.py` dışında Groq HTTP çağrısı bulunmuyor.
- [ ] `.env` GitHub'da veya Git indexinde bulunmuyor.
- [ ] Production response'ları traceback içermiyor.
- [ ] Kullanılmayan Flask-Cors bağımlılığı ve `CORS_ORIGINS` ayarı kaldırılmış.
- [ ] Tüm API cevaplarında `basari` alanı var.
- [ ] Template'lerde inline JavaScript, inline CSS ve iş mantığı bulunmuyor.
- [ ] HTTP çağrıları yalnızca `api-client.js` içinde bulunuyor.
- [ ] Kullanıcı verileri frontend'de `innerHTML` ile render edilmiyor.
- [ ] Flask B2C ve B2B sayfaları yayında.
- [ ] Render backend yayında.

### Demo akışı

1. Kullanıcı problemini ve çözümü açıkla.
2. Flask B2C sayfasında AI'ya soru sor.
3. Lead formunu doldurup kaydet.
4. Flask B2B panelini açıp yeni lead'i göster.
5. Kodda `database.py`, `ai_service.py`, `routes.py` ve `create_app()` sınırlarını göster.
6. Render `/health` endpoint'ini göster.
7. `api-client.js`, göreli API yolları, `.env`, parametrik SQL ve hata yönetimi kararlarını kısaca açıkla.

**Tamamlanma kriteri:** Dört teslim çıktısı hazırdır: GitHub, B2C ve B2B arayüzlerini içeren Render URL, README ve kısa demo.

## 4. Önerilen 10 günlük takvim

| Gün | Faz | Beklenen çıktı |
|---:|---|---|
| 1 | Faz 0–1 | Ortam, proje iskeleti ve config |
| 2 | Faz 2 | SQLite veri katmanı ve testleri |
| 3 | Faz 3 | AI servis katmanı ve mock testleri |
| 4 | Faz 3 ve 6 | Gerçek Groq bağlantısı |
| 5 | Faz 4 | REST API endpoint'leri |
| 6 | Faz 5 | Application factory, CORS ve health |
| 7 | Faz 6 | Backend entegrasyon ve hata yolu testleri |
| 8 | Faz 7–8 | Flask B2C ve B2B arayüzleri |
| 9 | Faz 9 | GitHub, tek Render servisi ve production E2E |
| 10 | Faz 10 | README, güvenlik kontrolü ve demo |

## 5. Faz bağımlılıkları

```text
Faz 0
  -> Faz 1
      -> Faz 2
      -> Faz 3
          -> Faz 4
              -> Faz 5
                  -> Faz 6
                      -> Faz 7
                      -> Faz 8
                          -> Faz 9
                              -> Faz 10
```

Faz 2 ve Faz 3, proje iskeleti tamamlandıktan sonra teknik olarak paralel ilerleyebilir. Ancak API fazına geçmeden önce ikisinin de test kapısını geçmesi gerekir.

## 6. Definition of Done

Proje ancak aşağıdaki koşulların tamamı sağlandığında bitmiş kabul edilir:

- [ ] Klasör yapısı ve katman sorumlulukları teknik sözleşmeye uygun.
- [ ] Tüm otomatik testler geçiyor.
- [ ] `/health` production ortamında `200` döndürüyor.
- [ ] Sohbet endpoint'i gerçek veya demo modunda güvenli cevap veriyor.
- [ ] AI servis hataları `503` olarak dönüyor.
- [ ] Geçerli lead `201` ile kaydediliyor.
- [ ] Lead listesi en yeniden eskiye doğru dönüyor.
- [ ] Flask/Jinja B2C sayfası üzerinden sohbet ve lead kaydı çalışıyor.
- [ ] Flask/Jinja B2B panelinde kayıtlar görünüyor.
- [ ] Frontend aynı-origin ve göreli `/api/*` yollarıyla çalışıyor.
- [ ] HTML, CSS, HTTP client ve DOM davranışı ayrı sorumluluklarda tutuluyor.
- [ ] Sayfalar responsive, klavye ile kullanılabilir ve temel erişilebilirlik kontrollerini geçiyor.
- [ ] `.env` ve secret değerler repoda bulunmuyor.
- [ ] Render SQLite persistence davranışı test edilmiş ve sonucu belgelenmiş.
- [ ] README ile proje temiz bir ortamda kurulabiliyor.
- [ ] Geliştirici her katmanın neden ayrı olduğunu açıklayabiliyor.

## 7. MVP sonrası backlog

Bu maddeler ana teslim tamamlandıktan sonra değerlendirilecektir:

- Dashboard sayfası ve API için gerçek kimlik doğrulama ve rol tabanlı yetki
- Sohbet endpoint'i için rate limiting
- SQLite'tan PostgreSQL'e geçiş
- Lead filtreleme, arama ve durum yönetimi
- Merkezi structured logging ve hata izleme
- CI üzerinde test/lint kontrolü
- E-posta veya CRM entegrasyonu
- RAG ve kontrollü bilgi tabanı
