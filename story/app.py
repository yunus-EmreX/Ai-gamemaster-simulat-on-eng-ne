import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from core.gemini_client import GeminiClient
from core.prompt_builder import PromptBuilder
from core.game_state import GameState

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = Flask(__name__, static_folder="static", static_url_path="/static")

# In-memory global game session
current_game = GameState()
active_api_key = os.environ.get("GEMINI_API_KEY", "").strip()

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
    return jsonify({
        "has_env_key": bool(active_api_key),
        "env_key_preview": f"{active_api_key[:6]}...{active_api_key[-4:]}" if len(active_api_key) > 10 else ""
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
    global active_api_key
    data = request.get_json(silent=True) or {}
    key = data.get("api_key", "").strip() or active_api_key
    model = data.get("model", "gemini-3.6-flash")

    if not key:
        return jsonify({"success": False, "error": "Lütfen bir Gemini API anahtarı girin."}), 400

    client = GeminiClient(key, default_model=model)
    res = client.test_connection(model=model)
    if res.get("success"):
        active_api_key = key
    return jsonify(res)

@app.route("/api/start_game", methods=["POST"])
def start_game():
    """Compiles the 3 tabs and starts the RPG adventure with Gemini."""
    global active_api_key
    data = request.get_json(silent=True) or {}

    key = data.get("api_key", "").strip() or active_api_key
    if not key:
        return jsonify({"success": False, "error": "Gemini API anahtarı zorunludur."}), 400

    active_api_key = key

    character = data.get("character", {})
    universe = data.get("universe", {})
    mode_data = data.get("mode_data", {})
    model_name = mode_data.get("model", "gemini-3.6-flash")

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
        # Fallback if raw text wasn't valid JSON: extract clean text without JSON syntax
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
                "location": universe.get("name", "Bilinmeyen Bölge"),
                "inventory_added": character.get("inventory", []),
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

    # Initialize Game State
    current_game.initialize_game(
        character=character,
        universe=universe,
        mode_data=mode_data,
        system_instruction=system_instruction,
        prologue_data=prologue_json
    )

    # Initialize context history with system prompt & first turn
    current_game.raw_chat_history = [
        {"role": "user", "parts": [{"text": prologue_prompt}]},
        {"role": "model", "parts": [{"text": json.dumps(prologue_json, ensure_ascii=False)}]}
    ]

    return jsonify({
        "success": True,
        "state": current_game.to_dict()
    })

@app.route("/api/take_action", methods=["POST"])
def take_action():
    """Processes player action, checks rule adherence, and advances story."""
    global active_api_key
    data = request.get_json(silent=True) or {}

    player_action = data.get("action", "").strip()
    if not player_action:
        return jsonify({"success": False, "error": "Lütfen bir eylem belirtin."}), 400

    if current_game.is_game_over:
        return jsonify({"success": False, "error": "Oyun sona erdi. Yeni bir oyun başlatın veya kayıt yükleyin."}), 400

    key = data.get("api_key", "").strip() or active_api_key
    if not key:
        return jsonify({"success": False, "error": "Gemini API anahtarı bulunamadı."}), 400

    model_name = current_game.mode_data.get("model", "gemini-3.6-flash")
    client = GeminiClient(key, default_model=model_name)

    # Pop any GM directives for this turn
    gm_directives = current_game.pop_gm_directives()

    # Build turn prompt with rule anchor and GM directives
    turn_prompt = PromptBuilder.build_action_turn_prompt(
        player_action=player_action,
        game_state=current_game.to_dict(),
        universe=current_game.universe,
        mode_data=current_game.mode_data,
        gm_directives=gm_directives
    )

    # Construct conversation history (keep last 6 turns to avoid context overflow while keeping immediate memory)
    history_slice = current_game.raw_chat_history[-8:] if len(current_game.raw_chat_history) > 8 else current_game.raw_chat_history
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
        # Ultimate fallback: NEVER put raw JSON syntax into story
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

    # Apply turn updates to game state
    current_game.apply_turn(player_action, turn_json)

    # Update raw chat history
    current_game.raw_chat_history.append({"role": "user", "parts": [{"text": turn_prompt}]})
    current_game.raw_chat_history.append({"role": "model", "parts": [{"text": json.dumps(turn_json, ensure_ascii=False)}]})

    return jsonify({
        "success": True,
        "state": current_game.to_dict(),
        "turn_result": turn_json
    })

# --- GAME MASTER / CHEAT PANEL API ENDPOINTS ---
@app.route("/api/gm/modify_stat", methods=["POST"])
def gm_modify_stat():
    data = request.get_json(silent=True) or {}
    if "health" in data:
        current_game.set_health(int(data["health"]))
    if "mental" in data:
        current_game.set_mental(int(data["mental"]))
    return jsonify({"success": True, "state": current_game.to_dict(), "message": "Değerler güncellendi."})

@app.route("/api/gm/toggle_godmode", methods=["POST"])
def gm_toggle_godmode():
    is_god = current_game.toggle_godmode() if hasattr(current_game, "toggle_godmode") else current_game.toggle_god_mode()
    msg = "Ölümsüzlük / Tanrı Modu AÇIK (Can azalamaz)" if is_god else "Tanrı Modu KAPALI (Normal kurallar devrede)"
    return jsonify({"success": True, "state": current_game.to_dict(), "god_mode": is_god, "message": msg})

@app.route("/api/gm/add_item", methods=["POST"])
def gm_add_item():
    data = request.get_json(silent=True) or {}
    item = data.get("item", "").strip()
    if not item:
        return jsonify({"success": False, "error": "Eşya adı boş olamaz."}), 400
    current_game.add_item(item)
    return jsonify({"success": True, "state": current_game.to_dict(), "message": f"'{item}' envantere eklendi."})

@app.route("/api/gm/remove_item", methods=["POST"])
def gm_remove_item():
    data = request.get_json(silent=True) or {}
    item = data.get("item", "").strip()
    if not item:
        return jsonify({"success": False, "error": "Eşya adı boş olamaz."}), 400
    current_game.remove_item(item)
    return jsonify({"success": True, "state": current_game.to_dict(), "message": f"'{item}' envanterden silindi."})

@app.route("/api/gm/set_npc", methods=["POST"])
def gm_set_npc():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    attitude = data.get("attitude", "").strip()
    if not name or not attitude:
        return jsonify({"success": False, "error": "Karakter adı ve tutumu zorunludur."}), 400
    current_game.set_npc_attitude(name, attitude)
    return jsonify({"success": True, "state": current_game.to_dict(), "message": f"'{name}' tutumu '{attitude}' olarak ayarlandı."})

@app.route("/api/gm/remove_npc", methods=["POST"])
def gm_remove_npc():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    current_game.remove_npc(name)
    return jsonify({"success": True, "state": current_game.to_dict(), "message": f"'{name}' listeden çıkarıldı."})

@app.route("/api/gm/clear_effects", methods=["POST"])
def gm_clear_effects():
    current_game.clear_negative_effects()
    return jsonify({"success": True, "state": current_game.to_dict(), "message": "Negatif durum efektleri temizlendi."})

@app.route("/api/gm/inject_directive", methods=["POST"])
def gm_inject_directive():
    data = request.get_json(silent=True) or {}
    directive = data.get("directive", "").strip()
    if not directive:
        return jsonify({"success": False, "error": "GM talimatı boş olamaz."}), 400
    current_game.add_gm_directive(directive)
    return jsonify({"success": True, "state": current_game.to_dict(), "message": "GM emri kuyruğa eklendi. Bir sonraki turda yapay zekaya zorunlu kılınacak."})

@app.route("/api/save_game", methods=["POST"])
def save_game():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "").strip() or f"kayit_{current_game.character.get('name', 'oyun')}"
    saved_as = current_game.save_to_file(filename)
    return jsonify({"success": True, "filename": saved_as, "message": "Oyun başarıyla kaydedildi."})

@app.route("/api/list_saves", methods=["GET"])
def list_saves():
    saves = GameState.list_saves()
    return jsonify({"success": True, "saves": saves})

@app.route("/api/load_game", methods=["POST"])
def load_game():
    data = request.get_json(silent=True) or {}
    filename = data.get("filename", "").strip()
    if not filename:
        return jsonify({"success": False, "error": "Kayıt dosyası adı belirtilmedi."}), 400

    ok = current_game.load_from_file(filename)
    if not ok:
        return jsonify({"success": False, "error": "Kayıt dosyası bulunamadı veya açılamadı."}), 404

    return jsonify({
        "success": True,
        "state": current_game.to_dict(),
        "message": f"{filename} başarıyla yüklendi."
    })

@app.route("/api/current_state", methods=["GET"])
def current_state():
    return jsonify({"success": True, "state": current_game.to_dict()})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logging.info(f"RPG Sunucusu başlatılıyor: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
