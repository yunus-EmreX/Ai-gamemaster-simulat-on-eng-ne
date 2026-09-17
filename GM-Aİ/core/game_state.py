import os
import json
import time
import re
from typing import Dict, Any, List, Optional

class GameState:
    """
    Manages the active game session, player stats, inventory,
    turn logs, NPC relationships, GM cheats, and serialization (save/load).
    """

    SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "saves")

    COMMON_ROLE_WORDS = {
        "kadın", "kadınlar", "kız", "kızlar", "adam", "adamlar", "asker", "askerler",
        "genç", "muhafız", "muhafızı", "nöbetçi", "çete", "lider", "lideri", "usta",
        "diğer", "biri", "doktor", "komutan", "komutanı", "albay", "yüzbaşı", "çavuş",
        "onbaşı", "er", "bey", "hanım", "savaşçı", "savaşçısı", "tek teknisyen", "teknisyeni",
        "subay", "subayı", "rehine", "tutsak", "esir", "köle", "reis", "rahip", "kral",
        "vezir", "prens", "prenses", "halk", "insan", "fani", "şey", "biriyle",
        "önce", "sonra", "için", "gibi", "kadar", "daha", "veya", "çünkü"
    }

    # Robust regex patterns with word boundaries (\b) to eliminate false positives
    # (e.g. 'gönüllü', 'ölümsüz', 'ölümüne', 'ölesiye' will NOT falsely trigger death)
    DEATH_PATTERN = re.compile(
        r'\b(öldü|ölen|katledildi|hayatını kaybetti|can verdi|şehit oldu|katledilmiş|ceset|vefat etti|vefat|ruhu çekildi|canı söndü|yok edildi)\b|\bölü\b',
        re.IGNORECASE
    )
    DEPARTED_PATTERN = re.compile(
        r'\b(ayrıldı|gitti|uzaklaştı|kaçtı|terk etti|kayboldu|gözden kayboldu)\b',
        re.IGNORECASE
    )

    @classmethod
    def is_npc_present_in_text(cls, npc_name: str, text: str) -> bool:
        """Determines if an NPC is mentioned or speaking in a given scene text with strict word boundaries."""
        if not npc_name or not text:
            return False
        name_clean = npc_name.lower().strip()
        text_clean = text.lower()
        
        # Dialogue format: [Karakter Adı]; "..."
        if f"[{name_clean}" in text_clean:
            return True
            
        # Full name word boundary check
        if re.search(rf'\b{re.escape(name_clean)}\b', text_clean):
            return True
            
        # Extract specific proper noun tokens with word boundaries
        # Prevents short tokens like 'can' matching 'canavar', 'han' matching 'herhangi'
        tokens = [w for w in re.findall(r'\w+', name_clean) if len(w) >= 3 and w not in cls.COMMON_ROLE_WORDS]
        for t in tokens:
            if re.search(rf'\b{re.escape(t)}\b', text_clean):
                return True
        return False

    def __init__(self):
        os.makedirs(self.SAVES_DIR, exist_ok=True)
        self.reset()

    def reset(self):
        self.character: Dict[str, Any] = {}
        self.universe: Dict[str, Any] = {}
        self.mode_data: Dict[str, Any] = {}
        self.system_instruction: str = ""
        self.health: int = 100
        self.mental: int = 100
        self.location: str = "Bilinmeyen Bölge"
        self.inventory: List[str] = []
        self.status_effects: List[str] = []
        self.npc_relationships: Dict[str, str] = {}
        self.npc_last_seen: Dict[str, int] = {}
        self.known_world_npcs: Dict[str, Dict[str, Any]] = {}
        self.god_mode: bool = False
        self.pending_gm_directives: List[str] = []
        self.turn_count: int = 0
        self.last_autosave_turn: int = 0
        self.is_game_over: bool = False
        self.game_over_reason: str = ""
        self.story_log: List[Dict[str, Any]] = []
        self.raw_chat_history: List[Dict[str, Any]] = []
        self.last_suggested_actions: List[str] = []
        self.last_arbiter_verdict: str = ""
        self.last_rule_warnings: str = ""

        # God Sim Mode Variables
        self.is_god_sim: bool = False
        self.faith: int = 50                 # İman (%0-100)
        self.fear: int = 15                  # Korku (%0-100)
        self.divine_power: int = 100         # İlahi Kudret (%0-100)
        self.civilization_era: str = "Yaratılış ve Kabileler Çağı"
        self.prayers: List[Dict[str, Any]] = []      # Aktif ölümlü duaları
        self.prophets: List[str] = []                # Seçilmiş peygamberler/avatarlar
        self.divine_decrees: List[str] = []          # Değiştirilen evren yasaları

    def initialize_game(
        self,
        character: Dict[str, Any],
        universe: Dict[str, Any],
        mode_data: Dict[str, Any],
        system_instruction: str,
        prologue_data: Dict[str, Any]
    ):
        """Initializes the session from prologue data."""
        self.reset()
        self.character = character
        self.universe = universe
        self.mode_data = mode_data
        self.system_instruction = system_instruction

        # Initialize inventory from character if not already in prologue
        initial_inv = character.get("inventory", [])
        if isinstance(initial_inv, str):
            initial_inv = [item.strip() for item in initial_inv.split(",") if item.strip()]
        self.inventory = list(initial_inv)

        # Apply prologue state updates
        state_updates = prologue_data.get("state_updates", {})
        self.health = max(0, min(100, 100 + state_updates.get("health_delta", 0)))
        self.mental = max(0, min(100, 100 + state_updates.get("mental_delta", 0)))
        if state_updates.get("location"):
            self.location = state_updates.get("location")
        
        for item in state_updates.get("inventory_added", []):
            if item and item not in self.inventory:
                self.inventory.append(item)
        
        for eff in state_updates.get("status_effects", []):
            if eff and eff not in self.status_effects:
                self.status_effects.append(eff)

        # NPC Relationships from prologue
        self.npc_relationships = {}
        self.npc_last_seen = {}
        self.known_world_npcs = {}
        npc_updates = state_updates.get("npc_attitude_updates", {})
        if isinstance(npc_updates, dict):
            for npc, att in npc_updates.items():
                if npc and att:
                    clean = str(npc).strip()
                    att_clean = str(att).strip()
                    self.npc_relationships[clean] = att_clean
                    self.npc_last_seen[clean] = 0
                    self.known_world_npcs[clean] = {
                        "name": clean,
                        "attitude": att_clean,
                        "status": "Aktif Sahnede",
                        "last_seen_turn": 0,
                        "location": self.location
                    }

    @staticmethod
    def normalize_prayer(p: Any, default_id: str = "p1") -> Optional[Dict[str, Any]]:
        """Ensures a prayer dictionary has uniform keys for frontend and engine."""
        if not isinstance(p, dict):
            return None
        item = dict(p)
        item["id"] = str(item.get("id") or default_id)

        mortal = (
            item.get("mortal_name") or
            item.get("mortal") or
            item.get("name") or
            item.get("person") or
            item.get("fani") or
            item.get("speaker") or
            "Bilinmeyen Fani"
        )
        item["mortal_name"] = str(mortal).strip()
        item["mortal"] = str(mortal).strip()

        loc = (
            item.get("mortal_location") or
            item.get("location") or
            item.get("place") or
            item.get("mekan") or
            item.get("bolge") or
            "Yeryüzü"
        )
        item["mortal_location"] = str(loc).strip()
        item["location"] = str(loc).strip()

        text = (
            item.get("prayer_text") or
            item.get("prayer") or
            item.get("text") or
            item.get("content") or
            item.get("yakari") or
            item.get("dua") or
            item.get("dilek") or
            ""
        )
        item["prayer_text"] = str(text).strip()
        item["prayer"] = str(text).strip()

        ptype = item.get("prayer_type") or item.get("type") or item.get("tur") or "Dua"
        item["prayer_type"] = str(ptype).strip()

        raw_status = str(item.get("status") or "beklemede").lower().strip()
        if "kabul" in raw_status or "grant" in raw_status:
            status = "kabul_edildi"
        elif "gazap" in raw_status or "smite" in raw_status:
            status = "gazap_yagdirildi"
        elif "bük" in raw_status or "buk" in raw_status or "twist" in raw_status:
            status = "bukuldu"
        elif "red" in raw_status or "ignore" in raw_status or "görmezden" in raw_status:
            status = "reddedildi"
        else:
            status = "beklemede"
        item["status"] = status
        return item

    @staticmethod
    def normalize_prophet(p: Any) -> Optional[Dict[str, Any]]:
        """Ensures a prophet dictionary has uniform keys for frontend and engine."""
        if not p:
            return None
        if isinstance(p, str):
            clean = p.strip()
            if not clean:
                return None
            return {
                "name": clean,
                "role": "Seçilmiş Peygamber",
                "region": "Kutsal Topraklar",
                "doctrine": "Tanrı'nın ilahi iradesini ve fermanlarını yayar."
            }
        if isinstance(p, dict):
            name = (
                p.get("name") or
                p.get("prophet") or
                p.get("peygamber") or
                p.get("fani") or
                p.get("person") or
                p.get("elci") or
                "Seçilmiş Fani"
            )
            role = (
                p.get("role") or
                p.get("title") or
                p.get("unvan") or
                p.get("gorev") or
                "Başpeygamber / Elçi"
            )
            region = (
                p.get("region") or
                p.get("location") or
                p.get("place") or
                p.get("mekan") or
                p.get("sehir") or
                "Yeryüzü"
            )
            doctrine = (
                p.get("doctrine") or
                p.get("teaching") or
                p.get("ogreti") or
                p.get("vahy") or
                p.get("mesaj") or
                ""
            )
            return {
                "name": str(name).strip(),
                "role": str(role).strip(),
                "region": str(region).strip(),
                "doctrine": str(doctrine).strip()
            }
        return None

    def initialize_game(
        self,
        character: Dict[str, Any],
        universe: Dict[str, Any],
        mode_data: Dict[str, Any],
        system_instruction: str = "",
        prologue_data: Optional[Dict[str, Any]] = None
    ):
        """Initializes a new game session with prologue outcomes."""
        self.reset()
        self.character = character
        self.universe = universe
        self.mode_data = mode_data
        self.system_instruction = system_instruction

        # If realistic mode, enforce godmode OFF initially
        if mode_data.get("mode") == "realistic":
            self.god_mode = False

        if not prologue_data:
            prologue_data = {}

        state_updates = prologue_data.get("state_updates", {})
        self.health = max(0, min(100, 100 + state_updates.get("health_delta", 0)))
        self.mental = max(0, min(100, 100 + state_updates.get("mental_delta", 0)))
        self.location = state_updates.get("location", character.get("initial_location", "Bilinmeyen Başlangıç"))
        self.inventory = list(character.get("inventory", []))
        for item in state_updates.get("inventory_added", []):
            if item and item not in self.inventory:
                self.inventory.append(item)

        self.status_effects = state_updates.get("status_effects", ["Normal"])

        # NPC Relationships from prologue
        self.npc_relationships = {}
        self.npc_last_seen = {}
        self.known_world_npcs = {}
        npc_updates = state_updates.get("npc_attitude_updates", {})
        if isinstance(npc_updates, dict):
            for npc, att in npc_updates.items():
                if npc and att:
                    clean = str(npc).strip()
                    att_clean = str(att).strip()
                    self.npc_relationships[clean] = att_clean
                    self.npc_last_seen[clean] = 0
                    self.known_world_npcs[clean] = {
                        "name": clean,
                        "attitude": att_clean,
                        "status": "Aktif Sahnede",
                        "last_seen_turn": 0,
                        "location": self.location
                    }

        # God Sim Mode Initialization
        mode_val = str(mode_data.get("mode", "")).lower().strip()
        if "tanri" in mode_val or "god" in mode_val:
            self.is_god_sim = True
            self.god_mode = True
            self.faith = 50
            self.fear = 15
            self.divine_power = 100
            self.civilization_era = state_updates.get("civilization_era", "Yaratılış ve Kabileler Çağı")
            seed_prayers = [
                {
                    "id": "p1",
                    "mortal_name": "Kabile Reisi Ogan",
                    "mortal_location": "Kuru Vadi",
                    "prayer_type": "yağmur",
                    "prayer_text": "Yüce Yaratıcı, kuraklıktan kavrulduk! Yağmur gönder, kabilenin ilk hasadını sana adayalım!",
                    "status": "beklemede"
                },
                {
                    "id": "p2",
                    "mortal_name": "Genç Avcı Asena",
                    "mortal_location": "Karanlık Mağaralar",
                    "prayer_type": "kurtuluş",
                    "prayer_text": "Karanlıkta kükreyen canavar kardeşimi yaraladı. Bize onu yenecek ilahi bir silah ya da cesaret bahşet!",
                    "status": "beklemede"
                }
            ]
            raw_prayers = state_updates.get("prayers_generated") or seed_prayers
            self.prayers = []
            for i, rp in enumerate(raw_prayers):
                norm = self.normalize_prayer(rp, f"p{i+1}")
                if norm:
                    self.prayers.append(norm)
            raw_prophets = state_updates.get("prophets_added") or state_updates.get("prophets") or []
            self.prophets = []
            for pr in raw_prophets:
                norm_pr = self.normalize_prophet(pr)
                if norm_pr and not any(p.get("name") == norm_pr.get("name") for p in self.prophets):
                    self.prophets.append(norm_pr)
            self.divine_decrees = state_updates.get("divine_decrees", [])

        self.last_arbiter_verdict = prologue_data.get("arbiter_verdict", "Giriş ortamı mühürlendi.")
        self.last_rule_warnings = prologue_data.get("rule_warnings", "Evren kuralları ve envanter aktif.")

        # Add prologue to story log
        self.story_log.append({
            "turn": 0,
            "action": "Hikaye Başlangıcı",
            "story": prologue_data.get("story", ""),
            "arbiter_verdict": self.last_arbiter_verdict,
            "rule_warnings": self.last_rule_warnings,
            "timestamp": time.strftime("%H:%M:%S")
        })

    def apply_turn(self, player_action: str, turn_data: Dict[str, Any], sim_eval: Optional[Dict[str, Any]] = None):
        """Applies updates from a player's action and model's response with deterministic rule enforcement."""
        from core.rule_enforcer import RuleEnforcer
        turn_data = RuleEnforcer.enforce_post_turn(self, player_action, turn_data, sim_eval)

        self.turn_count += 1
        state_updates = turn_data.get("state_updates", {})

        # Health & Mental (or God Sim Faith/Fear/Power)
        health_delta = state_updates.get("health_delta", 0)
        mental_delta = state_updates.get("mental_delta", 0)
        if self.god_mode:
            self.health = 100
            self.mental = 100
        else:
            self.health = max(0, min(100, self.health + health_delta))
            self.mental = max(0, min(100, self.mental + mental_delta))

        # God Sim Specific Metrics Updates
        if self.is_god_sim:
            faith_delta = state_updates.get("faith_delta", 0)
            fear_delta = state_updates.get("fear_delta", 0)
            power_delta = state_updates.get("divine_power_delta", state_updates.get("power_delta", -3))

            self.faith = max(0, min(100, self.faith + faith_delta))
            self.fear = max(0, min(100, self.fear + fear_delta))
            self.divine_power = max(0, min(100, self.divine_power + power_delta))

            if state_updates.get("civilization_era"):
                self.civilization_era = state_updates.get("civilization_era")

            new_prayers = state_updates.get("prayers_generated")
            if new_prayers and isinstance(new_prayers, list):
                for i, np in enumerate(new_prayers):
                    norm = self.normalize_prayer(np, f"p_{len(self.prayers) + i + 1}")
                    if norm:
                        existing = next((p for p in self.prayers if p.get("id") == norm.get("id") or (p.get("prayer_text") and p.get("prayer_text") == norm.get("prayer_text"))), None)
                        if existing:
                            if existing.get("status") == "beklemede":
                                existing.update(norm)
                        else:
                            self.prayers.append(norm)

            for pr in state_updates.get("prophets_added", []):
                norm_pr = self.normalize_prophet(pr)
                if norm_pr and not any(p.get("name") == norm_pr.get("name") for p in self.prophets):
                    self.prophets.append(norm_pr)

            decree = state_updates.get("decree_established") or state_updates.get("cosmic_law")
            if decree and decree not in self.divine_decrees:
                self.divine_decrees.append(decree)

        # Location
        if state_updates.get("location"):
            self.location = state_updates.get("location")

        # Inventory additions
        for item in state_updates.get("inventory_added", []):
            if item and item not in self.inventory:
                self.inventory.append(item)

        # Inventory removals
        for item in state_updates.get("inventory_removed", []):
            # Match item by name or partial
            for inv_item in list(self.inventory):
                if item.lower() in inv_item.lower() or inv_item.lower() in item.lower():
                    self.inventory.remove(inv_item)
                    break

        # Status effects
        new_effects = state_updates.get("status_effects")
        if new_effects is not None and isinstance(new_effects, list):
            self.status_effects = new_effects

        # NPC Tracking, Deceased Removal & Scene Pruning
        story_text = turn_data.get("story", "")
        combined_text = (story_text + " " + player_action).lower()

        # 0. Reactivate any known world NPC if they or their name is mentioned in this turn's action or story
        for k_name, k_info in list(self.known_world_npcs.items()):
            if k_name not in self.npc_relationships and "ölü" not in str(k_info.get("status", "")).lower():
                if self.is_npc_present_in_text(k_name, combined_text):
                    self.npc_relationships[k_name] = k_info.get("attitude", "Tanıdık")
                    self.npc_last_seen[k_name] = self.turn_count
                    k_info["status"] = "Aktif Sahnede"
                    k_info["last_seen_turn"] = self.turn_count
                    k_info["location"] = self.location

        # 1. Update/Add NPCs from model's attitude updates
        npc_updates = state_updates.get("npc_attitude_updates", {})
        if isinstance(npc_updates, dict):
            for npc, att in npc_updates.items():
                if npc and att:
                    clean = str(npc).strip()
                    att_clean = str(att).strip()
                    self.npc_relationships[clean] = att_clean
                    self.npc_last_seen[clean] = self.turn_count
                    if clean not in self.known_world_npcs:
                        self.known_world_npcs[clean] = {
                            "name": clean,
                            "attitude": att_clean,
                            "status": "Aktif Sahnede",
                            "last_seen_turn": self.turn_count,
                            "location": self.location
                        }
                    else:
                        self.known_world_npcs[clean]["attitude"] = att_clean
                        self.known_world_npcs[clean]["status"] = "Aktif Sahnede"
                        self.known_world_npcs[clean]["last_seen_turn"] = self.turn_count
                        self.known_world_npcs[clean]["location"] = self.location

        # 2. Check explicitly active NPCs in scene
        active_scene_npcs = state_updates.get("active_scene_npcs", [])
        if isinstance(active_scene_npcs, list):
            for npc in active_scene_npcs:
                clean = str(npc).strip()
                if clean:
                    if clean in self.known_world_npcs:
                        self.npc_relationships[clean] = self.known_world_npcs[clean].get("attitude", "Aktif")
                        self.known_world_npcs[clean]["status"] = "Aktif Sahnede"
                        self.known_world_npcs[clean]["last_seen_turn"] = self.turn_count
                        self.known_world_npcs[clean]["location"] = self.location
                    self.npc_last_seen[clean] = self.turn_count

        # 3. Detect if existing NPCs are mentioned or speaking in this turn's story or action
        for npc_name in list(self.npc_relationships.keys()):
            if self.is_npc_present_in_text(npc_name, combined_text):
                self.npc_last_seen[npc_name] = self.turn_count
                if npc_name in self.known_world_npcs:
                    self.known_world_npcs[npc_name]["last_seen_turn"] = self.turn_count
                    self.known_world_npcs[npc_name]["status"] = "Aktif Sahnede"
                    self.known_world_npcs[npc_name]["location"] = self.location

        # 4. Remove explicitly deceased or departed NPCs
        departed = state_updates.get("deceased_or_departed_npcs", []) or state_updates.get("npcs_removed", [])
        if isinstance(departed, list):
            for dep in departed:
                clean_dep = str(dep).strip()
                if not clean_dep:
                    continue
                clean_dep_lower = clean_dep.lower()
                is_death = bool(self.DEATH_PATTERN.search(clean_dep_lower))
                for npc_name in list(self.npc_relationships.keys()):
                    if clean_dep_lower in npc_name.lower() or npc_name.lower() in clean_dep_lower:
                        self.remove_npc(npc_name)
                for npc_name, k_info in list(self.known_world_npcs.items()):
                    if clean_dep_lower in npc_name.lower() or npc_name.lower() in clean_dep_lower:
                        k_info["status"] = "[Ölü - Hayatını Kaybetti]" if is_death else "[Uzakta / Ayrıldı]"

        # 5. Clean dead or absent (2-3 scenes inactive) NPCs from active scene
        self.clean_stale_npcs()

        # Game over check
        if not self.god_mode:
            if self.health <= 0:
                self.is_game_over = True
                self.game_over_reason = state_updates.get("game_over_reason") or "Ölümcül yaralanmalar nedeniyle hayatını kaybettin."
            elif state_updates.get("is_game_over"):
                self.is_game_over = True
                self.game_over_reason = state_updates.get("game_over_reason") or "Hikaye sona erdi."

        self.last_arbiter_verdict = turn_data.get("arbiter_verdict", "")
        self.last_rule_warnings = turn_data.get("rule_warnings", "")

        story_clean = turn_data.get("story", "")
        if isinstance(story_clean, str) and story_clean.strip().startswith("{") and ('"story"' in story_clean or '"arbiter_verdict"' in story_clean):
            m = re.search(r'"story"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"[a-zA-Z_]+"|\s*\}\s*$|$)', story_clean)
            if m:
                story_clean = m.group(1).replace(r'\"', '"').replace(r'\n', '\n').replace(r'\\', '\\')

        self.story_log.append({
            "turn": self.turn_count,
            "action": player_action,
            "story": story_clean,
            "arbiter_verdict": self.last_arbiter_verdict,
            "rule_warnings": self.last_rule_warnings,
            "health_delta": health_delta,
            "mental_delta": mental_delta,
            "timestamp": time.strftime("%H:%M:%S")
        })

    # --- GAME MASTER / CHEAT PANEL METHODS ---
    def add_item(self, item_name: str) -> bool:
        clean = item_name.strip()
        if clean and clean not in self.inventory:
            self.inventory.append(clean)
            return True
        return False

    def remove_item(self, item_name: str) -> bool:
        clean = item_name.strip()
        if clean in self.inventory:
            self.inventory.remove(clean)
            return True
        for it in list(self.inventory):
            if clean.lower() in it.lower():
                self.inventory.remove(it)
                return True
        return False

    def set_health(self, val: int):
        self.health = max(0, min(100, int(val)))
        if self.health > 0:
            self.is_game_over = False

    def set_mental(self, val: int):
        self.mental = max(0, min(100, int(val)))

    def toggle_god_mode(self) -> bool:
        self.god_mode = not self.god_mode
        if self.god_mode:
            self.health = 100
            self.mental = 100
            self.is_game_over = False
        return self.god_mode

    def set_npc_attitude(self, npc_name: str, attitude: str):
        clean_name = npc_name.strip()
        clean_att = attitude.strip()
        if clean_name:
            self.npc_relationships[clean_name] = clean_att
            self.npc_last_seen[clean_name] = self.turn_count
            if clean_name not in self.known_world_npcs:
                self.known_world_npcs[clean_name] = {
                    "name": clean_name,
                    "attitude": clean_att,
                    "status": "Aktif Sahnede",
                    "last_seen_turn": self.turn_count,
                    "location": self.location
                }
            else:
                self.known_world_npcs[clean_name]["attitude"] = clean_att
                self.known_world_npcs[clean_name]["status"] = "Aktif Sahnede"
                self.known_world_npcs[clean_name]["last_seen_turn"] = self.turn_count

    def remove_npc(self, npc_name: str):
        """Removes an NPC from the active scene list (keeps world memory intact)."""
        clean = npc_name.strip()
        target_keys = [k for k in self.npc_relationships if k == clean or k.lower() == clean.lower()]
        for k in target_keys:
            del self.npc_relationships[k]
        target_seen_keys = [k for k in self.npc_last_seen if k == clean or k.lower() == clean.lower()]
        for k in target_seen_keys:
            del self.npc_last_seen[k]

    def purge_npc(self, npc_name: str):
        """Completely purges an NPC from both active scene and known world memory (GM hard action)."""
        self.remove_npc(npc_name)
        target_known = [k for k in self.known_world_npcs if k == npc_name.strip() or k.lower() == npc_name.strip().lower()]
        for k in target_known:
            del self.known_world_npcs[k]

    def clean_stale_npcs(self):
        """
        Removes dead NPCs and characters absent for 3 or more turns from active scene,
        while preserving alive characters in known_world_npcs.
        Uses exact word boundaries to avoid false positives like 'gönüllü', 'ölümsüz', 'ölümüne'.
        """
        for npc_name, att_val in list(self.npc_relationships.items()):
            att_lower = str(att_val).lower()
            name_lower = npc_name.lower()
            
            # If name or attitude explicitly signals death using word boundaries
            if self.DEATH_PATTERN.search(att_lower) or "(ölü)" in name_lower or "(yaralı - öldü)" in name_lower:
                self.remove_npc(npc_name)
                if npc_name in self.known_world_npcs:
                    self.known_world_npcs[npc_name]["status"] = "[Ölü - Hayatını Kaybetti]"
                continue

            # If attitude contains departed keywords using word boundaries
            if self.DEPARTED_PATTERN.search(att_lower):
                self.remove_npc(npc_name)
                if npc_name in self.known_world_npcs:
                    self.known_world_npcs[npc_name]["status"] = "[Uzakta / Ayrıldı]"
                continue

            # Staleness check: absent for 3 or more turns from current scene
            last_seen = self.npc_last_seen.get(npc_name, self.turn_count)
            if (self.turn_count - last_seen) >= 3:
                self.remove_npc(npc_name)
                if npc_name in self.known_world_npcs:
                    if not str(self.known_world_npcs[npc_name].get("status", "")).startswith("[Ölü"):
                        self.known_world_npcs[npc_name]["status"] = "[Mevcut Sahnede Değil / Uzakta]"

    def generate_saga_chronicle(self, max_entries: int = 200) -> str:
        """
        Generates a chronological milestone summary of past scenes and key events from story_log.
        Guarantees Gemini never forgets past locations, major decisions, wounds, or storyline developments.
        """
        if not self.story_log:
            return "Henüz geçmiş sahne kaydı yok."

        entries = self.story_log
        if len(entries) > max_entries:
            chronicle_entries = entries[:2] + entries[-(max_entries - 2):]
            has_gap = True
        else:
            chronicle_entries = entries
            has_gap = False

        lines = []
        prev_turn = -1
        for idx, entry in enumerate(chronicle_entries):
            turn = entry.get("turn", idx)
            if has_gap and idx == 2 and prev_turn != -1 and (turn - prev_turn) > 1:
                lines.append(f"... [Aradaki {turn - prev_turn - 1} tur boyunca yolculuk ve olaylar devam etti] ...")
            prev_turn = turn

            action = entry.get("action", "").strip()
            verdict = entry.get("arbiter_verdict", "").strip()
            story = entry.get("story", "").strip()
            health_d = entry.get("health_delta")
            mental_d = entry.get("mental_delta")

            stat_notes = []
            if health_d and health_d != 0:
                stat_notes.append(f"Sağlık: {health_d:+d}")
            if mental_d and mental_d != 0:
                stat_notes.append(f"Zihin: {mental_d:+d}")
            stat_str = f" ({', '.join(stat_notes)})" if stat_notes else ""

            if turn == 0:
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', story) if s.strip()]
                prologue_brief = " ".join(sentences[:2]) if sentences else story[:160]
                if len(prologue_brief) > 180:
                    prologue_brief = prologue_brief[:177] + "..."
                lines.append(f"• [Tur 0 - Hikaye Başlangıcı]: {prologue_brief}")
            else:
                outcome = verdict
                if not outcome or outcome in ("Eylem değerlendirildi.", "Hakem tespiti."):
                    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', story) if s.strip()]
                    outcome = sentences[0] if sentences else story[:120]
                if len(outcome) > 180:
                    outcome = outcome[:177] + "..."
                lines.append(f"• [Tur {turn}]: Oyuncu: \"{action}\" ➔ Gelişme: {outcome}{stat_str}")

        return "\n".join(lines)

    def clear_negative_effects(self):
        # Keep positive or neutral tags, remove harms
        bad_words = ["kanama", "kırık", "zehir", "yorgunluk", "hipotermi", "ağrı", "şok", "panik", "felç", "açlık"]
        self.status_effects = [e for e in self.status_effects if not any(w in e.lower() for w in bad_words)]
        if not self.status_effects:
            self.status_effects = ["Dinç", "Sağlıklı"]

    def add_gm_directive(self, directive: str):
        clean = directive.strip()
        if clean:
            self.pending_gm_directives.append(clean)

    def pop_gm_directives(self) -> List[str]:
        directives = list(self.pending_gm_directives)
        self.pending_gm_directives.clear()
        return directives

    def answer_prayer(self, prayer_id: str, decision: str, notes: str = "") -> Optional[Dict[str, Any]]:
        """Answers or resolves an active prayer in God Sim mode."""
        status_map = {
            "grant": "kabul_edildi",
            "smite": "gazap_yagdirildi",
            "twist": "bukuldu",
            "ignore": "reddedildi"
        }
        status_val = status_map.get(decision.lower(), decision)
        for p in self.prayers:
            if p.get("id") == prayer_id or prayer_id.lower() in str(p.get("mortal_name", p.get("mortal", ""))).lower():
                p["status"] = status_val
                p["divine_response"] = notes or f"İlahi karar: {status_val}"
                return p
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the game state to a dictionary."""
        return {
            "character": self.character,
            "universe": self.universe,
            "mode_data": self.mode_data,
            "system_instruction": self.system_instruction,
            "health": self.health,
            "mental": self.mental,
            "location": self.location,
            "inventory": self.inventory,
            "status_effects": self.status_effects,
            "npc_relationships": self.npc_relationships,
            "npc_last_seen": self.npc_last_seen,
            "known_world_npcs": self.known_world_npcs,
            "god_mode": self.god_mode,
            "pending_gm_directives": self.pending_gm_directives,
            "turn_count": self.turn_count,
            "last_autosave_turn": self.last_autosave_turn,
            "is_game_over": self.is_game_over,
            "game_over_reason": self.game_over_reason,
            "story_log": self.story_log,
            "last_suggested_actions": self.last_suggested_actions,
            "last_arbiter_verdict": self.last_arbiter_verdict,
            "last_rule_warnings": self.last_rule_warnings,
            "is_god_sim": self.is_god_sim,
            "faith": self.faith,
            "fear": self.fear,
            "divine_power": self.divine_power,
            "civilization_era": self.civilization_era,
            "prayers": self.prayers,
            "prophets": self.prophets,
            "divine_decrees": self.divine_decrees,
            "saved_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def from_dict(self, data: Dict[str, Any]):
        """Restores the game state from a dictionary."""
        self.character = data.get("character", {})
        self.universe = data.get("universe", {})
        self.mode_data = data.get("mode_data", {})
        self.system_instruction = data.get("system_instruction", "")
        self.health = data.get("health", 100)
        self.mental = data.get("mental", 100)
        self.location = data.get("location", "Bilinmeyen Bölge")
        self.inventory = data.get("inventory", [])
        self.status_effects = data.get("status_effects", [])
        self.npc_relationships = data.get("npc_relationships", {})
        self.npc_last_seen = data.get("npc_last_seen", {})
        self.known_world_npcs = data.get("known_world_npcs", {})
        self.god_mode = data.get("god_mode", False)
        self.pending_gm_directives = data.get("pending_gm_directives", [])
        self.turn_count = data.get("turn_count", 0)
        self.last_autosave_turn = data.get("last_autosave_turn", 0)
        self.is_game_over = data.get("is_game_over", False)
        self.game_over_reason = data.get("game_over_reason", "")
        self.story_log = data.get("story_log", [])
        self.last_suggested_actions = data.get("last_suggested_actions", [])
        self.last_arbiter_verdict = data.get("last_arbiter_verdict", "")
        self.last_rule_warnings = data.get("last_rule_warnings", "")
        self.is_god_sim = data.get("is_god_sim", False)
        self.faith = data.get("faith", 50)
        self.fear = data.get("fear", 15)
        self.divine_power = data.get("divine_power", 100)
        raw_prayers = data.get("prayers", [])
        self.prayers = [self.normalize_prayer(p, f"p{i+1}") for i, p in enumerate(raw_prayers) if self.normalize_prayer(p, f"p{i+1}")]
        raw_prophets = data.get("prophets", [])
        self.prophets = []
        for pr in raw_prophets:
            norm_pr = self.normalize_prophet(pr)
            if norm_pr and not any(p.get("name") == norm_pr.get("name") for p in self.prophets):
                self.prophets.append(norm_pr)
        self.divine_decrees = data.get("divine_decrees", [])

        # If loading an older save without known_world_npcs, populate from npc_relationships
        if not self.known_world_npcs and self.npc_relationships:
            for k, att in self.npc_relationships.items():
                self.known_world_npcs[k] = {
                    "name": k,
                    "attitude": str(att),
                    "status": "Aktif Sahnede",
                    "last_seen_turn": self.turn_count,
                    "location": self.location
                }

        # If loading an older save without npc_last_seen, smartly recover recent activity
        if not self.npc_last_seen and self.npc_relationships:
            recent_text = ""
            for entry in self.story_log[-3:]:
                recent_text += " " + (entry.get("story", "") + " " + entry.get("action", "")).lower()
            for k in list(self.npc_relationships.keys()):
                if self.is_npc_present_in_text(k, recent_text):
                    self.npc_last_seen[k] = self.turn_count
                else:
                    self.npc_last_seen[k] = max(0, self.turn_count - 3)

        # Sanitize any legacy story_log entries that accidentally stored raw JSON as story
        for entry in self.story_log:
            raw_s = entry.get("story", "")
            if isinstance(raw_s, str) and raw_s.strip().startswith("{") and ('"story"' in raw_s or '"arbiter_verdict"' in raw_s):
                m = re.search(r'"story"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"[a-zA-Z_]+"|\s*\}\s*$|$)', raw_s)
                if m:
                    entry["story"] = m.group(1).replace(r'\"', '"').replace(r'\n', '\n').replace(r'\\', '\\')
                m_arb = re.search(r'"arbiter_verdict"\s*:\s*"((?:\\.|[^"\\])*)"', raw_s)
                if m_arb and (not entry.get("arbiter_verdict") or entry.get("arbiter_verdict") == "Eylem değerlendirildi."):
                    entry["arbiter_verdict"] = m_arb.group(1).replace(r'\"', '"').replace(r'\n', '\n')

        self.clean_stale_npcs()

    def save_to_file(self, filename: str) -> str:
        """Saves current state to a JSON file in SAVES_DIR."""
        if not filename.endswith(".json"):
            filename += ".json"
        
        safe_name = "".join([c for c in filename if c.isalnum() or c in ("-", "_", ".")]).strip()
        if not safe_name or safe_name == ".json":
            safe_name = f"save_{int(time.time())}.json"

        os.makedirs(self.SAVES_DIR, exist_ok=True)
        path = os.path.join(self.SAVES_DIR, safe_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return safe_name

    def auto_save(self) -> Optional[str]:
        """Automatically saves the current game state every 2 turns."""
        if self.turn_count <= 0 or self.turn_count % 2 != 0:
            return None

        os.makedirs(self.SAVES_DIR, exist_ok=True)
        char_name = self.character.get("name", "oyun") if isinstance(self.character, dict) else "oyun"
        safe_char = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(char_name).lower()).strip('_') or 'oyun'
        filename = f"otomatik_kayit_{safe_char}.json"

        save_dict = self.to_dict()
        save_dict["is_autosave"] = True
        save_dict["autosave_turn"] = self.turn_count

        path = os.path.join(self.SAVES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, ensure_ascii=False, indent=2)

        self.last_autosave_turn = self.turn_count
        return filename

    def load_from_file(self, filename: str) -> bool:
        """Loads state from a JSON file in SAVES_DIR with strict path sanitization."""
        if not filename.endswith(".json"):
            filename += ".json"
        safe_name = os.path.basename("".join([c for c in filename if c.isalnum() or c in ("-", "_", ".")]).strip())
        if not safe_name or safe_name == ".json":
            return False
        path = os.path.join(self.SAVES_DIR, safe_name)
        if not os.path.isfile(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.from_dict(data)
        return True

    @classmethod
    def list_saves(cls) -> List[Dict[str, Any]]:
        """Returns metadata for all available save files."""
        saves = []
        if not os.path.exists(cls.SAVES_DIR):
            return saves

        for fname in os.listdir(cls.SAVES_DIR):
            if fname.endswith(".json"):
                path = os.path.join(cls.SAVES_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    is_auto = bool(data.get("is_autosave") or fname.startswith("otomatik_kayit_"))
                    saves.append({
                        "filename": fname,
                        "character_name": data.get("character", {}).get("name", "Bilinmeyen"),
                        "universe_name": data.get("universe", {}).get("name", "Bilinmeyen Evren"),
                        "mode": data.get("mode_data", {}).get("mode", "Bilinmiyor"),
                        "turn_count": data.get("turn_count", 0),
                        "saved_at": data.get("saved_at", "Bilinmiyor"),
                        "is_autosave": is_auto
                    })
                except Exception:
                    continue
        return sorted(saves, key=lambda x: x.get("saved_at", ""), reverse=True)
