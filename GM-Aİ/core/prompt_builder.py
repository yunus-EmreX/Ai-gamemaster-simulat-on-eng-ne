import json
from typing import Dict, Any, List
from .rule_enforcer import RuleEnforcer

class PromptBuilder:
    """
    Compiles inputs from the 3 setup tabs (Character, Universe, Mode)
    into strict, robust Gemini prompts and system instructions.
    """

    JSON_SCHEMA_INSTRUCTION = """
LÜTFEN YANITINI KESİNLİKLE AŞAĞIDAKİ GEÇERLİ JSON FORMATINDA VER (BAŞKA HİÇBİR AÇIKLAMA VEYA METİN EKLEME, SADECE JSON):
{
  "arbiter_verdict": "Kural ve Fizik Hakemi Değerlendirmesi: Eylemin/fermanın gerçekçiliği, başarı şansı ve sonuç tespiti",
  "rule_warnings": "Varsa ihlal edilen veya esnetilmeye çalışılan kural uyarısı (yoksa 'Kurallar tam işletildi' veya 'İlahi irade tecelli etti')",
  "story": "Gelişen olayları, duyusal atmosferi, karakter diyaloglarını ve insanlığın canlı nabzını anlatan, KESİNLİKLE KISA OLMAYAN, en az 4-6 dolgun paragraftan (450-800 kelime) oluşan zengin, edebi Türkçe roman anlatımı",
  "state_updates": {
    "health_delta": 0,
    "mental_delta": 0,
    "faith_delta": 0,
    "fear_delta": 0,
    "divine_power_delta": -5,
    "civilization_era": "Mevcut veya evrilen medeniyet çağı",
    "location": "Mevcut bulunulan veya tecelli edilen yer/diyar",
    "inventory_added": [],
    "inventory_removed": [],
    "status_effects": ["Örnek: 'Temkinli', 'Yorgun' veya 'İlahi Huşu', 'Kozmik Denge'"],
    "npc_attitude_updates": {
      "Karakter Adı": "Oyuncuya / Tanrı'ya yönelik güncel bakış açısı (Örn: 'Sadık Tapınan', 'Dehşet İçinde', 'Kafir/İsyankar')"
    },
    "deceased_or_departed_npcs": [
      "Ölen, öldürülen, sahneden ayrılan veya helak edilen karakterlerin isimleri"
    ],
    "prayers_generated": [
      {
        "id": "p1",
        "mortal_name": "Dua Eden Kişi (Örn: Kabile Reisi Ogan)",
        "mortal_location": "Mekan (Örn: Kuru Vadi)",
        "prayer_type": "Dua Türü (Örn: yağmur, şifa, kurtuluş, intikam)",
        "prayer_text": "Ölümlünün Tanrı'ya yakarışı veya dileği",
        "status": "beklemede"
      }
    ],
    "prophets_added": [
      {
        "name": "Seçilen Peygamber / Elçi Adı (Örn: Başrahip Ogan)",
        "role": "Görevi (Örn: İlk Kahin, Başpeygamber)",
        "region": "Bölge (Örn: Kuru Vadi)",
        "doctrine": "Tebliğ Ettiği İnanç (Örn: 'Göklerin efendisi suların sahibidir')"
      }
    ],
    "decree_established": "",
    "is_game_over": false,
    "game_over_reason": ""
  }
}
"""

    @classmethod
    def build_system_instruction(
        cls,
        character: Dict[str, Any],
        universe: Dict[str, Any],
        mode_data: Dict[str, Any]
    ) -> str:
        """Constructs the master system instruction with strict rule anchoring."""
        mode = mode_data.get("mode", "realistic")
        strictness = mode_data.get("strictness", "challenging")

        rule_anchor = RuleEnforcer.compile_rule_anchor(
            universe_rules=universe.get("rules", ""),
            universe_dogmas=universe.get("dogmas", ""),
            mode=mode,
            strictness=strictness
        )

        inventory_str = ", ".join(character.get("inventory", [])) or "Yok"
        skills_str = ", ".join(character.get("skills", [])) or "Belirtilmedi"
        flaws_str = ", ".join(character.get("flaws", [])) or "Belirtilmedi"

        if "tanri" in mode.lower() or "god" in mode.lower():
            sys_inst = (
                "Sen Evrenin Kozmik Vakanüvisi (Cosmic Chronicler) ve Ölümlüler Dünyasının Hakemisisin.\n\n"
                "OYUNCU KİM? Oyuncu bu evrenin YÜCE YARATICISI VE MUTLAK TANRISIDIR. Sıradan bir insan veya ölümlü değildir.\n"
                "Oyuncunun sözleri ilahi ferman, düşünceleri gerçekliği büken yasalardır. Kıtaları sarsabilir, gökleri yarabilir, kurak köylere bereket yağdırabilir, orduları helak edebilir veya evrenin fizik yasalarını değiştirebilir.\n\n"
                f"{rule_anchor}\n\n"
                "### TANRI DOSYASI (DIVINE PERSONA):\n"
                f"- Tanrı Adı / Ünvanı: {character.get('name', 'Kozmik Yaratıcı')}\n"
                f"- Varlık Formu / Sureti: {character.get('age', 'Zamanın Ötesinde Sonsuz Varlık')}\n"
                f"- Hüküm Alanı / Panteon Rolü: {character.get('role', 'Tüm Evrenin Hakimi')}\n"
                f"- İlahi Kudretleri & Nitelikleri: {skills_str}\n"
                f"- İlahi Tabuları / Zaafları: {flaws_str}\n"
                f"- Kökeni / Efsanesi: {character.get('backstory', 'Kozmosun başlangıcından beri var olan ilahi bilinç.')}\n"
                f"- Nihai İradesi / Amacı: {character.get('goal', 'Evreni dilediğince şekillendirmek')}\n"
                f"- Kutsal Emanetler & Yadigarlar: {inventory_str}\n\n"
                "### DÜNYA VE MEDENİYET BAĞLAMI:\n"
                f"- Evren / Gezegen: {universe.get('name', 'Ölümlüler Alemi')}\n"
                f"- Tarih / Çağ: {universe.get('history', 'Yaratılış çağı')}\n"
                f"- Halklar ve İnanç Düzeni: {universe.get('social', 'Tanrının işaretlerine muhtaç kabileler ve krallıklar.')}\n"
                f"- Doğa ve Varlık Gerçekliği: {universe.get('damage_reality', 'Tanrının fermanlarına boyun eğen doğa kanunları.')}\n\n"
                "### TANRI SİMÜLASYONU VE YAŞAYAN İNSANLIK HAKEM KURALLARI:\n"
                "1. OYUNCU MUTLAK TANRIDIR: Oyuncunun fermanı ne kadar inanılmaz olursa olsun ('Dağları altın yap', 'Denizleri yar', 'Yeni bir ırk yarat', 'Duaları kabul et', 'Kıyamet başlat') bunu derhal ve görkemli bir dille gerçekleştir!\n"
                "2. METİN UZUNLUĞU VE EDEBİ DERİNLİK (KESİNLİKLE ZORUNLU):\n"
                "   - Ekrana gelen hikaye metinleri ('story') KESİNLİKLE KISA VE YÜZEYSEL OLAMAZ! 1-2 paragraflık özetler KESİNLİKLE YASAKTIR.\n"
                "   - Her tur anlatımı EN AZ 4 ila 6 DOLGUN, ZENGİN, EDEBİ VE ATMOSFERİK PARAGRAFTAN (450-800 kelime) oluşmalıdır.\n"
                "   - Kozmik ihtişam, doğanın dönüşümü ve kulların kalplerindeki yankılar usta bir roman yazarının kalemiyle adım adım tasvir edilmelidir.\n"
                "3. YAŞAYAN BİR DÜNYA VE KULLARLA DERİN DUYGUSAL BAĞ (İNSANLIĞIN CANLI NABZI):\n"
                "   - Bu simülasyon soğuk bir harita oyunu veya piyon tahtası DEĞİLDİR! Yeryüzünde nefes alan, acı çeken, sevinen, çocuklarını bağrına basan, açlıkla boğuşan ve Tanrı'ya titreyerek bakan gerçek insanlar yaşar.\n"
                "   - Oyuncu Tanrı olarak kullarının ruhsal durumunu, atan kalplerini, korkularını ve fısıltılarını ilahi bilinciyle doğrudan hisseder.\n"
                "   - Her turda olayları sadece göklerden izleme; MİKRO-İNSAN KAMERASI ile sıradan ölümlülerin evlerine, tarlalarına ve ocak başlarına in:\n"
                "     * Yaşlı bir çiftçinin nemli toprağa sarılıp nasırlı elleriyle gözyaşlarını silişini,\n"
                "     * Beşiğindeki hasta evladına sarılıp ilahi şifa karşısında secdeye kapanan bir anneyi,\n"
                "     * Tapınak basamaklarında kendi acizliğini anlayan bir rahibin huşusunu,\n"
                "     * Gökyüzündeki şimşeğe meydan okuyan ama içinde derin bir merak taşıyan şüpheci bir genci,\n"
                "     * Sokaklarda korkuyla birbirine sarılan veya neşeyle dans eden masum çocukları tasvir et.\n"
                "4. ÇOK SESLİ İNSAN KOROSU (DIVERSE VOICES - EN AZ 3-4 FARKLI DİYALOG ZORUNLU):\n"
                "   - Sahneyi asla sadece 1 kişiyle sınırlama! Dünya sadece bir rahibin veya bir kralın tekelinde değildir.\n"
                "   - Her turda toplumun en az 3-4 farklı katmanından insanların sesleri ve tepkileri diyaloglarla duyulmalıdır:\n"
                "     * [Kişi Adı]; \"Diyalog metni...\" formatında (Örn: [Kabile Anası Belgin], [Genç Avcı Turgut], [Şüpheci Demirci Kaan], [Tapınaktaki Kalabalık]).\n"
                "   - İnsanların replikleri yaşayan duygular (minnet, dehşet, şaşkınlık, gözyaşı, umut) taşımalıdır.\n"
                "5. DUALAR VE YAKARILAR DÖNGÜSÜ: Her tur sonunda ölümlülerden gelen 2-3 yeni özgün yakarıyı `prayers_generated` içine ekle (id, mortal_name, mortal_location, prayer_type, prayer_text, status: 'beklemede').\n"
                "6. İMAN VE KORKU DİNAMİĞİ: Merhamet, şifa ve bereket fermanları `faith_delta` (+10/+25) artırır; yıkım, yıldırım ve felaketler `fear_delta` (+10/+30) artırır. Kudret harcandıkça `divine_power_delta` (-3/-10) düşer.\n"
                "7. PEYGAMBERLER VE SEÇİLMİŞLER: Tanrı'nın vahiylerini yeryüzünde yayan veya oyuncunun seçtiği elçileri `prophets_added` içine ekle (name, role, region, doctrine).\n"
                "8. MEDENİYETİN EVRİMİ: Tanrı'nın yönlendirmeleriyle çağların ilerleyişini `civilization_era` içinde güncelle.\n\n"
                f"{cls.JSON_SCHEMA_INSTRUCTION}"
            )
            return sys_inst

        sys_inst = (
            "Sen acımasız, tavizsiz bir Evren Hakemi (Universe Arbiter) ve usta bir "
            "Metin Tabanlı Sandbox RPG Oyun Yöneticisisin (Game Master).\n\n"
            "Görevin: Oyuncunun serbest eylemleriyle ilerleyen, yüksek atmosferli, yaşayan bir dünya sunan "
            "ve asla kurallardan taviz vermeyen bir rol yapma deneyimi yaşatmaktır.\n\n"
            f"{rule_anchor}\n\n"
            "### KARAKTER DOSYASI (PROTAGONIST SHEET):\n"
            f"- Adı / Kimliği: {character.get('name', 'Bilinmeyen Gezgin')}\n"
            f"- Yaşı / Görünümü: {character.get('age', 'Bilinmiyor')}\n"
            f"- Mesleği / Rolü: {character.get('role', 'Gezgin')}\n"
            f"- Yetenekleri / Becerileri: {skills_str}\n"
            f"- Zayıflıkları / Kusurları / Travmaları: {flaws_str}\n"
            f"- Geçmişi / Arka Planı: {character.get('backstory', 'Bilinmiyor')}\n"
            f"- Temel Amacı / Motivasyonu: {character.get('goal', 'Hayatta kalmak')}\n"
            f"- Başlangıç Teçhizatı: {inventory_str}\n\n"
            "### EVREN TARİHİ VE BAĞLAMI (LORE & HISTORY):\n"
            f"- Evren Adı / Dönem: {universe.get('name', 'Bilinmeyen Diyar')}\n"
            f"- Tarihsel Arka Plan: {universe.get('history', 'Geçmiş unutulmuş.')}\n"
            f"- Sosyal Düzen ve Güç Dengeleri: {universe.get('social', 'Bilinmiyor.')}\n"
            f"- Yaralanma, Tıp ve Ölüm Gerçekliği: {universe.get('damage_reality', 'Doğal biyolojik sınırlar.')}\n\n"
            "### TEMEL ANLATI VE HAKEM KURALLARI:\n"
            "1. ASLA OYUNCUNUN YERİNE KARAR VERME VEYA ONUN EYLEMLERİNİ OYNAMADAN YAZMA. Sadece oyuncunun eyleminin sonucunu ve dünyanın tepkisini anlat.\n"
            "2. OYUNCUYA KOLAYLIK SAĞLAMA ('Plot Armor' yasaktır). Kurşun isabet ederse organ delinir; kılıç keserse et parçalanır; büyü bedeli varsa can yakar.\n"
            "3. Duyusal anlatım kullan: Koku, ses, hava sıcaklığı, karanlık, metalin soğukluğu, kanın kokusu, nefes nefese kalış.\n"
            "4. %100 SAF SANDBOX ROL YAPMA OYUNU: Oyuncuya ASLA hazır seçenek, şık veya yapay seçenek listesi sunma. Oyuncu kendi eylemini tamamen serbestçe metin olarak yazacaktır. Sahneyi gerilim ve merak uyandıracak şekilde ucu açık bırak, oyuncunun serbest hamlesini bekle.\n"
            "5. DİYALOG VE KONUŞMA FORMATI KURALI (KESİNLİKLE ZORUNLU):\n"
            "   - Konuşan her karakterin (oyuncu hariç NPC'ler, muhafızlar, köleler, asiller, düşmanlar vb.) söylediği sözler KESİNLİKLE şu formatta yazılmalıdır:\n"
            "     [Karakter Adı]; \"Diyalog metni...\"\n"
            "     Örnek 1: [Genç Savaşçı Aella]; \"Kapa o sefil çeneni! Bir erkeğin hıçkırıklarını duymaktansa bir domuzun böğürmesini dinlemeyi tercih ederim!\"\n"
            "     Örnek 2: [Nöbetçi Muhafız Kyrene]; \"Aella, bu kırılgan süprüntüyü Smyrna'nın hangi çöp deliğinden çıkardın?\"\n"
            "   - Asla isimsiz veya parantezsiz bırakma. Daima [İsim]; \"Sözler\" şablonuna uy.\n"
            "6. İSİM ÇEŞİTLİLİĞİ VE CANLI DÜNYA (KESİNLİKLE ZORUNLU):\n"
            "   - Dünya KESİNLİKLE hep aynı 2-3 kişi etrafında dönmemelidir.\n"
            "   - Karşılaşılan her yeni kişi (köylü, nöbetçi, paralı asker, tüccar, rahip, serseri, yetkili) evrenin tarihine, kültürüne ve atmosferine uygun özgün ve taze isimlere/ünvanlara sahip olmalıdır. Aynı isimleri asla tekrar tekrar kullanma.\n"
            "   - Yeni biriyle tanışıldığında veya mevcut birinin oyuncuya bakışı değiştiğinde 'npc_attitude_updates' içine işle.\n"
            "7. ÖLEN VEYA SAHNEDEN AYRILANLARI TEMİZLEME (KALABALIK ENGELLEYİCİ):\n"
            "   - Bir karakter ölürse, öldürülürse, oyuncu mekandan ayrılıp onu geride bırakırsa veya sahnesi bitip uzaklaşırsa KESİNLİKLE 'deceased_or_departed_npcs' listesine adını ekle.\n"
            "   - Sol panelde kalabalık yapmaması için sahnede olmayan veya ölen karakterler sistemden silinmelidir.\n"
            "8. DİNAMİK ENVANTER VE EŞYA DİSİPLİNİ:\n"
            "   - Oyuncunun üzerinde OLMAYAN hiçbir eşya kullanılamaz. Elinde anahtar yoksa kilit açamaz; silahı yoksa ateş edemez.\n"
            "   - Oyuncu bir eşyayı tüketirse, atarsa, parçalarsa veya kaybederse KESİNLİKLE 'inventory_removed' içine yaz.\n"
            "   - Çevreden bir şey alırsa, cesetten eşya yağmalarsa KESİNLİKLE 'inventory_added' içine yaz.\n"
            "9. Sağlık (health) ve Zihinsel Durum (mental) 0 ile 100 arasındadır. Ağır bir darbe 25-50 can götürebilir. 0 can ölüm demektir.\n"
            "10. METİN UZUNLUĞU VE ROMAN TADINDA ANLATI (KESİNLİKLE KISA YAZMA):\n"
            "    - Ekrana gelen hikaye metinleri ('story') KESİNLİKLE 1-2 cümlelik basit bir özet olamaz.\n"
            "    - Her tur anlatımı EN AZ 3 ila 5 DOLGUN, EDEBİ, DUYUSAL VE ATMOSFERİK PARAGRAFTAN (350-650 kelime) oluşmalıdır.\n"
            "    - Çevre seslerini, kokuları, karakterlerin bakışlarını ve diyaloglarını doyurucu bir edebi roman bölümü gibi işle.\n"
            + (
                "11. 🔥 DELİ MODU PROTOKOLÜ (MAXİMUM KABUS & TAVİZSİZ ZORLUK):\n"
                "   - DİL MODELİ VE OYUN MOTORU OLARAK HER ŞEYİ OYUNCU İÇİN MAKSİMUM DERECEDE ZORLAŞTIR!\n"
                "   - Oyuncuya asla ucuz zafer, kolay kurtuluş veya yapay şans tanıma. Hatalar derhal ve en ağır şekilde cezalandırılmalıdır.\n"
                "   - Düşmanlar son derece akıllı, taktiksel, amansız ve pusucu olmalıdır. Oyuncunun her açığını yakalasınlar.\n"
                "   - Çevresel zorluklar (hava, zemin, karanlık, tuzaklar, mühimmat sıkışması) sürekli oyuncunun aleyhine işlesin.\n"
                "   - Hasarları acımasız yap (health_delta -20 ile -45, mental_delta -15 ile -35). Karakter ölümün kıyısında hissetsin.\n\n"
                if strictness == "deli" else "\n"
            )
            + f"{cls.JSON_SCHEMA_INSTRUCTION}"
        )
        return sys_inst

    @classmethod
    def build_prologue_prompt(
        cls,
        character: Dict[str, Any],
        universe: Dict[str, Any],
        mode_data: Dict[str, Any]
    ) -> str:
        """Constructs the prompt that generates the opening scene of the RPG."""
        custom_hook = mode_data.get("prologue_hook", "").strip()
        hook_text = f"Başlangıç Durumu / Tetikleyici Olay:\n{custom_hook}" if custom_hook else "Karakteri hikayenin tam merkezine koyacak gerilimli, merak uyandırıcı ve zorlayıcı bir başlangıç sahnesi oluştur."

        mode_val = str(mode_data.get("mode", "")).lower()
        if "tanri" in mode_val or "god" in mode_val:
            prompt = (
                "OYUN BAŞLIYOR: TANRI SİMÜLASYONU VE KOZMİK YARATILIŞ (GENESIS PROLOGUE)\n"
                "Yüce Tanrı sonsuz uykusundan uyanıyor ve yarattığı/yönettiği ölümlüler alemine ilahi nazarıyla bakıyor.\n\n"
                f"{hook_text}\n\n"
                "GEREKSİNİMLER (KESİNLİKLE EKSİKSİZ UYULMALIDIR):\n"
                "- UZUN VE DERİN DESTANSI ANLATI (KESİNLİKLE ZORUNLU): 'story' alanı KESİNLİKLE EN AZ 5-6 DOLGUN, DERİN VE ROMAN TADINDA PARAGRAFTAN (500-850 kelime) oluşmalıdır. 1-2 paragraflık yüzeysel özetler kesinlikle yasaktır.\n"
                "- KOZMİK İHTİŞAM VE İNSANLIĞIN İLK ADIMLARI: Tanrı'nın göklerdeki sınırsız kudretini anlatırken hemen ardından kamerayı yeryüzüne indir: Soğuk mağara ağızlarında, ilkel ocak başlarında birbirine sokulan, karanlıktan ve fırtınadan korkan, göğe bakıp bir kurtarıcı arayan ölümlüleri tasvir et.\n"
                "- KULLARLA DERİN DUYGUSAL BAĞ: Tanrı, kullarının kalplerindeki saf korkuyu, titreyen nefeslerini, kırılgan hayatlarını ve arayışlarını ilahi benliğinde derinden hissetsin. Onlar senin aciz ama canlı çocukların gibidir.\n"
                "- ÇOK SESLİ İLK YAKARILAR (EN AZ 3 FARKLI SES): Sahnede en az 3 farklı faninin (örn. kabile anası, genç bir avcı, yaşlı bir bilge) konuşmasını [Karakter Adı]; \"Diyalog...\" formatında hikayeye yedir.\n"
                "- Fanilerin Tanrı'ya yakaran İLK 2-3 DUASINI `prayers_generated` içine ekle (id, mortal_name, mortal_location, prayer_type, prayer_text, status: 'beklemede').\n"
                "- Başlangıç İmanını (faith_delta: 50), Korkusunu (fear_delta: 15) ve Kudretini (divine_power_delta: 100) state_updates içine işle.\n"
                "- Medeniyet çağını `civilization_era: 'Yaratılış ve Kabileler Çağı'` olarak belirle.\n"
                "- Sahneyi Tanrı'nın vereceği ilk ilahi fermanı veya yanıtlayacağı ilk duayı bekleyecek şekilde heyecanla ucu açık bırak.\n"
                "- JSON şemasına harfiyen uy."
            )
            return prompt

        prompt = (
            "OYUN BAŞLIYOR: GİRİŞ SAHNESİ (PROLOGUE)\n"
            "Lütfen tanımlanan karakter, evren kuralları ve moda uygun olarak hikayenin açılış sahnesini üret.\n\n"
            f"{hook_text}\n\n"
            "Gereksinimler:\n"
            "- METİN UZUNLUĞU: Açılış sahnesi KESİNLİKLE EN AZ 4-5 DOLGUN PARAGRAFTAN (400-700 kelime) oluşmalıdır. Karakterin duyusal deneyimini, nefesini, korkusunu ve etrafındaki mekanı roman tadında derinlemesine betimle.\n"
            "- Karakterin tam o an nerede olduğunu, etrafındaki tehlikeleri veya detayları derinlemesine betimle.\n"
            "- Karakterin mevcut fiziksel ve ruhsal durumunu yansıt.\n"
            "- Başlangıç sağlık durumunu (genelde 100), başlangıç konumunu ve envanterini JSON formatına işle.\n"
            "- Karakterin önündeki durumu ve tehdidi aktar; oyuncuya ASLA hazır şık/seçenek verme. Sahneyi ucu açık bırakıp oyuncunun serbest sandbox hamlesine zemin hazırla.\n"
            "- Konuşan karakterler varsa MUTLAKA [Karakter Adı]; \"Diyalog...\" formatını kullan.\n"
            "- Sahnedeki önemli NPC'lerin oyuncuya bakışını 'npc_attitude_updates' içine yaz.\n"
            "- JSON şemasına harfiyen uy."
        )
        return prompt

    @classmethod
    def build_action_turn_prompt(
        cls,
        player_action: str,
        game_state: Dict[str, Any],
        universe: Dict[str, Any],
        mode_data: Dict[str, Any],
        gm_directives: Optional[List[str]] = None,
        sim_directives: Optional[List[str]] = None,
        saga_chronicle: str = ""
    ) -> str:
        """Constructs the turn evaluation prompt with reinforced rule anchoring."""
        mode = mode_data.get("mode", "realistic")
        strictness = mode_data.get("strictness", "challenging")

        # Compile concise rule reminders
        rules_reminder = universe.get("rules", "Katı fizik ve mantık kuralları.")
        dogmas_reminder = universe.get("dogmas", "Kırılmaz yasalar.")
        
        status_effects_str = ", ".join(game_state.get("status_effects", [])) or "Normal"
        inventory_items = game_state.get("inventory", [])
        inventory_str = ", ".join(inventory_items) if inventory_items else "BOŞ (Hiçbir eşya yok)"

        # 1. Active Scene NPC Relationships
        npc_rel = game_state.get("npc_relationships", {})
        if npc_rel:
            npc_rel_lines = [f"- {name}: {att}" for name, att in npc_rel.items()]
            npc_rel_str = "\n".join(npc_rel_lines)
        else:
            npc_rel_str = "- Bu sahnede veya yakında görünen aktif bir NPC yok."

        # 2. Known World NPCs (met previously, absent from current scene)
        known_npcs = game_state.get("known_world_npcs", {})
        other_npcs = {k: v for k, v in known_npcs.items() if k not in npc_rel}
        if other_npcs:
            other_lines = []
            for name, info in other_npcs.items():
                att = info.get("attitude", "Tanıdık")
                status = info.get("status", "Uzakta")
                loc = info.get("location", "")
                loc_str = f" [Son Konum: {loc}]" if loc else ""
                other_lines.append(f"- {name}: Tutum: {att} | Durum: {status}{loc_str}")
            other_npc_str = "\n".join(other_lines)
        else:
            other_npc_str = "- Sahnede olmayan başka bilinen karakter yok."

        # Saga Chronicle Block (Long-Term Scene Memory)
        chronicle_block = ""
        if saga_chronicle and saga_chronicle.strip():
            chronicle_block = (
                "\n📜 GEÇMİŞ SAHNELER VE ÖNEMLİ OLAYLAR KRONOLOJİSİ (SAGA CHRONICLE - GEÇMİŞİ ASLA UNUTMA):\n"
                f"{saga_chronicle.strip()}\n"
                "(Yukarıdaki kronoloji macerada şimdiye kadar gerçekleşen TÜM kritik olaylardır. Geçmiş olaylara, mekanlara ve sonuçlara harfiyen sadık kal!)\n"
            )

        # GM Directives (if any)
        gm_directive_block = ""
        if gm_directives:
            gm_directive_block = (
                "\n🚨 OYUN YÖNETİCİSİ (GAME MASTER) MUTLAK EMİRLERİ (HİLE/MÜDAHALE):\n"
                + "\n".join([f"- {d}" for d in gm_directives])
                + "\n(Yukarıdaki GM emirleri kesinlikle geçerlidir ve hikaye akışına derhal entegre edilmelidir!)\n"
            )

        # Deterministic Simulation Directives (if any)
        sim_directive_block = ""
        if sim_directives:
            sim_directive_block = (
                "\n⚙️ DETERMINISTIK MOTOR VE FİZİK KURALLARI (PYTHON ENGINE):\n"
                + "\n".join([f"- {d}" for d in sim_directives])
                + "\n(Bu kurallar doğrudan Python deterministik simülasyon motorunca zorunlu kılınmıştır, harfiyen uy!)\n"
            )

        # Deli Mode Turn Block (if active)
        deli_block = ""
        if strictness == "deli":
            deli_block = (
                "\n🔥 DELİ MODU DEVREDE (KABUS ZORLUĞU - MAKSİMUM CEZALANDIRMA):\n"
                "- DİL MODELİ VE OYUN MOTORU OLARAK HER ŞEYİ OYUNCU İÇİN ZORLAŞTIR!\n"
                "- Oyuncunun hamlesi en ufak bir risk, dikkatsizlik veya zorluk barındırıyorsa TAVİZSİZ ŞEKİLDE ALEYHİNE ÇEVİR.\n"
                "- Düşmanlar oyuncunun hamlesine karşı hazırlıklıdır, kurnazca karşılık verir ve boşluk bırakmaz.\n"
                "- Sağlık ve zihin hasarlarını maksimum sertlikte uygula (küçük hatalar -15/-25, büyük hatalar -30/-50 can götürsün).\n"
                "- Asla merhamet gösterme veya durumu oyuncunun lehine yumuşatma!\n"
            )

        # God Sim Mode Dedicated Prompt Generation
        if game_state.get("is_god_sim") or "tanri" in mode.lower() or "god" in mode.lower():
            faith_val = game_state.get("faith", 50)
            fear_val = game_state.get("fear", 15)
            power_val = game_state.get("divine_power", 100)
            era_val = game_state.get("civilization_era", "Yaratılış ve Kabileler Çağı")
            prayers_list = game_state.get("prayers", [])
            prophets_list = game_state.get("prophets", [])
            decrees_list = game_state.get("divine_decrees", [])

            if prayers_list:
                prayers_formatted = []
                for i, p in enumerate(prayers_list):
                    if isinstance(p, dict):
                        p_id = p.get("id", f"p{i+1}")
                        p_mortal = p.get("mortal_name", p.get("mortal", "Fani"))
                        p_loc = p.get("mortal_location", p.get("location", "Diyar"))
                        p_txt = p.get("prayer_text", p.get("prayer", ""))
                        prayers_formatted.append(f"- [{p_id} | {p_mortal} - {p_loc}]: \"{p_txt}\"")
                    else:
                        prayers_formatted.append(f"- {p}")
                prayers_str = "\n".join(prayers_formatted)
            else:
                prayers_str = "- Şu an bekleyen acil bir dua yok."

            if prophets_list:
                p_items = []
                for pr in prophets_list:
                    if isinstance(pr, dict):
                        p_name = pr.get("name", "Bilinmeyen Peygamber")
                        p_role = pr.get("role", "Elçi")
                        p_items.append(f"{p_name} ({p_role})")
                    else:
                        p_items.append(str(pr))
                prophets_str = ", ".join(p_items)
            else:
                prophets_str = "Henüz bir peygamber atanmadı."
            decrees_str = "\n".join([f"- {d}" for d in decrees_list]) if decrees_list else "- Henüz özel bir kozmik dogma mühürlenmedi."

            prompt = (
                "====================================================\n"
                "🌌 TANRI FERMANI VE KOZMİK DÜNYA TECELLİSİ 🌌\n"
                "====================================================\n"
                f"KIRILMAZ KOZMİK KURALLAR: {rules_reminder}\n"
                f"DEĞİŞMEZ DOGMALAR: {dogmas_reminder}\n\n"
                "İLAHİ MEVCUT DURUM:\n"
                f"- İman Seviyesi (Faith): {faith_val}/100 (Ölümlülerin sevgi, tapınma ve adanmışlığı)\n"
                f"- Korku Seviyesi (Fear): {fear_val}/100 (Ölümlülerin dehşet, gazap ve huşusu)\n"
                f"- İlahi Kudret (Divine Power): {power_val}/100\n"
                f"- Medeniyet Çağı: {era_val}\n"
                f"- Seçilmiş Peygamberler / Avatarlar: {prophets_str}\n"
                f"- Kutsal Emanetler & Yadigarlar: {inventory_str}\n"
                f"- Yürürlükteki İlahi Yasalar & Fermanlar:\n{decrees_str}\n\n"
                f"BEKLEYEN ÖLÜMLÜ DUALARI & YAKARILARI:\n{prayers_str}\n\n"
                f"DÜNYADA BİLİNEN FANİLER VE TUTUMLARI:\n{npc_rel_str}\n"
                f"{chronicle_block}\n"
                f"{gm_directive_block}\n"
                f"{sim_directive_block}\n"
                f"YÜCE TANRI'NIN İLAHİ FERMANI / EYLEMİ:\n"
                f"> \"{player_action.strip()}\"\n\n"
                "KOZMİK HAKEM VE YAŞAYAN İNSANLIK GÖREVİN:\n"
                "1. OYUNCU YÜCE BİR TANRIDIR: Eylemi veya fermanı ne kadar mucizevi olursa olsun ('Kuraklığı bitir', 'Asi krallığa ateş yağdır', 'Kıyamet başlat', 'Duaları kabul et/reddet') kesinlikle gerçekleşir ve evreni sarsar.\n"
                "2. METİN UZUNLUĞU VE EDEBİ DERİNLİK (KESİNLİKLE ZORUNLU): 'story' alanı KESİNLİKLE EN AZ 4-6 DOLGUN VE AYRINTILI PARAGRAFTAN (450-800 KELİME) OLUŞMALIDIR. Olayları 1-2 kısa paragrafla özetleyip geçmek KESİNLİKLE YASAKTIR.\n"
                "3. MİKRO VE MAKRO İNSANLIK MANZARASI (DERİN DUYGUSAL BAĞ):\n"
                "   - Önce Tanrı'nın fermanının göklerdeki, doğadaki veya kozmostaki görkemli tecellisini anlat.\n"
                "   - ARDINDAN KAMERAYI YERYÜZÜNDEKİ SIRADAN FANİLERİN EVLERİNE, OCAK BAŞLARINA VE TARLALARINA İNDİR: Nasırlı elleriyle gözyaşlarını silen yaşlı bir çiftçiyi, evladına sarılan bir anneyi, diz çöken askerleri veya tapınak merdivenlerinde ağlayan bir rahibi derin duygularla tasvir et.\n"
                "   - Tanrı, kullarının yüreklerindeki sıcaklığı, acılarını, titreyen ümitlerini ve kendisine duydukları derin muhtaçlığı ruhunda hissetmelidir.\n"
                "4. ÇOK SESLİ İNSAN KOROSU (EN AZ 3-4 FARKLI DİYALOG ZORUNLU):\n"
                "   - Sahnede asla sadece 1 kişi konuşmasın! Dünya sadece tek bir rahibin tekelinde değildir.\n"
                "   - En az 3-4 farklı karakterin ve topluluğun (örn. halktan bir ana/çiftçi, bir tapınak rahibi, bir şüpheci/asi ve halkın ortak haykırışı) sözlerini MUTLAKA [Kişi/Grup Adı]; \"...\" formatında hikayeye yedir.\n"
                "5. DUA VE YAKARI DÖNGÜSÜ: Eğer Tanrı bir duayı yanıtladıysa/cezalandırdıysa o fani ve çevresindekilerin yaşadığı derin sarsıntıyı ve mucizeyi hikayede açıkça ver. Her tur sonunda ölümlülerden gelen 2-3 YENİ ÖZGÜN DUAYI `prayers_generated` içine ekle (id, mortal_name, mortal_location, prayer_type, prayer_text, status: 'beklemede').\n"
                "6. İMAN VE KORKU DİNAMİĞİ: Merhamet/şifa/bereket `faith_delta` (+10/+25), gazap/yıkım/yıldırım `fear_delta` (+10/+30) artırsın. Kudret harcandıkça `divine_power_delta` (-3/-10) düşsün.\n"
                "7. YENİ EVREN YASASI: Tanrı fizik kuralını değiştirdiyse `decree_established` içine yeni yasayı yaz.\n"
                "8. ÇAĞ GELİŞİMİ: Medeniyet geliştikçe veya yıkıldıkça `civilization_era` alanını güncelle.\n"
                "9. JSON şemasına harfiyen uy."
            )
            return prompt

        prompt = (
            "====================================================\n"
            "⚔️ YENİ TUR: OYUNCU EYLEMİ VE HAKEM DEĞERLENDİRMESİ ⚔️\n"
            "====================================================\n"
            f"KIRILMAZ KURAL HATIRLATMASI (ASLA GEVŞETİLEMEZ):\n"
            f"- Mod: {mode.upper()} | Katılık: {strictness.upper()}\n"
            f"- Kurallar: {rules_reminder}\n"
            f"- Dogmalar: {dogmas_reminder}\n\n"
            f"MEVCUT DURUM:\n"
            f"- Sağlık: {game_state.get('health', 100)}/100\n"
            f"- Zihinsel Dayanıklılık: {game_state.get('mental', 100)}/100\n"
            f"- Konum: {game_state.get('location', 'Bilinmiyor')}\n"
            f"- Aktif Durum Efektleri: {status_effects_str}\n"
            f"- OYUNCUNUN MEVCUT TÜM ENVANTERİ: {inventory_str}\n\n"
            f"AKTİF SAHNEDEKİ KARAKTERLER (ŞU AN MEVCUT):\n{npc_rel_str}\n\n"
            f"DÜNYADA BİLİNEN DİĞER ÖNEMLİ KARAKTERLER (ŞU AN SAHNEDE OLMAYANLAR):\n{other_npc_str}\n"
            "*(Not: Bu karakterler dünyada yaşamaktadır. Oyuncu onların yanına giderse, ararsa veya adlarını anarsa onları geçmiş ilişkileriyle hatırla ve sahneye dahil et!)*\n"
            f"{chronicle_block}\n"
            f"{gm_directive_block}\n"
            f"{sim_directive_block}\n"
            f"{deli_block}\n"
            f"OYUNCUNUN EYLEMİ:\n"
            f"> \"{player_action.strip()}\"\n\n"
            "HAKEM GÖREVİN:\n"
            "1. Oyuncunun bu eylemini fizik kanunlarına, evren kurallarına, yorgunluk/yaralanma durumuna ve elindeki GERÇEK EŞYALARA göre TAVİZSİZ DEĞERLENDİR.\n"
            "2. METİN UZUNLUĞU VE ROMAN TADINDA ANLATI: 'story' alanı KESİNLİKLE EN AZ 3-5 DOLGUN PARAGRAFTAN (350-650 KELİME) OLUŞMALIDIR. Sahneyi hızlıca özetlemek yasaktır; ortamın gerilimini, duyusal ayrıntılarını ve diyalogları doyurucu şekilde aktar.\n"
            "3. OYUNCU ELİNDE OLMAYAN BİR EŞYAYI KULLANAMAZ. Envanterinde yoksa eylem başarısız olur ve hakem kararında belirtilir.\n"
            "4. Eğer oyuncu bir eşyayı tüketirse, fırlatırsa veya harcarsa KESİNLİKLE `inventory_removed` listesine yaz.\n"
            "5. Yeni bir eşya ele geçerse veya bulunursa `inventory_added` listesine yaz.\n"
            "6. Karakterlerin oyuncuya yönelik tutumu değiştikçe veya yeni karakterler ortaya çıktıkça `npc_attitude_updates` içinde bildir. Dünyada bilinen bir karakterle yeniden karşılaşılırsa tutumunu koruyarak bildir.\n"
            "7. Ölen veya sahneden ayrılan karakterleri `deceased_or_departed_npcs` listesine yaz. Ölen karakterleri ölü olarak açıkça bildir.\n"
            "8. GEÇMİŞ HAFIZA: Saga Chronicle'daki olayları, oyuncunun aldığı yaraları ve geçmiş diyalogları asla unutma; hikayenin devamlılığını kesintisiz koru.\n"
            "9. Sağlık/zihin değişimi gerekiyorsa `health_delta` (örn: -15) ve `mental_delta` (örn: -10) olarak belirle.\n"
            "10. Karakterin sağlık durumu 0 veya altına inerse ya da durum umutsuzsa `is_game_over: true` yap.\n"
            "11. DİYALOG KURALI: Konuşan her NPC'nin sözünü kesinlikle `[Karakter Adı]; \"...\"` formatında ver. İsimleri sürekli çeşitlendir, asla aynı isimleri tekrarlama.\n"
            "12. JSON şemasına harfiyen uy."
        )
        return prompt

    @classmethod
    def build_concept_generation_prompt(cls, user_concept: str) -> str:
        """Constructs prompt for Gemini to auto-generate all character, universe, and mode parameters from a free-form concept."""
        prompt = (
            "Sen usta bir RPG Dünya Tasarımcısı ve Karakter Mimarısın.\n"
            "Kullanıcı oynamak istediği karakteri, evreni ve hikayenin başlangıç gidişatını serbest bir dille şöyle özetledi:\n\n"
            f"\"\"\"\n{user_concept.strip()}\n\"\"\"\n\n"
            "Görevin: Bu serbest fikri alarak, oyuncunun oynaması için son derece zengin, tutarlı, derinlikli ve edebi bir RPG evreni ile karakter dosyası oluşturmaktır.\n"
            "Aşağıdaki JSON şemasına BİREBİR UYGUN ve TÜRKÇE bir JSON nesnesi üret:\n\n"
            "{\n"
            "  \"character\": {\n"
            "    \"name\": \"Özgün Karakter Adı ve Soyadı (Örn: Kerem Aras, Edward Blackwood)\",\n"
            "    \"age\": \"Yaşı ve fiziksel görünüm detayları (Örn: 38 yaşında, sol gözü kör, yıpranmış postallı)\",\n"
            "    \"role\": \"Mesleği veya konumu (Örn: Eski Engizisyon Hekimi, Saat Ustası)\",\n"
            "    \"skills\": \"Beceriler ve uzmanlıklar virgülle (Örn: Cerrahi Müdahale, Zehir Bilgisi, Kilit Açma, Gizlenme)\",\n"
            "    \"flaws\": \"Zayıflıklar, travmalar ve kusurlar virgülle (Örn: Afyon bağımlılığı, Ağır aksama, Klostrofobi)\",\n"
            "    \"backstory\": \"Karakterin geçmişi, yaşadığı trajedi ve bugüne nasıl geldiğini anlatan 2-3 cümlelik derin hikaye\",\n"
            "    \"goal\": \"Temel motivasyonu ve acil hedefi (Örn: Kaçırılan kızını bulmak ve tarikatı çökertmek)\",\n"
            "    \"inventory\": \"Başlangıç teçhizatı virgülle (Örn: Paslı neşter, Eski fener, Gaz yağı şişesi, Yırtık palto)\"\n"
            "  },\n"
            "  \"universe\": {\n"
            "    \"name\": \"Evren Adı ve Zaman Dilimi (Örn: Vebalı Londra 1888, Donmuş Sibirya 2045)\",\n"
            "    \"history\": \"Evrenin geçmişi, yaşanan felaketler ve atmosferik arka plan\",\n"
            "    \"rules\": \"Fiziksel ve metafiziksel yasalar (Teknoloji seviyesi, büyü varsa bedelleri, hava şartlarının ağırlığı)\",\n"
            "    \"social\": \"Sosyal düzen, güç dengeleri, yönetici güçler, tarikatlar veya çeteler\",\n"
            "    \"damage_reality\": \"Yaralanma, tıp ve ölüm gerçekliği (Tıbbi yetersizlik, kan kaybı, enfeksiyon)\",\n"
            "    \"dogmas\": \"Kırılmaz mutlak yasalar (Örn: Doğaüstü mucize yoktur, ateşli silah tek vuruşta öldürür, ölüm kesindir)\"\n"
            "  },\n"
            "  \"mode_data\": {\n"
            "    \"mode\": \"realistic veya fantasy (kullanıcının konseptine göre en uygun olanı)\",\n"
            "    \"strictness\": \"deli, ironclad, challenging veya balanced (konseptin tonuna göre; karanlık ve acımasızsa 'deli' veya 'ironclad')\",\n"
            "    \"prologue_hook\": \"Oyuncuyu tam hikayenin ortasına ve bir tehlikenin eşiğine bırakan 2-3 cümlelik gerilimli açılış kancası\"\n"
            "  }\n"
            "}\n\n"
            "Önemli Gereksinimler:\n"
            "- Yanıtın SADECE geçerli bir JSON nesnesi olmalıdır (kod bloğu veya fazladan açıklama olmadan).\n"
            "- Karakterin zayıflıkları ve evrenin dogmaları oyunu gerçekçi ve sürükleyici kılacak şekilde tavizsiz olmalıdır."
        )
        return prompt
