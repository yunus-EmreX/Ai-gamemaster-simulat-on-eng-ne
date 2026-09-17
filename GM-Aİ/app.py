import os
import json
import logging
import re
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, send_from_directory
from core.gemini_client import GeminiClient
from core.prompt_builder import PromptBuilder
from core.game_state import GameState
from core.simulation_engine import SimulationCore
from core.session_manager import SessionManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static", static_url_path="/static")

# Multi-session manager for concurrent client and multi-tab isolation
session_manager = SessionManager()

# Default session reference for backwards compatibility and tests
current_game = session_manager.get_game("default")
active_api_key = os.environ.get("GEMINI_API_KEY", "").strip()

def get_session_context():
    """
    Extracts isolated session_id, GameState, and API key for this request.
    If an explicit session_id is given (multi-user / multi-tab), isolated state is used.
    Otherwise, syncs with module-level current_game and active_api_key for 100%
    backwards compatibility with tests and standalone scripts.
    """
    global current_game, active_api_key
    req_json = request.get_json(silent=True) or {}
    session_id = (
        request.headers.get("X-Session-ID") or
        req_json.get("session_id") or
        request.cookies.get("story_session")
    )
    if session_id and session_id != session_manager.default_session_id:
        sid, game = session_manager.get_or_create(session_id)
        key = req_json.get("api_key", "").strip()
        if key:
            session_manager.set_api_key(key, sid)
        key = session_manager.get_api_key(sid) or active_api_key
        return sid, game, key
    else:
        key = req_json.get("api_key", "").strip() or active_api_key
        if key:
            active_api_key = key
        return session_manager.default_session_id, current_game, active_api_key

def get_compact_history(raw_history: List[Dict[str, Any]], max_messages: int = 12) -> List[Dict[str, Any]]:
    """
    Returns a token-optimized slice of recent chat history (last 5-6 turns).
    Compacts historical messages that contained bloated prompt templates down to
    the concise player action, and strips bulky state updates from model turns.
    Saves 85-95% of token consumption while keeping full conversational context.
    """
    if not raw_history:
        return []

    slice_msgs = raw_history[-max_messages:] if len(raw_history) > max_messages else raw_history
    compacted: List[Dict[str, Any]] = []

    for msg in slice_msgs:
        role = msg.get("role", "user")
        parts = msg.get("parts", [])
        if not parts:
            continue
        text = str(parts[0].get("text", "")).strip()

        if role == "user":
            # If historical message was an old full prompt, extract just the action
            if "OYUNCUNUN EYLEMİ:" in text or "YÜCE TANRI'NIN İLAHİ FERMANI / EYLEMİ:" in text:
                m = re.search(r'(?:OYUNCUNUN EYLEMİ|YÜCE TANRI\'NIN İLAHİ FERMANI / EYLEMİ):\s*\n>\s*"([^"]+)"', text)
                if m:
                    compacted.append({"role": "user", "parts": [{"text": f"Oyuncu Eylemi: \"{m.group(1)}\""}]})
                else:
                    compacted.append({"role": "user", "parts": [{"text": text[:300]}]})
            elif "OYUN BAŞLIYOR:" in text:
                compacted.append({"role": "user", "parts": [{"text": "Macerayı ve açılış sahnesini başlat."}]})
            else:
                compacted.append({"role": "user", "parts": [{"text": text}]})

        elif role == "model":
            # Compact model message if it has large JSON metadata
            try:
                data = json.loads(text)
                if isinstance(data, dict) and "story" in data:
                    comp_data = {
                        "story": data.get("story", ""),
                        "arbiter_verdict": data.get("arbiter_verdict", "")
                    }
                    compacted.append({"role": "model", "parts": [{"text": json.dumps(comp_data, ensure_ascii=False)}]})
                else:
                    compacted.append({"role": "model", "parts": [{"text": text}]})
            except Exception:
                compacted.append({"role": "model", "parts": [{"text": text}]})
        else:
            compacted.append(msg)

    return compacted

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/style.css")
def serve_css():
    return send_from_directory("static", "style.css")

@app.route("/app.js")
def serve_js():
    return send_from_directory("static", "app.js")

@app.route("/<path:filename>")
def serve_root_files(filename):
    static_file = os.path.join(app.static_folder, filename)
    if os.path.isfile(static_file):
        return send_from_directory(app.static_folder, filename)
    return "Dosya bulunamadı", 404

@app.route("/api/config", methods=["GET"])
def get_config():
    """Returns basic configuration, such as whether an environment API key exists."""
    sid, _, key = get_session_context()
    return jsonify({
        "session_id": sid,
        "has_env_key": bool(key),
        "env_key_preview": f"{key[:6]}...{key[-4:]}" if len(key) > 10 else ""
    })

@app.route("/api/presets", methods=["GET"])
def get_presets():
    """Loads all presets from the presets directory."""
    presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
    presets = []
    if os.path.exists(presets_dir):
        for fname in os.listdir(presets_dir):
            if fname.endswith(".json"):
                path = os.path.join(presets_dir, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        presets.append(data)
                except Exception as e:
                    logging.warning(f"Failed to read preset {fname}: {e}")
    return jsonify({"success": True, "presets": presets})

@app.route("/api/check_key", methods=["POST"])
def check_key():
    """Tests if a Gemini API key is valid."""
    sid, _, active_key = get_session_context()
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip() or active_key
    model = data.get("model", "gemini-2.5-flash")

    if not key:
        return jsonify({"success": False, "error": "Lütfen bir Gemini API anahtarı girin."}), 400

    client = GeminiClient(key, default_model=model)
    res = client.test_connection(model=model)
    if res.get("success"):
        session_manager.set_api_key(key, sid)
    res["session_id"] = sid
    return jsonify(res)

@app.route("/api/ai_create_concept", methods=["POST"])
def ai_create_concept():
    """Generates a complete character, universe, and mode setup from user's freeform concept description."""
    sid, _, key = get_session_context()
    data = request.get_json(silent=True) or {}
    concept = data.get("concept", "").strip()
    if not concept:
        return jsonify({"success": False, "error": "Lütfen hayal ettiğiniz karakter ve evreni kısaca açıklayın."}), 400

    if not key:
        return jsonify({"success": False, "error": "Gemini API anahtarı bulunamadı. Lütfen önce API anahtarınızı girin."}), 400

    model_name = data.get("model", "gemini-2.5-flash")
    client = GeminiClient(key, default_model=model_name)

    prompt = PromptBuilder.build_concept_generation_prompt(concept)
    contents = [{"role": "user", "parts": [{"text": prompt}]}]

    resp = client.generate_content(
        contents=contents,
        model=model_name,
        temperature=0.7,
        json_mode=True,
        max_tokens=8192
    )

    if not resp.get("success"):
        return jsonify({"success": False, "error": resp.get("error", "Yapay zeka yanıt veremedi.")}), 500

    parsed = GeminiClient.extract_json(resp.get("text", ""))
    if not parsed or not isinstance(parsed, dict) or "character" not in parsed or "universe" not in parsed:
        return jsonify({"success": False, "error": "Yapay zeka beklenen evren formatını oluşturamadı. Lütfen tekrar deneyin."}), 500

    return jsonify({"success": True, "session_id": sid, "data": parsed})

@app.route("/api/start_game", methods=["POST"])
def start_game():
    """Compiles the 3 tabs and starts the RPG adventure with Gemini."""
    sid, current_game, key = get_session_context()
    data = request.get_json(silent=True) or {}

    if not key:
        return jsonify({"success": False, "error": "Gemini API anahtarı zorunludur."}), 400

    character = data.get("character", {})
    universe = data.get("universe", {})
    mode_data = data.get("mode_data", {})
    model_name = mode_data.get("model", "gemini-2.5-flash")

    if not character.get("name"):
        return jsonify({"success": False, "error": "Karakter adı zorunludur."}), 400

    # Build Master System Instruction & Prologue Prompt
    system_instruction = PromptBuilder.build_system_instruction(character, universe, mode_data)
    prologue_prompt = PromptBuilder.build_prologue_prompt(character, universe, mode_data)

    client = GeminiClient(key, default_model=model_name)
    temperature = 0.5 if mode_data.get("mode") == "realistic" else 0.7

    contents = [{"role": "user", "parts": [{"text": prologue_prompt}]}]

    resp = client.generate_content(
        contents=contents,
        system_instruction=system_instruction,
        model=model_name,
        temperature=temperature,
        json_mode=True,
        max_tokens=8192
    )

    if not resp.get("success"):
        return jsonify({
            "success": False,
            "error": resp.get("error", "Gemini'den yanıt alınamadı.")
        }), 500

    prologue_json = GeminiClient.extract_json(resp.get("text", ""))
    if not prologue_json:
        # Fallback if raw text wasn't valid JSON
        raw_text = resp.get("text", "")
        clean_story = raw_text
        if clean_story.strip().startswith("{") and ('"story"' in clean_story or '"arbiter_verdict"' in clean_story):
            m = re.search(r'"story"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"|"\s*\}|$)', clean_story)
            if m:
                clean_story = m.group(1)
        clean_story = clean_story.replace(r'\"', '"').replace(r'\n', '\n').replace(r'\\', '\\')
        prologue_json = {
            "arbiter_verdict": "Başlangıç ortamı hazırlandı.",
            "rule_warnings": "Evren kuralları aktif.",
            "story": clean_story,
            "state_updates": {
                "health_delta": 0,
                "mental_delta": 0,
                "location": character.get("location") or universe.get("name", "Bilinmeyen Bölge"),
                "inventory_added": [],
                "inventory_removed": [],
                "status_effects": ["Temkinli"],
                "is_game_over": False
            },
            "suggested_actions": [
                "Etrafı dikkatlice gözlemle ve çevreyi incele",
                "Envanterindeki eşyaları kontrol et ve hazırla",
                "Sessizce hareket ederek güvenli bir köşe ara"
            ]
        }

    # Initialize Game State for this session
    current_game.initialize_game(
        character=character,
        universe=universe,
        mode_data=mode_data,
        system_instruction=system_instruction,
        prologue_data=prologue_json
    )

    # Initialize context history with token-optimized prologue entry
    current_game.raw_chat_history = [
        {"role": "user", "parts": [{"text": "Macerayı ve açılış sahnesini başlat."}]},
        {"role": "model", "parts": [{"text": json.dumps({
            "arbiter_verdict": prologue_json.get("arbiter_verdict", "Başlangıç ortamı hazırlandı."),
            "story": prologue_json.get("story", "")
        }, ensure_ascii=False)}]}
    ]

    return jsonify({
        "success": True,
        "session_id": sid,
        "state": current_game.to_dict()
    })

@app.route("/api/take_action", methods=["POST"])
def take_action():
    """Processes player action, checks rule adherence, and advances story."""
    sid, current_game, key = get_session_context()
    data = request.get_json(silent=True) or {}

    player_action = data.get("action", "").strip()
    if not player_action:
        return jsonify({"success": False, "error": "Lütfen bir eylem belirtin."}), 400

    if current_game.is_game_over:
        return jsonify({"success": False, "error": "Oyun sona erdi. Yeni bir oyun başlatın veya kayıt yükleyin."}), 400

    if not key:
        return jsonify({"success": False, "error": "Gemini API anahtarı bulunamadı."}), 400

    model_name = current_game.mode_data.get("model", "gemini-2.5-flash")
    client = GeminiClient(key, default_model=model_name)

    # Deterministic simulation pre-evaluation (Python core)
    sim_eval = SimulationCore.process_action(player_action, current_game.to_dict())
    sim_directives = sim_eval.get("all_directives", [])

    # Pop any GM directives for this turn
    gm_directives = current_game.pop_gm_directives()

    # Generate Saga Chronicle
    saga_chronicle = current_game.generate_saga_chronicle()

    # Build turn prompt with rule anchor, GM directives, deterministic physics directives, and saga chronicle
    turn_prompt = PromptBuilder.build_action_turn_prompt(
        player_action=player_action,
        game_state=current_game.to_dict(),
        universe=current_game.universe,
        mode_data=current_game.mode_data,
        gm_directives=gm_directives,
        sim_directives=sim_directives,
        saga_chronicle=saga_chronicle
    )

    history_slice = get_compact_history(current_game.raw_chat_history, max_messages=12)
    contents = list(history_slice)
    contents.append({"role": "user", "parts": [{"text": turn_prompt}]})

    temperature = 0.4 if current_game.mode_data.get("mode") == "realistic" else 0.7

    resp = client.generate_content(
        contents=contents,
        system_instruction=current_game.system_instruction,
        model=model_name,
        temperature=temperature,
        json_mode=True,
        max_tokens=8192
    )

    if not resp.get("success"):
        return jsonify({
            "success": False,
            "error": resp.get("error", "Gemini'den yanıt alınamadı.")
        }), 500

    turn_json = GeminiClient.extract_json(resp.get("text", ""))
    if not turn_json:
        # Fallback if raw text wasn't valid JSON
        raw_text = resp.get("text", "")
        clean_story = raw_text
        if clean_story.strip().startswith("{") and ('"story"' in clean_story or '"arbiter_verdict"' in clean_story):
            m = re.search(r'"story"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"|"\s*\}|$)', clean_story)
            if m:
                clean_story = m.group(1)
        clean_story = clean_story.replace(r'\"', '"').replace(r'\n', '\n').replace(r'\\', '\\')

        turn_json = {
            "arbiter_verdict": "Eylem değerlendirildi.",
            "rule_warnings": "Kurallar devrede.",
            "story": clean_story,
            "state_updates": {
                "health_delta": 0,
                "mental_delta": 0,
                "location": current_game.location,
                "inventory_added": [],
                "inventory_removed": [],
                "status_effects": current_game.status_effects,
                "npc_attitude_updates": {},
                "deceased_or_departed_npcs": [],
                "is_game_over": False
            },
            "suggested_actions": [
                "Durumu tekrar değerlendir",
                "Temkinli adımlarla ilerle",
                "Bir sonraki hamleni planla"
            ]
        }

    # Deterministic Post-Turn Rule Enforcement (Python Core Override/Clamping)
    turn_json = SimulationCore.enforce_turn(current_game, player_action, turn_json, sim_eval)

    # Apply turn updates to game state
    current_game.apply_turn(player_action, turn_json, sim_eval)

    # Auto-save mechanism every 2 turns
    autosaved_file = None
    if current_game.turn_count > 0 and current_game.turn_count % 2 == 0:
        try:
            autosaved_file = current_game.auto_save()
            logging.info(f"Auto-save triggered at turn {current_game.turn_count}: {autosaved_file}")
        except Exception as e:
            logging.error(f"Auto-save failed: {e}")

    # Update raw chat history with compact player action & story narrative
    current_game.raw_chat_history.append({"role": "user", "parts": [{"text": f"Oyuncu Eylemi: \"{player_action}\""}]})
    current_game.raw_chat_history.append({"role": "model", "parts": [{"text": json.dumps({
        "arbiter_verdict": turn_json.get("arbiter_verdict", ""),
        "story": turn_json.get("story", "")
    }, ensure_ascii=False)}]})

    usage_info = resp.get("usage_metadata", {})

    return jsonify({
        "success": True,
        "session_id": sid,
        "state": current_game.to_dict(),
        "turn_result": turn_json,
        "autosaved": bool(autosaved_file),
        "autosave_filename": autosaved_file,
        "autosave_turn": current_game.turn_count if autosaved_file else None,
        "usage": {
            "prompt_tokens": usage_info.get("promptTokenCount", 0),
            "output_tokens": usage_info.get("candidatesTokenCount", 0),
            "total_tokens": usage_info.get("totalTokenCount", 0)
        }
    })

# --- GAME MASTER / CHEAT PANEL API ENDPOINTS ---
@app.route("/api/gm/modify_stat", methods=["POST"])
def gm_modify_stat():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    if "health" in data:
        current_game.set_health(int(data["health"]))
    if "mental" in data:
        current_game.set_mental(int(data["mental"]))
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": "Değerler güncellendi."})

@app.route("/api/gm/toggle_godmode", methods=["POST"])
def gm_toggle_godmode():
    sid, current_game, _ = get_session_context()
    is_god = current_game.toggle_godmode() if hasattr(current_game, "toggle_godmode") else current_game.toggle_god_mode()
    msg = "Ölümsüzlük / Tanrı Modu AÇIK (Can azalamaz)" if is_god else "Tanrı Modu KAPALI (Normal kurallar devrede)"
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "god_mode": is_god, "message": msg})

@app.route("/api/gm/add_item", methods=["POST"])
def gm_add_item():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    item = data.get("item", "").strip()
    if not item:
        return jsonify({"success": False, "error": "Eşya adı boş olamaz."}), 400
    current_game.add_item(item)
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": f"'{item}' envantere eklendi."})

@app.route("/api/gm/remove_item", methods=["POST"])
def gm_remove_item():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    item = data.get("item", "").strip()
    if not item:
        return jsonify({"success": False, "error": "Eşya adı boş olamaz."}), 400
    current_game.remove_item(item)
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": f"'{item}' envanterden silindi."})

@app.route("/api/gm/set_npc", methods=["POST"])
def gm_set_npc():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    attitude = data.get("attitude", "").strip()
    if not name or not attitude:
        return jsonify({"success": False, "error": "Karakter adı ve tutumu zorunludur."}), 400
    current_game.set_npc_attitude(name, attitude)
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": f"'{name}' tutumu '{attitude}' olarak ayarlandı."})

@app.route("/api/gm/remove_npc", methods=["POST"])
def gm_remove_npc():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    purge = data.get("purge", False)
    if purge:
        current_game.purge_npc(name)
        msg = f"'{name}' tamamen hafızadan ve oyundan silindi."
    else:
        current_game.remove_npc(name)
        msg = f"'{name}' aktif sahneden çıkarıldı (dünya hafızasında korundu)."
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": msg})

@app.route("/api/gm/clear_effects", methods=["POST"])
def gm_clear_effects():
    sid, current_game, _ = get_session_context()
    current_game.clear_negative_effects()
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": "Negatif durum efektleri temizlendi."})

@app.route("/api/gm/inject_directive", methods=["POST"])
def gm_inject_directive():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    directive = data.get("directive", "").strip()
    if not directive:
        return jsonify({"success": False, "error": "GM talimatı boş olamaz."}), 400
    current_game.add_gm_directive(directive)
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict(), "message": "GM emri kuyruğa eklendi. Bir sonraki turda yapay zekaya zorunlu kılınacak."})

@app.route("/api/god/prayer_action", methods=["POST"])
def god_prayer_action():
    """Allows instant granting, smiting, ignoring, or twisting of mortal prayers in God Sim mode."""
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    prayer_id = data.get("prayer_id", "").strip()
    decision = data.get("decision", "grant").strip().lower()
    notes = data.get("notes", "").strip()

    prayer = current_game.answer_prayer(prayer_id, decision, notes)
    if not prayer:
        return jsonify({"success": False, "error": "Dua bulunamadı veya daha önce yanıtlandı."}), 404

    mortal = prayer.get("mortal_name") or prayer.get("mortal") or "Ölümlü"
    req_text = prayer.get("prayer_text") or prayer.get("prayer") or ""

    if decision == "grant":
        action_text = f"{mortal} adlı faninin yakarışını KABUL EDİYORUM ve bir mucize bahşediyorum: \"{req_text}\". {notes}"
    elif decision == "smite":
        action_text = f"{mortal} adlı faninin hadsiz yakarışına İLAHİ GAZAP VE YILDIRIMLA karşılık veriyorum: \"{req_text}\". {notes}"
    elif decision == "twist":
        action_text = f"{mortal} adlı faninin duasını çarpıtarak beklenmedik bir bedelle tecelli ettiriyorum: \"{req_text}\". {notes}"
    else:
        action_text = f"{mortal} adlı faninin yakarışını GÖRMEZDEN GELİP faniyi kaderiyle baş başa bırakıyorum: \"{req_text}\". {notes}"

    return jsonify({
        "success": True,
        "session_id": sid,
        "action_text": action_text,
        "prayer": prayer,
        "state": current_game.to_dict()
    })

@app.route("/api/god/set_era", methods=["POST"])
def god_set_era():
    """Updates the civilization era in God Sim mode."""
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    era = data.get("era", "").strip()
    if not era:
        return jsonify({"success": False, "error": "Çağ adı belirtilmedi."}), 400

    current_game.civilization_era = era
    return jsonify({
        "success": True,
        "session_id": sid,
        "era": era,
        "state": current_game.to_dict()
    })

@app.route("/api/god/appoint_prophet", methods=["POST"])
def god_appoint_prophet():
    """Appoints a new chosen prophet in God Sim mode."""
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip() or "Seçilmiş Elçi"
    role = data.get("role", "").strip() or "Başpeygamber / Elçi"
    region = data.get("region", "").strip() or "Kutsal Topraklar"
    doctrine = data.get("doctrine", "").strip() or "Tanrı'nın ilahi vahyini ve fermanlarını tebliğ eder."

    prophet = {
        "name": name,
        "role": role,
        "region": region,
        "doctrine": doctrine
    }
    if not any(p.get("name") == name for p in current_game.prophets):
        current_game.prophets.append(prophet)

    return jsonify({
        "success": True,
        "session_id": sid,
        "prophet": prophet,
        "state": current_game.to_dict()
    })

@app.route("/api/save_game", methods=["POST"])
def save_game():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "").strip() or f"kayit_{current_game.character.get('name', 'oyun')}"
    saved_as = current_game.save_to_file(filename)
    return jsonify({"success": True, "session_id": sid, "filename": saved_as, "message": "Oyun başarıyla kaydedildi."})

@app.route("/api/auto_save", methods=["POST"])
def trigger_auto_save():
    """Explicitly triggers auto_save if turn conditions match or manual call."""
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    force = data.get("force", False)
    if force and (current_game.turn_count == 0 or current_game.turn_count % 2 != 0):
        char_name = current_game.character.get("name", "oyun") if isinstance(current_game.character, dict) else "oyun"
        safe_char = re.sub(r'[^a-zA-Z0-9_\-]', '_', str(char_name).lower()).strip('_') or 'oyun'
        filename = f"otomatik_kayit_{safe_char}.json"
        save_dict = current_game.to_dict()
        save_dict["is_autosave"] = True
        save_dict["autosave_turn"] = current_game.turn_count
        os.makedirs(current_game.SAVES_DIR, exist_ok=True)
        path = os.path.join(current_game.SAVES_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(save_dict, f, ensure_ascii=False, indent=2)
        saved_as = filename
    else:
        saved_as = current_game.auto_save()

    return jsonify({
        "success": bool(saved_as),
        "session_id": sid,
        "filename": saved_as,
        "turn": current_game.turn_count,
        "message": f"Otomatik kayıt oluşturuldu: {saved_as}" if saved_as else "Otomatik kayıt koşulu sağlanmadı (Tur çift sayı değil veya 0)."
    })

@app.route("/api/list_saves", methods=["GET"])
def list_saves():
    saves = GameState.list_saves()
    return jsonify({"success": True, "saves": saves})

@app.route("/api/load_game", methods=["POST"])
def load_game():
    sid, current_game, _ = get_session_context()
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "").strip()
    if not filename:
        return jsonify({"success": False, "error": "Kayıt dosyası adı belirtilmedi."}), 400

    if data.get("api_key"):
        session_manager.set_api_key(data["api_key"].strip(), sid)

    ok = current_game.load_from_file(filename)
    if not ok:
        return jsonify({"success": False, "error": "Kayıt dosyası bulunamadı veya açılamadı."}), 404

    return jsonify({
        "success": True,
        "session_id": sid,
        "state": current_game.to_dict(),
        "message": f"{filename} başarıyla yüklendi."
    })

@app.route("/api/current_state", methods=["GET"])
def current_state():
    sid, current_game, _ = get_session_context()
    return jsonify({"success": True, "session_id": sid, "state": current_game.to_dict()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"RPG Sunucusu başlatılıyor: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
