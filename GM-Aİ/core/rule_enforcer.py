from typing import Dict, Any, List

class RuleEnforcer:
    """
    Ensures absolute consistency, strict physics/magic compliance,
    and prevents leniency drift / plot armor throughout the RPG session.
    """

    STRICTNESS_PRESETS = {
        "deli": {
            "name": "🔥 Deli Modu (Kabus / Acımasız Simülasyon)",
            "description": "Oyuncu için her şey cehenneme döner. Dil modeli ve motor en ufak hatayı affetmez. Çevre düşmandır, şans neredeyse sıfırdır, düşmanlar dahi ve acımasızdır, kaynaklar aşırı kısıtlıdır.",
            "rules": [
                "ACIMASIZ CEZALANDIRMA: Oyuncunun her riskli hamlesi ve dikkatsizliği felaketle sonuçlanır; hata payı sıfırdır.",
                "DÜŞMAN DEHASI VE MERHAMETSİZLİK: Karşılaşılan tüm düşmanlar ve rakipler taktiksel zekaya sahiptir, pusu kurar, zayıflıkları hedefler ve asla merhamet göstermez.",
                "AŞIRI YIKICI HASAR VE KIRILGANLIK: Karakter aşırı kırılgandır. Alınan hasarlar (-20/-45 health_delta) kalıcı travmalara yol açar, yaralar hızla kangrene/kanamaya dönüşür.",
                "DÜŞMAN ÇEVRE VE ŞANSSIZLIK: Doğa, hava şartları, zemin ve şans faktörü daima oyuncunun aleyhine işler; silahlar tutukluk yapabilir, zemin kayabilir.",
                "ZİHİNSEL YIKIM VE PANİK: Dehşet, korku ve umutsuzluk karakterin iradesini hızla kırar (-15/-35 mental_delta).",
                "SIFIR SENARYO ZIRHI: Oyuncuyu kurtaracak mucizevi tesadüfler, son dakika yardımları veya yapay şanslar KESİNLİKLE YASAKTIR."
            ]
        },
        "ironclad": {
            "name": "Demir Kural (Tavizsiz / Ölümcül)",
            "description": "Evren kuralları ve fizik asla esnetilmez. Hatalar kalıcı sakatlık veya anında ölümle sonuçlanır. Sıfır senaryo zırhı.",
            "rules": [
                "Senaryo zırhı (Plot Armor) kesinlikle yasaktır; ana karakter ölebilir veya kalıcı sakat kalabilir.",
                "Fiziksel veya evren sınırlarını aşan eylemler anında ve acımasızca başarısız olur.",
                "Her riskli hareketin somut bir bedeli (kan kaybı, travma, mühimmat/ekipman kaybı) olmalıdır.",
                "Düşmanlar veya çevre unsurları aptal değildir; avantajı asla oyuncuya bedava sunmazlar."
            ]
        },
        "challenging": {
            "name": "Zorlayıcı (Yüksek Gerçekçilik)",
            "description": "Zorlu simülasyon. Eylemler mantık ve olasılık çerçevesinde değerlendirilir. Hatalar ciddi sonuçlar doğurur.",
            "rules": [
                "Gerçekçi insan biyolojisi veya evren sınırlamaları geçerlidir.",
                "Yaralanmalar tedavi edilmezse kötüleşir.",
                "Eylemlerin başarı şansı karakterin becerilerine, çevresel faktörlere ve mantığa dayanır.",
                "Aşırı cüretkar veya absürt hamleler başarısızlıkla sonuçlanır."
            ]
        },
        "balanced": {
            "name": "Dengeli Sandbox (Tutarlı & Dinamik)",
            "description": "Kurallar tutarlı bir şekilde korunur ancak hikaye akışına ve oyuncu yaratıcılığına alan tanınır.",
            "rules": [
                "Evren kuralları ve belirlenen dogma asla çiğnenemez.",
                "İmkansız eylemler mantıklı alternatiflere veya uyarılara dönüşür.",
                "Karakterin zayıflıkları ve evren kanunları her zaman olayları şekillendirir."
            ]
        }
    }

    @staticmethod
    def get_mode_directives(mode: str) -> str:
        """Returns fundamental directives based on realistic vs fantasy mode."""
        mode_clean = mode.lower().strip()
        if "tanri" in mode_clean or "god" in mode_clean:
            return (
                "### MOD: TANRI SİMÜLASYONU (DIVINE GOD SIMULATION & LIVING HUMANITY)\n"
                "- Oyuncu bu oyunda bir ölümlü değil; evreni, ölümlüleri, doğayı ve gerçekliği yöneten YÜCE BİR TANRIDIR.\n"
                "- Oyuncunun sözleri evren için İLAHİ FERMANDIR. Eylemleri kıtaları sarsabilir, doğa kanunlarını bükebilir, mucizeler ve felaketler yaratabilir.\n"
                "- YAŞAYAN İNSANLIK VE DERİN DUYGUSAL BAĞ: Bu evren soğuk bir istatistik tablosu değildir! Yeryüzünde nefes alan, acı çeken, sevinen, çocuklarını bağrına basan, açlıkla boğuşan ve Tanrı'ya umutla/korkuyla bakan gerçek insanlar yaşar. Tanrı, kullarının yüreklerindeki fısıltıları, sevgiyi ve hüznü hisseder.\n"
                "- MİKRO VE MAKRO BAKIŞ: Her turda göklerin sarsılışını anlattıktan sonra, kamerayı yeryüzündeki sıradan fanilerin ocak başlarına, tarlalarına ve tapınaklarına indir. Bir annenin, bir çiftçinin, bir çocuğun veya bir askerin yaşadığı derin insani anları tasvir et.\n"
                "- ÇOK SESLİ İNSAN KOROSU: Asla sadece 1-2 kişi konuşmasın! Her turda halkın farklı kesimlerinden (çiftçi, anne, çocuk, şüpheci, rahip veya kalabalıklar) en az 3-4 farklı ses ve replik [Kişi/Topluluk]; \"...\" formatında yer almalıdır.\n"
                "- EDEBİ UZUNLUK VE DERİNLİK: Hikaye metinleri KESİNLİKLE KISA VE YÜZEYSEL GEÇİŞTİRİLEMEZ. Her tur en az 4-6 dolgun, edebi, duyusal ve roman tadında paragraftan oluşmalıdır.\n"
                "- İMAN, KORKU VE KUDRET: Ölümlülerin duyduğu İMAN (Sevgi & Adanmışlık), KORKU (Huşu & Dehşet) ve İLAHİ KUDRET seviyesi dinamik olarak takip edilir."
            )
        elif "gercek" in mode_clean or "real" in mode_clean:
            return (
                "### MOD: KATI GERÇEKÇİ MOD (STRICT REALISM)\n"
                "- Bu oyun KATI GERÇEKÇİ fizik ve biyoloji kurallarıyla yönetilmektedir.\n"
                "- Senaryo zırhı (PLOT ARMOR) kesinlikle yasaktır; kararların ölümcül sonuçları doğrudan yansıtılır.\n"
                "- HİÇBİR BÜYÜ, DOĞAÜSTÜ GÜÇ VEYA SÜPER KAHRAMAN YETENEĞİ YOKTUR.\n"
                "- İnsan vücudu kırılgandır: Tek bir kurşun, derin bir bıçak darbesi, 3 metreden yüksekten düşüş, iç kanama veya enfeksiyon ölümcüldür.\n"
                "- Ağrı, şok, kan kaybı, kas yırtılması, hipotermi, açlık ve susuzluk gibi etkenler karakteri anında yavaşlatır ve zayıflatır.\n"
                "- Çevre sesleri, mermi balistiği, ağırlık, şarjör kapasitesi ve görüş mesafesi gerçek dünyadaki gibidir.\n"
                "- Karakter asla 'aksiyon filmi kahramanı' değildir; 2-3 silahlı insana karşı açık alanda durmak neredeyse kesin ölümdür."
            )
        else:
            return (
                "### MOD: KATI FANTASTİK / EPİK MOD (STRICT FANTASY / SCI-FI)\n"
                "- Bu oyun zengin bir fantezi/bilimkurgu evreninde geçmektedir ancak EVRENİN KENDİ İÇ MANTIĞI VE KURALLARI TAVİZSİZDİR.\n"
                "- Büyü veya ileri teknoloji bedelsiz değildir; belirlenen kurallara, mana/enerji sınırlarına, bedellerine ve ritüellere sıkı sıkıya bağlıdır.\n"
                "- Evrende tanımlanmayan tanrısal mucizeler veya rastgele kurtuluşlar meydana gelemez.\n"
                "- Büyülü varlıklar, lanetler veya gizemli fenomenler kendi belirlenmiş evren kanunlarına uymak zorundadır."
            )

    @classmethod
    def compile_rule_anchor(
        cls,
        universe_rules: str,
        universe_dogmas: str,
        mode: str,
        strictness: str = "challenging"
    ) -> str:
        """
        Creates an unbreakable rule anchor block to be included in every evaluation step.
        """
        strict_info = cls.STRICTNESS_PRESETS.get(strictness, cls.STRICTNESS_PRESETS["challenging"])
        mode_directive = cls.get_mode_directives(mode)

        rules_list_str = "\n".join([f"- {r}" for r in strict_info["rules"]])

        anchor = (
            "====================================================\n"
            "🚨 EVRENİN KIRILMAZ YASALARI VE HAKEM PROTOKOLÜ 🚨\n"
            "====================================================\n"
            f"{mode_directive}\n\n"
            f"### SEÇİLEN KATILIK SEVİYESİ: {strict_info['name']}\n"
            f"{rules_list_str}\n\n"
            "### TANIMLANMIŞ ÖZEL EVREN KURALLARI:\n"
            f"{universe_rules.strip() or 'Genel fizik ve mantık kuralları geçerlidir.'}\n\n"
            "### ASLA ÇİĞNENEMEZ DEĞİŞMEZ DOGMALAR (ABSOLUTE DOGMAS):\n"
            f"{universe_dogmas.strip() or 'Tanımlanan fizik/evren yasaları asla esnetilemez.'}\n\n"
            "### HAKEM TALİMATI (ARBITER MANDATE):\n"
            "1. Oyuncunun her eylemini yukarıdaki yasalara ve fizik/biyoloji/büyü sınırlarına göre tarafsız bir hakem gibi sına.\n"
            "2. Oyuncu imkansız, aşırı kolaycı veya evren yasalarını çiğneyen bir şey denerse, bunu kesinlikle BAŞARISIZ kıl ve kuralların sonuçlarını acımasızca işlet.\n"
            "3. Asla 'oyuncunun hevesi kırılmasın' diye mantıktan veya kurallardan taviz verme! Gerçekçi, tutarlı ve gerilimli sonuçlar oyunun temelidir.\n"
            "===================================================="
        )
        return anchor
