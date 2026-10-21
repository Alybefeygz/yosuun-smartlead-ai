<div align="center">

# Yosuun SmartLead AI

**Wix sitesine hizmet veren yapay zekâ asistanı ve lead yönetimi API'si**

*"Sen hayatını yaşa, e-ticareti Yosuun halletsin."*

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-veri%20katmanı-003B57?logo=sqlite&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4)
![Tests](https://img.shields.io/badge/testler-116%20geçti-7CF56A)
![Render](https://img.shields.io/badge/deploy-Render-46E3B7?logo=render&logoColor=white)

[Wix sitesi](https://ygzefealyb.wixsite.com/yosuun-smartlead) ·
[Kurulum](#-yerel-kurulum) ·
[API](#-api) ·
[Güvenlik](#-güvenlik-kararları)

</div>

---

## 📌 Proje hakkında

Yosuun SmartLead AI, Wix üzerinde yayınlanan Yosuun sitesinin backend'idir. Ziyaretçilerin Yosuun hakkında yapay zekâ destekli yanıtlar almasını, iletişim talebi bırakmasını ve yöneticinin bu talepleri listelemesini sağlayan Flask tabanlı bir JSON API'sidir.

Arayüz tamamen Wix'tedir; bu servis HTML sayfası sunmaz. Wix'in backend kodu (`backend/smartlead.web.js`) `wix-fetch` ile bu API'ye sunucudan sunucuya istek atar. AI anahtarı tanımlanmadığında sohbet güvenli bir demo cevabı döndürür.

| Kullanıcı | Ne yapar? | Wix tarafı | API |
|---|---|---|---|
| **Ziyaretçi (B2C)** | AI asistana soru sorar | Ana sayfa | `POST /api/sohbet` |
| **Ziyaretçi (B2C)** | İletişim bilgisini bırakır | `/iletisim` | `POST /api/leads` |
| **Yönetici (B2B)** | Giriş yapar, lead'leri listeler | Admin sayfaları | `POST /api/admin/token`, `GET /api/leads` |

## 📑 İçindekiler

- [Özellikler](#-özellikler)
- [Teknoloji yığını](#-teknoloji-yığını)
- [Mimari](#-mimari)
- [Yerel kurulum](#-yerel-kurulum)
- [Environment değişkenleri](#-environment-değişkenleri)
- [API](#-api)
- [Testler](#-testler)
- [Render deployment](#-render-deployment)
- [Güvenlik kararları](#-güvenlik-kararları)
- [AI bilgi kaynağını güncelleme](#-ai-bilgi-kaynağını-güncelleme)
- [Bilinen sınırlamalar](#-bilinen-sınırlamalar)

## ✨ Özellikler

**Yapay zekâ asistanı**
- Küratörlü bilgi dokümanına dayanan Türkçe Yosuun AI asistanı
- Bilgi dokümanını parçalamadan modele veren basit RAG akışı
- Niyet sınıflandırması veya retrieval puanlaması olmadan doğrudan AI cevabı
- Hazır FAQ cevabı kullanmadan her normal soruda AI üretimi
- Sınırlı ve doğrulanmış sohbet geçmişi
- AI anahtarı yoksa çökmeyen demo modu

**Lead yönetimi**
- İsim, telefon ve isteğe bağlı mesaj ile lead oluşturma
- Lead'leri en yeniden eskiye döndüren korumalı liste endpoint'i
- SQLite veri katmanı ve parametrik sorgular

**Güvenlik ve kalite**
- Parola hash'i ve imzalı, süreli bearer token ile tek-admin yetkilendirme
- Ortak JSON hata zarfı, istek boyutu ve alan uzunluğu sınırları
- 116 otomatik test

## 🧰 Teknoloji yığını

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.9+, Flask |
| Veritabanı | SQLite |
| Arayüz | Wix (Velo backend modülü + `wix-fetch`) |
| Yapay zekâ | Gemini (`gemini-2.5-flash`), OpenAI uyumlu Chat Completions API üzerinden |
| Sunucu | Gunicorn |
| Test | Pytest |
| Yayın | Render |

### Öğrenci yönergesine uyarlamalar

Proje, SmartLead AI öğrenci yönergesinin backend mimarisini korur. Teslimde yanlış anlaşılmayı önlemek için iki noktanın altını çizmek gerekir:

- Wix istekleri tarayıcıdan değil Wix backend'inden gönderildiği için CORS açılmaz. Wix cookie session taşıyamadığından yönetici yetkisi bearer token ile verilir.
- Yönergedeki Groq yerine Gemini kullanılır: Groq'un ücretsiz planındaki dakikalık token sınırı (8.000 TPM), bilgi dokümanının tamamı her istekte gönderildiği için dakikada yalnızca 2–3 soruya izin veriyordu. Servis OpenAI uyumlu her sağlayıcıyla çalışır; sağlayıcı `AI_API_URL`, `AI_API_KEY` ve `AI_MODEL` ile değiştirilir.

## 🏗️ Mimari

```text
Wix sayfası (tarayıcı)
  └── Wix backend (smartlead.web.js, wix-fetch)
        └── Render: Flask API
              ├── /api/sohbet       -> AIService
              │                        ├── KnowledgeService -> dokümanın tamamı
              │                        └── Gemini -> tek AI cevabı
              ├── /api/leads        -> database -> SQLite
              ├── /api/admin/token  -> auth (imzalı token)
              └── /health
```

### Sohbet isteğinin yolculuğu

```text
Ziyaretçi mesajı
  → Wix sayfası + backend     (POST /api/sohbet)
  → routes.py                 (JSON doğrulama, hız sınırı)
  → ai_service.py             (sistem prompt'u + bilgi dokümanı + geçmiş)
  → Gemini API                (cevap üretimi)
  → routes.py                 ({"basari": true, "cevap": "..."})
  → Wix sayfası               (cevabı gösterir)
```

### Dosya sorumlulukları

| Dosya | Sorumluluk |
|---|---|
| `app/__init__.py` | Application factory, health endpoint'i ve ortak hata yönetimi |
| `app/auth.py` | Yönetici token'ı, bearer doğrulaması ve deneme sınırı |
| `app/responses.py` | Ortak JSON hata zarfı |
| `app/routes.py` | `api` Blueprint'i, HTTP doğrulama, servis çağrısı ve response mapping |
| `app/database.py` | Tüm SQLite bağlantıları ve SQL sorguları |
| `app/services/ai_service.py` | Tam bilgi dokümanıyla prompt oluşturma, AI sağlayıcı çağrısı ve demo modu |
| `app/services/knowledge_service.py` | Markdown bilgi dokümanını tek parça okuyup bellekte tutma |
| `app/services/rate_limiter.py` | Public sohbet endpoint'i için process-local hız sınırı |
| `knowledge/yosuun_mvp.md` | AI'nin her istekte tamamını kullandığı kısa bilgi dokümanı |
| `config.py` | Environment tabanlı tek yapılandırma kaynağı |

### Klasör yapısı

```text
yosuun-smartlead-ai/
├── app/
│   ├── __init__.py          # create_app()
│   ├── auth.py
│   ├── database.py
│   ├── responses.py
│   ├── routes.py
│   ├── services/
│   │   ├── ai_service.py
│   │   ├── knowledge_service.py
│   │   └── rate_limiter.py
├── knowledge/
│   └── yosuun_mvp.md        # AI bilgi kaynağı
├── tests/
├── config.py
├── run.py
├── requirements.txt         # production bağımlılıkları
└── requirements-dev.txt     # + pytest
```

## 🚀 Yerel kurulum

```bash
git clone https://github.com/Alybefeygz/yosuun-smartlead-ai.git
cd yosuun-smartlead-ai

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
python run.py
```

API varsayılan olarak `http://127.0.0.1:5000` adresinde çalışır. Hızlı kontrol:

```bash
curl http://127.0.0.1:5000/health
curl -X POST http://127.0.0.1:5000/api/sohbet \
  -H "Content-Type: application/json" \
  -d '{"mesaj": "Yosuun nedir?"}'
```

Gerçek AI yanıtları için `.env` dosyasındaki `AI_API_KEY` değerine Google AI Studio'dan aldığınız Gemini anahtarını yazın. Bu dosya Git tarafından yok sayılır; gerçek anahtarları hiçbir zaman commit etmeyin.

Yönetici parolasını düz metin olarak kaydetmeyin. Güçlü bir PBKDF2 hash'i üretip `.env` içindeki `ADMIN_PASSWORD_HASH` alanına ekleyin:

```bash
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Yönetici parolası: '), method='pbkdf2:sha256:600000'))"
```

## ⚙️ Environment değişkenleri

| Değişken | Gerekli | Varsayılan / açıklama |
|---|---:|---|
| `FLASK_ENV` | Production'da evet | `development`; production için `production` |
| `SECRET_KEY` | Production'da evet | Uzun ve rastgele bir secret |
| `ADMIN_USERNAME` | Production'da evet | Yönetici kullanıcı adı |
| `ADMIN_PASSWORD_HASH` | Production'da evet | Düz parola değil, PBKDF2 hash değeri |
| `ADMIN_TOKEN_MAX_AGE_SECONDS` | Hayır | `1800`; Wix'e verilen token'ın ömrü |
| `DATABASE_URL` | Hayır | `instance/yosuun.sqlite3` |
| `AI_API_KEY` | Gerçek AI için evet | Boşsa demo modu kullanılır |
| `AI_API_URL` | Hayır | Gemini'nin OpenAI uyumlu adresi |
| `AI_MODEL` | Hayır | `gemini-2.5-flash` |
| `AI_REASONING_EFFORT` | Hayır | `none`; Gemini 2.5 Flash'ın düşünme adımını kapatır, boşsa gönderilmez |
| `AI_TIMEOUT_SECONDS` | Hayır | `20` |
| `AI_HISTORY_MAX_MESSAGES` | Hayır | `20` |
| `AI_HISTORY_MAX_CHARS` | Hayır | `8000` |
| `AI_TEMPERATURE` | Hayır | `0.3`; daha tutarlı kurumsal cevaplar |
| `AI_MAX_COMPLETION_TOKENS` | Hayır | `500` |
| `KNOWLEDGE_BASE_PATH` | Hayır | `knowledge/yosuun_mvp.md` |
| `CHAT_RATE_LIMIT_REQUESTS` | Hayır | Pencere başına `10` sohbet isteği |
| `CHAT_RATE_LIMIT_WINDOW_SECONDS` | Hayır | `60` saniye |
| `LEAD_RATE_LIMIT_REQUESTS` | Hayır | Pencere başına `5` lead kaydı |
| `LEAD_RATE_LIMIT_WINDOW_SECONDS` | Hayır | `600` saniye |
| `WIX_SHARED_SECRET` | Hayır | Wix Secrets Manager'daki değerle aynı; boşsa limitler IP'ye göre |
| `WIX_CHAT_RATE_LIMIT_REQUESTS` | Hayır | Tüm Wix ziyaretçileri için pencere başına toplam `60` sohbet isteği |
| `MAX_CONTENT_LENGTH` | Hayır | `65536` byte |
| `BUSINESS_CONTEXT` | Hayır | Uygulamadaki varsayılan Yosuun sistem bağlamı |

## 🔌 API

Tüm API cevapları `basari` alanını içerir.

| Metot | Yol | Yetki | Açıklama |
|---|---|---|---|
| `POST` | `/api/sohbet` | Herkese açık (hız sınırlı) | AI asistandan cevap alır |
| `POST` | `/api/leads` | Herkese açık | Yeni iletişim talebi oluşturur |
| `POST` | `/api/admin/token` | Herkese açık (giriş limiti) | Yönetici bilgileriyle kısa ömürlü token alır |
| `GET` | `/api/leads` | Bearer token | Lead listesini döndürür |
| `GET` | `/health` | Herkese açık | Servis sağlık kontrolü |

### Sohbet

`POST /api/sohbet`

```json
{
  "mesaj": "Yosuun stok yönetiminde nasıl yardımcı olur?",
  "gecmis": [
    {"role": "user", "content": "Merhaba"},
    {"role": "assistant", "content": "Merhaba, nasıl yardımcı olabilirim?"}
  ]
}
```

Başarılı cevap:

```json
{"basari": true, "cevap": "..."}
```

Kullanıcı mesajı, sınırlı sohbet geçmişi ve `knowledge/yosuun_mvp.md` dokümanının tamamı AI sağlayıcısına gönderilir. Nihai `cevap` doğrudan AI tarafından üretilir.

### Lead oluşturma

`POST /api/leads`

```json
{
  "isim": "Ada Lovelace",
  "telefon": "+90 555 000 00 00",
  "mesaj": "Ürün hakkında görüşmek istiyorum."
}
```

Başarılı cevap `201 Created` durum koduyla döner:

```json
{"basari": true, "mesaj": "İletişim bilgileriniz kaydedildi."}
```

### Yönetici token'ı

`POST /api/admin/token`

Wix'in yönetici sayfaları lead listesini okumadan önce bu endpoint'ten token alır.

```json
{"kullanici_adi": "admin", "parola": "..."}
```

Başarılı cevap:

```json
{"basari": true, "token": "...", "sure_saniye": 1800}
```

Token `SECRET_KEY` ile imzalanır, `ADMIN_TOKEN_MAX_AGE_SECONDS` (varsayılan 30 dakika) kadar geçerlidir ve yönetici parolası değişince geçersiz olur. Tekrarlanan hatalı denemeler geçici olarak engellenir (`401 AUTH_FAILED`, `429 RATE_LIMITED`).

### Lead listesi

`GET /api/leads`

Bu endpoint `Authorization: Bearer <token>` başlığı gerektirir. Anonim istekler `401 AUTH_REQUIRED` alır.

```json
{
  "basari": true,
  "leads": [
    {
      "id": 1,
      "isim": "Ada Lovelace",
      "telefon": "+90 555 000 00 00",
      "mesaj": "Ürün hakkında görüşmek istiyorum.",
      "tarih": "2026-09-20 12:00:00"
    }
  ]
}
```

### Hata zarfı

Hata cevapları ortak bir zarf kullanır:

```json
{
  "basari": false,
  "hata": {"kod": "VALIDATION_ERROR", "mesaj": "..."}
}
```

## 🧪 Testler

```bash
python -m pytest -q
```

Proje; veritabanı, API, bilgi kaynağı, AI servisi, kimlik doğrulama ve yapılandırmayı denetleyen **116 otomatik test** içerir.

| Test dosyası | Kapsam |
|---|---|
| `tests/test_database.py` | SQLite sorguları ve veri katmanı |
| `tests/test_routes.py` | API sözleşmesi, doğrulama ve hata cevapları |
| `tests/test_ai_service.py` | Prompt oluşturma, AI sağlayıcı çağrısı, hata normalizasyonu, demo modu |
| `tests/test_knowledge_service.py` | Bilgi dokümanının okunması |
| `tests/test_auth.py` | Yetki sınırları ve güvenlik başlıkları |
| `tests/test_admin_token.py` | Token alma, doğrulama, süre ve deneme sınırı |
| `tests/test_client_identity.py` | Wix ziyaretçi kimliği ve ziyaretçi başına limitler |
| `tests/test_config.py` | Environment tabanlı yapılandırma |

Belirli bir katmanı çalıştırmak için örnek:

```bash
python -m pytest -q tests/test_database.py
```

## ☁️ Render deployment

1. Bu repoyu Render'da yeni bir Web Service'e bağlayın.
2. Build command olarak `pip install -r requirements.txt` kullanın.
3. Start command olarak `gunicorn run:app` kullanın.
4. Health check path değerini `/health` yapın.
5. Aşağıdaki production environment değişkenlerini tanımlayın:

```text
FLASK_ENV=production
SECRET_KEY=<uzun-rastgele-secret>
ADMIN_USERNAME=<yonetici-kullanici-adi>
ADMIN_PASSWORD_HASH=<pbkdf2-parola-hash-degeri>
AI_API_KEY=<gemini-api-anahtari>
AI_MODEL=gemini-2.5-flash
AI_TEMPERATURE=0.3
AI_MAX_COMPLETION_TOKENS=500
KNOWLEDGE_BASE_PATH=knowledge/yosuun_mvp.md
CHAT_RATE_LIMIT_REQUESTS=10
CHAT_RATE_LIMIT_WINDOW_SECONDS=60
DATABASE_URL=<kalici-disk-uzerindeki-sqlite-yolu>
```

> ⚠️ SQLite dosyasının deploy/restart sonrasında korunması gerekiyorsa `DATABASE_URL` mutlaka Render persistent disk üzerindeki bir yolu göstermelidir. Persistent disk kullanılmayan ortamlarda lead verileri ephemeral olabilir.

## 🔒 Güvenlik kararları

- `.env`, SQLite runtime dosyaları, sanal ortamlar ve cache çıktıları repoya alınmaz.
- SQL yalnızca `app/database.py` içinde ve `?` placeholder'larıyla çalışır.
- AI sağlayıcı çağrısı ve API anahtarı yalnızca backend tarafındadır.
- `GET /api/leads` imzalı, süreli ve parola değişince geçersizleşen bir bearer token ile korunur.
- Düz parola saklanmaz; Werkzeug doğrulamalı PBKDF2 hash'i kullanılır.
- Tekrarlanan başarısız token denemeleri geçici olarak sınırlandırılır; lead ve token cevapları cache'lenmez.
- MIME-sniffing ve (production'da) HSTS başlıkları uygulanır.
- İstemciden `system` rolü kabul edilmez; geçmiş mesaj sayısı ve karakter bütçesi sınırlıdır.
- Bilgi dokümanının tamamı yalnızca backend tarafından okunur ve AI sistem mesajına eklenir.
- Sistem prompt'u bilgi dokümanı içindeki talimat benzeri metinlerin yeni komut olarak yorumlanmamasını söyler.
- AI sağlayıcı timeout, ağ, HTTP, boş veya bozuk cevap hataları `AIServiceError` olarak normalize edilir ve API'den güvenli `503` cevabı döner.
- Public sohbet endpoint'i kayan pencere hız sınırıyla korunur. Wix'ten gelen isteklerde (`X-Wix-Secret` doğruysa) limit `X-Client-Id` ile ziyaretçi başına uygulanır, ayrıca tüm Wix trafiği için toplam bir limit vardır; diğer istekler IP'ye göre sınırlanır.
- Production hata cevapları traceback veya secret içermez.

## 📚 AI bilgi kaynağını güncelleme

AI cevaplarının çalışma kaynağı `knowledge/yosuun_mvp.md` dosyasıdır. Ürün, fiyat, entegrasyon veya iletişim bilgisi değiştiğinde bu dosyadaki ilgili bölüm ve `last_updated` alanı birlikte güncellenmelidir. Bilgi kaynağı secret, müşteri verisi veya yayınlanması istenmeyen kişisel veri içermemelidir.

Her değişiklikten sonra bilgi kaynağı ve AI servis testlerini çalıştırın:

```bash
python -m pytest -q tests/test_knowledge_service.py tests/test_ai_service.py
```

## 🚧 Bilinen sınırlamalar

- Kimlik doğrulama tek yönetici hesabına yöneliktir; kullanıcı yönetimi ve parola sıfırlama akışı yoktur.
- Login, sohbet ve lead hız sınırları process belleğindedir; birden fazla instance için Redis gibi ortak bir rate-limit deposu gerekir.
- Wix ziyaretçi kimliği tarayıcıda üretilir; kimliğini sıfırlayan biri kişisel limiti aşabilir ama Wix toplam limitini aşamaz.
- Render free tier uykudan uyanırken ilk istek, Wix backend'inin zaman aşımından uzun sürebilir.
- SQLite tek servisli MVP için uygundur; yatay ölçekleme için ortak bir veritabanına geçilmelidir.
- Bilgi dokümanının tamamı her AI isteğine eklendiği için dosyanın sağlayıcının token limitinin altında tutulması gerekir. Doküman ciddi ölçüde büyürse daha sonra chunking veya vektör arama eklenebilir.
- Filtreleme, arama, CRM aktarımı ve lead durum yönetimi kapsam dışıdır.

## 🔗 Bağlantılar

- GitHub: <https://github.com/Alybefeygz/yosuun-smartlead-ai>
- Wix sitesi: <https://ygzefealyb.wixsite.com/yosuun-smartlead>
- API: <https://yosuun-smartlead-ai.onrender.com>
