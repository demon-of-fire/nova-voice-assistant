"""AI brain — Gemini only, kept intentionally lightweight.

Gemini (cloud, needs API key):
  - Function calling for PC control
  - Smart action routing
"""

import logging
import os
from datetime import datetime
import config
import actions

log = logging.getLogger("nova")

# Lazy imports keep startup small until an API key is available.
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
    "get_time": "allow_system_control",
    "get_date": "allow_system_control",
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
    # Screen control
    "click_at": "allow_screen_control",
    "double_click_at": "allow_screen_control",
    "right_click_at": "allow_screen_control",
    "move_mouse": "allow_screen_control",
    "scroll_screen": "allow_screen_control",
    "drag_to": "allow_screen_control",
    "get_screen_size": "allow_screen_control",
    "get_mouse_position": "allow_screen_control",
    # Utility
    "calculate": "allow_system_control",
    "create_timer": "allow_system_control",
    "take_note": "allow_file_write",
    "list_notes": "allow_file_access",
    "read_note": "allow_file_access",
    "convert_units": "allow_system_control",
    "lookup_word": "allow_web_search",
    "get_word_of_the_day": "allow_web_search",
    # Internet
    "get_weather": "allow_web_search",
    "get_news": "allow_web_search",
    "get_stock_price": "allow_web_search",
    "get_currency_rate": "allow_web_search",
    "translate_text": "allow_web_search",
    "check_website": "allow_network",
    "get_public_ip_info": "allow_network",
    "shorten_url": "allow_web_search",
    # Automation
    "start_pomodoro": "allow_system_control",
    "keep_awake": "allow_system_control",
    "stop_keeping_awake": "allow_system_control",
    "save_window_layout": "allow_system_control",
    "restore_window_layout": "allow_system_control",
    "list_layouts": "allow_file_access",
    "get_battery_report": "allow_system_control",
    # Text tools
    "transform_text": "allow_typing",
    "count_words": "allow_typing",
    "format_json": "allow_system_control",
    "minify_json": "allow_system_control",
    "convert_base": "allow_system_control",
    "extract_emails": "allow_system_control",
    "extract_urls": "allow_system_control",
    "compare_texts": "allow_system_control",
    # System tools
    "delete_note": "allow_file_delete",
    "set_power_plan": "allow_system_control",
    "get_power_plan": "allow_system_control",
    "get_storage_usage": "allow_system_control",
    "list_drives": "allow_system_control",
    "empty_recycle_bin": "allow_file_delete",
    "manage_startup_app": "allow_system_control",
    "create_restore_point": "allow_system_control",
    "disk_cleanup": "allow_system_control",
    "get_system_uptime": "allow_system_control",
    # More utility
    "generate_password": "allow_typing",
    "generate_uuid": "allow_system_control",
    "roll_dice": "allow_system_control",
    "flip_coin": "allow_system_control",
    "pick_random": "allow_system_control",
    "create_shopping_list": "allow_file_write",
    "add_to_shopping_list": "allow_file_write",
    "remove_from_shopping_list": "allow_file_write",
    "show_shopping_list": "allow_file_access",
    "set_reminder": "allow_system_control",
    "start_stopwatch": "allow_system_control",
    "stop_stopwatch": "allow_system_control",
    "lap_stopwatch": "allow_system_control",
    # More system
    "list_services": "allow_system_control",
    "restart_service": "allow_system_control",
    "start_service": "allow_system_control",
    "stop_service": "allow_system_control",
    "get_audio_devices": "allow_system_control",
    "get_display_info": "allow_system_control",
    "get_env_var": "allow_system_control",
    "list_env_vars": "allow_system_control",
    "list_startup_programs": "allow_system_control",
    # More internet
    "get_random_fact": "allow_web_search",
    "get_joke": "allow_web_search",
    "get_random_quote": "allow_web_search",
    "get_timezone_info": "allow_web_search",
    "define_slang": "allow_web_search",
    "generate_qr_code": "allow_web_search",
    # More text
    "strip_markdown": "allow_typing",
    "caesar_cipher": "allow_typing",
    "generate_lorem_ipsum": "allow_typing",
    "check_palindrome": "allow_typing",
    "check_anagram": "allow_typing",
    "text_statistics": "allow_typing",
    # More automation
    "delayed_screenshot": "allow_screen_control",
    "set_window_transparency": "allow_system_control",
    "get_clipboard_history": "allow_typing",
    "clear_clipboard_history": "allow_typing",
    "batch_rename": "allow_file_write",
    "organize_downloads": "allow_file_write",
    # More media
    "get_now_playing": "allow_system_control",
    "set_app_volume": "allow_system_control",
    "take_region_screenshot": "allow_screen_control",
    "pick_color": "allow_system_control",
    "toggle_magnifier": "allow_system_control",
    "set_magnifier_zoom": "allow_system_control",
    # quit_assistant has no permission gate — always allowed
}


class Brain:
    def __init__(self, settings):
        self.settings = settings
        self.gemini_client = None
        self.gemini_tools = None
        self.gemini_history = []
        self.screen_sharing = False  # When True, screenshots are sent with each message

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

        self.model = settings.get("gemini_model") or "gemini-2.5-flash"
        log.info("Brain init: model=%s, gemini=%s", self.model, self.has_gemini)

    @property
    def has_gemini(self):
        return self.gemini_client is not None

    def process(self, user_text):
        """Send every request through the single configured Gemini backend."""
        if self.has_gemini:
            return self._gemini_process(user_text)
        return "Gemini API key not set. Add it in Settings."

    def _gemini_process(self, user_text):
        """Full Gemini processing with function calling."""
        _load_gemini()
        now = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        msg = f"[{now}] {user_text}"

        # Build message parts — text + optional screenshot
        parts = [_types.Part(text=msg)]
        if self.screen_sharing:
            try:
                from actions.screen import take_screenshot
                img_bytes = take_screenshot()
                parts.append(_types.Part.from_bytes(data=img_bytes, mime_type="image/png"))
                parts[0] = _types.Part(
                    text=msg + "\n\n[A screenshot of the user's screen is attached. "
                    "Use it to see what the user sees. If they ask you to click something, "
                    "identify the element's coordinates from the screenshot and use click_at. "
                    "The screenshot resolution matches the screen pixel coordinates.]"
                )
            except Exception as e:
                log.error("Screenshot failed: %s", e)

        self.gemini_history.append(
            _types.Content(role="user", parts=parts)
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
            return f"Sorry, Gemini error: {str(e)[:100]}"

        if not response.candidates:
            log.error("Gemini returned empty candidates")
            return "I didn't get a response. Please try again."

        candidate = response.candidates[0]
        if not candidate.content or not candidate.content.parts:
            log.error("Gemini returned empty parts")
            return "I didn't get a response. Please try again."

        # Check if ANY part has a function call
        has_fn = any(p.function_call for p in candidate.content.parts)
        if has_fn:
            return self._handle_function_calls(candidate)

        reply = candidate.content.parts[0].text
        reply = reply.strip() if reply else "I didn't catch that."
        self.gemini_history.append(candidate.content)
        return reply

    def _execute_one(self, fn_name, fn_args):
        """Execute a single function call. Returns (result_str, cancelled_bool)."""
        log.info("Gemini called: %s(%s)", fn_name, fn_args)
        # Check permission
        required_perm = ACTION_PERMISSIONS.get(fn_name)
        if required_perm and not self.settings.get(required_perm):
            perm_label = required_perm.replace("allow_", "").replace("_", " ")
            return f"Blocked: '{perm_label}' is disabled in Settings.", False

        # Check if action needs confirmation
        from actions.confirmation import needs_confirmation, ask_confirmation
        if needs_confirmation(fn_name):
            desc = f"{fn_name}({', '.join(f'{k}={v!r}' for k, v in fn_args.items())})"
            if not ask_confirmation(f"Nova wants to: {desc}"):
                return "Cancelled by user.", True

        result = actions.execute(fn_name, fn_args)
        log.info("Action %s(%s) -> %s", fn_name, fn_args, result[:100] if result else "None")
        return result, False

    def _handle_function_calls(self, candidate):
        """Execute ALL function calls from a Gemini response, then loop for more.

        Supports multi-action: Gemini can return multiple function_call parts
        in one response, AND the follow-up response can contain more calls.
        Loops up to 10 rounds to prevent infinite chains.
        """
        MAX_ROUNDS = 10

        try:
            return self._function_call_loop(candidate, MAX_ROUNDS)
        except Exception as e:
            log.error("Function call chain crashed: %s", e, exc_info=True)
            return f"Something went wrong while executing that action."

    def _function_call_loop(self, candidate, MAX_ROUNDS):
        for _round in range(MAX_ROUNDS):
            parts = candidate.content.parts

            # Gather all function calls in this response
            fn_calls = [(p.function_call.name, dict(p.function_call.args) if p.function_call.args else {})
                        for p in parts if p.function_call]

            if not fn_calls:
                # No more function calls — extract text reply
                text_parts = [p.text.strip() for p in parts if p.text and p.text.strip()]
                reply = " ".join(text_parts) if text_parts else "Done."
                self.gemini_history.append(candidate.content)
                return reply

            # Add model's function-call content to history
            self.gemini_history.append(candidate.content)

            # Execute each function call and collect results
            response_parts = []
            any_cancelled = False
            last_result = ""

            for fn_name, fn_args in fn_calls:
                result, cancelled = self._execute_one(fn_name, fn_args)
                if cancelled:
                    any_cancelled = True
                last_result = result
                response_parts.append(
                    _types.Part(
                        function_response=_types.FunctionResponse(
                            name=fn_name, response={"result": result},
                        )
                    )
                )

            # If screen sharing, attach a fresh screenshot so Gemini sees the result
            if self.screen_sharing:
                try:
                    from actions.screen import take_screenshot
                    img_bytes = take_screenshot()
                    response_parts.append(
                        _types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                    )
                    response_parts.append(
                        _types.Part(text="[Updated screenshot after executing the action(s).]")
                    )
                except Exception:
                    pass

            # Add all function results to history in one message
            self.gemini_history.append(
                _types.Content(role="user", parts=response_parts)
            )

            if any_cancelled and len(fn_calls) == 1:
                self.gemini_history.append(
                    _types.Content(role="model", parts=[_types.Part(text="Alright, cancelled.")])
                )
                return "Alright, cancelled."

            # Ask Gemini for a follow-up (might be text OR more function calls)
            try:
                follow_up = self.gemini_client.models.generate_content(
                    model=self.model,
                    contents=self.gemini_history,
                    config=_types.GenerateContentConfig(
                        system_instruction=config.SYSTEM_PROMPT,
                        tools=[self.gemini_tools],
                        temperature=0.5,
                        max_output_tokens=300,
                    ),
                )
                if not follow_up.candidates or not follow_up.candidates[0].content:
                    self.gemini_history.append(
                        _types.Content(role="model", parts=[_types.Part(text="Done.")])
                    )
                    return "Done."

                candidate = follow_up.candidates[0]
                # Loop continues — next iteration checks if this has more function calls

            except Exception as e:
                log.error("Follow-up Gemini call failed: %s", e)
                if "error" in last_result.lower() or "couldn't" in last_result.lower():
                    reply = last_result
                else:
                    reply = "Done."
                self.gemini_history.append(
                    _types.Content(role="model", parts=[_types.Part(text=reply)])
                )
                return reply

        # Exhausted max rounds
        self.gemini_history.append(
            _types.Content(role="model", parts=[_types.Part(text="Done.")])
        )
        return "Done."

    def clear_history(self):
        self.gemini_history = []
