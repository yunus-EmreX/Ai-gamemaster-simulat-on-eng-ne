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

if __name__ == "__main__":
    unittest.main()

