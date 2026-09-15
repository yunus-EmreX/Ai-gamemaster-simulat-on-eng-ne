# Chronicles of Gemini - Tavizsiz Yapay Zeka Rol Yapma (RPG) Motoru

Bu proje, Google Gemini API kullanarak çalışan, derinlikli, edebi ve **evren kurallarından / gerçekçilikten asla taviz vermeyen** metin tabanlı bir sandbox rol yapma (RPG) oyun motorudur.

---

## 🌟 Temel Özellikler

### 1. 3 Sekmeli Kurulum Sihirbazı
1. **1. Sekme (Karakter Dosyası):**
   - Karakter adı, yaşı, mesleği ve rolü.
   - Beceriler ve uzmanlık alanları (başarı şansını şekillendirir).
   - Zayıflıklar, travmalar ve kusurlar (gerçekçiliği sağlayan ana unsurlar).
   - Geçmiş hikaye, kişisel hedef ve başlangıç envanteri.
2. **2. Sekme (Evren Kuralları & Tarihi):**
   - Evren adı ve zaman dilimi.
   - Evrenin tarihi ve mevcut durumu (felaketler, medeniyetin çöküşü, fraksiyonlar).
   - Fiziksel ve metafiziksel kanunlar (büyü/teknoloji kuralları ve bedelleri, hava koşulları, akustik vb.).
   - Sosyal düzen, hiyerarşi ve yasalar.
   - Yaralanma ve ölüm gerçekliği.
   - **KIRILMAZ DOGMALAR:** Asla esnetilemeyecek mutlak kurallar (Örn: *"Ölüler asla diriltilemez"*, *"Yerçekimi ve mermi kinetiği tavizsizdir"*).
3. **3. Sekme (Oyun Modu & Katılık):**
   - **Gerçekçi Mod (Strict Realism):** Sıfır senaryo zırhı (plot armor). İnsan biyolojisi kırılgandır, mermiler öldürür, hipotermi ve enfeksiyon gerçektir. İmkansız eylemler anında başarısız olur ve ağır travmayla cezalandırılır.
   - **Fantezi / Epik Mod (Consistent Fantasy):** Büyü ve doğaüstü unsurlar aktiftir ancak evrenin kendi kuralları ve bedelleri katiyetle tahsil edilir.
   - **Katılık Seviyeleri:**
     - 🔒 *Demir Kural (Ironclad):* Tavizsiz ve ölümcül.
     - ⚔️ *Zorlayıcı (Challenging):* Yüksek gerçekçilik ve risk-bedel dengesi.
     - ⚖️ *Dengeli (Balanced):* Tutarlı ve akıcı.
    - **API & Model:** `gemini-3.6-flash` (Önerilen & Güncel Model), `gemini-2.5-flash`, `gemini-1.5-flash` veya `gemini-1.5-pro` seçimi, yerel API anahtarı testi.
    - **Header Tabanlı Güvenli İletişim:** API anahtarı URL sorgu dizesi yerine modern `x-goog-api-key` HTTP başlığı ile şifrelenmiş olarak iletilir.

---

### 2. %100 Saf Sandbox Deneyimi (Freeform Sandbox)
- Oyuncuya asla hazır şıklar (A, B, C seçenekleri) sunulmaz.
- Oyuncu aklına gelen her taktiksel eylemi serbest metin olarak yazar.
- Hakem motoru eylemin gerçekçiliğini, oyuncunun elindeki gerçek envanteri ve evren kurallarını sınayarak sonucu dinamik olarak üretir.

---

### 3. 👑 Oyun İçi GM / Hile Paneli (Game Master Panel)
- **Can & Zihinsel Sağlık:** Tek tıkla tam iyileşme veya anlık stat düzenleme.
- **🛡️ Tanrı Modu (God Mode):** Ölümsüzlük ve hasar almama anahtarı.
- **🎒 Envanter Düzenleyici:** İstenen eşyayı doğrudan envantere ekleme, mevcut eşyaları tek tıkla silme çipleri.
- **👥 Karakter & İlişki Düzenleyici:** Hikayedeki NPC'lerin oyuncuya yönelik tutumunu belirleme veya tek tıkla (`×`) silme.
- **🧪 Durum Temizleyici:** Zehirlenme, hipotermi, kırık gibi zararlı durumları arındırma.
- **📜 GM Olay / Direktif Enjeksiyonu:** Bir sonraki turda yapay zekaya zorunlu kılınacak gizli olayları ve kuralları enjekte etme.

---

### 4. 👥 Yaşayan Dünya ve Sahne Yönetimi (NPC Pruning)
- **Ölenlerin Temizlenmesi:** Hikayede ölen ya da hayatını kaybeden karakterler sol panelden anında silinir.
- **2-3 Sahne İnaktif Olanların Düşürülmesi:** Bir karakter 3 tur (2-3 sahne) boyunca sahnede görünmezse sol panelden otomatik temizlenerek arayüz kalabalığı önlenir.

---

## 🛡️ Evren Kurallarının Gevşememesini Garanti Eden Mekanizma (Rule Enforcer)

Dil modellerinin uzun süren oyunlarda kuralları unutmasını veya oyuncuya kolaylık sağlamasını önlemek için çok katmanlı sistem uygulanır:
- **System Instruction Koruması:** Evren yasaları ve katılık direktifleri modelin sistem seviyesine kilitlenir.
- **Tur Başına Kural Çapası (Rule Anchor):** Her oyuncu eyleminde tanımlanmış kırılmaz dogmalar ve güncel envanter modele tekrar hatırlatılır.
- **Evren Hakemi (Rule Arbiter):** Model her eylemde önce eylemin fizik ve kurallara uygunluğunu denetler, hakem kararını (`arbiter_verdict`) verir ve kurallara aykırı durumlarda oyuncuya taviz vermeden bedelini ödetir.
- **Self-Healing JSON Engine:** 8192 token çıkış kapasitesi ve kesilen yanıtları dahi kurtaran otomatik onarma motoru.

---

## ⚡ Hazır Şablonlar (Presets)

Kurulum ekranındaki açılır listeden tek tıkla yüklenebilir:
1. **Kıyamet Sonrası Sert Kış (Gerçekçi Hayatta Kalma):** Nükleer kış, dondurucu soğuk, açlık, mermi kısıtı, sıfır zombi/büyü.
2. **Kül Krallığı ve Kan Yemini (Karanlık Fantezi):** Kadim karanlık, can ve et bedeliyle çalışan kan büyüsü, fanatik Engizisyon.
3. **Neo-İstanbul 2099: Asit Yağmuru (Sert Siberpunk):** Dikey mega-kent, siber aşırı ısınma, mega şirket suikastçıları, asit yağmuru.

---

## 🚀 Çalıştırma Talimatı

### Yöntem 1: Tek Tıkla Başlatma (Windows)
Proje klasöründeki `run.bat` dosyasına çift tıklayın. Eksik paket varsa kurup otomatik olarak sunucuyu başlatır ve tarayıcınızda açar (`http://127.0.0.1:5000`).

### Yöntem 2: Komut Satırından Başlatma
```bash
# 1. Gerekli kütüphaneleri yükleyin
python -m pip install -r requirements.txt

# 2. Sunucuyu başlatın
python app.py
```
Ardından tarayıcınızdan `http://127.0.0.1:5000` adresine gidin.

---

## 💾 Kaydetme ve Yükleme (Save / Load)
Oyun sırasında sağ üstteki **"Kaydet"** butonuna basarak maceranızı istediğiniz bir isimle JSON olarak kaydedebilir, **"Kayıtlar"** penceresinden dilediğiniz zaman kaldığınız yerden devam edebilirsiniz. Path traversal saldırılarına karşı dosya adı otomatik olarak sanitize edilir.

---

## 🧪 Birim Testleri
Proje kapsamlı bir birim test paketine sahiptir:
```bash
python test_app.py
```
