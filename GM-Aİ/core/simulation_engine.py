import re
from typing import Dict, Any, List, Optional

class InventoryEngine:
    """
    Deterministik Envanter ve Teçhizat Motoru.
    Eylemlerde kullanılan eşyaları, mermi adetlerini ve envanter mevcudiyetini
    doğrudan Python seviyesinde doğrular.
    """

    WEAPON_VERBS = ["ateş", "vurdu", "sıktı", "taramak", "tara", "nişan", "tetik", "kurşun", "ateşle", "vur"]

    @classmethod
    def evaluate_inventory_action(cls, action: str, inventory: List[str]) -> Dict[str, Any]:
        action_lower = action.lower()
        result = {
            "has_inventory_interaction": False,
            "matched_item": None,
            "ammo_consumed": 0,
            "ammo_remaining": None,
            "updated_item_name": None,
            "deterministic_directive": None
        }

        # 1. Silah ve Mermi Kontrolü
        for item in inventory:
            ammo_match = re.search(r'\((\d+)\s*(?:mermi|fişek|kurşun)\)', item, re.IGNORECASE)
            if ammo_match:
                ammo_count = int(ammo_match.group(1))
                item_words = [w.lower() for w in re.sub(r'\(.*?\)', '', item).split() if len(w) > 2]
                if any(v in action_lower for v in cls.WEAPON_VERBS) or any(w in action_lower for w in item_words):
                    result["has_inventory_interaction"] = True
                    result["matched_item"] = item
                    if ammo_count > 0:
                        new_count = ammo_count - 1
                        result["ammo_consumed"] = 1
                        result["ammo_remaining"] = new_count
                        base_name = re.sub(r'\s*\(\d+\s*(?:mermi|fişek|kurşun)\)', '', item).strip()
                        result["updated_item_name"] = f"{base_name} ({new_count} mermi)" if new_count > 0 else f"{base_name} (BOŞ)"
                        result["deterministic_directive"] = (
                            f"DETERMİNİSTİK SİMÜLASYON KURALI: Oyuncu '{item}' kullandı. "
                            f"1 adet mermi harcandı, kalan mermi: {new_count}. "
                            f"State içinde 'inventory_removed': ['{item}'] ve 'inventory_added': ['{result['updated_item_name']}'] olarak güncelle."
                        )
                    else:
                        result["deterministic_directive"] = (
                            f"DETERMİNİSTİK SİMÜLASYON KURALI: Oyuncunun '{item}' silahında MERMİ BİTMİŞTİR (0 mermi). "
                            f"Silah sadece tık sesi çıkarır, ateş alamaz! Hakem eylemi mermisizlik nedeniyle başarısız saymalıdır."
                        )
                    return result

        return result


class SurvivalEngine:
    """
    Deterministik Hayatta Kalma ve Çevre Motoru.
    Açık kanama, enfeksiyon, dondurucu soğuk maruziyeti gibi biyolojik riskleri
    tur bazında hesaplar. Deli modunda ceza kat sayılarını katlar.
    """

    @classmethod
    def evaluate_turn_conditions(cls, game_state: Dict[str, Any]) -> List[str]:
        directives = []
        status_effects = [e.lower() for e in game_state.get("status_effects", [])]
        is_deli = game_state.get("mode_data", {}).get("strictness") == "deli"

        if is_deli:
            directives.append(
                "DETERMİNİSTİK DELİ MODU KURALI (ACIMASIZ ÇEVRE & DÜŞMANLAR): "
                "Oyun motoru ve dünya oyuncu aleyhine kuruludur. Her hamlede beklenmedik terslikler, "
                "zemin kayması, silah tutukluğu/arızası, düşman pusuları ve aşırı sert fiziksel sonuçlar üret. "
                "Oyuncunun şansı sıfırdır, hatalar ölümcüldür."
            )

        if any("kanama" in e for e in status_effects):
            if is_deli:
                directives.append(
                    "DETERMİNİSTİK DELİ MODU (AĞIR KAN KAYBI): Karakterde aktif 'Kanama' var! "
                    "Yara ölümcül hızla kan kaybettiriyor. Bu tur en az -15 ile -35 arası can kaybı (health_delta) ZORUNLUDUR! "
                    "Acil dikiş veya baskı yapılmadıkça bilinç bulanıklaşmalıdır."
                )
            else:
                directives.append(
                    "DETERMİNİSTİK SAĞLIK KURALI: Karakterde aktif 'Kanama' etkisi var. "
                    "Bandajlanmadığı sürece bu tur -5 ile -15 arası can kaybı (health_delta) uygulanması zorunludur."
                )

        if any("hipotermi" in e for e in status_effects):
            if is_deli:
                directives.append(
                    "DETERMİNİSTİK DELİ MODU (DONDURUCU ŞOK): Karakterde 'Hipotermi' var! "
                    "Donma eşiğine gelindi; zihinsel direnç -25, can -15 düşmeli, uzuvlar hissizleştiği için eylemler aksamalıdır."
                )
            else:
                directives.append(
                    "DETERMİNİSTİK SAĞLIK KURALI: Karakterde 'Hipotermi' etkisi var. "
                    "Isınmadığı takdirde zihinsel direnç -10, can -5 düşmelidir."
                )

        if any("zehir" in e for e in status_effects):
            if is_deli:
                directives.append(
                    "DETERMİNİSTİK DELİ MODU (ÖLÜMCÜL NÖROTOKSİN): Karakterde 'Zehirlenme' var! "
                    "Toksin organları parçalıyor; her tur -20 can kaybı ve -20 zihinsel halüsinasyon zorunludur."
                )
            else:
                directives.append(
                    "DETERMİNİSTİK SAĞLIK KURALI: Karakterde 'Zehirlenme' etkisi var. "
                    "Panzehir alınmadıkça her tur -10 can kaybı gerçekleşmelidir."
                )

        return directives


class SimulationCore:
    """
    Tüm deterministik simülasyon kurallarını birleştiren merkezi orkestratör.
    Gemini'ye gitmeden önce eylemi fiziksel/envantersel filtreden geçirir.
    """

    @classmethod
    def process_action(cls, action: str, game_state: Dict[str, Any]) -> Dict[str, Any]:
        inv = game_state.get("inventory", [])
        inv_eval = InventoryEngine.evaluate_inventory_action(action, inv)
        surv_eval = SurvivalEngine.evaluate_turn_conditions(game_state)

        directives = []
        if inv_eval.get("deterministic_directive"):
            directives.append(inv_eval["deterministic_directive"])
        directives.extend(surv_eval)

        return {
            "inventory_eval": inv_eval,
            "survival_directives": surv_eval,
            "all_directives": directives
        }