/* Nova Voice Assistant — Frontend Logic */

// Screen reader announcement via ARIA live regions
function announce(msg, polite) {
  if (!msg) return;
  // Use assertive for urgent messages, polite for status
  const id = polite ? "sr-status" : "sr-announce";
  const el = document.getElementById(id);
  if (!el) return;
  // Clear + set with delay triggers screen reader announcement
  el.textContent = "";
  setTimeout(() => { el.textContent = msg; }, 50);
}

// ===== STATE =====
let currentState = "idle";
let isMuted = false;

// ===== MAIN VIEW =====

function updateState(state, status, response) {
  currentState = state;
  const orb = document.getElementById("orb");
  const statusEl = document.getElementById("status-text");
  const responseEl = document.getElementById("response-area");
  const mainEl = document.getElementById("main-view");

  // Update orb class
  orb.className = "orb " + (isMuted ? "muted" : state);

  if (status) {
    statusEl.textContent = status;
  }

  if (response) {
    responseEl.textContent = response;
    responseEl.classList.add("visible");
    // Screen reader announcement for response
    announce(response);
    // Auto-collapse after 8 seconds
    clearTimeout(window._collapseTimer);
    window._collapseTimer = setTimeout(() => {
      if (currentState === "idle") {
        responseEl.classList.remove("visible");
      }
    }, 8000);
  } else if (state === "idle") {
    responseEl.classList.remove("visible");
  }

  // Update aria-label on main-view for screen reader context
  if (mainEl) {
    mainEl.setAttribute("aria-label", "Nova Voice Assistant - " + (status || state));
  }

  // Announce state changes for screen readers
  const stateMessages = {
    "idle": status || "Nova ready",
    "listening": "Listening for your command",
    "thinking": "Processing your request",
    "speaking": "Nova is speaking",
    "error": status || "An error occurred",
  };
  const msg = stateMessages[state] || status || state;
  announce(msg);
}

function updateMuted(muted) {
  isMuted = muted;
  const btn = document.getElementById("btn-mute");
  const orb = document.getElementById("orb");

  if (muted) {
    btn.textContent = "Muted";
    btn.classList.add("muted");
    orb.className = "orb muted";
    announce("Microphone muted");
  } else {
    btn.textContent = "Mic on";
    btn.classList.remove("muted");
    orb.className = "orb " + currentState;
    announce("Microphone on");
  }
}

// Button handlers
function onTalk() {
  if (currentState === "idle" && !isMuted) {
    pywebview.api.activate();
  }
}

function onMute() {
  pywebview.api.toggle_mute();
}

function onSettings() {
  showSettings();
}

function onScreenShare() {
  pywebview.api.toggle_screen_share().then(active => {
    const btn = document.getElementById("btn-screen");
    if (active) {
      btn.textContent = "Screen ON";
      btn.classList.add("active");
      btn.setAttribute("aria-label", "Screen sharing on. Nova can see your screen. Press to turn off.");
      announce("Screen sharing on. Nova can now see your screen.");
    } else {
      btn.textContent = "Screen";
      btn.classList.remove("active");
      btn.setAttribute("aria-label", "Screen sharing off. Press to toggle screen sharing. Shortcut Ctrl Shift S.");
      announce("Screen sharing off.");
    }
  });
}

function onHide() {
  pywebview.api.minimize_to_tray();
}

function onOrbClick() {
  onTalk();
}

// ===== SETTINGS =====

let settingsData = {};
let activeTab = null;

async function showSettings() {
  settingsData = await pywebview.api.get_settings();
  const dark = settingsData.dark_mode !== false;
  document.body.classList.toggle("light", !dark);

  // Resize window to a proper settings size, centered on screen
  pywebview.api.resize_for_settings(true);

  document.getElementById("main-view").classList.add("hidden");
  document.getElementById("settings-view").classList.add("active");

  buildSettings();
  announce("Nova Settings. Use Tab to navigate. Arrow keys to move between tabs. Escape to close.");

  // Focus first tab
  setTimeout(() => {
    const firstTab = document.querySelector(".tab-btn");
    if (firstTab) firstTab.focus();
  }, 100);
}

function closeSettings() {
  document.getElementById("main-view").classList.remove("hidden");
  document.getElementById("settings-view").classList.remove("active");
  // Resize back to compact pill
  pywebview.api.resize_for_settings(false);
  announce("Settings closed");
  document.getElementById("btn-settings").focus();
}

function buildSettings() {
  const sidebar = document.getElementById("settings-sidebar");
  const content = document.getElementById("settings-content");
  sidebar.innerHTML = '<div class="sidebar-title" role="heading" aria-level="1">Settings</div>';
  content.innerHTML = "";

  const tabs = [
    { id: "integration", label: "Windows", build: buildWindowsIntegration },
    { id: "ai", label: "AI Models", build: buildAIModels },
    { id: "perms", label: "Permissions", build: buildPermissions },
    { id: "voice", label: "Voice", build: buildVoice },
    { id: "general", label: "General", build: buildGeneral },
    { id: "appearance", label: "Appearance", build: buildAppearance },
  ];

  const tabBtns = [];

  tabs.forEach((tab, i) => {
    // Sidebar button
    const btn = document.createElement("button");
    btn.className = "tab-btn";
    btn.textContent = tab.label;
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", "false");
    btn.setAttribute("aria-controls", "panel-" + tab.id);
    btn.addEventListener("click", () => switchTab(tab.id));
    btn.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        const next = tabBtns[(i + 1) % tabBtns.length];
        next.focus();
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        const prev = tabBtns[(i - 1 + tabBtns.length) % tabBtns.length];
        prev.focus();
      } else if (e.key === "Tab" && !e.shiftKey) {
        // Jump into content
        e.preventDefault();
        const panel = document.getElementById("panel-" + (activeTab || tabs[0].id));
        const first = panel && panel.querySelector("button, input, select");
        if (first) first.focus();
      } else if (e.key === "Escape") {
        e.preventDefault();
        closeSettings();
      }
    });
    sidebar.appendChild(btn);
    tabBtns.push(btn);

    // Content panel
    const panel = document.createElement("div");
    panel.className = "tab-panel";
    panel.id = "panel-" + tab.id;
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-label", tab.label + " settings");
    tab.build(panel);

    // Close button at bottom of each panel
    const closeBtn = document.createElement("button");
    closeBtn.className = "btn-close-settings";
    closeBtn.textContent = "Close Settings";
    closeBtn.addEventListener("click", closeSettings);
    panel.appendChild(closeBtn);

    content.appendChild(panel);
  });

  // Bind Shift-Tab on first content element to go back to sidebar
  tabs.forEach((tab) => {
    const panel = document.getElementById("panel-" + tab.id);
    const first = panel && panel.querySelector("button, input, select");
    if (first) {
      first.addEventListener("keydown", (e) => {
        if (e.key === "Tab" && e.shiftKey) {
          e.preventDefault();
          const tabBtn = sidebar.querySelector(".tab-btn.active");
          if (tabBtn) tabBtn.focus();
        }
      });
    }
  });

  // Show first tab
  switchTab(tabs[0].id);
}

function switchTab(tabId) {
  activeTab = tabId;
  // Update sidebar
  document.querySelectorAll(".tab-btn").forEach(btn => {
    const isActive = btn.getAttribute("aria-controls") === "panel-" + tabId;
    btn.classList.toggle("active", isActive);
    btn.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  // Update panels
  document.querySelectorAll(".tab-panel").forEach(panel => {
    panel.classList.toggle("active", panel.id === "panel-" + tabId);
  });
}

// --- Settings builders ---

function heading(parent, text) {
  const h = document.createElement("h2");
  h.className = "setting-heading";
  h.textContent = text;
  parent.appendChild(h);
}

function toggleBtn(parent, label, key) {
  const val = settingsData[key];
  const btn = document.createElement("button");
  btn.className = "setting-btn " + (val ? "on" : "off");
  btn.textContent = label + ": " + (val ? "ON" : "OFF");
  btn.setAttribute("aria-pressed", val ? "true" : "false");
  btn.addEventListener("click", async () => {
    const newVal = await pywebview.api.toggle_setting(key);
    settingsData[key] = newVal;
    btn.textContent = label + ": " + (newVal ? "ON" : "OFF");
    btn.className = "setting-btn " + (newVal ? "on" : "off");
    btn.setAttribute("aria-pressed", newVal ? "true" : "false");
    announce(label + ", " + (newVal ? "ON" : "OFF"));
  });
  parent.appendChild(btn);
}

function choiceGroup(parent, label, key, choices) {
  choices.forEach(([value, text]) => {
    const btn = document.createElement("button");
    const isSelected = settingsData[key] === value;
    btn.className = "setting-btn" + (isSelected ? " selected" : "");
    btn.textContent = (isSelected ? "[selected] " : "") + text;
    btn.setAttribute("aria-pressed", isSelected ? "true" : "false");
    btn.addEventListener("click", async () => {
      await pywebview.api.set_setting(key, value);
      settingsData[key] = value;
      // Update all buttons in this group
      const siblings = parent.querySelectorAll("[data-group='" + key + "']");
      siblings.forEach(s => {
        const sv = s.dataset.value;
        const sel = sv === value;
        s.className = "setting-btn" + (sel ? " selected" : "");
        s.textContent = (sel ? "[selected] " : "") + s.dataset.label;
        s.setAttribute("aria-pressed", sel ? "true" : "false");
      });
      announce(text + ", selected");
    });
    btn.dataset.group = key;
    btn.dataset.value = value;
    btn.dataset.label = text;
    parent.appendChild(btn);
  });
}

function buildAIModels(panel) {
  heading(panel, "Gemini Model");
  choiceGroup(panel, "Gemini Model", "gemini_model", [
    ["gemini-2.5-flash", "Gemini 2.5 Flash — fast, recommended"],
    ["gemini-2.5-pro", "Gemini 2.5 Pro — smartest"],
    ["gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite — fastest"],
    ["gemini-3-flash-preview", "Gemini 3.0 Flash Preview"],
    ["gemini-3-pro-preview", "Gemini 3.0 Pro Preview"],
  ]);

  heading(panel, "Gemini API Key");
  const currentKey = settingsData.gemini_api_key;
  const keyStatus = currentKey ? "Key is saved. Gemini AI is active." : "No key set.";

  const statusEl = document.createElement("p");
  statusEl.textContent = keyStatus;
  statusEl.style.color = currentKey ? "var(--accent)" : "var(--text-dim)";
  statusEl.setAttribute("aria-live", "polite");
  panel.appendChild(statusEl);

  const row = document.createElement("div");
  row.className = "input-row";

  const input = document.createElement("input");
  input.type = "password";
  input.placeholder = "Paste API key here";
  if (currentKey) input.value = currentKey;
  input.setAttribute("aria-label", "Gemini API key. " + keyStatus);
  row.appendChild(input);

  const saveBtn = document.createElement("button");
  saveBtn.className = "btn btn-save";
  saveBtn.textContent = "Save key";
  saveBtn.addEventListener("click", async () => {
    const k = input.value.trim();
    if (!k) {
      announce("No key entered.");
      return;
    }
    announce("Checking API key...");
    const result = await pywebview.api.save_api_key(k);
    if (result && result.ok === false) {
      announce(result.error || "Invalid API key.");
      statusEl.textContent = "Invalid key. Try again.";
      statusEl.style.color = "var(--text-dim)";
    } else {
      announce("API key saved and verified. Gemini AI is active.");
      statusEl.textContent = "Key is saved. Gemini AI is active.";
      statusEl.style.color = "var(--accent)";
    }
  });
  row.appendChild(saveBtn);
  panel.appendChild(row);
}

function buildWindowsIntegration(panel) {
  heading(panel, "Reach Nova");

  const status = document.createElement("div");
  status.className = "integration-status";
  status.setAttribute("aria-live", "polite");
  status.textContent = "Checking Windows integration...";
  panel.appendChild(status);

  const refresh = async () => {
    const data = await pywebview.api.get_windows_integration();
    if (data.error) {
      status.textContent = "Integration status unavailable: " + data.error;
      return;
    }
    status.innerHTML = "";
    [
      ["Platform", data.platform || "Windows"],
      ["Installed app", data.installed ? "Ready" : "Portable run"],
      ["Desktop shortcut", data.desktop_shortcut ? "Ready" : "Not created"],
      ["Start Menu shortcut", data.start_menu_shortcut ? "Ready" : "Not created"],
      ["Start with Windows", data.start_with_windows ? "On" : "Off"],
      ["nova:// links", data.uri_protocol ? "Registered" : "Not registered"],
      ["Win+R Nova.exe", data.app_path_alias ? "Registered" : "Not registered"],
      ["Start minimized", data.start_minimized ? "On" : "Off"],
      ["Wake word", data.wake_word_enabled ? "On" : "Off"],
    ].forEach(([label, value]) => {
      const row = document.createElement("div");
      row.className = "status-row";
      row.textContent = label + ": " + value;
      status.appendChild(row);
    });
  };

  const repair = document.createElement("button");
  repair.className = "setting-btn on";
  repair.textContent = "Repair all native integration";
  repair.addEventListener("click", async () => {
    announce("Repairing Nova integration.");
    const result = await pywebview.api.repair_native_integration();
    announce(result.ok ? "Nova integration repaired." : "Repair failed. " + result.message);
    settingsData.start_minimized = true;
    refresh();
  });
  panel.appendChild(repair);

  const desktop = document.createElement("button");
  desktop.className = "setting-btn";
  desktop.textContent = "Create desktop shortcut";
  desktop.addEventListener("click", async () => {
    announce("Creating desktop shortcut.");
    const result = await pywebview.api.create_desktop_shortcut();
    announce(result.ok ? "Desktop shortcut ready." : "Desktop shortcut failed. " + result.message);
    refresh();
  });
  panel.appendChild(desktop);

  const startMenu = document.createElement("button");
  startMenu.className = "setting-btn";
  startMenu.textContent = "Create Start Menu shortcut";
  startMenu.addEventListener("click", async () => {
    announce("Creating Start Menu shortcut.");
    const result = await pywebview.api.create_start_menu_shortcut();
    announce(result.ok ? "Start Menu shortcut ready." : "Start Menu shortcut failed. " + result.message);
    refresh();
  });
  panel.appendChild(startMenu);

  const startup = document.createElement("button");
  startup.className = "setting-btn";
  startup.textContent = "Turn on Start with Windows";
  startup.addEventListener("click", async () => {
    announce("Turning on Start with Windows.");
    const result = await pywebview.api.set_start_with_windows(true);
    announce(result.ok ? "Nova will start with Windows." : "Startup shortcut failed. " + result.message);
    refresh();
  });
  panel.appendChild(startup);

  const startupOff = document.createElement("button");
  startupOff.className = "setting-btn";
  startupOff.textContent = "Turn off Start with Windows";
  startupOff.addEventListener("click", async () => {
    announce("Turning off Start with Windows.");
    const result = await pywebview.api.set_start_with_windows(false);
    announce(result.ok ? "Nova will not start with Windows." : "Could not update startup. " + result.message);
    refresh();
  });
  panel.appendChild(startupOff);

  const uri = document.createElement("button");
  uri.className = "setting-btn";
  uri.textContent = "Register nova:// links";
  uri.addEventListener("click", async () => {
    announce("Registering Nova links.");
    const result = await pywebview.api.register_uri_handler();
    announce(result.ok ? "Nova links registered." : "Nova links failed. " + result.message);
    refresh();
  });
  panel.appendChild(uri);

  const alias = document.createElement("button");
  alias.className = "setting-btn";
  alias.textContent = "Register Win+R Nova.exe";
  alias.addEventListener("click", async () => {
    announce("Registering Win R alias.");
    const result = await pywebview.api.register_app_alias();
    announce(result.ok ? "Win R alias registered." : "Win R alias failed. " + result.message);
    refresh();
  });
  panel.appendChild(alias);

  const openInstall = document.createElement("button");
  openInstall.className = "setting-btn";
  openInstall.textContent = "Open installed Nova folder";
  openInstall.addEventListener("click", async () => {
    const result = await pywebview.api.open_install_location();
    announce(result.ok ? "Opening Nova folder." : "Could not open Nova folder. " + result.message);
  });
  panel.appendChild(openInstall);

  const openStartup = document.createElement("button");
  openStartup.className = "setting-btn";
  openStartup.textContent = "Open Windows Startup folder";
  openStartup.addEventListener("click", async () => {
    const result = await pywebview.api.open_startup_folder();
    announce(result.ok ? "Opening Startup folder." : "Could not open Startup folder. " + result.message);
  });
  panel.appendChild(openStartup);

  const openLogs = document.createElement("button");
  openLogs.className = "setting-btn";
  openLogs.textContent = "Open Nova logs folder";
  openLogs.addEventListener("click", async () => {
    const result = await pywebview.api.open_logs_folder();
    announce(result.ok ? "Opening logs folder." : "Could not open logs folder. " + result.message);
  });
  panel.appendChild(openLogs);

  const disconnect = document.createElement("button");
  disconnect.className = "setting-btn off";
  disconnect.textContent = "Disconnect startup and shell integration";
  disconnect.addEventListener("click", async () => {
    announce("Removing startup and shell integration.");
    const result = await pywebview.api.disconnect_native_integration();
    announce(result.ok ? "Startup and shell integration removed." : "Cleanup failed. " + result.message);
    refresh();
  });
  panel.appendChild(disconnect);

  toggleBtn(panel, "Start minimized to tray", "start_minimized");
  toggleBtn(panel, "Wake word — say Hey Nova to activate", "wake_word_enabled");
  refresh();
}

function buildPermissions(panel) {
  heading(panel, "Basic Permissions");
  const basic = [
    ["allow_typing", "Allow typing in documents"],
    ["allow_keyboard_control", "Allow keyboard and window control"],
    ["allow_app_launch", "Allow launching and closing apps"],
    ["allow_system_control", "Allow volume, brightness, shutdown"],
    ["allow_web_search", "Allow web search and URLs"],
    ["allow_file_access", "Allow reading files and folders"],
    ["allow_process_control", "Allow managing processes"],
    ["allow_network", "Allow network info, wifi, ping"],
  ];
  basic.forEach(([k, l]) => toggleBtn(panel, l, k));

  heading(panel, "Advanced Permissions (use with caution)");
  const advanced = [
    ["allow_file_write", "Allow writing and moving files"],
    ["allow_file_delete", "Allow deleting files and folders"],
    ["allow_shell_commands", "Allow shell commands"],
    ["allow_install_apps", "Allow installing and uninstalling apps"],
    ["allow_code_execution", "Allow running Python code"],
    ["allow_screen_control", "Allow screen sharing and mouse control"],
  ];
  advanced.forEach(([k, l]) => toggleBtn(panel, l, k));
}

function buildVoice(panel) {
  heading(panel, "Text to Speech Voice");
  // Voice list will be populated from Python
  const voiceContainer = document.createElement("div");
  voiceContainer.id = "voice-list";
  voiceContainer.textContent = "Loading voices...";
  panel.appendChild(voiceContainer);

  pywebview.api.get_voices().then(voices => {
    voiceContainer.textContent = "";
    if (voices && voices.length > 0) {
      choiceGroup(voiceContainer, "Voice", "tts_voice", voices);
    } else {
      voiceContainer.textContent = "No voices available";
    }
  });

  heading(panel, "Speech Speed");
  const rate = settingsData.tts_rate || 160;

  const speedDisplay = document.createElement("p");
  speedDisplay.id = "speed-display";
  speedDisplay.textContent = "Current speed: " + rate + " words per minute";
  speedDisplay.setAttribute("aria-live", "polite");
  panel.appendChild(speedDisplay);

  const slower = document.createElement("button");
  slower.className = "setting-btn";
  slower.textContent = "Slow down speech";
  slower.addEventListener("click", async () => {
    const newRate = Math.max(80, (settingsData.tts_rate || 160) - 20);
    await pywebview.api.set_setting("tts_rate", newRate);
    settingsData.tts_rate = newRate;
    document.getElementById("speed-display").textContent = "Current speed: " + newRate + " words per minute";
    announce("Speed " + newRate);
  });
  panel.appendChild(slower);

  const faster = document.createElement("button");
  faster.className = "setting-btn";
  faster.textContent = "Speed up speech";
  faster.addEventListener("click", async () => {
    const newRate = Math.min(300, (settingsData.tts_rate || 160) + 20);
    await pywebview.api.set_setting("tts_rate", newRate);
    settingsData.tts_rate = newRate;
    document.getElementById("speed-display").textContent = "Current speed: " + newRate + " words per minute";
    announce("Speed " + newRate);
  });
  panel.appendChild(faster);

  heading(panel, "Speech Recognition");
  const sttContainer = document.createElement("div");
  sttContainer.id = "stt-list";
  sttContainer.textContent = "Loading engines...";
  panel.appendChild(sttContainer);

  pywebview.api.get_stt_engines().then(engines => {
    sttContainer.textContent = "";
    if (engines && engines.length > 0) {
      choiceGroup(sttContainer, "STT Engine", "stt_engine", engines);
    }
  });
}

function buildGeneral(panel) {
  heading(panel, "Behavior");
  toggleBtn(panel, "Follow-up mode — keep listening after response", "follow_up_mode");
  toggleBtn(panel, "Confirm before dangerous actions", "confirm_actions");
}

function buildAppearance(panel) {
  heading(panel, "Theme");
  const dark = settingsData.dark_mode !== false;
  const themeBtn = document.createElement("button");
  themeBtn.className = "setting-btn";
  themeBtn.textContent = "Theme: " + (dark ? "Dark" : "Light") + " mode — press to switch";
  themeBtn.addEventListener("click", async () => {
    const newDark = !settingsData.dark_mode;
    await pywebview.api.set_setting("dark_mode", newDark);
    settingsData.dark_mode = newDark;
    document.body.classList.toggle("light", !newDark);
    themeBtn.textContent = "Theme: " + (newDark ? "Dark" : "Light") + " mode — press to switch";
    announce((newDark ? "Dark" : "Light") + " mode");
  });
  panel.appendChild(themeBtn);

  heading(panel, "Floating Orb Position");
  choiceGroup(panel, "Orb Position", "orb_position", [
    ["bottom-right", "Bottom right"],
    ["bottom-left", "Bottom left"],
    ["top-right", "Top right"],
    ["top-left", "Top left"],
  ]);
}

// ===== CONFIRMATION MODAL =====

function trapFocus(overlayId) {
  const overlay = document.getElementById(overlayId);
  if (!overlay) return;
  const focusable = overlay.querySelectorAll('button, input, select, textarea, [tabindex]:not([tabindex="-1"])');
  if (focusable.length === 0) return;
  const first = focusable[0];
  const last = focusable[focusable.length - 1];
  overlay.addEventListener("keydown", function trap(e) {
    if (e.key !== "Tab") return;
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }, { once: false });
}

function showConfirmation(description) {
  const overlay = document.getElementById("confirm-modal");
  document.getElementById("confirm-desc").textContent = description;
  overlay.classList.add("active");
  announce("Confirmation required. " + description + ". Press Enter to confirm, Escape to cancel.");
  setTimeout(() => {
    document.getElementById("btn-confirm-yes").focus();
    trapFocus("confirm-modal");
  }, 100);
}

function hideConfirmation() {
  document.getElementById("confirm-modal").classList.remove("active");
}

function cancelConfirmation() {
  pywebview.api.confirm_response(false);
  hideConfirmation();
  announce("Cancelled");
}

// ===== TYPE-TO-CHAT MODAL =====

function showTypeChat() {
  const overlay = document.getElementById("type-modal");
  overlay.classList.add("active");
  const input = document.getElementById("type-input");
  input.value = "";
  announce("Type your message to Nova. Press Enter to send, Escape to cancel.");
  setTimeout(() => input.focus(), 100);
}

function hideTypeChat() {
  document.getElementById("type-modal").classList.remove("active");
  announce("Prompt closed");
}

function sendTypedMessage() {
  const input = document.getElementById("type-input");
  const text = input.value.trim();
  if (text) {
    hideTypeChat();
    pywebview.api.process_text(text);
  } else {
    announce("Please type a message first.");
    input.focus();
  }
}

// ===== API KEY VIEW =====

function showApiKeyView() {
  document.getElementById("main-view").classList.add("hidden");
  document.getElementById("apikey-view").classList.add("active");
  announce("Nova first time setup. You need a Gemini API key. Tab through for instructions.");
  setTimeout(() => document.getElementById("apikey-input").focus(), 200);
}

async function saveApiKey() {
  const input = document.getElementById("apikey-input");
  const key = input.value.trim();
  if (!key) {
    announce("The field is empty. Please paste your API key first.");
    input.focus();
    return;
  }
  announce("Checking your API key...");
  const result = await pywebview.api.save_api_key(key);
  if (result && result.ok === false) {
    announce(result.error || "Invalid API key. Please try again.");
    input.focus();
    input.select();
  } else {
    announce("API key saved and verified. Setting up Nova...");
  }
}

function exitWithoutSaving() {
  pywebview.api.exit_app();
}

// ===== KEYBOARD SHORTCUTS =====
function isActive(id) {
  const el = document.getElementById(id);
  return !!(el && el.classList.contains("active"));
}

function closeActivePrompt() {
  if (isActive("confirm-modal")) {
    cancelConfirmation();
    return true;
  }

  if (isActive("type-modal")) {
    hideTypeChat();
    return true;
  }

  if (isActive("settings-view")) {
    closeSettings();
    return true;
  }

  if (isActive("apikey-view")) {
    exitWithoutSaving();
    return true;
  }

  onHide();
  return true;
}

function handleEscape(e) {
  if (e.key !== "Escape" && e.code !== "Escape") {
    return;
  }

  e.preventDefault();
  e.stopPropagation();
  if (typeof e.stopImmediatePropagation === "function") {
    e.stopImmediatePropagation();
  }
  closeActivePrompt();
}

document.addEventListener("keydown", (e) => {
  // Block browser shortcuts that would close/navigate the webview
  if ((e.ctrlKey && (e.key === "w" || e.key === "W")) ||
      (e.ctrlKey && (e.key === "F4")) ||
      (e.altKey && (e.key === "F4"))) {
    e.preventDefault();
    e.stopPropagation();
    return;
  }

  handleEscape(e);
}, true);

// Called by Python when pywebview is ready
window.addEventListener("pywebviewready", () => {
  pywebview.api.ui_ready();
});
