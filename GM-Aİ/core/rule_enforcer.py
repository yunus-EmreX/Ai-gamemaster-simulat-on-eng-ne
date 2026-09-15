from typing import Dict, Any, List

class RuleEnforcer:
    """
    Ensures absolute consistency, strict physics/magic compliance,
    and prevents leniency drift / plot armor throughout the RPG session.
    """

    STRICTNESS_PRESETS = {
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
        if "gercek" in mode_clean or "real" in mode_clean:
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
