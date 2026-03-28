"""AI brain — Gemini for actions, Ollama for free conversation.

Gemini (cloud, needs API key):
  - Function calling for PC control
  - Smart action routing
  - Costs money per request

Ollama (local, free):
  - Conversational chat
  - No function calling (can't control PC)
  - Runs entirely on your machine
  - Requires Ollama installed: https://ollama.com

The brain auto-picks: if user wants an action → Gemini.
If just chatting → Ollama (if available), else Gemini.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime
import config
import actions

# Log to file so errors are never invisible
_log_path = os.path.join(os.path.expanduser("~"), "nova_error.log")
logging.basicConfig(
    filename=_log_path,
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("nova")

# Lazy imports for Gemini (may not be needed if Ollama-only)
_genai = None
_types = None


def _load_gemini():
    global _genai, _types
    if _genai is None:
        from google import genai
        from google.genai import types
        _genai = genai
        _types = types


# Map action names to the settings permission they require
ACTION_PERMISSIONS = {
    "launch_app": "allow_app_launch",
    "close_app": "allow_app_launch",
    "type_text": "allow_typing",
    "press_keys": "allow_keyboard_control",
    "minimize_window": "allow_keyboard_control",
    "maximize_window": "allow_keyboard_control",
    "close_window": "allow_keyboard_control",
    "switch_window": "allow_keyboard_control",
    "snap_window": "allow_keyboard_control",
    "set_volume": "allow_system_control",
    "get_volume": "allow_system_control",
    "set_brightness": "allow_system_control",
    "get_system_info": "allow_system_control",
    "shutdown_pc": "allow_system_control",
    "restart_pc": "allow_system_control",
    "lock_pc": "allow_system_control",
    "cancel_shutdown": "allow_system_control",
    "search_web": "allow_web_search",
    "quick_search": "allow_web_search",
    "open_url": "allow_web_search",
    "search_youtube": "allow_web_search",
    "open_folder": "allow_file_access",
    "find_files": "allow_file_access",
    "read_file": "allow_file_access",
    "list_directory": "allow_file_access",
    "get_file_info": "allow_file_access",
    "copy_to_clipboard": "allow_typing",
    "read_clipboard": "allow_typing",
    "write_file": "allow_file_write",
    "edit_file": "allow_file_write",
    "append_to_file": "allow_file_write",
    "create_folder": "allow_file_write",
    "copy_file": "allow_file_write",
    "move_file": "allow_file_write",
    "delete_file": "allow_file_delete",
    "delete_folder": "allow_file_delete",
    "run_command": "allow_shell_commands",
    "run_powershell": "allow_shell_commands",
    "install_app": "allow_install_apps",
    "uninstall_app": "allow_install_apps",
    "list_installed_apps": "allow_install_apps",
    "list_processes": "allow_process_control",
    "kill_process": "allow_process_control",
    "get_process_info": "allow_process_control",
    "get_network_info": "allow_network",
    "get_wifi_networks": "allow_network",
    "ping": "allow_network",
    "get_public_ip": "allow_network",
    "run_python": "allow_code_execution",
    "create_script": "allow_code_execution",
    "media_play_pause": "allow_system_control",
    "media_next": "allow_system_control",
    "media_previous": "allow_system_control",
    "media_stop": "allow_system_control",
    # quit_assistant has no permission gate — always allowed
}


class OllamaChat:
    """Free local conversation via Ollama."""

    def __init__(self, model="llama3.2", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        self.history = []
        self.available = self._check()

    def _check(self):
        """Check if Ollama is running."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags")
            resp = urllib.request.urlopen(req, timeout=2)
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            if models:
                # Use first available model if our preferred one isn't there
                if not any(self.model in m for m in models):
                    self.model = models[0].split(":")[0]
                return True
            return False
        except Exception:
            return False

    def chat(self, user_text):
        """Send message to Ollama and get response."""
        now = datetime.now().strftime("%I:%M %p")
        self.history.append({"role": "user", "content": f"[{now}] {user_text}"})

        if len(self.history) > 200:
            self.history = self.history[-200:]

        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": (
                    f"You are {config.ASSISTANT_NAME}, a friendly voice assistant. "
                    "Keep responses SHORT (1-3 sentences) since they're spoken aloud. "
                    "Be natural, witty, and conversational. No markdown or emojis. "
                    "You're having a casual voice conversation."
                )},
                *self.history,
            ],
            "stream": False,
            "options": {"num_predict": 150},
        }).encode()

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=30)
            data = json.loads(resp.read())
            reply = data["message"]["content"].strip()
            self.history.append({"role": "assistant", "content": reply})
            return reply
        except urllib.error.URLError:
            return "Ollama doesn't seem to be running. Start it with 'ollama serve' in a terminal."
        except Exception as e:
            return f"Sorry, had trouble talking to Ollama: {e}"


class Brain:
    def __init__(self, settings):
        self.settings = settings
        self.gemini_client = None
        self.gemini_tools = None
        self.gemini_history = []

        # Try to set up Gemini
        api_key = settings.get("gemini_api_key") or config.GEMINI_API_KEY
        if api_key:
            try:
                _load_gemini()
                self.gemini_client = _genai.Client(api_key=api_key)
                self.gemini_tools = _types.Tool(
                    function_declarations=[
                        _types.FunctionDeclaration(**decl)
                        for decl in actions.TOOL_DECLARATIONS
                    ]
                )
            except Exception as e:
                log.error("Gemini init failed: %s", e)

        ollama_model = settings.get("ollama_model") or "llama3.2"
        self.ollama = OllamaChat(model=ollama_model)

        self.model = settings.get("gemini_model") or "gemini-2.5-flash"
        log.info("Brain init: model=%s, gemini=%s, ollama=%s",
                 self.model, self.has_gemini, self.has_ollama)

    @property
    def has_gemini(self):
        return self.gemini_client is not None

    @property
    def has_ollama(self):
        return self.ollama.available

    def process(self, user_text):
        """Route to Gemini (actions) or Ollama (chat)."""
        mode = self.settings.get("ai_mode") or "auto"

        if mode == "ollama_only":
            if self.has_ollama:
                return self.ollama.chat(user_text)
            return "Ollama is not running. Start it or switch to Gemini mode."

        if mode == "gemini_only":
            if self.has_gemini:
                return self._gemini_process(user_text)
            return "Gemini API key not set. Add it in Settings."

        # Auto mode: use Gemini for actions, Ollama for chat
        if self.has_gemini:
            return self._gemini_process(user_text)
        elif self.has_ollama:
            return self.ollama.chat(user_text)
        else:
            return "No AI backend available. Set a Gemini API key or install Ollama."

    def _gemini_process(self, user_text):
        """Full Gemini processing with function calling."""
        _load_gemini()
        now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        msg = f"[{now}] {user_text}"

        self.gemini_history.append(
            _types.Content(role="user", parts=[_types.Part(text=msg)])
        )
        if len(self.gemini_history) > 200:
            self.gemini_history = self.gemini_history[-200:]

        try:
            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=self.gemini_history,
                config=_types.GenerateContentConfig(
                    system_instruction=config.SYSTEM_PROMPT,
                    tools=[self.gemini_tools],
                    temperature=0.4,
                    max_output_tokens=300,
                ),
            )
        except Exception as e:
            log.error("Gemini API error (model=%s): %s", self.model, e)
            err_msg = str(e).lower()
            if "api key" in err_msg or "api_key" in err_msg or "unauthorized" in err_msg or "403" in err_msg:
                return "Your Gemini API key seems invalid. Check it in Settings."
            if "not found" in err_msg or "404" in err_msg:
                # Auto-fix: switch to a known working model
                self.model = "gemini-2.5-flash"
                self.settings.set("gemini_model", self.model)
                log.warning("Auto-migrated to %s", self.model)
                return f"That model is no longer available. I've switched to {self.model}. Please try again."
            if "quota" in err_msg or "429" in err_msg or "rate" in err_msg:
                return "API rate limit hit. Wait a moment and try again."
            # Fallback to Ollama if available
            if self.has_ollama:
                return self.ollama.chat(user_text)
            return f"Sorry, Gemini error: {str(e)[:100]}"

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        if part.function_call:
            return self._handle_function_call(candidate, part)

        reply = part.text.strip() if part.text else "I didn't catch that."
        self.gemini_history.append(candidate.content)
        return reply

    def _handle_function_call(self, candidate, part):
        """Execute a Gemini function call."""
        fn = part.function_call
        fn_name = fn.name
        fn_args = dict(fn.args) if fn.args else {}

        # Check permission
        required_perm = ACTION_PERMISSIONS.get(fn_name)
        if required_perm and not self.settings.get(required_perm):
            perm_label = required_perm.replace("allow_", "").replace("_", " ")
            result = f"That action is disabled. Enable '{perm_label}' in the Settings menu."
            self.gemini_history.append(candidate.content)
            self.gemini_history.append(
                _types.Content(role="user", parts=[_types.Part(
                    function_response=_types.FunctionResponse(
                        name=fn_name, response={"result": result},
                    )
                )])
            )
            self.gemini_history.append(
                _types.Content(role="model", parts=[_types.Part(text=result)])
            )
            return result

        # Check if action needs confirmation
        from actions.confirmation import needs_confirmation, ask_confirmation
        if needs_confirmation(fn_name):
            desc = f"{fn_name}({', '.join(f'{k}={v!r}' for k, v in fn_args.items())})"
            if not ask_confirmation(f"Nova wants to: {desc}"):
                cancel_msg = "Cancelled by user."
                self.gemini_history.append(candidate.content)
                self.gemini_history.append(
                    _types.Content(role="user", parts=[_types.Part(
                        function_response=_types.FunctionResponse(
                            name=fn_name, response={"result": cancel_msg},
                        )
                    )])
                )
                self.gemini_history.append(
                    _types.Content(role="model", parts=[_types.Part(text="Alright, cancelled.")])
                )
                return "Alright, cancelled."

        result = actions.execute(fn_name, fn_args)
        log.info("Action %s(%s) -> %s", fn_name, fn_args, result[:100] if result else "None")

        self.gemini_history.append(candidate.content)
        self.gemini_history.append(
            _types.Content(
                role="user",
                parts=[_types.Part(
                    function_response=_types.FunctionResponse(
                        name=fn_name, response={"result": result},
                    )
                )],
            )
        )

        try:
            follow_up = self.gemini_client.models.generate_content(
                model=self.model,
                contents=self.gemini_history,
                config=_types.GenerateContentConfig(
                    system_instruction=config.SYSTEM_PROMPT,
                    tools=[self.gemini_tools],
                    temperature=0.5,
                    max_output_tokens=150,
                ),
            )
            # Make sure it's a text response, not another function call
            fp = follow_up.candidates[0].content.parts[0]
            if fp.text:
                reply = fp.text.strip()
            else:
                reply = "Done."
        except Exception as e:
            log.error("Follow-up Gemini call failed: %s", e)
            # Generate a natural response from the raw result instead of speaking it
            if "opened" in result.lower() or "closed" in result.lower():
                reply = result
            elif "error" in result.lower() or "couldn't" in result.lower():
                reply = result
            else:
                reply = "Done."

        self.gemini_history.append(
            _types.Content(role="model", parts=[_types.Part(text=reply)])
        )
        return reply

    def clear_history(self):
        self.gemini_history = []
        self.ollama.history = []
