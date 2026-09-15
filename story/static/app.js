// Chronicles of Gemini - RPG Game Engine & Rule Arbiter Frontend

document.addEventListener("DOMContentLoaded", () => {
  // Elements - Setup
  const setupView = document.getElementById("setupView");
  const gameView = document.getElementById("gameView");
  const stepBtns = document.querySelectorAll(".step-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");
  const nextBtns = document.querySelectorAll(".next-btn");
  const prevBtns = document.querySelectorAll(".prev-btn");
  const presetCards = document.querySelectorAll(".preset-quick-card");
  const presetLoadedNotice = document.getElementById("presetLoadedNotice");

  // Mode radio cards
  const modeCards = document.querySelectorAll(".mode-card");
  const modeRadios = document.querySelectorAll("input[name='gameMode']");

  // API Config
  const apiKeyInput = document.getElementById("apiKeyInput");
  const btnToggleKeyVisibility = document.getElementById("btnToggleKeyVisibility");
  const btnTestKey = document.getElementById("btnTestKey");
  const apiStatusPill = document.getElementById("apiStatusPill");
  const testFeedbackMsg = document.getElementById("testFeedbackMsg");
  const modelSelect = document.getElementById("modelSelect");

  // Setup Form Fields
  const charName = document.getElementById("charName");
  const charAge = document.getElementById("charAge");
  const charRole = document.getElementById("charRole");
  const charSkills = document.getElementById("charSkills");
  const charFlaws = document.getElementById("charFlaws");
  const charBackstory = document.getElementById("charBackstory");
  const charGoal = document.getElementById("charGoal");
  const charInventory = document.getElementById("charInventory");

  const uniName = document.getElementById("uniName");
  const uniHistory = document.getElementById("uniHistory");
  const uniRules = document.getElementById("uniRules");
  const uniSocial = document.getElementById("uniSocial");
  const uniDamage = document.getElementById("uniDamage");
  const uniDogmas = document.getElementById("uniDogmas");

  const strictnessSelect = document.getElementById("strictnessSelect");
  const prologueHook = document.getElementById("prologueHook");
  const btnStartGame = document.getElementById("btnStartGame");

  // Elements - Header & Badges
  const modeBadge = document.getElementById("modeBadge");
  const modeBadgeText = document.getElementById("modeBadgeText");
  const strictnessBadge = document.getElementById("strictnessBadge");
  const strictnessBadgeText = document.getElementById("strictnessBadgeText");
  const btnSaveGame = document.getElementById("btnSaveGame");
  const btnLoadModalOpen = document.getElementById("btnLoadModalOpen");
  const btnNewGame = document.getElementById("btnNewGame");

  // Elements - Gameplay
  const displayCharName = document.getElementById("displayCharName");
  const displayCharRole = document.getElementById("displayCharRole");
  const displayLocation = document.getElementById("displayLocation");
  const healthVal = document.getElementById("healthVal");
  const healthBar = document.getElementById("healthBar");
  const mentalVal = document.getElementById("mentalVal");
  const mentalBar = document.getElementById("mentalBar");
  const statusEffectsList = document.getElementById("statusEffectsList");
  const inventoryList = document.getElementById("inventoryList");
  const anchorRulesBox = document.getElementById("anchorRulesBox");
  const storyLog = document.getElementById("storyLog");
  const playerActionInput = document.getElementById("playerActionInput");
  const btnSendAction = document.getElementById("btnSendAction");
  const actionHub = document.getElementById("actionHub");
  const gameOverBanner = document.getElementById("gameOverBanner");
  const gameOverText = document.getElementById("gameOverText");
  const btnRestartAfterDeath = document.getElementById("btnRestartAfterDeath");
  const btnLoadSaveAfterDeath = document.getElementById("btnLoadSaveAfterDeath");

  // Loading & Modal
  const globalLoading = document.getElementById("globalLoading");
  const loadingTitle = document.getElementById("loadingTitle");
  const loadingSubtitle = document.getElementById("loadingSubtitle");
  const savesModal = document.getElementById("savesModal");
  const btnCloseSavesModal = document.getElementById("btnCloseSavesModal");
  const saveNewContainer = document.getElementById("saveNewContainer");
  const saveFilenameInput = document.getElementById("saveFilenameInput");
  const btnConfirmSave = document.getElementById("btnConfirmSave");
  const savesListContainer = document.getElementById("savesListContainer");

  // State cache
  let allPresets = [];
  let isGameRunning = false;

  // Load saved API Key from localStorage
  const cachedKey = localStorage.getItem("gemini_rpg_api_key");
  if (cachedKey) {
    apiKeyInput.value = cachedKey;
    apiStatusPill.textContent = "Kayıtlı Anahtar Mevcut";
    apiStatusPill.className = "status-pill";
  }

  // Toggle API key visibility
  if (btnToggleKeyVisibility) {
    btnToggleKeyVisibility.addEventListener("click", () => {
      if (apiKeyInput.type === "password") {
        apiKeyInput.type = "text";
        btnToggleKeyVisibility.textContent = "🙈";
      } else {
        apiKeyInput.type = "password";
        btnToggleKeyVisibility.textContent = "👁️";
      }
    });
  }

  // Check backend config
  fetch("/api/config")
    .then(r => r.json())
    .then(data => {
      if (data.has_env_key) {
        apiStatusPill.textContent = "Çevre Değişkeni Aktif";
        apiStatusPill.className = "status-pill success";
        if (!apiKeyInput.value) {
          apiKeyInput.placeholder = `Aktif Çevre Anahtarı (${data.env_key_preview})`;
        }
      }
    })
    .catch(() => {});

  // Fetch presets from backend
  fetch("/api/presets")
    .then(r => r.json())
    .then(data => {
      if (data.success && data.presets) {
        allPresets = data.presets;
      }
    })
    .catch(err => console.warn("Şablonlar yüklenemedi:", err));

  // Quick Preset Cards click
  presetCards.forEach(card => {
    card.addEventListener("click", () => {
      const presetId = card.getAttribute("data-preset-id");
      applyPresetById(presetId);
    });
  });

  function applyPresetById(presetId) {
    const preset = allPresets.find(p => p.id === presetId);
    if (!preset) return;

    // Character
    charName.value = preset.character.name || "";
    charAge.value = preset.character.age || "";
    charRole.value = preset.character.role || "";
    charSkills.value = (preset.character.skills || []).join(", ");
    charFlaws.value = (preset.character.flaws || []).join(", ");
    charBackstory.value = preset.character.backstory || "";
    charGoal.value = preset.character.goal || "";
    charInventory.value = (preset.character.inventory || []).join(", ");

    // Universe
    uniName.value = preset.universe.name || "";
    uniHistory.value = preset.universe.history || "";
    uniRules.value = preset.universe.rules || "";
    uniSocial.value = preset.universe.social || "";
    uniDamage.value = preset.universe.damage_reality || "";
    uniDogmas.value = preset.universe.dogmas || "";

    // Mode
    if (preset.mode_data) {
      const mode = preset.mode_data.mode || "realistic";
      const radio = document.querySelector(`input[name='gameMode'][value='${mode}']`);
      if (radio) {
        radio.checked = true;
        updateModeCardSelection();
      }
      if (preset.mode_data.strictness) {
        strictnessSelect.value = preset.mode_data.strictness;
      }
      if (preset.mode_data.model) {
        modelSelect.value = preset.mode_data.model;
      }
      if (preset.mode_data.prologue_hook) {
        prologueHook.value = preset.mode_data.prologue_hook;
      }
    }

    // Show visual confirmation badge
    presetLoadedNotice.textContent = `✓ "${preset.title}" şablonu yüklendi!`;
    presetLoadedNotice.style.display = "block";
    setTimeout(() => {
      presetLoadedNotice.style.display = "none";
    }, 4000);
  }

  // Stepper navigation
  stepBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTabId = btn.getAttribute("data-tab");
      switchTab(targetTabId);
    });
  });

  nextBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const nextId = btn.getAttribute("data-next");
      switchTab(nextId);
    });
  });

  prevBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const prevId = btn.getAttribute("data-prev");
      switchTab(prevId);
    });
  });

  function switchTab(tabId) {
    stepBtns.forEach(b => b.classList.toggle("active", b.getAttribute("data-tab") === tabId));
    tabPanes.forEach(p => p.classList.toggle("active", p.id === tabId));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Mode radio cards toggle
  modeRadios.forEach(radio => {
    radio.addEventListener("change", updateModeCardSelection);
  });

  function updateModeCardSelection() {
    const selectedValue = document.querySelector("input[name='gameMode']:checked")?.value;
    document.getElementById("cardRealistic")?.classList.toggle("active", selectedValue === "realistic");
    document.getElementById("cardFantasy")?.classList.toggle("active", selectedValue === "fantasy");
  }

  // Test API Key
  btnTestKey.addEventListener("click", async () => {
    const key = apiKeyInput.value.trim();
    const model = modelSelect.value;

    if (!key) {
      testFeedbackMsg.textContent = "Lütfen önce bir API anahtarı yapıştırın.";
      testFeedbackMsg.className = "test-feedback-msg error";
      testFeedbackMsg.style.display = "block";
      apiKeyInput.focus();
      return;
    }

    btnTestKey.disabled = true;
    btnTestKey.textContent = "⏳ Sınanıyor...";
    apiStatusPill.textContent = "Test Ediliyor...";
    apiStatusPill.className = "status-pill";
    testFeedbackMsg.style.display = "none";

    try {
      const res = await fetch("/api/check_key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ api_key: key, model: model })
      });
      const data = await res.json();
      btnTestKey.disabled = false;
      btnTestKey.textContent = "Test Et";

      if (data.success) {
        apiStatusPill.textContent = "✓ Bağlantı Başarılı";
        apiStatusPill.className = "status-pill success";
        testFeedbackMsg.textContent = `✓ Tebrikler! Google Gemini API bağlantısı doğrulandı. (${model} modeli hazır)`;
        testFeedbackMsg.className = "test-feedback-msg success";
        testFeedbackMsg.style.display = "block";
        localStorage.setItem("gemini_rpg_api_key", key);
      } else {
        apiStatusPill.textContent = "Bağlantı Hatası";
        apiStatusPill.className = "status-pill error";
        testFeedbackMsg.textContent = `❌ API Hatası: ${data.error || "Bilinmeyen hata"}`;
        testFeedbackMsg.className = "test-feedback-msg error";
        testFeedbackMsg.style.display = "block";
      }
    } catch (e) {
      btnTestKey.disabled = false;
      btnTestKey.textContent = "Test Et";
      apiStatusPill.textContent = "Ağ Hatası";
      apiStatusPill.className = "status-pill error";
      testFeedbackMsg.textContent = `❌ Sunucuya erişilemedi: ${e.message}`;
      testFeedbackMsg.className = "test-feedback-msg error";
      testFeedbackMsg.style.display = "block";
    }
  });

  // START GAME
  btnStartGame.addEventListener("click", async () => {
    const nameVal = charName.value.trim();
    const roleVal = charRole.value.trim();
    const flawsVal = charFlaws.value.trim();
    const uniNameVal = uniName.value.trim();
    const uniRulesVal = uniRules.value.trim();
    const uniDogmasVal = uniDogmas.value.trim();
    const keyVal = apiKeyInput.value.trim();

    if (!nameVal || !roleVal) {
      alert("Lütfen 1. Sekmede Karakter Adı ve Rolünü doldurun.");
      switchTab("tabCharacter");
      charName.focus();
      return;
    }

    if (!flawsVal) {
      alert("Gerçekçi bir deneyim için karakterinize en az bir kusur veya zayıflık girmelisiniz.");
      switchTab("tabCharacter");
      charFlaws.focus();
      return;
    }

    if (!uniNameVal || !uniRulesVal || !uniDogmasVal) {
      alert("Lütfen 2. Sekmede Evren Adı, Kuralları ve Kırılmaz Dogmaları doldurun.");
      switchTab("tabUniverse");
      uniName.focus();
      return;
    }

    if (!keyVal && apiStatusPill.textContent !== "Çevre Değişkeni Aktif") {
      alert("Lütfen 3. Sekmede Gemini API Anahtarınızı girin.");
      switchTab("tabMode");
      apiKeyInput.focus();
      return;
    }

    const payload = {
      api_key: keyVal,
      character: {
        name: nameVal,
        age: charAge.value.trim(),
        role: roleVal,
        skills: charSkills.value.split(",").map(s => s.trim()).filter(Boolean),
        flaws: charFlaws.value.split(",").map(s => s.trim()).filter(Boolean),
        backstory: charBackstory.value.trim(),
        goal: charGoal.value.trim(),
        inventory: charInventory.value.split(",").map(s => s.trim()).filter(Boolean)
      },
      universe: {
        name: uniNameVal,
        history: uniHistory.value.trim(),
        rules: uniRulesVal,
        social: uniSocial.value.trim(),
        damage_reality: uniDamage.value.trim(),
        dogmas: uniDogmasVal
      },
      mode_data: {
        mode: document.querySelector("input[name='gameMode']:checked")?.value || "realistic",
        strictness: strictnessSelect.value,
        model: modelSelect.value,
        prologue_hook: prologueHook.value.trim()
      }
    };

    if (keyVal) {
      localStorage.setItem("gemini_rpg_api_key", keyVal);
    }

    showLoading("Evren Mühürleniyor...", "Gemini API evren kurallarını işliyor ve başlangıç sahnesini kuruyor...");

    try {
      const res = await fetch("/api/start_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      hideLoading();

      if (data.success && data.state) {
        renderGameState(data.state);
        setupView.style.display = "none";
        gameView.style.display = "grid";
        isGameRunning = true;
        updateHeaderControls(data.state);
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        alert(`Oyun başlatılamadı:\n${data.error || "Bilinmeyen hata"}`);
      }
    } catch (e) {
      hideLoading();
      alert(`Sunucu hatası: ${e.message}`);
    }
  });

  // TAKE ACTION
  btnSendAction.addEventListener("click", () => sendPlayerAction());
  playerActionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendPlayerAction();
    }
  });

  async function sendPlayerAction(customText = null) {
    const actionText = customText || playerActionInput.value.trim();
    if (!actionText) return;

    playerActionInput.value = "";
    btnSendAction.disabled = true;
    showLoading("Evren Hakemi Karar Veriyor...", "Eylemin fizik kanunlarına ve evren yasalarına uygunluğu denetleniyor...");

    try {
      const res = await fetch("/api/take_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionText })
      });
      const data = await res.json();
      hideLoading();
      btnSendAction.disabled = false;

      if (data.success && data.state) {
        renderGameState(data.state);
      } else {
        alert(`Eylem işlenirken hata oluştu:\n${data.error || "Bilinmeyen hata"}`);
      }
    } catch (e) {
      hideLoading();
      btnSendAction.disabled = false;
      alert(`İletişim hatası: ${e.message}`);
    }
  }

  // Helper: Cleans any escaped characters or raw JSON envelopes from story narrative
  function cleanStoryNarrative(raw) {
    if (!raw) return "";
    let s = String(raw).trim();
    // If raw text starts with JSON artifact { and has "story":, salvage clean story
    if (s.startsWith("{") && (s.includes('"story"') || s.includes('"arbiter_verdict"'))) {
      const match = s.match(/"story"\s*:\s*"([\s\S]*?)(?:"\s*,\s*"[a-zA-Z_]+"|\s*\}\s*$|$)/);
      if (match) {
        s = match[1];
      }
    }
    // Convert escaped newlines, returns, and escaped quotes to real characters
    s = s.replace(/\\n/g, "\n").replace(/\\r/g, "").replace(/\\"/g, '"');
    return s.trim();
  }

  // Helper: Format dialogues cleanly as [Speaker]; "Quote" without broken tag leaks
  function formatDialogueHTML(text) {
    if (!text) return "";
    let s = text.replace(/\\"/g, '"').replace(/\\n/g, "\n");
    let safe = s
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Match [Speaker]; "quote" or [Speaker]: "quote" or with typographic quotes
    safe = safe.replace(/\[([^\]]+)\]\s*[;:]\s*["“]([^"”]+)["”]/g, (match, speaker, quote) => {
      return `<strong class="dialogue-speaker">[${speaker}];</strong> <span class="dialogue-quote">"${quote}"</span>`;
    });

    // Also match Speaker: "quote" if model omitted brackets
    safe = safe.replace(/(^|[\n\s])([A-ZÇĞİÖŞÜ][A-Za-zÇĞİÖŞÜçğıöşü\s'’\-]+):\s*["“]([^"”]+)["”]/g, (match, pre, speaker, quote) => {
      return `${pre}<strong class="dialogue-speaker">[${speaker}];</strong> <span class="dialogue-quote">"${quote}"</span>`;
    });

    return safe;
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // RENDER GAME STATE
  function renderGameState(state) {
    displayCharName.textContent = state.character.name || "Bilinmeyen Gezgin";
    displayCharRole.textContent = `${state.character.role || "Gezgin"} (${state.character.age || "Yaş Belirsiz"})`;
    displayLocation.textContent = `📍 ${state.location || "Bilinmeyen Konum"}`;

    // Health
    const hp = Math.max(0, Math.min(100, state.health || 0));
    healthVal.textContent = `${hp}%`;
    healthBar.style.width = `${hp}%`;
    if (hp <= 25) {
      healthBar.style.background = "var(--accent-red)";
    } else if (hp <= 50) {
      healthBar.style.background = "linear-gradient(90deg, #ef4444 0%, #f59e0b 100%)";
    } else {
      healthBar.style.background = "linear-gradient(90deg, #ef4444 0%, #10b981 100%)";
    }

    // Mental
    const mental = Math.max(0, Math.min(100, state.mental || 0));
    mentalVal.textContent = `${mental}%`;
    mentalBar.style.width = `${mental}%`;

    // Status Effects
    statusEffectsList.innerHTML = "";
    const effects = state.status_effects || [];
    if (effects.length === 0) {
      statusEffectsList.innerHTML = '<span class="status-tag">Normal</span>';
    } else {
      effects.forEach(eff => {
        const tag = document.createElement("span");
        tag.className = "status-tag";
        tag.textContent = eff;
        statusEffectsList.appendChild(tag);
      });
    }

    // Inventory
    inventoryList.innerHTML = "";
    const items = state.inventory || [];
    if (items.length === 0) {
      inventoryList.innerHTML = '<li style="color: var(--text-dim); font-style: italic;">Envanter boş</li>';
    } else {
      items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        inventoryList.appendChild(li);
      });
    }

    // NPC Relationships
    const npcRelationsList = document.getElementById("npcRelationsList");
    if (npcRelationsList) {
      npcRelationsList.innerHTML = "";
      const relations = state.npc_relationships || {};
      const keys = Object.keys(relations);
      if (keys.length === 0) {
        npcRelationsList.innerHTML = '<span class="empty-hint">Sahnede veya yakında kimse yok</span>';
      } else {
        keys.forEach(npcName => {
          const card = document.createElement("div");
          card.className = "npc-relation-card";
          const attText = typeof relations[npcName] === 'object' ? relations[npcName].attitude : relations[npcName];
          card.innerHTML = `
            <div class="npc-card-header">
              <span class="npc-name">${escapeHtml(npcName)}</span>
              <button class="npc-card-remove-btn" title="Karakteri listeden sil" data-name="${escapeHtml(npcName)}">×</button>
            </div>
            <span class="npc-attitude-pill">${escapeHtml(attText || "Bilinmiyor")}</span>
          `;
          const removeBtn = card.querySelector(".npc-card-remove-btn");
          if (removeBtn) {
            removeBtn.addEventListener("click", async (e) => {
              e.stopPropagation();
              try {
                const res = await fetch("/api/gm/remove_npc", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ name: npcName })
                });
                const data = await res.json();
                if (data.success && data.state) {
                  renderGameState(data.state);
                }
              } catch (err) {
                console.error("NPC silme hatası:", err);
              }
            });
          }
          npcRelationsList.appendChild(card);
        });
      }
    }

    // Update GM Modal inventory chips if open
    renderGmInventoryChips(items);

    // Anchor Rules Box
    const rulesText = state.universe.dogmas || state.universe.rules || "Tanımlanmış katı kurallar geçerlidir.";
    anchorRulesBox.textContent = `[KIRILMAZ DOGMALAR]\n${rulesText}`;

    // Render Story Log
    storyLog.innerHTML = "";
    const logs = state.story_log || [];
    logs.forEach(entry => {
      const card = document.createElement("div");
      card.className = "turn-card";

      // Turn Header
      const header = document.createElement("div");
      header.className = "turn-header";
      header.innerHTML = `
        <span class="turn-badge">${entry.turn === 0 ? "Açılış Sahnesi" : `Tur #${entry.turn}`}</span>
        <span>${entry.timestamp || ""}</span>
      `;
      card.appendChild(header);

      // Player Action Bubble (if not prologue)
      if (entry.turn > 0 && entry.action) {
        const actionBubble = document.createElement("div");
        actionBubble.className = "player-action-bubble";
        actionBubble.textContent = `"${entry.action}"`;
        card.appendChild(actionBubble);
      }

      // Arbiter Box
      if (entry.arbiter_verdict) {
        const arbBox = document.createElement("div");
        arbBox.className = "arbiter-box";
        arbBox.innerHTML = `
          <div class="arbiter-title">⚖️ Evren Hakemi Analizi:</div>
          <div class="arbiter-text">${entry.arbiter_verdict}</div>
          ${entry.rule_warnings && entry.rule_warnings !== "Kurallar tam işletildi" && entry.rule_warnings !== "Evren kuralları aktif." ? `<div class="rule-warning-line">⚠️ Kural Notu: ${entry.rule_warnings}</div>` : ""}
        `;
        card.appendChild(arbBox);
      }

      // Story Narrative
      const narrative = document.createElement("div");
      narrative.className = "story-narrative";
      const cleanStory = cleanStoryNarrative(entry.story || "");
      const paragraphs = cleanStory.split("\n\n").filter(Boolean);
      if (paragraphs.length === 0) {
        narrative.innerHTML = `<p>${formatDialogueHTML(cleanStory)}</p>`;
      } else {
        paragraphs.forEach(p => {
          const pEl = document.createElement("p");
          pEl.innerHTML = formatDialogueHTML(p);
          narrative.appendChild(pEl);
        });
      }
      card.appendChild(narrative);

      storyLog.appendChild(card);
    });

    // Auto scroll to bottom
    setTimeout(() => {
      storyLog.scrollTop = storyLog.scrollHeight;
    }, 50);

    // Game Over Check
    if (state.is_game_over) {
      gameOverBanner.style.display = "flex";
      gameOverText.textContent = state.game_over_reason || "Ölümcül sonuçlar nedeniyle hikaye sona erdi.";
      actionHub.style.display = "none";
    } else {
      gameOverBanner.style.display = "none";
      actionHub.style.display = "flex";
    }
  }

  // Header Controls Update
  function updateHeaderControls(state) {
    modeBadge.style.display = "inline-flex";
    const modeName = state.mode_data.mode === "realistic" ? "🛡️ Gerçekçi Mod" : "✨ Fantezi Modu";
    modeBadgeText.textContent = modeName;

    strictnessBadge.style.display = "inline-flex";
    const strictMap = {
      ironclad: "🔒 Demir Kural",
      challenging: "⚔️ Zorlayıcı",
      balanced: "⚖️ Dengeli"
    };
    strictnessBadgeText.textContent = strictMap[state.mode_data.strictness] || "Tavizsiz";

    btnSaveGame.style.display = "inline-block";
    btnOpenGMModal.style.display = "inline-block";
    btnNewGame.style.display = "inline-block";

    // Update Godmode label if GM panel is loaded
    if (btnGmToggleGodmode) {
      btnGmToggleGodmode.textContent = state.god_mode 
        ? "🛡️ Ölümsüzlük (God Mode): AÇIK ✓" 
        : "🛡️ Ölümsüzlük (God Mode): KAPALI";
    }
  }

  // Return to Setup / New Game
  btnNewGame.addEventListener("click", () => {
    if (confirm("Mevcut oyundan çıkıp kurulum ekranına dönmek istiyor musunuz? (Kaydedilmemiş ilerlemeler kaybolabilir)")) {
      gameView.style.display = "none";
      setupView.style.display = "flex";
      modeBadge.style.display = "none";
      strictnessBadge.style.display = "none";
      btnSaveGame.style.display = "none";
      btnOpenGMModal.style.display = "none";
      btnNewGame.style.display = "none";
      isGameRunning = false;
    }
  });

  // Restart After Death
  btnRestartAfterDeath.addEventListener("click", () => {
    gameView.style.display = "none";
    setupView.style.display = "flex";
    modeBadge.style.display = "none";
    strictnessBadge.style.display = "none";
    btnSaveGame.style.display = "none";
    btnOpenGMModal.style.display = "none";
    btnNewGame.style.display = "none";
    isGameRunning = false;
  });

  btnLoadSaveAfterDeath.addEventListener("click", () => {
    openSavesModal();
  });

  // SAVES MODAL
  btnSaveGame.addEventListener("click", () => {
    saveNewContainer.style.display = "flex";
    saveFilenameInput.value = `kayit_${displayCharName.textContent.toLowerCase().replace(/\s+/g, "_")}`;
    openSavesModal();
  });

  btnLoadModalOpen.addEventListener("click", () => {
    saveNewContainer.style.display = isGameRunning ? "flex" : "none";
    openSavesModal();
  });

  btnCloseSavesModal.addEventListener("click", () => {
    savesModal.style.display = "none";
  });

  async function openSavesModal() {
    savesModal.style.display = "flex";
    await refreshSavesList();
  }

  async function refreshSavesList() {
    savesListContainer.innerHTML = '<div class="loading-state">Kayıtlar aranıyor...</div>';
    try {
      const res = await fetch("/api/list_saves");
      const data = await res.json();
      savesListContainer.innerHTML = "";

      if (!data.success || !data.saves || data.saves.length === 0) {
        savesListContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; font-size: 0.9rem; padding: 20px;">Henüz kaydedilmiş bir macera bulunmuyor.</p>';
        return;
      }

      data.saves.forEach(s => {
        const item = document.createElement("div");
        item.className = "save-item";
        item.innerHTML = `
          <div class="save-info">
            <h5>${s.character_name} - ${s.universe_name}</h5>
            <p>Tur: ${s.turn_count} | Mod: ${s.mode} | Tarih: ${s.saved_at}</p>
          </div>
          <button class="primary-btn load-save-btn" data-filename="${s.filename}">Yükle</button>
        `;
        item.querySelector(".load-save-btn").addEventListener("click", async () => {
          await loadSaveFile(s.filename);
        });
        savesListContainer.appendChild(item);
      });
    } catch (e) {
      savesListContainer.innerHTML = `<p style="color: var(--accent-red);">Kayıtlar alınırken hata oluştu: ${e.message}</p>`;
    }
  }

  btnConfirmSave.addEventListener("click", async () => {
    const fname = saveFilenameInput.value.trim();
    if (!fname) return;

    try {
      const res = await fetch("/api/save_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: fname })
      });
      const data = await res.json();
      if (data.success) {
        alert(data.message || "Kaydedildi!");
        await refreshSavesList();
      } else {
        alert("Kaydetme hatası: " + (data.error || "Bilinmiyor"));
      }
    } catch (e) {
      alert("Hata: " + e.message);
    }
  });

  async function loadSaveFile(filename) {
    showLoading("Kayıt Yükleniyor...", "Evren durumu ve hikaye geçmişi geri yükleniyor...");
    try {
      const res = await fetch("/api/load_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: filename })
      });
      const data = await res.json();
      hideLoading();

      if (data.success && data.state) {
        renderGameState(data.state);
        savesModal.style.display = "none";
        setupView.style.display = "none";
        gameView.style.display = "grid";
        isGameRunning = true;
        updateHeaderControls(data.state);
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        alert("Kayıt yüklenemedi: " + (data.error || "Bilinmeyen hata"));
      }
    } catch (e) {
      hideLoading();
      alert("Hata: " + e.message);
    }
  }

  // --- GM / CHEAT PANEL LOGIC ---
  const btnOpenGMModal = document.getElementById("btnOpenGMModal");
  const gmModal = document.getElementById("gmModal");
  const btnCloseGMModal = document.getElementById("btnCloseGMModal");
  const gmFeedbackBanner = document.getElementById("gmFeedbackBanner");

  const btnGmHealFull = document.getElementById("btnGmHealFull");
  const btnGmMentalFull = document.getElementById("btnGmMentalFull");
  const btnGmToggleGodmode = document.getElementById("btnGmToggleGodmode");
  const gmAddItemInput = document.getElementById("gmAddItemInput");
  const btnGmAddItem = document.getElementById("btnGmAddItem");
  const gmInventoryChips = document.getElementById("gmInventoryChips");
  const gmNpcNameInput = document.getElementById("gmNpcNameInput");
  const gmNpcAttitudeSelect = document.getElementById("gmNpcAttitudeSelect");
  const btnGmSetNpc = document.getElementById("btnGmSetNpc");
  const btnGmClearEffects = document.getElementById("btnGmClearEffects");
  const gmDirectiveInput = document.getElementById("gmDirectiveInput");
  const btnGmInjectDirective = document.getElementById("btnGmInjectDirective");

  function showGmFeedback(msg) {
    if (gmFeedbackBanner) {
      gmFeedbackBanner.textContent = `✓ ${msg}`;
      gmFeedbackBanner.style.display = "block";
      setTimeout(() => {
        gmFeedbackBanner.style.display = "none";
      }, 3500);
    }
  }

  function renderGmInventoryChips(items) {
    if (!gmInventoryChips) return;
    gmInventoryChips.innerHTML = "";
    if (!items || items.length === 0) {
      gmInventoryChips.innerHTML = '<span class="empty-hint">Envanter boş</span>';
      return;
    }
    items.forEach(item => {
      const chip = document.createElement("div");
      chip.className = "gm-chip";
      chip.innerHTML = `
        <span>${item}</span>
        <button class="gm-chip-delete" type="button" title="Eşyayı Sil">&times;</button>
      `;
      chip.querySelector(".gm-chip-delete").addEventListener("click", async () => {
        const res = await fetch("/api/gm/remove_item", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ item: item })
        });
        const data = await res.json();
        if (data.success && data.state) {
          renderGameState(data.state);
          showGmFeedback(data.message);
        }
      });
      gmInventoryChips.appendChild(chip);
    });
  }

  if (btnOpenGMModal) {
    btnOpenGMModal.addEventListener("click", () => {
      if (gmModal) gmModal.style.display = "flex";
    });
  }

  if (btnCloseGMModal) {
    btnCloseGMModal.addEventListener("click", () => {
      if (gmModal) gmModal.style.display = "none";
    });
  }

  if (btnGmHealFull) {
    btnGmHealFull.addEventListener("click", async () => {
      const res = await fetch("/api/gm/modify_stat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ health: 100 })
      });
      const data = await res.json();
      if (data.success && data.state) {
        renderGameState(data.state);
        showGmFeedback("Can %100 yapıldı!");
      }
    });
  }

  if (btnGmMentalFull) {
    btnGmMentalFull.addEventListener("click", async () => {
      const res = await fetch("/api/gm/modify_stat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mental: 100 })
      });
      const data = await res.json();
      if (data.success && data.state) {
        renderGameState(data.state);
        showGmFeedback("Zihinsel direnç %100 yapıldı!");
      }
    });
  }

  if (btnGmToggleGodmode) {
    btnGmToggleGodmode.addEventListener("click", async () => {
      const res = await fetch("/api/gm/toggle_godmode", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.success && data.state) {
        renderGameState(data.state);
        btnGmToggleGodmode.textContent = data.god_mode 
          ? "🛡️ Ölümsüzlük (God Mode): AÇIK ✓" 
          : "🛡️ Ölümsüzlük (God Mode): KAPALI";
        showGmFeedback(data.message);
      }
    });
  }

  if (btnGmAddItem) {
    btnGmAddItem.addEventListener("click", async () => {
      const item = gmAddItemInput.value.trim();
      if (!item) return;
      gmAddItemInput.value = "";
      const res = await fetch("/api/gm/add_item", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item: item })
      });
      const data = await res.json();
      if (data.success && data.state) {
        renderGameState(data.state);
        showGmFeedback(data.message);
      }
    });
  }

  if (btnGmSetNpc) {
    btnGmSetNpc.addEventListener("click", async () => {
      const name = gmNpcNameInput.value.trim();
      const attitude = gmNpcAttitudeSelect.value;
      if (!name) return;
      const res = await fetch("/api/gm/set_npc", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: name, attitude: attitude })
      });
      const data = await res.json();
      if (data.success && data.state) {
        renderGameState(data.state);
        showGmFeedback(data.message);
      }
    });
  }

  if (btnGmClearEffects) {
    btnGmClearEffects.addEventListener("click", async () => {
      const res = await fetch("/api/gm/clear_effects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      const data = await res.json();
      if (data.success && data.state) {
        renderGameState(data.state);
        showGmFeedback(data.message);
      }
    });
  }

  if (btnGmInjectDirective) {
    btnGmInjectDirective.addEventListener("click", async () => {
      const directive = gmDirectiveInput.value.trim();
      if (!directive) return;
      gmDirectiveInput.value = "";
      const res = await fetch("/api/gm/inject_directive", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ directive: directive })
      });
      const data = await res.json();
      if (data.success) {
        showGmFeedback(data.message);
      }
    });
  }

  // Loading helper
  function showLoading(title, subtitle) {
    if (loadingTitle) loadingTitle.textContent = title;
    if (loadingSubtitle) loadingSubtitle.textContent = subtitle;
    globalLoading.style.display = "flex";
  }

  function hideLoading() {
    globalLoading.style.display = "none";
  }
});
