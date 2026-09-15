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
   - **API & Model:** Gemini 2.0 Flash, 1.5 Flash veya 1.5 Pro seçimi, yerel API anahtarı testi.

---

## 🛡️ Evren Kurallarının Gevşememesini Garanti Eden Mekanizma (Rule Enforcer)

Dil modellerinin uzun süren oyunlarda kuralları unutmasını veya oyuncuya kolaylık sağlamasını önlemek için 3 kademeli sistem uygulanır:
- **System Instruction Koruması:** Evren yasaları ve katılık direktifleri modelin sistem seviyesine kilitlenir.
- **Tur Başına Kural Çapası (Rule Anchor):** Her oyuncu eyleminde tanımlanmış kırılmaz dogmalar modele tekrar hatırlatılır.
- **Evren Hakemi (Rule Arbiter):** Model her eylemde önce eylemin fizik ve kurallara uygunluğunu denetler, hakem kararını (`arbiter_verdict`) verir ve kurallara aykırı durumlarda oyuncuya taviz vermeden bedelini ödetir.

---

## ⚡ Hazır Şablonlar (Presets)

Kurulum ekranındaki açılır listeden tek tıkla yüklenebilir:
1. **Kıyamet Sonrası Sert Kış (Gerçekçi Hayatta Kalma):** Nükleer kış, dondurucu soğuk, açlık, mermi kısıtı, sıfır zombi/büyü.
2. **Kül Krallığı ve Kan Yemini (Karanlık Fantezi):** Kadim karanlık, can ve et bedeliyle çalışan kan büyüsü, fanatik Engizisyon.
3. **Neo-İstanbul 2099: Asit Yağmuru (Sert Siberpunk):** Dikey mega-kent, siber aşırı ısınma, mega şirket suikastçıları, asit yağmuru.

---

## 🚀 Çalıştırma Talimatı

### Yöntem 1: Tek Tıkla Başlatma (Windows)
Proje klasöründeki `run.bat` dosyasına çift tıklayın. Otomatik olarak sunucuyu başlatıp varsayılan tarayıcınızda açacaktır (`http://127.0.0.1:5000`).

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
Oyun sırasında sağ üstteki **"Kaydet"** butonuna basarak maceranızı istediğiniz bir isimle JSON olarak kaydedebilir, **"Kayıtlar"** penceresinden dilediğiniz zaman kaldığınız yerden devam edebilirsiniz.
