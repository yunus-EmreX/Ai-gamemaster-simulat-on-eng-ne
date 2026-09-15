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
        "subay", "subayı", "rehine", "tutsak", "esir", "köle"
    }

    @classmethod
    def is_npc_present_in_text(cls, npc_name: str, text: str) -> bool:
        """Determines if an NPC is mentioned or speaking in a given scene text."""
        if not npc_name or not text:
            return False
        name_clean = npc_name.lower().strip()
        text_clean = text.lower()
        if name_clean in text_clean or f"[{name_clean}" in text_clean:
            return True
        # Extract specific proper noun tokens (excluding generic titles/roles)
        tokens = [w for w in re.findall(r'\w+', name_clean) if len(w) >= 3 and w not in cls.COMMON_ROLE_WORDS]
        return bool(tokens and any(t in text_clean for t in tokens))

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
        self.god_mode: bool = False
        self.pending_gm_directives: List[str] = []
        self.turn_count: int = 0
        self.is_game_over: bool = False
        self.game_over_reason: str = ""
        self.story_log: List[Dict[str, Any]] = []
        self.raw_chat_history: List[Dict[str, Any]] = []
        self.last_suggested_actions: List[str] = []
        self.last_arbiter_verdict: str = ""
        self.last_rule_warnings: str = ""

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
        npc_updates = state_updates.get("npc_attitude_updates", {})
        if isinstance(npc_updates, dict):
            for npc, att in npc_updates.items():
                if npc and att:
                    clean = str(npc).strip()
                    self.npc_relationships[clean] = str(att).strip()
                    self.npc_last_seen[clean] = 0

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

    def apply_turn(self, player_action: str, turn_data: Dict[str, Any]):
        """Applies updates from a player's action and model's response."""
        self.turn_count += 1
        state_updates = turn_data.get("state_updates", {})

        # Health
        health_delta = state_updates.get("health_delta", 0)
        if self.god_mode:
            self.health = 100
        else:
            self.health = max(0, min(100, self.health + health_delta))

        # Mental
        mental_delta = state_updates.get("mental_delta", 0)
        if self.god_mode:
            self.mental = 100
        else:
            self.mental = max(0, min(100, self.mental + mental_delta))

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

        # 1. Update/Add NPCs from model's attitude updates
        npc_updates = state_updates.get("npc_attitude_updates", {})
        if isinstance(npc_updates, dict):
            for npc, att in npc_updates.items():
                if npc and att:
                    clean = str(npc).strip()
                    self.npc_relationships[clean] = str(att).strip()
                    self.npc_last_seen[clean] = self.turn_count

        # 2. Check explicitly active NPCs in scene
        active_scene_npcs = state_updates.get("active_scene_npcs", [])
        if isinstance(active_scene_npcs, list):
            for npc in active_scene_npcs:
                clean = str(npc).strip()
                if clean in self.npc_relationships:
                    self.npc_last_seen[clean] = self.turn_count

        # 3. Detect if existing NPCs are mentioned or speaking in this turn's story or action
        for npc_name in list(self.npc_relationships.keys()):
            if self.is_npc_present_in_text(npc_name, combined_text):
                self.npc_last_seen[npc_name] = self.turn_count

        # 4. Remove explicitly deceased or departed NPCs
        departed = state_updates.get("deceased_or_departed_npcs", []) or state_updates.get("npcs_removed", [])
        if isinstance(departed, list):
            for dep in departed:
                clean_dep = str(dep).strip().lower()
                if not clean_dep:
                    continue
                for npc_name in list(self.npc_relationships.keys()):
                    if clean_dep in npc_name.lower() or npc_name.lower() in clean_dep:
                        self.remove_npc(npc_name)

        # 5. Clean dead or absent (2-3 scenes inactive) NPCs
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

    def remove_npc(self, npc_name: str):
        clean = npc_name.strip()
        target_keys = [k for k in self.npc_relationships if k == clean or k.lower() == clean.lower()]
        for k in target_keys:
            del self.npc_relationships[k]
        target_seen_keys = [k for k in self.npc_last_seen if k == clean or k.lower() == clean.lower()]
        for k in target_seen_keys:
            del self.npc_last_seen[k]

    def clean_stale_npcs(self):
        """Removes dead NPCs and characters absent for 3 or more turns (2-3 scenes inactive)."""
        dead_keywords = ["öldü", "ölü", "ceset", "katledildi", "hayatını kaybetti", "vefat", "yok edildi", "ayrıldı", "gitti", "uzaklaştı", "kaçtı", "terk etti"]
        for npc_name, att_val in list(self.npc_relationships.items()):
            att_lower = str(att_val).lower()
            name_lower = npc_name.lower()
            # If name or attitude contains death or departure keywords
            if any(kw in att_lower for kw in dead_keywords) or "(ölü)" in name_lower or "öldü" in name_lower or "(yaralı - öldü)" in name_lower:
                self.remove_npc(npc_name)
                continue

            last_seen = self.npc_last_seen.get(npc_name, self.turn_count)
            if (self.turn_count - last_seen) >= 3:
                self.remove_npc(npc_name)

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
            "god_mode": self.god_mode,
            "pending_gm_directives": self.pending_gm_directives,
            "turn_count": self.turn_count,
            "is_game_over": self.is_game_over,
            "game_over_reason": self.game_over_reason,
            "story_log": self.story_log,
            "last_suggested_actions": self.last_suggested_actions,
            "last_arbiter_verdict": self.last_arbiter_verdict,
            "last_rule_warnings": self.last_rule_warnings,
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
        self.god_mode = data.get("god_mode", False)
        self.pending_gm_directives = data.get("pending_gm_directives", [])
        self.turn_count = data.get("turn_count", 0)
        self.is_game_over = data.get("is_game_over", False)
        self.game_over_reason = data.get("game_over_reason", "")
        self.story_log = data.get("story_log", [])
        self.last_suggested_actions = data.get("last_suggested_actions", [])
        self.last_arbiter_verdict = data.get("last_arbiter_verdict", "")
        self.last_rule_warnings = data.get("last_rule_warnings", "")

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

        path = os.path.join(self.SAVES_DIR, safe_name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        return safe_name

    def load_from_file(self, filename: str) -> bool:
        """Loads state from a JSON file in SAVES_DIR."""
        if not filename.endswith(".json"):
            filename += ".json"
        path = os.path.join(self.SAVES_DIR, filename)
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
                    saves.append({
                        "filename": fname,
                        "character_name": data.get("character", {}).get("name", "Bilinmeyen"),
                        "universe_name": data.get("universe", {}).get("name", "Bilinmeyen Evren"),
                        "mode": data.get("mode_data", {}).get("mode", "Bilinmiyor"),
                        "turn_count": data.get("turn_count", 0),
                        "saved_at": data.get("saved_at", "Bilinmiyor")
                    })
                except Exception:
                    continue
        return sorted(saves, key=lambda x: x.get("saved_at", ""), reverse=True)
