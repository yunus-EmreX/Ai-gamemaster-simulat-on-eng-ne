import json
import os
import unittest
from core.rule_enforcer import RuleEnforcer
from core.prompt_builder import PromptBuilder
from core.game_state import GameState
from app import app

class TestRPGArchitecture(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_rule_enforcer_modes(self):
        realistic_dir = RuleEnforcer.get_mode_directives("realistic")
        self.assertIn("PLOT ARMOR", realistic_dir)
        self.assertIn("HİÇBİR BÜYÜ", realistic_dir)

        fantasy_dir = RuleEnforcer.get_mode_directives("fantasy")
        self.assertIn("Büyü veya ileri teknoloji bedelsiz değildir", fantasy_dir)

        anchor = RuleEnforcer.compile_rule_anchor(
            universe_rules="Mermiler nadirdir",
            universe_dogmas="Ölüler dirilemez",
            mode="realistic",
            strictness="ironclad"
        )
        self.assertIn("Ölüler dirilemez", anchor)
        self.assertIn("Demir Kural", anchor)

    def test_prompt_builder(self):
        char = {
            "name": "Test Savaşçı",
            "role": "Muhafız",
            "skills": ["Kılıç", "Kalkan"],
            "flaws": ["Ağır zırh yüzünden yavaş"],
            "inventory": ["Demir Kılıç", "Bandaj"]
        }
        uni = {
            "name": "Karanlık Diyar",
            "history": "Büyük Yıkım yaşandı",
            "rules": "Büyü can yakar",
            "dogmas": "Diriliş yok"
        }
        mode = {
            "mode": "realistic",
            "strictness": "challenging",
            "model": "gemini-3.6-flash",
            "prologue_hook": "Zindandasın."
        }

        sys_inst = PromptBuilder.build_system_instruction(char, uni, mode)
        self.assertIn("Test Savaşçı", sys_inst)
        self.assertIn("Diriliş yok", sys_inst)
        self.assertIn("KIRILMAZ YASALARI", sys_inst)

        prologue_prompt = PromptBuilder.build_prologue_prompt(char, uni, mode)
        self.assertIn("Zindandasın.", prologue_prompt)

    def test_game_state_lifecycle(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Kerem", "role": "İzci", "inventory": ["Pusula"]},
            universe={"name": "Kış Çölü", "rules": "Hipotermi tehlikesi", "dogmas": "Fizik katıdır"},
            mode_data={"mode": "realistic", "strictness": "ironclad"},
            system_instruction="Sistem Talimatı Test",
            prologue_data={
                "story": "Soğuk bir rüzgar yüzüne çarpıyor.",
                "arbiter_verdict": "Karakter rüzgar altında.",
                "state_updates": {
                    "health_delta": 0,
                    "mental_delta": 0,
                    "location": "Eski Kulübe",
                    "inventory_added": ["Kibrit"],
                    "status_effects": ["Üşümüş"]
                },
                "suggested_actions": ["Ateş yak", "Kapıyı kapat"]
            }
        )

        self.assertEqual(gs.health, 100)
        self.assertEqual(gs.location, "Eski Kulübe")
        self.assertIn("Pusula", gs.inventory)
        self.assertIn("Kibrit", gs.inventory)
        self.assertIn("Üşümüş", gs.status_effects)

        # Apply a turn where character takes damage
        gs.apply_turn(
            player_action="Dışarı çıkıp tipi altında koşuyorum",
            turn_data={
                "story": "Dizindeki sakatlık nüksetti ve kayıp düştün.",
                "arbiter_verdict": "Hipotermi ve sakatlık riski tetiklendi.",
                "rule_warnings": "Plot armor yok: Sakat bacakla koşu başarısız oldu.",
                "state_updates": {
                    "health_delta": -25,
                    "mental_delta": -15,
                    "location": "Karlı Tepe",
                    "status_effects": ["Hipotermi Başlangıcı", "Bacak Burkulması"],
                    "inventory_removed": ["Kibrit"]
                },
                "suggested_actions": ["Sürünerek geri dön", "Sığınak ara"]
            }
        )

        self.assertEqual(gs.health, 75)
        self.assertEqual(gs.mental, 85)
        self.assertEqual(gs.location, "Karlı Tepe")
        self.assertNotIn("Kibrit", gs.inventory)
        self.assertEqual(gs.turn_count, 1)

        # Test Save & Load
        save_file = gs.save_to_file("test_save_unit")
        self.assertTrue(os.path.exists(os.path.join(gs.SAVES_DIR, save_file)))

        gs2 = GameState()
        success = gs2.load_from_file("test_save_unit")
        self.assertTrue(success)
        self.assertEqual(gs2.character.get("name"), "Kerem")
        self.assertEqual(gs2.health, 75)

        # Clean up unit test save
        try:
            os.remove(os.path.join(gs.SAVES_DIR, save_file))
        except Exception:
            pass

    def test_api_endpoints(self):
        # 1. Config endpoint
        r = self.client.get("/api/config")
        self.assertEqual(r.status_code, 200)

        # 2. Presets endpoint
        r = self.client.get("/api/presets")
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("presets", [])), 3)

        # 3. List saves endpoint
        r = self.client.get("/api/list_saves")
        self.assertEqual(r.status_code, 200)

    def test_gm_cheat_functions(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Kael", "role": "Büyücü", "inventory": ["Asa", "İksir"]},
            universe={"name": "Antik Çağ", "rules": "Büyü zayıflatır", "dogmas": "Ölüm kesindir"},
            mode_data={"mode": "fantasy", "strictness": "balanced"},
            system_instruction="Talimat",
            prologue_data={"story": "Giriş", "state_updates": {}}
        )

        # 1. Health & Mental modification
        gs.set_health(80)
        self.assertEqual(gs.health, 80)
        gs.set_mental(40)
        self.assertEqual(gs.mental, 40)

        # 2. God Mode toggle
        status = gs.toggle_god_mode()
        self.assertTrue(status)
        self.assertTrue(gs.god_mode)

        # 3. Add & Remove inventory item
        gs.add_item("Efsanevi Kılıç")
        self.assertIn("Efsanevi Kılıç", gs.inventory)
        gs.remove_item("Asa")
        self.assertNotIn("Asa", gs.inventory)

        # 4. NPC attitude tracking
        gs.set_npc_attitude("Lord Vane", "Sadık Dost")
        self.assertIn("Lord Vane", gs.npc_relationships)
        self.assertEqual(gs.npc_relationships["Lord Vane"], "Sadık Dost")

        # 5. Clear negative effects
        gs.status_effects = ["Zehirlenmiş", "Kanama", "Odaklanmış"]
        gs.clear_negative_effects()
        self.assertNotIn("Zehirlenmiş", gs.status_effects)
        self.assertNotIn("Kanama", gs.status_effects)
        self.assertIn("Odaklanmış", gs.status_effects)

        # 6. GM Directives
        gs.add_gm_directive("Karakterin önüne aniden bir ejderha düşsün.")
        self.assertEqual(len(gs.pending_gm_directives), 1)
        popped = gs.pop_gm_directives()
        self.assertEqual(len(popped), 1)
        self.assertEqual(len(gs.pending_gm_directives), 0)

        # 7. Serialization verification
        d = gs.to_dict()
        self.assertIn("npc_relationships", d)
        self.assertIn("god_mode", d)
        self.assertIn("pending_gm_directives", d)

        gs_loaded = GameState()
        gs_loaded.from_dict(d)
        self.assertEqual(gs_loaded.npc_relationships["Lord Vane"], "Sadık Dost")
        self.assertTrue(gs_loaded.god_mode)

    def test_gm_api_endpoints(self):
        # Populate current_game
        import app as app_module
        app_module.current_game.initialize_game(
            character={"name": "TestKahraman", "role": "Savaşçı", "inventory": ["Kalkan"]},
            universe={"name": "TestEvren", "rules": "Kurallar", "dogmas": "Dogmalar"},
            mode_data={"mode": "realistic", "strictness": "ironclad", "model": "gemini-3.6-flash"},
            system_instruction="sys",
            prologue_data={"story": "Giriş hikayesi", "state_updates": {}}
        )

        # Test GM API: modify_stat
        r = self.client.post("/api/gm/modify_stat", json={"health": 85, "mental": 90})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["state"]["health"], 85)
        self.assertEqual(r.get_json()["state"]["mental"], 90)

        # Test GM API: toggle_godmode
        r = self.client.post("/api/gm/toggle_godmode")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_json()["god_mode"])

        # Test GM API: add_item
        r = self.client.post("/api/gm/add_item", json={"item": "Altın Anahtar"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Altın Anahtar", r.get_json()["state"]["inventory"])

        # Test GM API: remove_item
        r = self.client.post("/api/gm/remove_item", json={"item": "Kalkan"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("Kalkan", r.get_json()["state"]["inventory"])

        # Test GM API: set_npc
        r = self.client.post("/api/gm/set_npc", json={"name": "Kral Arthur", "attitude": "Müttefik"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("Kral Arthur", r.get_json()["state"]["npc_relationships"])

        # Test GM API: clear_effects
        r = self.client.post("/api/gm/clear_effects")
        self.assertEqual(r.status_code, 200)

        # Test GM API: inject_directive
        r = self.client.post("/api/gm/inject_directive", json={"directive": "Gökten meteor düşsün."})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.get_json()["state"]["pending_gm_directives"]), 1)

    def test_npc_pruning_and_death_removal(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Savaşçı", "role": "Muhafız", "inventory": []},
            universe={"name": "Test Evren", "rules": "", "dogmas": ""},
            mode_data={"mode": "realistic", "strictness": "ironclad"},
            system_instruction="",
            prologue_data={
                "story": "Zindandasın. Muhafız Kaan kapıda bekliyor.",
                "state_updates": {
                    "npc_attitude_updates": {
                        "Muhafız Kaan": "Sert ve şüpheli",
                        "Hancı Berfin": "Sessizce izliyor"
                    }
                }
            }
        )
        self.assertIn("Muhafız Kaan", gs.npc_relationships)
        self.assertIn("Hancı Berfin", gs.npc_relationships)
        self.assertEqual(gs.npc_last_seen["Muhafız Kaan"], 0)

        # Turn 1: Kaan speaks, Berfin is not mentioned
        gs.apply_turn(
            player_action="Muhafıza yaklaşıyorum",
            turn_data={
                "story": '[Muhafız Kaan]; "Uzak dur!" diye bağırdı.',
                "state_updates": {}
            }
        )
        self.assertIn("Muhafız Kaan", gs.npc_relationships)
        self.assertIn("Hancı Berfin", gs.npc_relationships)
        self.assertEqual(gs.npc_last_seen["Muhafız Kaan"], 1)
        self.assertEqual(gs.npc_last_seen["Hancı Berfin"], 0)

        # Turn 2: New character appears (Demirci), Berfin still not mentioned
        gs.apply_turn(
            player_action="Koridora çıkıyorum",
            turn_data={
                "story": "Koridorda Demirci Usta Veli çalışıyor.",
                "state_updates": {
                    "npc_attitude_updates": {
                        "Demirci Veli": "İlgisiz"
                    }
                }
            }
        )
        self.assertIn("Demirci Veli", gs.npc_relationships)
        self.assertIn("Hancı Berfin", gs.npc_relationships)  # diff = 2 - 0 = 2, still kept

        # Turn 3: Berfin has now been absent for 3 turns (diff = 3 - 0 = 3), should be automatically pruned!
        # Also, Kaan is explicitly reported dead via deceased_or_departed_npcs!
        gs.apply_turn(
            player_action="Demirciyle konuşuyorum",
            turn_data={
                "story": "Demirci Veli sana bir çekiç uzattı. Uzaktan Kaan'ın öldüğü haberi geldi.",
                "state_updates": {
                    "deceased_or_departed_npcs": ["Muhafız Kaan"]
                }
            }
        )
        # Berfin was pruned due to inactivity (3 turns absent)
        self.assertNotIn("Hancı Berfin", gs.npc_relationships)
        # Kaan was removed because he is deceased/departed
        self.assertNotIn("Muhafız Kaan", gs.npc_relationships)
        # Demirci Veli was mentioned in story, so he is still active
        self.assertIn("Demirci Veli", gs.npc_relationships)
        self.assertEqual(gs.npc_last_seen["Demirci Veli"], 3)

        # Turn 4: Test attitude containing death keyword ("Öldü")
        gs.apply_turn(
            player_action="İlerliyorum",
            turn_data={
                "story": "Demirci Veli aniden yere yığıldı.",
                "state_updates": {
                    "npc_attitude_updates": {
                        "Demirci Veli": "Kalp krizi geçirip öldü"
                    }
                }
            }
        )
        # Demirci Veli should be removed because attitude contains 'öldü'
        self.assertNotIn("Demirci Veli", gs.npc_relationships)

    def test_truncated_json_recovery(self):
        from core.gemini_client import GeminiClient
        truncated_raw = (
            '{ "arbiter_verdict": "Hakem tespiti.", "rule_warnings": "Uyarı yok.", '
            '"story": "Karakter kapıyı zorladı.\\n\\n[Muhafız Ali]; \\"Dur orada!\\"'
        )  # Notice missing closing quotes and braces!
        res = GeminiClient.extract_json(truncated_raw)
        self.assertIsNotNone(res)
        self.assertEqual(res["arbiter_verdict"], "Hakem tespiti.")
        self.assertIn("Muhafız Ali", res["story"])
        self.assertIn("Dur orada!", res["story"])

    def test_deterministic_simulation_core(self):
        from core.simulation_engine import SimulationCore, InventoryEngine, SurvivalEngine

        # 1. Weapon ammo consumption test
        inventory = ["Eski Çanta", "Revolver (6 mermi)", "Paslı Bıçak"]
        eval_res = InventoryEngine.evaluate_inventory_action("Hedefe nişan alıp bir el ateş ediyorum", inventory)
        self.assertTrue(eval_res["has_inventory_interaction"])
        self.assertEqual(eval_res["matched_item"], "Revolver (6 mermi)")
        self.assertEqual(eval_res["ammo_consumed"], 1)
        self.assertEqual(eval_res["ammo_remaining"], 5)
        self.assertEqual(eval_res["updated_item_name"], "Revolver (5 mermi)")
        self.assertIn("DETERMİNİSTİK SİMÜLASYON KURALI", eval_res["deterministic_directive"])

        # 2. Empty weapon test (dry fire)
        inventory_empty = ["Revolver (0 mermi)"]
        empty_res = InventoryEngine.evaluate_inventory_action("Tetiği çekip ateşliyorum", inventory_empty)
        self.assertTrue(empty_res["has_inventory_interaction"])
        self.assertEqual(empty_res["ammo_consumed"], 0)
        self.assertIn("MERMİ BİTMİŞTİR", empty_res["deterministic_directive"])

        # 3. Survival status effect directives test
        game_state = {
            "inventory": ["Sırt Çantası"],
            "status_effects": ["Açık Kanama", "Hipotermi"]
        }
        surv_directives = SurvivalEngine.evaluate_turn_conditions(game_state)
        self.assertEqual(len(surv_directives), 2)
        self.assertTrue(any("Kanama" in d for d in surv_directives))
        self.assertTrue(any("Hipotermi" in d for d in surv_directives))

        # 4. SimulationCore end-to-end processing
        core_state = {
            "inventory": ["Pompalı Tüfek (2 fişek)"],
            "status_effects": ["Zehirlenme"]
        }
        core_eval = SimulationCore.process_action("Pompalıyı doğrultup ateş ediyorum", core_state)
        self.assertEqual(len(core_eval["all_directives"]), 2)
        self.assertEqual(core_eval["inventory_eval"]["ammo_remaining"], 1)

    def test_deli_mode_and_32k_tokens(self):
        from core.rule_enforcer import RuleEnforcer
        from core.prompt_builder import PromptBuilder
        from core.simulation_engine import SurvivalEngine
        from core.gemini_client import GeminiClient
        import inspect

        # 1. RuleEnforcer has deli preset
        self.assertIn("deli", RuleEnforcer.STRICTNESS_PRESETS)
        deli_info = RuleEnforcer.STRICTNESS_PRESETS["deli"]
        self.assertIn("Deli Modu", deli_info["name"])
        self.assertTrue(len(deli_info["rules"]) >= 5)

        # 2. SurvivalEngine deli mode behavior
        deli_state = {
            "mode_data": {"strictness": "deli"},
            "status_effects": ["Açık Kanama", "Hipotermi"]
        }
        directives = SurvivalEngine.evaluate_turn_conditions(deli_state)
        # Should have global deli hostility directive + heavy bleeding + freezing shock
        self.assertTrue(any("DELİ MODU KURALI" in d for d in directives))
        self.assertTrue(any("AĞIR KAN KAYBI" in d for d in directives))
        self.assertTrue(any("-15 ile -35" in d for d in directives))

        # 3. PromptBuilder includes deli directives
        sys_inst = PromptBuilder.build_system_instruction(
            character={"name": "Kurban", "role": "Kaçak"},
            universe={"rules": "Acımasız dünya", "dogmas": "Ölüm kesin"},
            mode_data={"mode": "realistic", "strictness": "deli"}
        )
        self.assertIn("DELİ MODU PROTOKOLÜ", sys_inst)
        self.assertIn("HER ŞEYİ OYUNCU İÇİN MAKSİMUM DERECEDE ZORLAŞTIR", sys_inst)

        turn_prompt = PromptBuilder.build_action_turn_prompt(
            player_action="Kapıyı kırmaya çalışıyorum",
            game_state={"health": 100, "mental": 100, "inventory": []},
            universe={"rules": "", "dogmas": ""},
            mode_data={"strictness": "deli"}
        )
        self.assertIn("DELİ MODU DEVREDE", turn_prompt)
        self.assertIn("MAKSİMUM CEZALANDIRMA", turn_prompt)

        # 4. GeminiClient token limit is 65536 (64K maximum output tokens)
        sig = inspect.signature(GeminiClient.generate_content)
        self.assertEqual(sig.parameters["max_tokens"].default, 65536)

    def test_ai_create_concept_and_prompt(self):
        from core.prompt_builder import PromptBuilder
        concept = "Viktorya Londra saat ustası intikam arıyor"
        prompt = PromptBuilder.build_concept_generation_prompt(concept)
        self.assertIn("Viktorya Londra saat ustası intikam arıyor", prompt)
        self.assertIn("character", prompt)
        self.assertIn("universe", prompt)
        self.assertIn("mode_data", prompt)
        self.assertIn("dogmas", prompt)
        self.assertIn("flaws", prompt)

        # Validation testing on endpoint
        r1 = self.client.post("/api/ai_create_concept", json={"concept": ""})
        self.assertEqual(r1.status_code, 400)
        self.assertIn("Lütfen hayal ettiğiniz", r1.get_json()["error"])

        # Test without key
        import app as app_module
        old_key = app_module.active_api_key
        app_module.active_api_key = ""
        r2 = self.client.post("/api/ai_create_concept", json={"concept": "Deneme konsept", "api_key": ""})
        self.assertEqual(r2.status_code, 400)
        self.assertIn("Gemini API anahtarı bulunamadı", r2.get_json()["error"])
        app_module.active_api_key = old_key

    def test_two_tier_npc_memory_and_reactivation(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Kayıp Gezgin", "role": "İzci", "inventory": []},
            universe={"name": "Antik Harabeler", "rules": "", "dogmas": ""},
            mode_data={"mode": "realistic", "strictness": "ironclad"},
            system_instruction="",
            prologue_data={
                "story": "Akıl Hocan Bilge Elidor ile tapınaktasın.",
                "state_updates": {
                    "npc_attitude_updates": {
                        "Bilge Elidor": "Şefkatli Rehber"
                    }
                }
            }
        )
        self.assertIn("Bilge Elidor", gs.npc_relationships)
        self.assertIn("Bilge Elidor", gs.known_world_npcs)
        self.assertEqual(gs.known_world_npcs["Bilge Elidor"]["attitude"], "Şefkatli Rehber")

        # Turn 1: Player leaves the temple, Elidor is not mentioned
        gs.apply_turn("Tapınaktan çıkıp ormana giriyorum", {"story": "Ormanın derinliklerine girdin.", "state_updates": {}})
        # Turn 2: Player encounters a wolf, Elidor still not mentioned
        gs.apply_turn("Kurtla savaşıyorum", {"story": "Kurdu savuşturdun.", "state_updates": {}})
        # Turn 3: 3 turns have passed without Elidor (diff = 3 - 0 = 3)
        gs.apply_turn("Mağaraya sığınıyorum", {"story": "Mağarada dinlendin.", "state_updates": {}})

        # Elidor should be pruned from active sidebar (so sidebar is clean)
        self.assertNotIn("Bilge Elidor", gs.npc_relationships)
        # BUT Elidor MUST be preserved in known world memory!
        self.assertIn("Bilge Elidor", gs.known_world_npcs)
        self.assertEqual(gs.known_world_npcs["Bilge Elidor"]["status"], "[Mevcut Sahnede Değil / Uzakta]")

        # Turn 4: Player mentions or returns to Elidor
        gs.apply_turn("Elidor'un yanına dönüyorum", {"story": "Tapınağa geri döndün.", "state_updates": {}})
        # Elidor should be INSTANTLY reactivated into active sidebar!
        self.assertIn("Bilge Elidor", gs.npc_relationships)
        self.assertEqual(gs.known_world_npcs["Bilge Elidor"]["status"], "Aktif Sahnede")

    def test_saga_chronicle_generation_and_prompt_injection(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Ragnar", "role": "Savaşçı", "inventory": ["Balta"]},
            universe={"name": "Kuzey", "rules": "", "dogmas": ""},
            mode_data={"mode": "realistic", "strictness": "ironclad"},
            system_instruction="",
            prologue_data={
                "story": "Fiyort kıyısında fırtına başladı. Soğuk dalgalar kıyıya vuruyor.",
                "arbiter_verdict": "Fırtına ortasında başlangıç.",
                "state_updates": {}
            }
        )
        gs.apply_turn("Kıyıdaki kulübeye koşuyorum", {
            "story": "Kulübenin kapısını kırıp içeri girdin.",
            "arbiter_verdict": "Kulübeye sığınıldı fakat omuz zedelendi.",
            "state_updates": {"health_delta": -10}
        })
        gs.apply_turn("Ateş yakıyorum", {
            "story": "Kuru odunlarla ocakta ateş yaktın.",
            "arbiter_verdict": "Hipotermi önlendi, ısınma sağlandı.",
            "state_updates": {"mental_delta": 15}
        })

        chronicle = gs.generate_saga_chronicle()
        self.assertIn("Tur 0 - Hikaye Başlangıcı", chronicle)
        self.assertIn("Tur 1", chronicle)
        self.assertIn("Kulübeye sığınıldı", chronicle)
        self.assertIn("Sağlık: -10", chronicle)
        self.assertIn("Tur 2", chronicle)
        self.assertIn("Ateş yakıyorum", chronicle)

        # Verify prompt builder incorporates both active NPCs, world NPCs, and chronicle
        prompt = PromptBuilder.build_action_turn_prompt(
            player_action="Dışarıyı gözetliyorum",
            game_state=gs.to_dict(),
            universe=gs.universe,
            mode_data=gs.mode_data,
            saga_chronicle=chronicle
        )
        self.assertIn("AKTİF SAHNEDEKİ KARAKTERLER", prompt)
        self.assertIn("DÜNYADA BİLİNEN DİĞER ÖNEMLİ KARAKTERLER", prompt)
        self.assertIn("GEÇMİŞ SAHNELER VE ÖNEMLİ OLAYLAR KRONOLOJİSİ", prompt)
        self.assertIn("Kulübeye sığınıldı", prompt)

    def test_gm_purge_npc(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Kahraman", "role": "Muhafız", "inventory": []},
            universe={"name": "Evren", "rules": "", "dogmas": ""},
            mode_data={"mode": "realistic", "strictness": "ironclad"},
            system_instruction="",
            prologue_data={"story": "Giriş", "state_updates": {"npc_attitude_updates": {"Hain Casus": "Düşman"}}}
        )
        self.assertIn("Hain Casus", gs.npc_relationships)
        self.assertIn("Hain Casus", gs.known_world_npcs)

        # Soft remove: removed from active scene, kept in world memory
        gs.remove_npc("Hain Casus")
        self.assertNotIn("Hain Casus", gs.npc_relationships)
        self.assertIn("Hain Casus", gs.known_world_npcs)

        # Hard purge: completely removed from memory
        gs.purge_npc("Hain Casus")
        self.assertNotIn("Hain Casus", gs.known_world_npcs)

    def test_god_sim_initialization_and_metrics(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Aethelgard", "role": "Kozmik Mimar", "inventory": ["Kozmik Asa"]},
            universe={"name": "Genesis Diyarı", "rules": "İrade gerçeği büker", "dogmas": "Yaratıcı tektir"},
            mode_data={"mode": "god_sim", "strictness": "balanced"},
            system_instruction="Kozmik Hakem",
            prologue_data={
                "story": "Evrenin şafağında ilk yıldızlar parıldıyor.",
                "arbiter_verdict": "Kozmik irade aktif.",
                "state_updates": {
                    "location": "Aşkın Boyut / Kozmik Taht"
                }
            }
        )

        self.assertTrue(gs.is_god_sim)
        self.assertTrue(gs.god_mode)
        self.assertEqual(gs.faith, 50)
        self.assertEqual(gs.fear, 15)
        self.assertEqual(gs.divine_power, 100)
        self.assertEqual(gs.civilization_era, "Yaratılış ve Kabileler Çağı")
        self.assertGreaterEqual(len(gs.prayers), 2)

        # Apply a turn updating faith, fear, power, era, prophets, and decrees
        gs.apply_turn(
            player_action="Dağları yarıp kurak vadiye nehir akıtıyorum",
            turn_data={
                "story": "Dağlar gürleyerek ikiye yarıldı ve billur sular aktı.",
                "arbiter_verdict": "İlahi mucize gerçekleşti, kabilenin imanı arttı.",
                "state_updates": {
                    "faith_delta": 20,
                    "fear_delta": 5,
                    "divine_power_delta": -10,
                    "civilization_era": "Bronz ve Tapınak Çağı",
                    "decree_established": "Sular daima yaratıcının adıyla akar",
                    "prophets_added": [{"name": "Kabile Reisi Elor", "role": "İlk Kahin", "region": "Vadi"}],
                    "prayers_generated": [
                        {
                            "id": "prayer_new_1",
                            "mortal_name": "Elor",
                            "mortal_location": "Vadi",
                            "prayer_type": "şükran",
                            "prayer_text": "Lütfun için tapınak yükseltiyoruz!",
                            "status": "beklemede"
                        }
                    ]
                }
            }
        )

        self.assertEqual(gs.faith, 70)
        self.assertEqual(gs.fear, 20)
        self.assertEqual(gs.divine_power, 90)
        self.assertEqual(gs.civilization_era, "Bronz ve Tapınak Çağı")
        self.assertIn("Sular daima yaratıcının adıyla akar", gs.divine_decrees)
        self.assertEqual(len(gs.prophets), 1)
        self.assertEqual(gs.prophets[0]["name"], "Kabile Reisi Elor")
        self.assertTrue(any(p["id"] == "prayer_new_1" for p in gs.prayers))

    def test_god_sim_answer_prayer_methods(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Kozmik Varlık", "role": "Yaratıcı", "inventory": []},
            universe={"name": "Evren", "rules": "", "dogmas": ""},
            mode_data={"mode": "god_sim"},
            system_instruction="",
            prologue_data={"story": "Evren doğdu."}
        )

        first_prayer_id = gs.prayers[0]["id"]
        res = gs.answer_prayer(first_prayer_id, "grant", "Duaları kabul edildi, yağmur yağdırıldı.")
        self.assertIsNotNone(res)
        self.assertEqual(gs.prayers[0]["status"], "kabul_edildi")
        self.assertIn("Duaları kabul edildi", gs.prayers[0]["divine_response"])

        second_prayer_id = gs.prayers[1]["id"]
        res2 = gs.answer_prayer(second_prayer_id, "smite", "Kibirli kabileye yıldırım indirildi.")
        self.assertIsNotNone(res2)
        self.assertEqual(gs.prayers[1]["status"], "gazap_yagdirildi")

    def test_god_sim_prayer_action_api(self):
        import app as app_module
        app_module.current_game.initialize_game(
            character={"name": "Aethelgard", "role": "Kozmik Tanrı", "skills": [], "flaws": []},
            universe={"name": "Kozmos", "rules": "Yaratıcı mutlak", "dogmas": "Fizik tanrının emrindedir"},
            mode_data={"mode": "god_sim", "strictness": "balanced"},
            system_instruction="Kozmik Hakem",
            prologue_data={"story": "Evren doğdu."}
        )
        self.assertTrue(app_module.current_game.is_god_sim)

        prayers = app_module.current_game.prayers
        self.assertGreaterEqual(len(prayers), 1)
        target_id = prayers[0]["id"]

        # Call prayer action endpoint
        action_res = self.client.post("/api/god/prayer_action", json={
            "prayer_id": target_id,
            "decision": "grant",
            "notes": "İlahi lütuf bahşedildi."
        })
        action_data = json.loads(action_res.data.decode("utf-8"))
        self.assertTrue(action_data["success"])
        updated_prayers = action_data["state"]["prayers"]
        matching = [p for p in updated_prayers if p["id"] == target_id]
        self.assertEqual(matching[0]["status"], "kabul_edildi")

    def test_god_sim_set_era_api(self):
        import app as app_module
        app_module.current_game = GameState()
        app_module.current_game.initialize_game(
            character={"name": "Kozmik Varlık", "role": "Yaratıcı"},
            universe={"name": "Kozmos", "rules": "Yaratıcı mutlak", "dogmas": "Fizik tanrının emrindedir"},
            mode_data={"mode": "god_sim", "strictness": "balanced"},
            system_instruction="Kozmik Hakem",
            prologue_data={"story": "Evren doğdu."}
        )
        res = self.client.post("/api/god/set_era", json={"era": "Demir ve Krallıklar Çağı"})
        data = json.loads(res.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["era"], "Demir ve Krallıklar Çağı")
        self.assertEqual(app_module.current_game.civilization_era, "Demir ve Krallıklar Çağı")

    def test_god_sim_appoint_prophet_api(self):
        import app as app_module
        app_module.current_game = GameState()
        app_module.current_game.initialize_game(
            character={"name": "Kozmik Varlık", "role": "Yaratıcı"},
            universe={"name": "Kozmos", "rules": "Yaratıcı mutlak", "dogmas": "Fizik tanrının emrindedir"},
            mode_data={"mode": "god_sim", "strictness": "balanced"},
            system_instruction="Kozmik Hakem",
            prologue_data={"story": "Evren doğdu."}
        )
        res = self.client.post("/api/god/appoint_prophet", json={
            "name": "Bilge Ogan",
            "role": "Başkahin & Elçi",
            "region": "Kutsal Vadi",
            "doctrine": "Tanrının birliğini ve adaletini yayın."
        })
        data = json.loads(res.data.decode("utf-8"))
        self.assertTrue(data["success"])
        self.assertEqual(data["prophet"]["name"], "Bilge Ogan")
        self.assertEqual(data["prophet"]["role"], "Başkahin & Elçi")
        self.assertEqual(data["prophet"]["region"], "Kutsal Vadi")
        self.assertTrue(any(p["name"] == "Bilge Ogan" for p in app_module.current_game.prophets))

    def test_god_sim_prompt_builder(self):
        char = {"name": "Kozmik Tanrı", "role": "Mimar"}
        uni = {"name": "İlk Boyut", "rules": "Kozmik İrade", "dogmas": "Dogmalar esnetilebilir"}
        mode = {"mode": "god_sim", "strictness": "balanced"}

        sys_inst = PromptBuilder.build_system_instruction(char, uni, mode)
        self.assertIn("Cosmic Chronicler", sys_inst)
        self.assertIn("MUTLAK TANRISIDIR", sys_inst)
        self.assertIn("DUALAR VE YAKARILAR", sys_inst)

        prologue_prompt = PromptBuilder.build_prologue_prompt(char, uni, mode)
        self.assertIn("GENESIS PROLOGUE", prologue_prompt)
        self.assertIn("prayers_generated", prologue_prompt)

        # Action turn prompt
        gs_dict = {
            "character": char,
            "turn_count": 1,
            "is_god_sim": True,
            "faith": 65,
            "fear": 30,
            "divine_power": 85,
            "civilization_era": "Tapınak Çağı",
            "divine_decrees": ["Gündüz 3 güneş doğar"],
            "prophets": [{"name": "Kahran", "role": "Baş Rahip"}],
            "prayers": [
                {
                    "id": "p_1",
                    "mortal_name": "Tüccar",
                    "mortal_location": "Liman",
                    "prayer_type": "zenginlik",
                    "prayer_text": "Gemimi fırtınadan koru",
                    "status": "beklemede"
                }
            ],
            "story_log": []
        }
        action_prompt = PromptBuilder.build_action_turn_prompt(
            player_action="Fırtınayı dindirip denizi çarşaf gibi yapıyorum",
            game_state=gs_dict,
            universe=uni,
            mode_data=mode
        )
        self.assertIn("İLAHİ MEVCUT DURUM", action_prompt)
        self.assertIn("İman Seviyesi (Faith): 65/100", action_prompt)
        self.assertIn("Korku Seviyesi (Fear): 30/100", action_prompt)
        self.assertIn("İlahi Kudret (Divine Power): 85/100", action_prompt)
        self.assertIn("BEKLEYEN ÖLÜMLÜ DUALARI", action_prompt)
        self.assertIn("Gemimi fırtınadan koru", action_prompt)

    def test_god_sim_narrative_length_and_humanity_instructions(self):
        char = {"name": "Gök Tanrısı", "role": "Yaratıcı"}
        uni = {"name": "İlk Topraklar", "rules": "İlahi Ferman", "dogmas": "Doğa boyun eğer"}
        mode = {"mode": "god_sim", "strictness": "challenging"}

        sys_inst = PromptBuilder.build_system_instruction(char, uni, mode)
        self.assertIn("YAŞAYAN İNSANLIK VE DERİN DUYGUSAL BAĞ", sys_inst)
        self.assertIn("ÇOK SESLİ İNSAN KOROSU", sys_inst)
        self.assertIn("METİN UZUNLUĞU VE EDEBİ DERİNLİK", sys_inst)
        self.assertIn("4 ila 6 DOLGUN", sys_inst)

        prologue = PromptBuilder.build_prologue_prompt(char, uni, mode)
        self.assertIn("EN AZ 5-6 DOLGUN", prologue)
        self.assertIn("KULLARLA DERİN DUYGUSAL BAĞ", prologue)
        self.assertIn("ÇOK SESLİ İLK YAKARILAR", prologue)

        gs_dict = {
            "character": char,
            "turn_count": 1,
            "is_god_sim": True,
            "faith": 50,
            "fear": 20,
            "divine_power": 95,
            "civilization_era": "Yaratılış ve Kabileler Çağı",
            "divine_decrees": [],
            "prophets": [],
            "prayers": [],
            "story_log": []
        }
        action_prompt = PromptBuilder.build_action_turn_prompt(
            player_action="Toprağa bereket ve yağmur indiriyorum",
            game_state=gs_dict,
            universe=uni,
            mode_data=mode
        )
        self.assertIn("EN AZ 4-6 DOLGUN VE AYRINTILI PARAGRAFTAN", action_prompt)
        self.assertIn("MİKRO VE MAKRO İNSANLIK MANZARASI", action_prompt)
        self.assertIn("ÇOK SESLİ İNSAN KOROSU", action_prompt)

    def test_autosave_every_2_turns(self):
        gs = GameState()
        gs.initialize_game(
            character={"name": "Oto Kahraman", "role": "Kaşif"},
            universe={"name": "Gizemli Ada", "rules": "Vahşi Doğa", "dogmas": "Fizik"},
            mode_data={"mode": "realistic", "strictness": "ironclad"},
            system_instruction="Sistem",
            prologue_data={"story": "Adaya çıktın."}
        )

        # Turn 0: should not autosave
        self.assertIsNone(gs.auto_save())

        # Turn 1: should not autosave (odd turn)
        gs.turn_count = 1
        self.assertIsNone(gs.auto_save())

        # Turn 2: should autosave! (even turn > 0)
        gs.turn_count = 2
        saved_file = gs.auto_save()
        self.assertIsNotNone(saved_file)
        self.assertTrue(saved_file.startswith("otomatik_kayit_"))
        self.assertEqual(gs.last_autosave_turn, 2)

        # Verify file existence and content
        file_path = os.path.join(gs.SAVES_DIR, saved_file)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        self.assertTrue(saved_data.get("is_autosave"))
        self.assertEqual(saved_data.get("autosave_turn"), 2)
        self.assertEqual(saved_data.get("character", {}).get("name"), "Oto Kahraman")

        # Turn 3: should not autosave
        gs.turn_count = 3
        self.assertIsNone(gs.auto_save())

        # Turn 4: should autosave again
        gs.turn_count = 4
        saved_file_4 = gs.auto_save()
        self.assertEqual(saved_file, saved_file_4) # Reuses single active autosave slot
        self.assertEqual(gs.last_autosave_turn, 4)

        # Verify list_saves reflects is_autosave
        saves = GameState.list_saves()
        auto_entries = [s for s in saves if s["filename"] == saved_file]
        self.assertTrue(len(auto_entries) > 0)
        self.assertTrue(auto_entries[0]["is_autosave"])

        # Test API endpoint /api/auto_save
        r = self.client.post("/api/auto_save", json={"force": True})
        self.assertEqual(r.status_code, 200)
        resp_data = r.get_json()
        self.assertTrue(resp_data.get("success"))

        # Cleanup created autosave test file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    def test_token_optimization_and_compact_history(self):
        from app import get_compact_history
        from core.gemini_client import GeminiClient

        # 1. Test empty history
        self.assertEqual(get_compact_history([]), [])

        # 2. Test bloated historical prompt compaction
        bloated_prompt = (
            "====================================================\n"
            "⚔️ YENİ TUR: OYUNCU EYLEMİ VE HAKEM DEĞERLENDİRMESİ ⚔️\n"
            "KIRILMAZ KURAL HATIRLATMASI (ASLA GEVŞETİLEMEZ):\n"
            "MEVCUT DURUM:\n- Sağlık: 100/100\n"
            "OYUNCUNUN EYLEMİ:\n> \"Kütüphanedeki eski el yazmasını okuyorum\"\n\n"
            "HAKEM GÖREVİN: Kurallara uy."
        )
        bloated_model_json = json.dumps({
            "arbiter_verdict": "El yazması incelendi.",
            "rule_warnings": "Kurallar devrede.",
            "story": "Eski parşömen tozlar içinde açıldı.",
            "state_updates": {
                "health_delta": 0,
                "inventory_added": [],
                "inventory_removed": [],
                "status_effects": ["Meraklı"],
                "npc_attitude_updates": {},
                "deceased_or_departed_npcs": []
            },
            "suggested_actions": ["Okumaya devam et"]
        })

        raw_history = [
            {"role": "user", "parts": [{"text": "OYUN BAŞLIYOR: GİRİŞ SAHNESİ (PROLOGUE)\nÇok uzun kural metinleri..."}]},
            {"role": "model", "parts": [{"text": bloated_model_json}]},
            {"role": "user", "parts": [{"text": bloated_prompt}]},
            {"role": "model", "parts": [{"text": bloated_model_json}]}
        ]

        compacted = get_compact_history(raw_history, max_messages=12)
        self.assertEqual(len(compacted), 4)

        # First turn was prologue prompt -> compacted to start hook
        self.assertEqual(compacted[0]["parts"][0]["text"], "Macerayı ve açılış sahnesini başlat.")

        # Second user message was bloated turn prompt -> compacted to clean action
        self.assertEqual(compacted[2]["parts"][0]["text"], 'Oyuncu Eylemi: "Kütüphanedeki eski el yazmasını okuyorum"')

        # Model messages stripped down to story & verdict (omitted bulky state deltas)
        model_payload = json.loads(compacted[1]["parts"][0]["text"])
        self.assertIn("story", model_payload)
        self.assertIn("arbiter_verdict", model_payload)
        self.assertNotIn("state_updates", model_payload)
        self.assertNotIn("suggested_actions", model_payload)

        # 3. Test max_messages window slicing
        many_msgs = [{"role": "user", "parts": [{"text": f"Eylem {i}"}]} for i in range(25)]
        sliced = get_compact_history(many_msgs, max_messages=10)
        self.assertEqual(len(sliced), 10)
        self.assertEqual(sliced[-1]["parts"][0]["text"], "Eylem 24")

if __name__ == "__main__":
    unittest.main()


