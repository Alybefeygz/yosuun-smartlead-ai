# Yosuun SmartLead AI

Yosuun SmartLead AI; ziyaretçilerin Yosuun hakkında yapay zekâ destekli yanıtlar almasını, iletişim talebi bırakmasını ve bu taleplerin tek bir yönetim ekranında görüntülenmesini sağlayan Flask tabanlı bir MVP'dir.

Uygulama tek servis olarak çalışır: Flask hem Jinja arayüzlerini ve statik dosyaları sunar hem de sohbet/lead API'lerini sağlar. Groq anahtarı tanımlanmadığında sohbet güvenli bir demo cevabı döndürür.

## Özellikler

- Türkçe Yosuun AI asistanı ve sınırlı sohbet geçmişi
- İsim, telefon ve isteğe bağlı mesaj ile lead oluşturma
- Lead'leri en yeniden eskiye sıralayan responsive dashboard
- Parola hash'i, CSRF ve oturum korumalı tek-admin yönetici girişi
- Aynı-origin, göreli `/api/*` istekleri
- SQLite veri katmanı ve parametrik sorgular
- Güvenli hata cevapları, istek boyutu ve alan uzunluğu sınırları
- Klavye kullanımını ve temel erişilebilirliği gözeten arayüzler
- 95 otomatik test

## Teknoloji yığını

- Python 3.9+
- Flask ve Jinja
- SQLite
- Vanilla JavaScript ve CSS
- Groq Chat Completions API
- Gunicorn
- Pytest

## Mimari

```text
Browser
  ├── /            -> B2C sohbet ve lead formu
  ├── /login       -> Yönetici kimlik doğrulaması
  ├── /dashboard   -> Korumalı B2B lead listesi
  └── /api/*       -> Flask route katmanı
                         ├── AIService -> Groq
                         └── database  -> SQLite
```

Başlıca dosya sorumlulukları:

| Dosya | Sorumluluk |
|---|---|
| `app/__init__.py` | Application factory, health endpoint'i ve ortak hata yönetimi |
| `app/auth.py` | Yönetici girişi, session, CSRF ve deneme sınırı |
| `app/routes.py` | HTTP parse, doğrulama, servis çağrısı ve response mapping |
| `app/database.py` | Tüm SQLite bağlantıları ve SQL sorguları |
| `app/services/ai_service.py` | Prompt oluşturma, Groq çağrısı ve demo modu |
| `app/static/js/api-client.js` | Frontend HTTP sözleşmesi |
| `app/static/js/home.js` | Sohbet, slider ve lead formu davranışları |
| `app/static/js/dashboard.js` | Lead listesinin güvenli DOM render işlemleri |
| `config.py` | Environment tabanlı tek yapılandırma kaynağı |

## Yerel kurulum

```bash
git clone https://github.com/Alybefeygz/yosuun-smartlead-ai.git
cd yosuun-smartlead-ai

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python run.py
```

Uygulama varsayılan olarak `http://127.0.0.1:5000` adresinde açılır:

- Ziyaretçi arayüzü: `http://127.0.0.1:5000/`
- Yönetim ekranı: `http://127.0.0.1:5000/dashboard`
- Yönetici girişi: `http://127.0.0.1:5000/login`
- Sağlık kontrolü: `http://127.0.0.1:5000/health`

Gerçek AI yanıtları için `.env` dosyasındaki `GROQ_API_KEY` değerini doldurun. Bu dosya Git tarafından yok sayılır; gerçek anahtarları hiçbir zaman commit etmeyin.

Yönetici parolasını düz metin olarak kaydetmeyin. Güçlü bir PBKDF2 hash'i üretip `.env` içindeki `ADMIN_PASSWORD_HASH` alanına ekleyin:

```bash
python -c "from getpass import getpass; from werkzeug.security import generate_password_hash; print(generate_password_hash(getpass('Yönetici parolası: '), method='pbkdf2:sha256:600000'))"
```

## Environment değişkenleri

| Değişken | Gerekli | Varsayılan / açıklama |
|---|---:|---|
| `FLASK_ENV` | Production'da evet | `development`; production için `production` |
| `SECRET_KEY` | Production'da evet | Uzun ve rastgele bir secret |
| `ADMIN_USERNAME` | Production'da evet | Yönetici kullanıcı adı |
| `ADMIN_PASSWORD_HASH` | Production'da evet | Düz parola değil, PBKDF2 hash değeri |
| `DATABASE_URL` | Hayır | `instance/yosuun.sqlite3` |
| `GROQ_API_KEY` | Gerçek AI için evet | Boşsa demo modu kullanılır |
| `AI_PROVIDER` | Hayır | `groq` |
| `GROQ_MODEL` | Hayır | `openai/gpt-oss-20b` |
| `AI_TIMEOUT_SECONDS` | Hayır | `20` |
| `AI_HISTORY_MAX_MESSAGES` | Hayır | `20` |
| `AI_HISTORY_MAX_CHARS` | Hayır | `8000` |
| `MAX_CONTENT_LENGTH` | Hayır | `65536` byte |
| `BUSINESS_CONTEXT` | Hayır | Uygulamadaki varsayılan Yosuun sistem bağlamı |

## API

Tüm API cevapları `basari` alanını içerir.

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

### Lead listesi

`GET /api/leads`

Bu endpoint geçerli bir yönetici session cookie'si gerektirir. Anonim istekler `401 AUTH_REQUIRED` alır.

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

Hata cevapları ortak bir zarf kullanır:

```json
{
  "basari": false,
  "hata": {"kod": "VALIDATION_ERROR", "mesaj": "..."}
}
```

## Testler

```bash
python -m pytest -q
```

Belirli bir katmanı çalıştırmak için örnek:

```bash
python -m pytest -q tests/test_database.py
```

## Render deployment

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
GROQ_API_KEY=<gercek-groq-anahtari>
AI_PROVIDER=groq
GROQ_MODEL=openai/gpt-oss-20b
DATABASE_URL=<kalici-disk-uzerindeki-sqlite-yolu>
```

SQLite dosyasının deploy/restart sonrasında korunması gerekiyorsa `DATABASE_URL` mutlaka Render persistent disk üzerindeki bir yolu göstermelidir. Persistent disk kullanılmayan ortamlarda lead verileri ephemeral olabilir.

## Güvenlik kararları

- `.env`, SQLite runtime dosyaları, sanal ortamlar ve cache çıktıları repoya alınmaz.
- SQL yalnızca `app/database.py` içinde ve `?` placeholder'larıyla çalışır.
- Groq çağrısı ve API anahtarı yalnızca backend tarafındadır.
- `/dashboard` ve `GET /api/leads` sunucu tarafında yönetici oturumuyla korunur.
- Düz parola saklanmaz; Werkzeug doğrulamalı PBKDF2 hash'i kullanılır.
- Login ve logout formları session-bound CSRF token kullanır.
- Production cookie'si `Secure`, `HttpOnly` ve `SameSite=Lax` olarak ayarlanır.
- Tekrarlanan başarısız girişler geçici olarak sınırlandırılır; hassas sayfalar cache'lenmez.
- CSP, clickjacking, MIME-sniffing, referrer ve HSTS güvenlik başlıkları uygulanır.
- Frontend kullanıcı verisini `textContent` ile render eder; `innerHTML` kullanmaz.
- İstemciden `system` rolü kabul edilmez; geçmiş mesaj sayısı ve karakter bütçesi sınırlıdır.
- Production hata cevapları traceback veya secret içermez.

## Bilinen sınırlamalar

- Kimlik doğrulama tek yönetici hesabına yöneliktir; kullanıcı yönetimi ve parola sıfırlama akışı yoktur.
- Login deneme sınırı process belleğindedir; birden fazla instance için Redis gibi ortak bir rate-limit deposu gerekir.
- Sohbet endpoint'inde rate limiting yoktur.
- SQLite tek servisli MVP için uygundur; yatay ölçekleme için ortak bir veritabanına geçilmelidir.
- Filtreleme, arama, CRM aktarımı ve lead durum yönetimi kapsam dışıdır.

## Bağlantılar

- GitHub: <https://github.com/Alybefeygz/yosuun-smartlead-ai>
- Canlı demo: <https://yosuun-smartlead-ai.onrender.com>

Ayrıntılı uygulama fazları için [`plan.md`](plan.md), teknik sözleşme için [`project_documents.md`](project_documents.md) dosyasına bakın.
