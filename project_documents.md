YOSUUN

SmartLead AI

Senior Seviye Teknik Mimari, Uygulama ve Teslim Planı

Python ile Ürün Geliştirme • 10 Günlük MVP • Flask + SQLite + Groq + Wix Velo + Render



Belgenin amacı — Bu doküman bir “kod örneği” değil; projeyi baştan sona uygulayacak kıdemli geliştirici veya kod üreten AI için teknik sözleşmedir. Yönergede zorunlu tutulan mimariyi korur, fakat uygulama kararlarını production-grade mühendislik disipliniyle netleştirir.

Alan

Değer

Proje adı

Yosuun SmartLead AI / Yosuun AI Lead Assistant

Teslim tipi

Çalışan MVP + GitHub + Render + Wix + README + kısa demo

Ana backend

Python 3.9+ / Flask

Veritabanı

SQLite — ödev zorunluluğu

AI sağlayıcı

Groq API / llama-3.1-8b-instant — yönergede belirtilen teslim yolu

Frontend

Wix Velo — iki yayınlanmış arayüz

Deploy

Render Web Service

Temel mimari prensip

Separation of Concerns (SoC)

Doküman statüsü

Implementation-ready teknik plan

İçindekiler

1. Belgeyi Nasıl Okumalı?

2. Kaynak Yönergenin Değiştirilemez Sözleşmesi

3. Ürün Tanımı ve Yosuun’a Uyarlama

4. Hedefler, Kapsam ve Kapsam Dışı Konular

5. Fonksiyonel Gereksinimler

6. Kalite Nitelikleri ve Non-Functional Requirements

7. Sistem Bağlamı ve Üst Seviye Mimari

8. Backend Katmanları ve Paket Sınırları

9. Veri Modeli ve SQLite Tasarımı

10. REST API Sözleşmesi

11. AI Servisi ve Prompt Mimarisi

12. Wix Velo Frontend Mimarisi

13. Güvenlik Tasarımı

14. Hata Yönetimi ve Dayanıklılık

15. CORS ve Frontend–Backend Bağlantı Modeli

16. Deployment ve Ortam Yönetimi

17. Logging, Gözlemlenebilirlik ve Operasyon

18. Test Stratejisi

19. Kod Kalitesi ve Geliştirme Standartları

20. Git, Branch ve CI Yaklaşımı

21. 10 Günlük Uygulama Planı

22. Acceptance Criteria / Definition of Done

23. Puanlama Kriterlerine Doğrudan Eşleme

24. Riskler ve Teknik Borç Yönetimi

25. README ve Demo Taslağı

26. AI Kodlayıcı İçin Uygulama Sözleşmesi

Ek A. Önerilen Dosya Ağacı

Ek B. API Örnekleri

Ek C. Kaynak İzlenebilirlik Matrisi

1. Belgeyi Nasıl Okumalı?

Bu doküman üç seviyeli karar yapısı kullanır. Böylece ödev yönergesine sadakat ile kıdemli mühendislik kararları birbirine karışmaz.

Etiket

Anlamı

Uygulamadaki etkisi

YÖNERGE ZORUNLULUĞU

PDF’te açıkça talep edilen şart.

Değiştirilmez. Örneğin Flask, SQLite, Wix Velo, dosya ayrımı, .env gizliliği.

SENIOR TASARIM KARARI

Yönergenin izin verdiği alanda kaliteyi yükselten karar.

Uygulamanın profesyonel, test edilebilir ve anlaşılır olmasını sağlar.

OPSİYONEL HARDENING

MVP sonrası veya süre kalırsa eklenebilecek iyileştirme.

Ödev teslimini riske atmadan güvenlik, gözlemlenebilirlik veya UX’i artırır.



Ana ilke — Karmaşıklık uğruna “enterprise cosplay” yapılmayacak. Senior kalite; gereksiz katman sayısı değil, sınırların netliği, sözleşmelerin açık olması, hata yollarının düşünülmesi, test edilebilirlik ve güvenli varsayılanlarla ölçülür.

2. Kaynak Yönergenin Değiştirilemez Sözleşmesi

SmartLead AI yönergesi bu projeyi yeniden kullanılabilir bir iskelet olarak tanımlar: ziyaretçi AI ile konuşur, lead bırakır; işletme sahibi kayıtları panelden görür. Konu/marka değişebilir fakat mimari yapı ve katman sorumlulukları korunmalıdır.

Zorunlu alan

Yönerge beklentisi

Bu projedeki karşılığı

Backend

Python + Flask

Flask application factory ile modüler backend

Veritabanı

SQLite

Lead kayıtları için SQLite, SQL sadece database.py içinde

AI

Groq API

AI çağrıları yalnız app/services/ai_service.py içinde

Frontend

Wix Velo

Karşılama + yönetim paneli; wix-fetch ile REST çağrıları

SoC

Her dosya tek sorumluluk

config/database/routes/services sınırları ihlal edilmeyecek

Secrets

.env; GitHub’a yüklenmez

GROQ_API_KEY ve SECRET_KEY environment üzerinden

SQL güvenliği

? placeholders

Parametreli sorgular zorunlu

Hata yönetimi

try-except + güvenli JSON

Dış servis sınırlarında kontrollü exception mapping

Deploy

GitHub + Render

Render Web Service + gunicorn run

Teslim

5 çıktı

GitHub, Render URL, Wix URL, README, kısa demo



Kritik puan gerçeği — Değerlendirmenin en yüksek ağırlığı mimaridir (%30). Çalışırlık %25; kod kalitesi %15; güvenlik %10; hata yönetimi %10; yayın + sunum %10. Bu nedenle “çok özellik” yerine doğru sınırlar ve uçtan uca çalışırlık önceliklidir.

3. Ürün Tanımı ve Yosuun’a Uyarlama

Proje iskeleti Yosuun markasına uyarlanacaktır. Nihai ürün; Yosuun hakkında bilgi veren, e-ticaret operasyon ihtiyaçlarını konuşma üzerinden keşfeden, uygun kullanıcıyı iletişim bırakmaya yönlendiren ve bu lead’leri Yosuun tarafındaki basit bir yönetim ekranında görünür kılan bir AI lead assistant olacaktır.

Boyut

Karar

Ürün adı

Yosuun SmartLead AI / kullanıcıya görünen isim: Yosuun AI Asistan

Ziyaretçi değeri

Yosuun’un ürün, stok, rakip ve operasyon otomasyonu yetenekleri hakkında hızlı, bağlama uygun cevap

İş değeri

İlgili ziyaretçiyi kaybedilmeden lead’e dönüştürmek ve yönetim panelinde toplamak

Ana CTA

“Bilgilerimi bırak / Yosuun ekibi benimle iletişime geçsin”

Toplanan minimum veri

isim, telefon, mesaj; tarih otomatik

İletişim tonu

Sade, teknolojik, güven veren, genç ve samimi

Marka mesajı

“Sen hayatını yaşa, e-ticareti Yosuun halletsin.”

Önerilen ziyaretçi akışı:

Ziyaretçi Wix karşılama sayfasına gelir.

Yosuun AI’ya e-ticaret operasyonu veya Yosuun özellikleri hakkında soru sorar.

Wix Velo, mesajı ve izin verilen konuşma geçmişini POST /api/sohbet ile Flask backend’e yollar.

Backend doğrular, AIService’e delege eder; AIService BUSINESS_CONTEXT + geçmiş + yeni mesaj ile Groq’a gider.

Yanıt Wix’te gösterilir. Kullanıcı ilgilenirse ad/telefon/mesaj formunu doldurur.

POST /api/leads lead’i SQLite’a kaydeder ve 201 döner.

Yönetim paneli GET /api/leads ile lead listesini çeker ve Wix Repeater üzerinde gösterir.

4. Hedefler, Kapsam ve Kapsam Dışı Konular

MVP’nin hedefi gerçek bir CRM veya Yosuun ana ürününün tamamını inşa etmek değildir. Hedef, yönergede istenen mimari becerileri çalışan bir ürün üzerinden kanıtlamaktır.

Kapsamda

Kapsam dışı / MVP sonrası

AI sohbet endpoint’i

Gerçek kullanıcı hesabı / auth sistemi

Lead oluşturma ve listeleme

Tam CRM pipeline, görev atama, e-posta otomasyonu

Wix B2C karşılama sayfası

Yosuun production web sitesine tam entegrasyon

Wix B2B lead paneli

RBAC, çoklu kullanıcı/rol yönetimi

Render üzerinde canlı Flask backend

Kubernetes, microservices, service mesh

SQLite

PostgreSQL migration — ödevden sonra

Basit konuşma geçmişi

Vector DB / RAG / uzun süreli memory



Scope guard — Senior yaklaşımın önemli bir parçası “neyi yapmayacağını” bilmektir. Bu MVP’de teknik gösteriş için Redis, Celery, Kafka, Docker Swarm veya mikroservis eklemek puan kazandırmaz; aksine teslim riskini artırır.

5. Fonksiyonel Gereksinimler

ID

Gereksinim

Kabul notu

FR-01

Karşılama sayfası açılabilmeli

GET /; Wix tarafında yayınlanmış B2C sayfa

FR-02

Ziyaretçi AI’ya soru sorabilmeli

POST /api/sohbet; mesaj zorunlu

FR-03

AI bağlama uygun Türkçe cevap vermeli

BUSINESS_CONTEXT + geçmiş + kullanıcı mesajı

FR-04

API anahtarı yoksa servis çökmeden demo mesajı dönmeli

AIService fallback

FR-05

Ziyaretçi ad ve telefon ile lead bırakabilmeli

POST /api/leads

FR-06

Lead kalıcı olarak SQLite’a yazılmalı

id, isim, telefon, mesaj, tarih

FR-07

Lead listesi en yeniden eskiye getirilebilmeli

GET /api/leads

FR-08

Yönetim paneli lead’leri gösterebilmeli

Wix Repeater, _id zorunlu

FR-09

Health endpoint canlılık dönmeli

GET /health

FR-10

Eksik/bozuk istekler uygun HTTP koduyla reddedilmeli

400 / 503 / 201 sözleşmesi

6. Kalite Nitelikleri ve Non-Functional Requirements

ID

Beklenti

NFR-01 Modülerlik

SQL yalnız database.py; AI yalnız ai_service.py; routes sadece orchestration.

NFR-02 Okunabilirlik

PEP 8’e yakın stil, anlamlı isimler, küçük fonksiyonlar, kritik yerlerde yorum.

NFR-03 Güvenlik

Secrets env’de; SQL parametrik; CORS allowlist; güvenli hata mesajı.

NFR-04 Test edilebilirlik

Katmanlar yan etkileri izole edecek; provider ve DB fonksiyonları ayrı test edilebilir.

NFR-05 Dayanıklılık

AI timeout/HTTP hatası Flask process’i çökertmeyecek; 503’e map edilecek.

NFR-06 Performans

MVP hacminde SQLite yeterli; endpoint’ler bloklayıcı uzun iş yapmayacak.

NFR-07 Gözlemlenebilirlik

Request sonucu, exception ve health bilgisi loglanmalı; secret/telefon tam değer loglanmamalı.

NFR-08 Taşınabilirlik

Tüm config environment üzerinden; local ve Render aynı kod tabanını kullanır.

7. Sistem Bağlamı ve Üst Seviye Mimari

Sistem iki deployment yüzeyinden oluşur: Wix Velo frontend ve Render üzerinde Flask backend. SQLite backend’in veri katmanıdır; Groq dış AI sağlayıcıdır. Tarayıcı doğrudan Groq’a veya SQLite’a erişmez.

[ Browser / Visitor ]
|
v
[ Wix Velo - B2C ] ---- POST /api/sohbet ----> [ Flask / Render ] ----> [ AIService ] ----> [ Groq ]
| |
+---- POST /api/leads -----------------+----> [ database.py ] ----> [ SQLite ]

[ Browser / Admin ]
|
v
[ Wix Velo - B2B ] ---- GET /api/leads -----> [ Flask / Render ] ----> [ database.py ] ----> [ SQLite ]

Bağımlılık yönü içe doğrudur: route katmanı servis/veri fonksiyonlarını çağırır; servis katmanı Flask route bilgisi bilmez; database katmanı AI’dan habersizdir. Bu, yönergenin SoC beklentisini doğrudan karşılar.

Sınır

İzin verilen bağımlılık

Yasak bağımlılık

routes.py

database fonksiyonları, ai_service, render_template, request/jsonify

Doğrudan SQL; doğrudan Groq requests.post

database.py

sqlite3, Flask app context/config gerektiği kadar

AIService, HTTP request nesnesi

ai_service.py

requests, config/BUSINESS_CONTEXT

sqlite3, Flask request, template

config.py

os, dotenv

Route veya DB mantığı

Wix Velo

HTTP API contract

DB dosyasına/doğrudan Groq’a erişim

8. Backend Katmanları ve Paket Sınırları

8.1 config.py — Configuration boundary

Görevi yalnızca konfigürasyon sağlamaktır. Import edildiğinde uygulama iş akışı başlatmamalı; DB’ye bağlanmamalı; HTTP çağrısı yapmamalıdır.

Config
SECRET_KEY
DATABASE_URL
GROQ_API_KEY
AI_PROVIDER
BUSINESS_CONTEXT
CORS_ORIGINS

DevelopmentConfig(Config): DEBUG = True
ProductionConfig(Config): DEBUG = False
config_by_name = {"development": DevelopmentConfig, "production": ProductionConfig}

Senior karar: env isimleri tek yerde normalize edilir. Virgülle ayrılmış CORS_ORIGINS gibi listeler config seviyesinde parse edilebilir; route katmanında env string’i parçalanmaz.

8.2 database.py — Persistence boundary

Tüm SQL bu modülde tutulur. Üst katmanlara sqlite cursor veya raw connection sızdırılmaz. Fonksiyonlar plain Python dict/list döndürür.

Fonksiyon

Sözleşme

get_db()

Uygulama/request bağlamında bağlantı üretir veya yeniden kullanır; row_factory ile sütun adına erişim sağlar.

init_db(app)

Uygulama bağlamında tabloyu idempotent biçimde CREATE TABLE IF NOT EXISTS ile hazırlar.

lead_ekle(isim, telefon, mesaj)

Parametreli INSERT yapar; oluşan kimlik veya başarı bilgisi döndürebilir.

tum_leadler()

ORDER BY tarih DESC, id DESC; JSON’a çevrilebilir kayıt listesi döndürür.

Senior karar: route içinde satır formatlama yapılmaması için DB katmanı record → dict dönüşümünü kendi sınırında tamamlar. Ancak HTTP status code seçimi database.py’ye konmaz.

8.3 services/ai_service.py — External AI boundary

Groq entegrasyonunun tamamı bu dosyadadır. requests.post, provider URL, auth header, model adı ve provider response parsing burada kalır.

Eleman

Sorumluluk

AIService

Provider ile konuşmak, message dizisini kurmak, cevabı normalize etmek

yanit_uret(mesaj, gecmis)

Public method; validate edilmiş mesaj ve geçmiş alır, string cevap döndürür

_build_messages(...)

system → history → new user message sırasını kurar

_call_provider(...)

requests.post ve timeout; HTTP/provider hata kontrolü

AIServiceError

Dış servis hatalarını route katmanına tek tip exception olarak taşır

ai_service = AIService()

Yönergeyle uyumlu tek servis örneği

8.4 routes.py — HTTP adapter / controller

Route fonksiyonları mümkün olduğunca ince tutulur: parse → validate → delegate → map response. Business logic veya provider detayları burada yer almaz.

request JSON
↓ parse / validate
service or database function
↓
normalized result
↓ map to JSON + HTTP status

8.5 app/__init__.py — Composition root

create_app() uygulamanın tek composition root’udur. Konfigürasyon seçimi, CORS, init_db, blueprint registration ve health route burada birleştirilir. Böylece import-time global side effect azaltılır ve testlerde farklı config ile app üretilebilir.

8.6 run.py — Process entrypoint

Sadece app = create_app() ve local development için __main__ guard içerir. Business logic yoktur. Render start command gunicorn run ile bu objeyi yükler.

9. Veri Modeli ve SQLite Tasarımı

9.1 Zorunlu tablo

CREATE TABLE IF NOT EXISTS leads (
id INTEGER PRIMARY KEY AUTOINCREMENT,
isim TEXT NOT NULL,
telefon TEXT NOT NULL,
mesaj TEXT,
tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



Yönerge uyumu — Bu şema yönergede verilen minimum alanları korur: id, isim, telefon, mesaj, tarih. İsteğe bağlı iş alanı eklenebilir; ancak MVP’de gereksiz kolon eklememek önerilir.

9.2 Veri doğrulama ilkeleri

isim: trim sonrası boş olamaz; makul maksimum uzunluk uygulanır (ör. 100).

telefon: trim sonrası boş olamaz; server-side normalization aşırı karmaşıklaştırılmadan yapılır. Kullanıcının ham girdisi SQL’e string interpolation ile asla eklenmez.

mesaj: opsiyonel; boşsa null/empty kabul politikası tek tip olmalıdır. Maksimum uzunluk ör. 2000 karakterle sınırlandırılabilir.

tarih: client’tan kabul edilmez; server/DB üretir.

id: client tarafından gönderilmez.

9.3 Hosting/persistence riski

SQLite tek dosyalı DB olduğu için deployment ortamındaki filesystem davranışı kritik bir tasarım riskidir. Yönerge SQLite kullanımını zorunlu tuttuğundan teslimde SQLite korunur; fakat canlı ortamda veri dosyasının yeniden deploy/restart sonrası kalıcılığı ayrıca test edilmelidir. Platformda kalıcı disk/volume gerekiyorsa deployment ayarıyla çözülür; bu mümkün değilse demo verisinin ephemeral olabileceği README’de açıkça belirtilir. Bu, yönergeyi değiştirmeden operasyonel gerçeği yönetir.

10. REST API Sözleşmesi

API contract frontend ve backend arasında “tek gerçek kaynak” kabul edilir. Wix’te kullanılan alan adları backend ile harf harfine aynı olmalıdır; yönerge bunu özellikle kritik olarak vurgular.

10.1 Ortak response zarfı

Başarılı:
{
"basari": true,
"veri": { ... }
}

Hatalı:
{
"basari": false,
"hata": {
"kod": "VALIDATION_ERROR",
"mesaj": "Kullanıcıya güvenli açıklama"
}
}

Yönerge yalnızca her API cevabında basari alanını zorunlu tutar; yukarıdaki veri/hata zarfı senior seviye tutarlılık için önerilen standardizasyondur.

Method

Path

Request

Status

Amaç

GET

/health

-

200

Sunucu canlılık kontrolü

GET

/

-

200

Flask template karşılama sayfası; Wix tesliminde asıl UI Wix olabilir

GET

/dashboard

-

200

Flask template dashboard; yönerge endpoint’i

POST

/api/sohbet

{mesaj, gecmis?}

200 / 400 / 503

AI cevabı

POST

/api/leads

{isim, telefon, mesaj?}

201 / 400 / 500

Lead oluşturur

GET

/api/leads

-

200 / 500

Tüm lead’leri newest-first döndürür

10.2 POST /api/sohbet

Request
{
"mesaj": "Ajans olarak 10 mağazayı yönetebilir miyim?",
"gecmis": [
{"role": "user", "content": "Yosuun nedir?"},
{"role": "assistant", "content": "Yosuun ..."}
]
}

200
{
"basari": true,
"cevap": "Evet, Yosuun ..."
}

Validation: mesaj string olmalı, trim sonrası boş olmamalı. Gecmis opsiyoneldir; yalnız user/assistant rolleri kabul edilir. System role frontend’den kabul edilmez; system prompt yalnız backend config’inden gelir.

10.3 POST /api/leads

Request
{
"isim": "Ayşe Yılmaz",
"telefon": "05xx xxx xx xx",
"mesaj": "Ajans paketleri hakkında bilgi almak istiyorum."
}

201
{
"basari": true,
"mesaj": "İletişim bilgileriniz kaydedildi."
}

10.4 GET /api/leads

200
{
"basari": true,
"leads": [
{
"id": 17,
"isim": "Ayşe Yılmaz",
"telefon": "05xx...",
"mesaj": "...",
"tarih": "2026-09-13 20:15:00"
}
]
}

Wix Repeater için client mapping sırasında her kayda string `_id` üretilir; backend DB id’si ayrı korunur.

11. AI Servisi ve Prompt Mimarisi

11.1 BUSINESS_CONTEXT

Yönergenin kişiselleştirme merkezi BUSINESS_CONTEXT’tir. Kodu Yosuun’a gömmek yerine marka bilgisi bu konfigürasyon metninde tutulur; böylece aynı iskelet başka işletmeye uyarlanabilir.

Sen Yosuun E-Ticaret Ekosistemi'nin yapay zekâ asistanısın.
Yosuun; e-ticaret markaları, satıcıları ve operasyon ekiplerinin ürün, stok,
rakip ve operasyon süreçlerini tek merkezden yönetmesine yardımcı olan
yapay zekâ destekli bir SaaS platformudur.

Görevin:

Yosuun hakkında açık, kısa ve doğru bilgi vermek.

Kullanıcının e-ticaret operasyon ihtiyacını anlamaya yardımcı olmak.

Bilmediğin bir özelliği varmış gibi söylememek.

Uygun kullanıcıyı iletişim bilgisi bırakmaya yönlendirmek.

Türkçe, sade, profesyonel ve samimi konuşmak.

Hassas bilgi veya ödeme bilgisi istememek.

Ana marka yaklaşımı: “Sen hayatını yaşa, e-ticareti Yosuun halletsin.”

11.2 Message assembly

messages = [
{role: "system", content: BUSINESS_CONTEXT},
...validated_history,
{role: "user", content: current_message}
]

Senior karar: system prompt hiçbir zaman frontend’den alınmaz. Frontend history içinde role=system gönderse dahi reject edilir. History boyutu sınırlandırılır; örneğin son 10–20 mesaj veya karakter bütçesi. Bu hem maliyet hem prompt injection yüzeyini azaltır.

11.3 Provider çağrısı

Karar

Öneri

HTTP client

Yönerge gereği requests.post

Timeout

Mutlaka finite timeout (örn. 15–30 sn); sonsuz bekleme yok

Model

llama-3.1-8b-instant — yönergedeki model

API key

Authorization header; yalnız server env

Non-2xx

AIServiceError’a dönüştür

Malformed provider JSON

AIServiceError; kullanıcıya internal detay sızdırma

No key

Demo modu mesajı; process crash etmez

11.4 AI güvenlik ve doğruluk sınırı

AI, Yosuun’da olmayan ürün/entegrasyon/özellikleri uydurmamalıdır.

AI kullanıcıdan kart, şifre, API key gibi hassas sırlar istememelidir.

Lead toplama CTA’sı agresif spam tonuna dönüşmemelidir.

Prompt injection denemeleri BUSINESS_CONTEXT’i değiştirmemeli; sistem rolü backend tarafından sabit tutulmalıdır.

Provider hatası olduğunda teknik stack trace kullanıcıya gösterilmemelidir.

12. Wix Velo Frontend Mimarisi

Wix, bu ödevde yalnız “görsel vitrin” değil; teslim şartı olan aktif frontend katmanıdır. İki sayfa yayınlanacak ve Render API’ye bağlanacaktır.

12.1 B2C Karşılama Sayfası

Bileşen

Önerilen ID

Davranış

Mesaj input

#messageInput

Kullanıcı sorusu

Sor butonu

#askButton

POST /api/sohbet

Cevap alanı

#answerText

AI cevabını gösterir

İsim input

#nameInput

Lead adı

Telefon input

#phoneInput

Lead telefon

Mesaj/ilgi alanı

#leadMessageInput

Opsiyonel lead notu

Kaydet butonu

#saveLeadButton

POST /api/leads

Durum alanı

#statusText

Loading/success/error feedback

UX yönergesi: Z-Pattern; logo sol üst, sohbet sağ ağırlıklı, lead formu gözün doğal akışında alt bölgede; sohbet kartında glassmorphism. Yosuun renk sistemi #78F666 + siyah + beyaz kullanılmalıdır.

12.2 B2B Yönetim Paneli

Bileşen

Önerilen ID

Davranış

Repeater

#leadRepeater

GET /api/leads sonucunu satırlar halinde gösterir

İsim

#leadName

En önemli kolon; F-pattern gereği solda

Telefon

#leadPhone

Lead telefonu

Mesaj

#leadMessage

İlgi / not

Tarih

#leadDate

Kayıt zamanı

Refresh

#refreshButton

Listeyi manuel yeniler

Status

#dashboardStatus

Loading/error

Wix Repeater her obje için `_id` beklediğinden GET sonucu client-side map edilir: `_id: String(lead.id)`. `$item` ile satır içi binding yapılır.

12.3 Wix API client ilkesi

Endpoint URL’leri sayfa kodu içinde dağınık hard-code edilmemelidir. Tek bir `API_BASE_URL` sabiti veya ortak helper kullanılmalıdır. Local testte localhost; canlıda Render URL kullanılır. Request ve response alan adları backend contract ile birebir eşleşir.

const API_BASE_URL = "https://<render-service>.onrender.com";

// concept only
async function apiPost(path, payload) {
// wix-fetch, JSON headers, status check, normalized error
}

async function apiGet(path) {
// wix-fetch, status check, normalized error
}



Not — Yönerge “wix-fetch” kullanımını ve iki yayınlanmış arayüzü açıkça ister. Kendi Angular/React frontend’i teknik olarak mümkün olsa da ödev teslim sözleşmesini tek başına karşılamaz.

13. Güvenlik Tasarımı

Bu proje eğitim MVP’si olsa da güvenlik puan kriteridir. Minimum güvenlik kontrolleri zorunlu kabul edilir.

Kontrol

Uygulama

Seviye

Secret management

.env local; Render Environment Variables; .env .gitignore içinde

Zorunlu

SQL injection

Tüm sorgularda ? placeholder + params

Zorunlu

CORS

Sadece yayınlanmış Wix origin(ler)i + local dev originleri

Zorunlu

Input validation

Body type/required fields/max length

Senior karar

Error leakage

Stack trace ve provider body kullanıcıya dönmez

Zorunlu/Senior

Log privacy

Telefonun tamamını loglamama; API key asla loglanmaz

Senior karar

Rate limiting

Sohbet endpoint’inde temel limit, süre kalırsa

Opsiyonel hardening

Auth dashboard

Yönergede yok; Wix sayfa erişim kontrolü düşünülebilir

Opsiyonel / scope dışı

13.1 .gitignore minimum

.env
venv/
.venv/
__pycache__/
*.pyc
*.sqlite3
.DS_Store
.vscode/
.idea/

DB dosyasının repoya eklenip eklenmeyeceği teslim stratejisine göre seçilir. Güvenli varsayılan: runtime DB dosyasını commit etmemek; schema init_db ile kendiliğinden kurulur.

14. Hata Yönetimi ve Dayanıklılık

Hata yönetimi puanın %10’udur. “try-except her yere koymak” değil; exception’ı doğru sınırda yakalamak hedeflenir.

Hata

Nerede yakalanır

HTTP karşılığı

Kullanıcı mesajı

Eksik mesaj/isim/telefon

routes validation

400

Eksik veya geçersiz alanları düzeltin.

Groq timeout

AIService → AIServiceError; route map

503

AI servisine şu anda ulaşılamıyor.

Groq non-2xx / parse

AIService

503

AI servisi geçici olarak kullanılamıyor.

SQLite write/read error

database exception → route boundary

500

İşlem tamamlanamadı. Lütfen tekrar deneyin.

Beklenmeyen exception

Global/route safe fallback

500

Beklenmeyen bir hata oluştu.

Senior karar: Development ortamında ayrıntılı log; Production response’unda generic mesaj. Exception chaining/log stack trace server logunda kalır.

15. CORS ve Frontend–Backend Bağlantı Modeli

Wix tarayıcı kodu farklı origin’den Render API’ye gideceği için CORS doğru yapılandırılmalıdır. `*` kullanmak yerine allowlist tercih edilir.

CORS_ORIGINS=https://<your-wix-domain>,http://localhost:...

create_app():
origins = Config.CORS_ORIGINS
CORS(app, resources={r"/api/*": {"origins": origins}})

Wix site domain’i yayınlandıktan sonra gerçek origin environment’a eklenir. Preflight/OPTIONS davranışı canlı ortamda test edilir. Health endpoint için geniş CORS gerekmeyebilir; yalnız API scope’a CORS uygulamak daha kontrollüdür.

16. Deployment ve Ortam Yönetimi

16.1 Ortamlar

Ortam

Amaç

Config

Local development

Kodlama ve manuel test

DEBUG=True, local SQLite, local .env

Production / Render

Teslim edilen canlı backend

DEBUG=False, Render env vars, production CORS

16.2 Render deployment contract

Build command:
pip install -r requirements.txt

Start command:
gunicorn run

Environment variables (minimum):
FLASK_ENV=production
SECRET_KEY=<strong-secret>
GROQ_API_KEY=<gsk_...>
AI_PROVIDER=groq
CORS_ORIGINS=https://<wix-domain>
DATABASE_URL=<sqlite path>

Deploy sırası: GitHub public repo → Render Web Service → env vars → deploy → /health doğrulama → Wix API_BASE_URL’ini Render URL ile güncelleme → Wix publish → uçtan uca test.

16.3 Health check

GET /health
200
{
"basari": true,
"durum": "aktif"
}

Health check AI veya DB’ye pahalı çağrı yapmamalıdır. Amaç process’in ayakta olduğunu hızlı göstermek. İstenirse lightweight DB check opsiyonel readiness endpoint olarak ayrı düşünülebilir; MVP’de gerekli değildir.

17. Logging, Gözlemlenebilirlik ve Operasyon

Yönergede ayrı observability modülü istenmiyor; ancak canlı demo sırasında hata çözme kabiliyeti senior kaliteyi belirler.

Log olayı

Önerilen alanlar

Asla loglanmamalı

API request sonucu

method, path, status, duration_ms

GROQ_API_KEY

AI hata

provider, exception type, status if available

Provider auth header, tam prompt gerekiyorsa dikkat

Lead kayıt

lead id, success/fail

Telefonun tamamı, hassas kullanıcı verisi

Startup

environment, config names (secret values değil)

SECRET_KEY value

Python `logging` modülü yeterlidir. Structured JSON logging bu MVP için zorunlu değildir; fakat log mesajlarında component prefix ve request path bulunması debug süresini ciddi düşürür.

18. Test Stratejisi

Yönerge manuel kontrol noktaları verir. Senior plan bu kontrolleri üç katmana ayırır: unit, integration/API, end-to-end Wix.

18.1 Unit tests

Test alanı

Örnek

Config

.env değeri okunuyor; default değer güvenli

AI message assembly

system ilk, geçmiş ortada, current user son; frontend system role reddedilir

DB lead_ekle

parametreli INSERT ile kayıt eklenir

DB tum_leadler

newest-first döner

Validation helper

boş isim/telefon reddedilir

18.2 API integration tests

Senaryo

Beklenen

GET /health

200 + aktif

POST /api/sohbet boş mesaj

400

POST /api/sohbet AI mock success

200 + cevap

POST /api/sohbet AIServiceError

503

POST /api/leads valid

201 + DB row

POST /api/leads eksik telefon

400

GET /api/leads

200 + yeni kayıt listede

18.3 Manual E2E checklist

Render /health browser/curl ile 200 dönüyor.

Wix B2C sayfasında soru gönderiliyor; loading state gösteriliyor; AI cevabı geliyor.

Lead formunda invalid state kullanıcıya gösteriliyor.

Geçerli lead kaydediliyor ve success feedback geliyor.

Wix B2B panel yenilenince lead görünür.

Render loglarında secret görünmüyor.

GitHub’da .env görünmüyor.

Wix production origin ile CORS sorunsuz.

19. Kod Kalitesi ve Geliştirme Standartları

Python Komutları dokümanı temel Python kavramlarını hatırlatma kaynağıdır. Bu projede özellikle fonksiyonlar, sınıflar, sözlük/list yapıları ve try-except doğrudan kullanılacaktır. Kodun değerlendirmede açıklanabilmesi zorunlu olduğundan her satırın amacı anlaşılır olmalıdır.

Standart

Karar

İsimlendirme

Python’da snake_case; class PascalCase; env UPPER_SNAKE_CASE

Fonksiyon boyutu

Tek sorumluluk; route fonksiyonları kısa

Docstring

Public service fonksiyonları ve karmaşık yardımcılar

Yorum

“Ne yaptığını” değil, “neden bu kararın alındığını” açıklayan kritik yorumlar

Formatting

4 spaces; tutarlı stil; gereksiz one-liner kaçın

Type hints

Yönergede zorunlu değil; mümkünse service/helper imzalarında kullanılabilir

Magic values

Timeout/model/API URL config veya module constant

Imports

Katman bağımlılıklarını ihlal edecek circular import yok

20. Git, Branch ve CI Yaklaşımı

Ödev GitHub public repo ister. Tek geliştiricili 10 günlük MVP’de ağır GitFlow yerine basit ve temiz tarihçe tercih edilir.

Konu

Öneri

Default branch

main

Feature branch

feature/config, feature/database, feature/ai-service gibi kısa ömürlü branch’ler; süre azsa doğrudan main + anlamlı commit de kabul edilebilir

Commit dili

feat:, fix:, docs:, test:, chore: önekleri

Secret check

Push öncesi git status / git ls-files .env kontrolü

CI

Opsiyonel: pytest + basic lint GitHub Actions; teslimi geciktirmeyecekse

Örnek commit sırası:

chore: bootstrap flask project structure

feat: add environment based configuration

feat: implement sqlite lead repository

feat: add groq ai service

feat: expose chat and lead api routes

feat: wire application factory and cors

test: cover api error paths

docs: add setup and deployment guide

21. 10 Günlük Uygulama Planı

Gün

Odak

İş

Exit criteria

Öncesi

Ortam

Python 3.9+, Git, GitHub, Render, Wix, Groq; venv; smoke test

hello.py browser’da çalışıyor

1

Config

config.py, .env.example, .gitignore, requirements

env value import ediliyor

2

Database

SQLite schema + get_db/init_db/lead_ekle/tum_leadler

insert/list local test

3

AI Core

AIService, message builder, error type, demo mode

mock/provider request hazırlanıyor

4

AI Live

Groq gerçek bağlantı, timeout/error paths

Türkçe gerçek cevap

5

Routes

Blueprints + 5 endpoint contract

curl/Postman basic

6

Composition

create_app, CORS, /health, run.py

python run.py stabil

7

Backend QA

integration test + hata yolları + README draft

backend acceptance pass

8

Wix

B2C + B2B, wix-fetch, repeater mapping

local/canlı API bağlantısı

9

Deploy

GitHub public, Render deploy, env vars, Wix publish

production E2E pass

10

Polish

README, demo script, final checklist, security review

5 teslim çıktısı hazır

22. Acceptance Criteria / Definition of Done

Proje “kod bitti” olduğunda değil, aşağıdaki tüm maddeler sağlandığında Done kabul edilir:

Klasör yapısı yönerge mimarisine uyuyor.

database.py dışında SQL string’i bulunmuyor.

ai_service.py dışında Groq API çağrısı bulunmuyor.

routes.py yalnız parse/validate/delegate/map yapıyor.

.env Git indexinde yok ve GitHub’da görünmüyor.

requirements.txt temiz bir venv’de projeyi kurmaya yetiyor.

python run.py localde çalışıyor.

/health 200 dönüyor.

/api/sohbet gerçek veya demo modunda güvenli cevap veriyor; AI failure 503.

/api/leads POST 201 ile kayıt ekliyor; GET newest-first listeliyor.

Wix B2C sayfasında chat ve lead formu uçtan uca çalışıyor.

Wix B2B sayfasında Repeater lead’leri gösteriyor.

Render backend live.

README setup + env + run + deploy + endpoint bilgisini içeriyor.

Demo sırasında geliştirici her katmanın neden ayrı olduğunu açıklayabiliyor.

23. Puanlama Kriterlerine Doğrudan Eşleme

Kriter

Ağırlık

100’e yakın puan için somut kanıt

Mimari / SoC

%30

Dosya sınırları; SQL ve AI izolasyonu; thin routes; create_app composition root.

Çalışırlık

%25

Wix → Render → AI/SQLite uçtan uca; chat, lead save, lead list, health.

Kod Kalitesi

%15

Anlamlı isimler, küçük fonksiyonlar, açıklayıcı yorumlar, tutarlı response contract.

Güvenlik

%10

.env gizli; ? placeholders; CORS allowlist; input validation.

Hata Yönetimi

%10

AIServiceError; try-except dış sınırda; 400/503/500 güvenli JSON.

Yayın + Sunum

%10

Public GitHub, live Render, live Wix, kısa demo ve kod açıklama.



Stratejik sonuç — İlk 55 puan doğrudan mimari + çalışırlıktan gelir. Bu nedenle önce backend contract ve katman sınırları kilitlenmeli; UI cilası daha sonra yapılmalıdır.

24. Riskler ve Teknik Borç Yönetimi

Risk

Etkisi

Mitigasyon

Render/hosting filesystem kalıcılığı

SQLite verisi restart/deploy sonrası kaybolabilir

Persistence davranışını erken test et; gerekirse persistent storage kullan veya demo limitation belgele.

CORS origin hatası

Wix API’ye bağlanamaz

Wix production domain’i allowlist’e koy; preflight test.

Frontend/backend key mismatch

İstekler sessizce bozulur

Contract sabitle; mesaj/cevap, isim/telefon alanlarını tek listeyle doğrula.

Groq rate/availability

Chat 503 döner

Timeout + AIServiceError + kullanıcıya kibar fallback.

Secret leak

API key compromise

gitignore, GitHub kontrolü, sızıntıda key rotate.

Scope creep

10 günde deploy yetişmez

DoD dışı özellikleri backlog’a at.

AI hallucination

Marka yanlış bilgi verir

BUSINESS_CONTEXT guardrails; bilmediğinde kesin konuşmama.

Demo günü sürprizi

Canlı sistem çalışmaz

Demo öncesi smoke checklist + kayıtlı kısa backup walkthrough.

25. README ve Demo Taslağı

25.1 README minimum başlıkları

Proje özeti

Mimari ve dosya yapısı

Teknoloji yığını

Local kurulum

Environment variables / .env.example

Çalıştırma

API endpoint’leri

Wix bağlantısı

Render deployment

Güvenlik notları

Bilinen sınırlamalar

Demo linkleri

25.2 3–5 dakikalık demo akışı

30 sn — problem: Yosuun ziyaretçisi ürün hakkında hızlı bilgi ister; işletme nitelikli lead toplamak ister.

45 sn — Wix B2C: soru sor, AI cevabı göster.

30 sn — lead formu doldur ve kaydet.

30 sn — Wix B2B: yeni lead’i Repeater’da göster.

45 sn — GitHub klasör yapısını aç; database.py / ai_service.py / routes.py sınırlarını anlat.

30 sn — Render /health ve production URL göster.

30 sn — güvenlik: .env yok, SQL placeholder, CORS ve hata mapping anlat.

26. AI Kodlayıcı İçin Uygulama Sözleşmesi

Aşağıdaki bölüm, bu projeyi bir kodlama AI’sına verdiğinizde “senior seviye” davranmasını sağlamak için doğrudan kullanılabilecek çalışma sözleşmesidir. AI kodu tek seferde rastgele üretmek yerine modül modül, test kapılarıyla ilerlemelidir.

ROL
Sen bu projede senior Python/Flask backend engineer + integration engineer olarak çalışıyorsun.
Amaç “çalışıyor gibi görünen demo” değil; kaynak yönergeye birebir uyan, okunabilir, test edilebilir,
güvenli varsayılanlara sahip ve geliştiricinin sözlü olarak açıklayabileceği bir MVP üretmek.

DEĞİŞTİRİLEMEZ KURALLAR

Python + Flask + SQLite + Groq + Wix Velo + Render stack korunacak.

SQL yalnız app/database.py içinde.

Groq/API çağrıları yalnız app/services/ai_service.py içinde.

routes.py içinde SQL string, requests.post(Groq) veya business logic olmayacak.

config.py tüm environment ayarlarının tek kaynağı olacak.

.env asla repoya eklenmeyecek; .env.example secret içermeyecek.

SQL sorguları parametreli ? placeholder kullanacak.

AI dış servis hataları AIServiceError üzerinden route katmanında 503’e çevrilecek.

Eksik kullanıcı girdisi 400; başarılı lead oluşturma 201.

create_app application factory kullanılacak.

Her modül, bir sonraki modüle geçmeden önce kontrol noktasından geçirilecek.

ÇALIŞMA YÖNTEMİ

Önce mevcut dosya ağacını ve requirements.txt’i analiz et.

Her adımda yalnız o modül için gerekli dosyaları değiştir.

Değişiklik öncesi plan, değişiklik sonrası test komutu ve beklenen sonucu yaz.

Kodu gereksiz abstraction ile şişirme; fakat katman sınırlarını tavizsiz koru.

Hata durumlarını happy path kadar ciddiye al.

Secret veya gerçek API key’i hiçbir örnek çıktıda yazma.

Kullanıcı istemeden yönerge stack’ini FastAPI/PostgreSQL/React ile değiştirme.

Wix entegrasyonunda backend contract alan adlarını birebir kullan.

KOD KALİTESİ

Fonksiyonlar tek iş yapsın.

Değişken adları anlaşılır olsun.

Yorumlar “neden”i anlatsın.

Provider timeout finite olsun.

Server kullanıcıya raw exception/traceback döndürmesin.

Loglarda secret ve tam telefon gibi hassas veriler bulunmasın.

TEST GATE
Config -> DB -> AI -> Routes -> App Factory -> Backend Integration -> Wix -> Deploy sırası bozulmayacak.
Bir gate başarısızsa sonraki katmana geçme.

ÇIKTI
Her modül tamamlandığında: değişen dosyalar, nedenleri, test sonucu, kalan riskler ve sonraki adımı raporla.



AI kullanım notu — Yönergede akademik dürüstlük açıkça vurgulanır: hazır şablondan/AI’dan yararlansanız bile kodu açıklayamamak projeyi geçersiz kılabilir. Bu nedenle AI’nın ürettiği her modül geliştirici tarafından okunmalı, çalıştırılmalı ve neden o şekilde tasarlandığı anlaşılmalıdır.

Ek A. Önerilen Dosya Ağacı

yosuun-smartlead-ai/
├── run.py
├── config.py
├── requirements.txt
├── .env # local only, git ignored
├── .env.example # secret içermez
├── .gitignore
├── README.md
├── app/
│ ├── __init__.py
│ ├── database.py
│ ├── routes.py
│ ├── templates/
│ │ ├── index.html
│ │ └── dashboard.html
│ └── services/
│ ├── __init__.py
│ └── ai_service.py
└── tests/ # senior öneri; yönergede zorunlu değil
├── test_database.py
├── test_ai_service.py
└── test_routes.py

Not: `tests/` ve `.env.example` senior seviye ek öneridir. Yönergenin temel klasör ağacını bozmaz; tersine teslim edilebilirliği ve açıklanabilirliği artırır.

Ek B. API Örnekleri ve Curl Testleri

# Health
curl https://<render>/health

# Chat
curl -X POST https://<render>/api/sohbet \
-H "Content-Type: application/json" \
-d '{"mesaj":"Yosuun stok takibinde nasıl yardımcı olur?","gecmis":[]}'

# Lead create
curl -X POST https://<render>/api/leads \
-H "Content-Type: application/json" \
-d '{"isim":"Test Kullanıcı","telefon":"05550000000","mesaj":"Demo lead"}'

# Lead list
curl https://<render>/api/leads

Bu komutlar demo verisiyle çalıştırılmalı; gerçek kişisel veri kullanmak gerekmez.

Ek C. Kaynak İzlenebilirlik Matrisi

Kaynak gereksinimi

Kaynak yeri

Bu plandaki karşılığı

SmartLead yeniden kullanılabilir iskelet; konu kişiselleştirilir

Yönerge s.3–4

Bölüm 3, 11

SoC; SQL/AI ayrımı

Yönerge s.3–5

Bölüm 7–8

Config class ve env ayarları

Yönerge s.6

Bölüm 8.1, 16

SQLite lead fonksiyonları ve ? placeholder

Yönerge s.6–7

Bölüm 8.2, 9, 13

AIService + Groq + llama-3.1-8b-instant

Yönerge s.7

Bölüm 8.3, 11

5 endpoint + status codes + Blueprint

Yönerge s.8

Bölüm 10

create_app + /health + run.py

Yönerge s.8

Bölüm 8.5–8.6, 16.3

Backend test sequence

Yönerge s.9

Bölüm 18

Wix B2C/B2B + Z/F pattern + Repeater

Yönerge s.9

Bölüm 12

GitHub + Render commands + env

Yönerge s.10

Bölüm 16, 20

10 günlük plan

Yönerge s.10

Bölüm 21

5 teslim çıktısı + puanlama

Yönerge s.11

Bölüm 22–25

Python list/dict/function/class/exception temel referansı

Python Komutları.pdf

Bölüm 19 ve uygulama boyunca

Sonuç

Bu planın hedefi, yönergedeki basit öğrenci iskeletini “gereksiz ağırlaştırmadan” senior mühendislik kalitesine taşımaktır. Mimarinin gücü şu dört noktada görünmelidir: net sorumluluk sınırları, açık API sözleşmesi, güvenli hata/secret yönetimi ve tekrarlanabilir test-deploy akışı. Bunlar doğru kurulursa proje, küçük bir MVP olmasına rağmen profesyonel bir yazılım ekibinin kod incelemesinden geçebilecek açıklıkta ve disiplinde olur.