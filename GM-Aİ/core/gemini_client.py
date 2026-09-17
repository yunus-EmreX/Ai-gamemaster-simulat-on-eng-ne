import json
import re
import requests
from typing import Dict, Any, List, Optional

class GeminiClient:
    """
    Direct REST client for Google Gemini API.
    Provides robust communication, error diagnostics, and JSON extraction.
    """
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self, api_key: str, default_model: str = "gemini-3.6-flash"):
        self.api_key = api_key.strip() if api_key else ""
        self.default_model = default_model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def test_connection(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Tests if the API key and selected model are valid with a minimal query."""
        if not self.api_key:
            return {"success": False, "error": "API anahtarı girilmedi."}
        
        target_model = model or self.default_model
        url = f"{self.BASE_URL}/{target_model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": "Ping test. Respond with OK."}]}
            ],
            "generationConfig": {
                "maxOutputTokens": 10
            }
        }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=12)
            if resp.status_code == 200:
                return {"success": True, "message": f"Bağlantı başarılı! ({target_model})"}
            else:
                try:
                    err_json = resp.json()
                    err_msg = err_json.get("error", {}).get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                return {"success": False, "status_code": resp.status_code, "error": err_msg}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Gemini API bağlantısı zaman aşımına uğradı (12s)."}
        except Exception as e:
            return {"success": False, "error": f"Bağlantı hatası: {str(e)}"}

    def generate_content(
        self,
        contents: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        json_mode: bool = False,
        max_tokens: int = 65536
    ) -> Dict[str, Any]:
        """
        Sends generation request to Gemini API via official x-goog-api-key header.
        Supports up to 65,536 output tokens (maximum possible in Gemini ecosystem).
        Returns a dict with {"success": True, "text": ..., "raw": ...} or error info.
        """
        if not self.api_key:
            return {"success": False, "error": "Gemini API anahtarı ayarlanmamış."}

        target_model = model or self.default_model
        url = f"{self.BASE_URL}/{target_model}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        # Maximum Output Tokens:
        # Gemini 2.5 / 3.x series supports up to 65,536 tokens (64K).
        # Gemini 1.5 series strictly caps output at 8,192 tokens.
        effective_max_tokens = max_tokens
        if "1.5" in target_model and effective_max_tokens > 8192:
            effective_max_tokens = 8192
        elif effective_max_tokens > 65536:
            effective_max_tokens = 65536

        generation_config: Dict[str, Any] = {
            "maxOutputTokens": effective_max_tokens
        }
        # Only inject temperature if explicitly specified and non-zero
        if temperature is not None:
            generation_config["temperature"] = max(0.0, min(1.0, float(temperature)))

        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config
        }

        if system_instruction:
            payload["system_instruction"] = {
                "parts": [{"text": system_instruction}]
            }

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code != 200:
                try:
                    err_data = resp.json()
                    err_text = err_data.get("error", {}).get("message", resp.text)
                except Exception:
                    err_text = resp.text

                # Auto-fallback: If model rejects tokens > 8192, retry automatically with 8192
                if resp.status_code == 400 and "maxOutputTokens" in err_text and effective_max_tokens > 8192:
                    payload["generationConfig"]["maxOutputTokens"] = 8192
                    resp = requests.post(url, json=payload, headers=headers, timeout=60)
                    if resp.status_code != 200:
                        return {
                            "success": False,
                            "status_code": resp.status_code,
                            "error": f"Gemini API Hatası ({resp.status_code}): {err_text}"
                        }
                else:
                    return {
                        "success": False,
                        "status_code": resp.status_code,
                        "error": f"Gemini API Hatası ({resp.status_code}): {err_text}"
                    }

            result_json = resp.json()
            candidates = result_json.get("candidates", [])
            if not candidates:
                return {
                    "success": False,
                    "error": "Model yanıt üretmedi (muhtemelen güvenlik filtreleri veya boş çıktı)."
                }

            first_candidate = candidates[0]
            finish_reason = first_candidate.get("finishReason", "UNKNOWN")
            
            parts = first_candidate.get("content", {}).get("parts", [])
            text_response = "".join([p.get("text", "") for p in parts if "text" in p])

            if not text_response:
                return {
                    "success": False,
                    "error": f"Model boş metin döndürdü. Bitiş nedeni: {finish_reason}"
                }

            usage_metadata = result_json.get("usageMetadata", {})

            return {
                "success": True,
                "text": text_response,
                "finish_reason": finish_reason,
                "usage_metadata": usage_metadata,
                "raw": result_json
            }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Gemini API yanıtı zaman aşımına uğradı (60s)."}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Ağ bağlantı hatası: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Beklenmeyen hata: {str(e)}"}

    @staticmethod
    def extract_json(raw_text: str) -> Optional[Dict[str, Any]]:
        """Safely extracts JSON even if enclosed in markdown code blocks, truncated, or malformed."""
        if not raw_text:
            return None
        cleaned = raw_text.strip()
        # Remove ```json ... ``` or ``` ... ```
        if "```" in cleaned:
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
            if match:
                cleaned = match.group(1).strip()

        # 1. Direct JSON parse
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        # 2. Try slicing from first { to last }
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(cleaned[start:end+1])
            except Exception:
                pass

        # 3. Try auto-completing truncated JSON endings
        if start != -1:
            snippet = cleaned[start:]
            for suffix in ['"}', '"}}', '"]}}', '"]}', '}', '\n}', '""}}}']:
                try:
                    return json.loads(snippet + suffix)
                except Exception:
                    pass

        # 4. Heuristic regex extraction fallback for story, arbiter_verdict, rule_warnings, state_updates
        def clean_unescape(val: str) -> str:
            if not val:
                return ""
            return (val.replace(r'\"', '"')
                       .replace(r'\n', '\n')
                       .replace(r'\r', '')
                       .replace(r'\t', '\t')
                       .replace(r'\\', '\\'))

        res: Dict[str, Any] = {
            "arbiter_verdict": "Eylem değerlendirildi.",
            "rule_warnings": "Kurallar devrede.",
            "story": "",
            "state_updates": {
                "health_delta": 0,
                "mental_delta": 0,
                "location": "",
                "inventory_added": [],
                "inventory_removed": [],
                "status_effects": [],
                "npc_attitude_updates": {},
                "deceased_or_departed_npcs": [],
                "is_game_over": False
            },
            "suggested_actions": []
        }

        # Extract arbiter_verdict
        m_arb = re.search(r'"arbiter_verdict"\s*:\s*"((?:\\.|[^"\\])*)"', cleaned)
        if m_arb:
            res["arbiter_verdict"] = clean_unescape(m_arb.group(1))

        # Extract rule_warnings
        m_warn = re.search(r'"rule_warnings"\s*:\s*"((?:\\.|[^"\\])*)"', cleaned)
        if m_warn:
            res["rule_warnings"] = clean_unescape(m_warn.group(1))

        # Extract story (even if unterminated at the end!)
        m_story = re.search(r'"story"\s*:\s*"((?:\\.|[^"\\])*?)(?:"\s*,\s*"[a-zA-Z_]+"|\s*\}\s*$|$)', cleaned, re.DOTALL)
        if not m_story:
            m_story = re.search(r'"story"\s*:\s*"([\s\S]*)$', cleaned)
        if m_story:
            story_val = m_story.group(1)
            # Remove trailing dangling quotes/braces
            story_val = re.sub(r'[\s"\}\],]+$', '', story_val)
            res["story"] = clean_unescape(story_val)

        # Extract location if present
        m_loc = re.search(r'"location"\s*:\s*"((?:\\.|[^"\\])*)"', cleaned)
        if m_loc:
            res["state_updates"]["location"] = clean_unescape(m_loc.group(1))

        # Extract health_delta if present
        m_hp = re.search(r'"health_delta"\s*:\s*(-?\d+)', cleaned)
        if m_hp:
            try:
                res["state_updates"]["health_delta"] = int(m_hp.group(1))
            except Exception:
                pass

        # Extract mental_delta if present
        m_mp = re.search(r'"mental_delta"\s*:\s*(-?\d+)', cleaned)
        if m_mp:
            try:
                res["state_updates"]["mental_delta"] = int(m_mp.group(1))
            except Exception:
                pass

        if res.get("story") or (m_arb and m_arb.group(1)):
            return res

        return None
