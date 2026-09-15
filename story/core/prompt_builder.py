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
  "arbiter_verdict": "Kural ve Fizik Hakemi Değerlendirmesi: Eylemin gerçekçiliği, başarı şansı ve sonuç tespiti",
  "rule_warnings": "Varsa ihlal edilen veya esnetilmeye çalışılan kural uyarısı (yoksa 'Kurallar tam işletildi')",
  "story": "Gelişen olayların sürükleyici, edebi, duyusal ve tavizsiz Türkçe hikaye anlatımı",
  "state_updates": {
    "health_delta": 0,
    "mental_delta": 0,
    "location": "Mevcut bulunulan yer veya mekan",
    "inventory_added": [],
    "inventory_removed": [],
    "status_effects": ["Örnek: 'Yorgun', 'Kanama', 'Temkinli'"],
    "npc_attitude_updates": {
      "Karakter Adı": "Oyuncuya yönelik güncel bakış açısı (Örn: 'Kibirli ve düşmanca', 'Meraklı', 'Saygılı', 'Korku dolu')"
    },
    "deceased_or_departed_npcs": [
      "Ölen, öldürülen, sahneden ayrılan, kaçan veya geride bırakılan karakterlerin isimleri (Örn: 'Muhafız Kaan')"
    ],
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
            "9. Sağlık (health) ve Zihinsel Durum (mental) 0 ile 100 arasındadır. Ağır bir darbe 25-50 can götürebilir. 0 can ölüm demektir.\n\n"
            f"{cls.JSON_SCHEMA_INSTRUCTION}"
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

        prompt = (
            "OYUN BAŞLIYOR: GİRİŞ SAHNESİ (PROLOGUE)\n"
            "Lütfen tanımlanan karakter, evren kuralları ve moda uygun olarak hikayenin açılış sahnesini üret.\n\n"
            f"{hook_text}\n\n"
            "Gereksinimler:\n"
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
        gm_directives: Optional[List[str]] = None
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

        # NPC Relationships formatting
        npc_rel = game_state.get("npc_relationships", {})
        if npc_rel:
            npc_rel_lines = [f"- {name}: {att}" for name, att in npc_rel.items()]
            npc_rel_str = "\n".join(npc_rel_lines)
        else:
            npc_rel_str = "- Henüz tanınan belirgin bir NPC yok."

        # GM Directives (if any)
        gm_directive_block = ""
        if gm_directives:
            gm_directive_block = (
                "\n🚨 OYUN YÖNETİCİSİ (GAME MASTER) MUTLAK EMİRLERİ (HİLE/MÜDAHALE):\n"
                + "\n".join([f"- {d}" for d in gm_directives])
                + "\n(Yukarıdaki GM emirleri kesinlikle geçerlidir ve hikaye akışına derhal entegre edilmelidir!)\n"
            )

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
            f"BİLİNEN KARAKTERLER VE İLİŞKİLER:\n{npc_rel_str}\n"
            f"{gm_directive_block}\n"
            f"OYUNCUNUN EYLEMİ:\n"
            f"> \"{player_action.strip()}\"\n\n"
            "HAKEM GÖREVİN:\n"
            "1. Oyuncunun bu eylemini fizik kanunlarına, evren kurallarına, yorgunluk/yaralanma durumuna ve elindeki GERÇEK EŞYALARA göre TAVİZSİZ DEĞERLENDİR.\n"
            "2. OYUNCU ELİNDE OLMAYAN BİR EŞYAYI KULLANAMAZ. Envanterinde yoksa eylem başarısız olur ve hakem kararında belirtilir.\n"
            "3. Eğer oyuncu bir eşyayı tüketirse, fırlatırsa veya harcarsa KESİNLİKLE `inventory_removed` listesine yaz.\n"
            "4. Yeni bir eşya ele geçerse veya bulunursa `inventory_added` listesine yaz.\n"
            "5. Karakterlerin oyuncuya yönelik tutumu değiştikçe veya yeni karakterler ortaya çıktıkça `npc_attitude_updates` içinde bildir.\n"
            "6. Ölen, öldürülen, sahneden tamamen ayrılan veya geride kalan karakterleri KESİNLİKLE `deceased_or_departed_npcs` listesine yazarak panelden düşürülmesini sağla.\n"
            "7. Sağlık/zihin değişimi gerekiyorsa `health_delta` (örn: -15) ve `mental_delta` (örn: -10) olarak belirle.\n"
            "8. Karakterin sağlık durumu 0 veya altına inerse ya da durum umutsuzsa `is_game_over: true` yap.\n"
            "9. DİYALOG KURALI: Konuşan her NPC'nin sözünü kesinlikle `[Karakter Adı]; \"...\"` formatında ver. İsimleri sürekli çeşitlendir, asla aynı isimleri tekrarlama.\n"
            "10. JSON şemasına harfiyen uy."
        )
        return prompt
