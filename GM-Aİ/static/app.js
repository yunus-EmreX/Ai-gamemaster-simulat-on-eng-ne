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

  // AI Concept Creator Elements
  const btnToggleAiCreator = document.getElementById("btnToggleAiCreator");
  const aiCreatorBody = document.getElementById("aiCreatorBody");
  const aiConceptInput = document.getElementById("aiConceptInput");
  const btnGenerateFromConcept = document.getElementById("btnGenerateFromConcept");
  const aiGenStatus = document.getElementById("aiGenStatus");
  const aiChips = document.querySelectorAll(".ai-chip");

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
  const autosaveToast = document.getElementById("autosaveToast");
  const autosaveToastText = document.getElementById("autosaveToastText");
  const tokenUsagePill = document.getElementById("tokenUsagePill");
  const tokenUsageText = document.getElementById("tokenUsageText");
  const btnSaveGame = document.getElementById("btnSaveGame");
  const btnLoadModalOpen = document.getElementById("btnLoadModalOpen");
  const btnNewGame = document.getElementById("btnNewGame");

  function updateTokenUsageDisplay(usage) {
    if (!tokenUsagePill || !tokenUsageText || !usage) return;
    const total = usage.total_tokens || 0;
    const prompt = usage.prompt_tokens || 0;
    const output = usage.output_tokens || 0;
    if (total > 0) {
      tokenUsageText.textContent = `${total.toLocaleString()} token`;
      tokenUsagePill.title = `Son Hamle Token Özeti:\n• Giriş (Prompt): ${prompt.toLocaleString()} token\n• Çıkış (Hikaye): ${output.toLocaleString()} token\n• Toplam: ${total.toLocaleString()} token\n\n(85-95% Token Tasarruf Mimarisi Aktif)`;
      tokenUsagePill.style.display = "inline-flex";
    }
  }

  let autosaveTimeout = null;
  function showAutosaveNotification(turn) {
    if (!autosaveToast) return;
    if (autosaveToastText) {
      autosaveToastText.textContent = `Otomatik Kaydedildi (Tur #${turn})`;
    }
    autosaveToast.style.display = "inline-flex";
    autosaveToast.style.opacity = "1";

    if (autosaveTimeout) {
      clearTimeout(autosaveTimeout);
    }
    autosaveTimeout = setTimeout(() => {
      autosaveToast.style.opacity = "0";
      setTimeout(() => {
        if (autosaveToast.style.opacity === "0") {
          autosaveToast.style.display = "none";
        }
      }, 400);
    }, 3500);
  }

  // Elements - Gameplay
  const displayCharName = document.getElementById("displayCharName");
  const displayCharRole = document.getElementById("displayCharRole");
  const displayLocation = document.getElementById("displayLocation");
  const healthLabel = document.getElementById("healthLabel");
  const healthVal = document.getElementById("healthVal");
  const healthBar = document.getElementById("healthBar");
  const mentalLabel = document.getElementById("mentalLabel");
  const mentalVal = document.getElementById("mentalVal");
  const mentalBar = document.getElementById("mentalBar");
  const godPowerStatItem = document.getElementById("godPowerStatItem");
  const divinePowerVal = document.getElementById("divinePowerVal");
  const divinePowerBar = document.getElementById("divinePowerBar");
  const godSimMetaSection = document.getElementById("godSimMetaSection");
  const godCivilizationEra = document.getElementById("godCivilizationEra");
  const godCivilizationEraBtn = document.getElementById("godCivilizationEraBtn");
  const btnOpenEraModal = document.getElementById("btnOpenEraModal");
  const godEraModal = document.getElementById("godEraModal");
  const btnCloseGodEraModal = document.getElementById("btnCloseGodEraModal");
  const eraCardsGrid = document.getElementById("eraCardsGrid");
  const modalCurrentEraPill = document.getElementById("modalCurrentEraPill");
  const btnAppointProphetQuick = document.getElementById("btnAppointProphetQuick");
  const godProphetsList = document.getElementById("godProphetsList");
  const godPrayersHub = document.getElementById("godPrayersHub");
  const godPrayersCount = document.getElementById("godPrayersCount");
  const godPrayersList = document.getElementById("godPrayersList");
  const btnTogglePrayers = document.getElementById("btnTogglePrayers");

  const CIVILIZATION_ERAS = [
    {
      id: "era_tribal",
      name: "Yaratılış ve Kabileler Çağı",
      icon: "🏕️",
      techLevel: "İlkel / Taş ve Ateş",
      desc: "Ölümlüler henüz doğanın vahşi güçlerinden korkuyor. Mağara duvarlarına senin sembollerini çiziyor, ateş etrafında sana yakarıyorlar.",
      traits: "Basit kurbanlar, avcı-toplayıcı klanlar, ilkel mabetler, doğa korkusu"
    },
    {
      id: "era_bronze",
      name: "Bronz ve Mabetler Çağı",
      icon: "🏛️",
      techLevel: "Bronz & Şehir Devletleri",
      desc: "İlk devasa piramitler, zigguratlar ve görkemli mabetler senin adına yükseliyor. Ruhban sınıfı doğdu, kanunlar taş tabletlere kazınıyor.",
      traits: "Görkemli tapınaklar, organize din, ilk yazılı yasalar, şehir surları"
    },
    {
      id: "era_iron",
      name: "Demir ve Krallıklar Çağı",
      icon: "⚔️",
      techLevel: "Demir & Feodal İmparatorluklar",
      desc: "Çelik kılıçlar, surlarla çevrili krallıklar ve senin adınla sefere çıkan kutsal ordular. Krallar senin yeryüzündeki gölgen olduğunu iddia ediyor.",
      traits: "Kutsal seferler, feodal sadakat, çelik ordular, imparatorluklar"
    },
    {
      id: "era_philosophy",
      name: "Altın Felsefe ve Teokrasi Çağı",
      icon: "📜",
      techLevel: "Akademi & Teolojik İlahiyat",
      desc: "Büyük kütüphaneler kuruldu; filozoflar senin varlığını ve evrenin kökenini tartışıyor. Teokratik yüksek meclisler toplumu senin dogmalarınla yönetiyor.",
      traits: "Kutsal metin tefsirleri, ilahiyat fakülteleri, mimari şaheserler, derin inanç"
    },
    {
      id: "era_alchemy",
      name: "Buhar, Simya ve Akıl Çağı",
      icon: "⚙️",
      techLevel: "Simya, Buhar & Pozitif Bilim",
      desc: "Çarklar dönüyor, simyacılar elementleri dönüştürüyor. Bilim insanları senin yarattığın doğa kanunlarını formüllere dökmeye başladı.",
      traits: "Simyasal dönüşüm, buharlı makineler, akıl & inanç dengesi, fabrikalar"
    },
    {
      id: "era_cosmic",
      name: "Aşkın Kozmik Yıldız Çağı",
      icon: "🚀",
      techLevel: "Yıldızlararası & Metafizik Enerji",
      desc: "Ölümlüler gökyüzünü aşıp yıldızlara ulaştı. Senin ilahi gücünü galaksiler boyunca yayan devasa tapınak-gemiler uzay boşluğunda süzülüyor.",
      traits: "Yıldız gemileri, aşkın boyut kapıları, kozmik tebaalar, galaktik inanç"
    },
    {
      id: "era_apocalypse",
      name: "Büyük Tufan & Kıyamet Çağı",
      icon: "💀",
      techLevel: "Kozmik Yıkım & İlahi Yargı",
      desc: "Dünya günah ve sapkınlıkla doldu. Yüce Tanrı olarak göklerin kapısını açtın; tufan, göktaşı yağmurları ve ilahi ateş dünyayı arındırıyor.",
      traits: "Kozmik kıyamet, ruhların tartılması, yeni baştan yaratılış, nihai tecelli"
    }
  ];
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
  let lastGameState = null;

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

  // --- AI WORLD & CHARACTER CREATOR (FREEFORM CONCEPT MODE) ---
  if (btnToggleAiCreator && aiCreatorBody) {
    btnToggleAiCreator.addEventListener("click", () => {
      const isHidden = aiCreatorBody.style.display === "none";
      aiCreatorBody.style.display = isHidden ? "flex" : "none";
      btnToggleAiCreator.textContent = isHidden ? "▲ Kapat" : "✍️ Konsept Yaz";
      if (isHidden && aiConceptInput) {
        aiConceptInput.focus();
      }
    });
  }

  aiChips.forEach(chip => {
    chip.addEventListener("click", () => {
      const concept = chip.getAttribute("data-concept");
      if (concept && aiConceptInput) {
        aiConceptInput.value = concept;
        aiConceptInput.focus();
      }
    });
  });

  if (btnGenerateFromConcept) {
    btnGenerateFromConcept.addEventListener("click", async () => {
      const conceptText = aiConceptInput ? aiConceptInput.value.trim() : "";
      if (!conceptText) {
        alert("Lütfen hayal ettiğiniz karakteri, evreni ve hikaye başlangıcını kısaca yazın veya örnek fikirlerden birini seçin.");
        if (aiConceptInput) aiConceptInput.focus();
        return;
      }

      const activeKey = localStorage.getItem("gemini_rpg_api_key") || (apiKeyInput ? apiKeyInput.value.trim() : "");
      if (!activeKey) {
        alert("Lütfen önce 3. Sekmeden veya ayar alanından Gemini API anahtarınızı girin.");
        switchTab("tabMode");
        if (apiKeyInput) apiKeyInput.focus();
        return;
      }

      // Show loading status
      btnGenerateFromConcept.disabled = true;
      btnGenerateFromConcept.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Evren & Karakter İnşa Ediliyor...</span>';
      if (aiGenStatus) {
        aiGenStatus.className = "ai-gen-status loading";
        aiGenStatus.textContent = "✨ Gemini tüm karakter dosyasını, kuralları ve dogmaları yazıyor...";
        aiGenStatus.style.display = "block";
      }

      try {
        const res = await fetch("/api/ai_create_concept", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            concept: conceptText,
            api_key: activeKey,
            model: modelSelect ? modelSelect.value : "gemini-3.6-flash"
          })
        });
        const data = await res.json();

        if (data.success && data.data) {
          const generated = data.data;

          // 1. Populate Character
          if (generated.character) {
            charName.value = generated.character.name || "";
            charAge.value = generated.character.age || "";
            charRole.value = generated.character.role || "";
            charSkills.value = Array.isArray(generated.character.skills) ? generated.character.skills.join(", ") : (generated.character.skills || "");
            charFlaws.value = Array.isArray(generated.character.flaws) ? generated.character.flaws.join(", ") : (generated.character.flaws || "");
            charBackstory.value = generated.character.backstory || "";
            charGoal.value = generated.character.goal || "";
            charInventory.value = Array.isArray(generated.character.inventory) ? generated.character.inventory.join(", ") : (generated.character.inventory || "");
          }

          // 2. Populate Universe
          if (generated.universe) {
            uniName.value = generated.universe.name || "";
            uniHistory.value = generated.universe.history || "";
            uniRules.value = generated.universe.rules || "";
            uniSocial.value = generated.universe.social || "";
            uniDamage.value = generated.universe.damage_reality || "";
            uniDogmas.value = generated.universe.dogmas || "";
          }

          // 3. Populate Mode & Strictness
          if (generated.mode_data) {
            const isFantasy = generated.mode_data.mode === "fantasy";
            const radioRealistic = document.getElementById("modeRealistic");
            const radioFantasy = document.getElementById("modeFantasy");
            if (isFantasy && radioFantasy) {
              radioFantasy.checked = true;
            } else if (radioRealistic) {
              radioRealistic.checked = true;
            }
            updateModeCardSelection();

            if (generated.mode_data.strictness && strictnessSelect) {
              strictnessSelect.value = generated.mode_data.strictness;
            }
            if (generated.mode_data.prologue_hook && prologueHook) {
              prologueHook.value = generated.mode_data.prologue_hook;
            }
          }

          if (aiGenStatus) {
            aiGenStatus.className = "ai-gen-status success";
            aiGenStatus.textContent = "✓ Evren, Karakter ve Kurallar başarıyla oluşturuldu! Tüm sekmeler dolduruldu.";
          }

          // Switch to Tab 1 with a smooth highlight effect so the user sees their generated character
          switchTab("tabCharacter");

          // Show floating notice
          if (presetLoadedNotice) {
            presetLoadedNotice.textContent = `✨ "${generated.character?.name || 'Karakter'}" ve "${generated.universe?.name || 'Evren'}" başarıyla oluşturuldu!`;
            presetLoadedNotice.style.display = "block";
            setTimeout(() => { presetLoadedNotice.style.display = "none"; }, 5000);
          }
        } else {
          alert("Oluşturma hatası: " + (data.error || "Bilinmeyen hata"));
          if (aiGenStatus) {
            aiGenStatus.className = "ai-gen-status error";
            aiGenStatus.textContent = "❌ Hata: " + (data.error || "Oluşturulamadı");
          }
        }
      } catch (err) {
        alert("Bağlantı hatası: " + err.message);
        if (aiGenStatus) {
          aiGenStatus.className = "ai-gen-status error";
          aiGenStatus.textContent = "❌ Bağlantı hatası: " + err.message;
        }
      } finally {
        btnGenerateFromConcept.disabled = false;
        btnGenerateFromConcept.innerHTML = '<span class="btn-icon">⚡</span><span class="btn-text">Evreni & Karakteri Tekrar Oluştur</span>';
      }
    });
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
    document.getElementById("cardGodSim")?.classList.toggle("active", selectedValue === "god_sim");
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
      const activeKey = localStorage.getItem("gemini_rpg_api_key") || (apiKeyInput ? apiKeyInput.value.trim() : "");
      const res = await fetch("/api/take_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: actionText, api_key: activeKey })
      });
      const data = await res.json();
      hideLoading();
      btnSendAction.disabled = false;

      if (data.success && data.state) {
        renderGameState(data.state);
        if (data.autosaved) {
          showAutosaveNotification(data.autosave_turn || data.state.turn_count);
        }
        if (data.usage) {
          updateTokenUsageDisplay(data.usage);
        }
      } else {
        alert(`Eylem işlenirken hata oluştu:\n${data.error || "Bilinmeyen hata"}`);
      }
    } catch (e) {
      hideLoading();
      btnSendAction.disabled = false;
      alert(`Sunucu ile iletişim kurulamadı (${e.message}).\nLütfen 'run.bat' dosyasının açık ve sunucunun çalışıyor olduğundan emin olun.`);
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
    lastGameState = state;
    displayCharName.textContent = state.character.name || "Bilinmeyen Gezgin";
    displayCharRole.textContent = `${state.character.role || "Gezgin"} (${state.character.age || "Yaş Belirsiz"})`;
    displayLocation.textContent = `📍 ${state.location || "Bilinmeyen Konum"}`;

    if (state.is_god_sim) {
      const avatarBox = document.getElementById("avatarBox");
      if (avatarBox) avatarBox.textContent = "🌌";

      if (healthLabel) healthLabel.textContent = "✨ Kozmik İman (Faith)";
      const faith = Math.max(0, Math.min(100, state.faith ?? 50));
      healthVal.textContent = `${faith}%`;
      healthBar.style.width = `${faith}%`;
      healthBar.style.background = "linear-gradient(90deg, #f59e0b 0%, #fbbf24 100%)";

      if (mentalLabel) mentalLabel.textContent = "⚡ Korku & Dehşet (Fear)";
      const fear = Math.max(0, Math.min(100, state.fear ?? 15));
      mentalVal.textContent = `${fear}%`;
      mentalBar.style.width = `${fear}%`;
      mentalBar.style.background = "linear-gradient(90deg, #8b5cf6 0%, #ec4899 100%)";

      if (godPowerStatItem) godPowerStatItem.style.display = "block";
      const power = Math.max(0, Math.min(100, state.divine_power ?? 100));
      if (divinePowerVal) divinePowerVal.textContent = `${power}%`;
      if (divinePowerBar) {
        divinePowerBar.style.width = `${power}%`;
        divinePowerBar.style.background = "linear-gradient(90deg, #06b6d4 0%, #3b82f6 100%)";
      }

      // God Sim Meta: Civilization Era & Prophets
      if (godSimMetaSection) {
        godSimMetaSection.style.display = "block";
        const currentEra = state.civilization_era || "Yaratılış ve Kabileler Çağı";
        if (godCivilizationEra) {
          godCivilizationEra.textContent = currentEra;
        }
        if (modalCurrentEraPill) {
          modalCurrentEraPill.textContent = `Mevcut: ${currentEra}`;
        }
        if (godProphetsList) {
          godProphetsList.innerHTML = "";
          const prophets = state.prophets || [];
          if (prophets.length === 0) {
            godProphetsList.innerHTML = '<span class="empty-hint">Henüz seçilmiş peygamber yok</span>';
          } else {
            prophets.forEach(p => {
              let pName = typeof p === "string" ? p : (p.name || p.prophet || p.peygamber || p.fani || "Seçilmiş Fani");
              let pRole = (typeof p === "object" && (p.role || p.unvan || p.makam)) || "Başpeygamber / Elçi";
              let pRegion = (typeof p === "object" && (p.region || p.bolge || p.location || p.mekan)) || "Kutsal Topraklar";
              let pDoctrine = (typeof p === "object" && (p.doctrine || p.ogreti || p.doktrin)) || "";

              const pCard = document.createElement("div");
              pCard.className = "god-prophet-item";
              pCard.innerHTML = `
                <div class="prophet-card-header">
                  <div class="prophet-name">👑 ${escapeHtml(pName)}</div>
                  <button type="button" class="prophet-commune-btn" title="Bu peygambere ilahi vahiy fısılda">💬 Vahiy İndir</button>
                </div>
                <div class="prophet-role">${escapeHtml(pRole)} • ${escapeHtml(pRegion)}</div>
                ${pDoctrine ? `<div class="prophet-doctrine">"${escapeHtml(pDoctrine)}"</div>` : ""}
              `;

              const communeBtn = pCard.querySelector(".prophet-commune-btn");
              if (communeBtn) {
                communeBtn.addEventListener("click", () => {
                  if (playerActionInput) {
                    playerActionInput.value = `[Peygamberime Vahiy]: Ey ${pName}, sana ve halkına ilahi vahyim şudur ki: `;
                    playerActionInput.focus();
                    actionHub?.scrollIntoView({ behavior: "smooth", block: "center" });
                  }
                });
              }

              godProphetsList.appendChild(pCard);
            });
          }
        }
      }

      // Render God Sim Prayers Hub
      renderGodPrayers(state.prayers || []);
    } else {
      const avatarBox = document.getElementById("avatarBox");
      if (avatarBox) avatarBox.textContent = "👤";

      if (healthLabel) healthLabel.textContent = "❤️ Can / Fiziksel Sağlık";
      if (mentalLabel) mentalLabel.textContent = "🧠 Zihinsel Direnç";
      if (godPowerStatItem) godPowerStatItem.style.display = "none";
      if (godSimMetaSection) godSimMetaSection.style.display = "none";
      if (godPrayersHub) godPrayersHub.style.display = "none";

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
      mentalBar.style.background = "linear-gradient(90deg, #6366f1 0%, #8b5cf6 100%)";
    }

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

    // Known World NPCs (Long-Term Memory Roster)
    const knownWorldList = document.getElementById("knownWorldNpcsList");
    const knownBadge = document.getElementById("knownNpcCountBadge");
    if (knownWorldList) {
      knownWorldList.innerHTML = "";
      const knownNpcs = state.known_world_npcs || {};
      const activeKeys = Object.keys(state.npc_relationships || {});
      const awayKeys = Object.keys(knownNpcs).filter(k => !activeKeys.includes(k));
      if (knownBadge) {
        knownBadge.textContent = awayKeys.length;
      }
      if (awayKeys.length === 0) {
        knownWorldList.innerHTML = '<span class="empty-hint">Hafızada başka karakter yok</span>';
      } else {
        awayKeys.forEach(npcName => {
          const info = knownNpcs[npcName] || {};
          const isDeceased = String(info.status || "").toLowerCase().includes("ölü");
          const card = document.createElement("div");
          card.className = `npc-relation-card known-card ${isDeceased ? "deceased" : ""}`;
          card.innerHTML = `
            <div class="npc-card-header">
              <span class="npc-name">${escapeHtml(npcName)}</span>
              <button class="npc-card-remove-btn" title="Karakteri tamamen hafızadan sil" data-name="${escapeHtml(npcName)}">×</button>
            </div>
            <span class="npc-attitude-pill">${escapeHtml(info.attitude || "Bilinmiyor")}</span>
            <span class="npc-status-pill ${isDeceased ? "deceased" : ""}">${escapeHtml(info.status || "Uzakta")}</span>
          `;
          const removeBtn = card.querySelector(".npc-card-remove-btn");
          if (removeBtn) {
            removeBtn.addEventListener("click", async (e) => {
              e.stopPropagation();
              try {
                const res = await fetch("/api/gm/remove_npc", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ name: npcName, purge: true })
                });
                const data = await res.json();
                if (data.success && data.state) {
                  renderGameState(data.state);
                }
              } catch (err) {
                console.error("Karakter silme hatası:", err);
              }
            });
          }
          knownWorldList.appendChild(card);
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
    let modeName = "🛡️ Gerçekçi Mod";
    if (state.is_god_sim || state.mode_data?.mode === "god_sim") {
      modeName = "🌌 Tanrı Simülasyonu";
    } else if (state.mode_data?.mode === "fantasy") {
      modeName = "✨ Fantezi Modu";
    }
    modeBadgeText.textContent = modeName;

    strictnessBadge.style.display = "inline-flex";
    const strictMap = {
      deli: "🔥 Deli Modu",
      ironclad: "🔒 Demir Kural",
      challenging: "⚔️ Zorlayıcı",
      balanced: "⚖️ Dengeli"
    };
    strictnessBadgeText.textContent = strictMap[state.mode_data.strictness] || "Tavizsiz";
    if (state.mode_data.strictness === "deli") {
      strictnessBadge.classList.add("strictness-deli");
    } else {
      strictnessBadge.classList.remove("strictness-deli");
    }

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

  // RENDER GOD SIM PRAYERS HUB
  function renderGodPrayers(prayers) {
    if (!godPrayersHub || !godPrayersList) return;
    godPrayersHub.style.display = "block";
    const prayersArr = Array.isArray(prayers) ? prayers : [];
    if (godPrayersCount) godPrayersCount.textContent = prayersArr.length;

    godPrayersList.innerHTML = "";
    if (prayersArr.length === 0) {
      godPrayersList.innerHTML = '<div class="no-prayers-msg">Şu anda kozmik sessizlik hakim. Henüz yeni bir fani yakarısı ulaşmadı.</div>';
      return;
    }

    prayersArr.forEach(p => {
      const mortalName = p.mortal_name || p.mortal || p.name || p.person || p.fani || "Bilinmeyen Fani";
      const mortalLoc = p.mortal_location || p.location || p.place || p.mekan || "Yeryüzü";
      const prayerText = p.prayer_text || p.prayer || p.text || p.content || p.yakari || p.dua || "";
      const prayerType = p.prayer_type || p.type || p.tur || "Dua";
      const rawStatus = String(p.status || "beklemede").toLowerCase().trim();
      const isPending = !p.status || rawStatus === "beklemede" || rawStatus === "pending";

      const card = document.createElement("div");
      card.className = `prayer-card ${rawStatus}`;

      const statusBadges = {
        beklemede: '<span class="prayer-status-badge pending">⏳ Beklemede</span>',
        kabul_edildi: '<span class="prayer-status-badge granted">✨ Lütuf Bahşedildi</span>',
        gazap_yagdirildi: '<span class="prayer-status-badge smited">⚡ Gazap İndirildi</span>',
        bukuldu: '<span class="prayer-status-badge twisted">🌀 Kader Büküldü</span>',
        reddedildi: '<span class="prayer-status-badge ignored">❌ Görmezden Gelindi</span>'
      };

      card.innerHTML = `
        <div class="prayer-header">
          <div class="prayer-mortal-info">
            <span class="mortal-name">👤 ${escapeHtml(mortalName)}</span>
            <span class="mortal-loc">📍 ${escapeHtml(mortalLoc)}</span>
            <span class="prayer-type-tag">${escapeHtml(prayerType)}</span>
          </div>
          ${statusBadges[rawStatus] || `<span class="prayer-status-badge">${escapeHtml(rawStatus)}</span>`}
        </div>
        <div class="prayer-text">"${escapeHtml(prayerText)}"</div>
        ${p.divine_response ? `<div class="prayer-response-note"><strong>İlahi Karar:</strong> ${escapeHtml(p.divine_response)}</div>` : ""}
        ${isPending ? `
          <div class="prayer-action-buttons">
            <button class="prayer-btn grant-btn" title="Kabul Et & Mucize Göster" data-act="grant">✨ Kabul Et</button>
            <button class="prayer-btn smite-btn" title="Kibirli Faniye Gazap İndir" data-act="smite">⚡ Gazap İndir</button>
            <button class="prayer-btn twist-btn" title="Kaderini İronik / Tekinsiz Biçimde Bük" data-act="twist">🌀 Kaderi Bük</button>
            <button class="prayer-btn ignore-btn" title="Cevapsız Bırak" data-act="ignore">❌ Görmezden Gel</button>
          </div>
        ` : ""}
      `;

      if (isPending) {
        const buttons = card.querySelectorAll(".prayer-btn");
        buttons.forEach(btn => {
          btn.addEventListener("click", () => {
            const act = btn.getAttribute("data-act");
            handlePrayerAction(p, act, mortalName, prayerText);
          });
        });
      }

      godPrayersList.appendChild(card);
    });
  }

  async function handlePrayerAction(prayer, action, mortalName, prayerText) {
    const prayerId = prayer.id || "p1";
    mortalName = mortalName || prayer.mortal_name || prayer.mortal || "Fani";
    prayerText = prayerText || prayer.prayer_text || prayer.prayer || "";

    try {
      showLoading("İlahi Ferman İndiriliyor...", `${mortalName} adlı faninin yakarışına ilahi iradeniz tecelli ediyor...`);
      const res = await fetch("/api/god/prayer_action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prayer_id: prayerId,
          decision: action
        })
      });
      const data = await res.json();
      hideLoading();

      if (data.success && data.state) {
        renderGameState(data.state);
        if (playerActionInput && data.action_text) {
          playerActionInput.value = data.action_text;
          playerActionInput.focus();
          actionHub?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      } else {
        let fallbackText = "";
        if (action === "grant") {
          fallbackText = `[İlahi Kabul]: ${mortalName} adlı faninin "${prayerText}" duasını cömertçe kabul edip mucize bahşediyorum.`;
        } else if (action === "smite") {
          fallbackText = `[İlahi Gazap]: ${mortalName} adlı faninin "${prayerText}" duasına yıldırımlarla gazap indiriyorum!`;
        } else if (action === "twist") {
          fallbackText = `[Kaderi Bükme]: ${mortalName} adlı faninin "${prayerText}" duasını beklenmedik bir bedelle çarpıtıyorum.`;
        } else {
          fallbackText = `[İlahi Sessizlik]: ${mortalName} adlı faninin "${prayerText}" yakarışını görmezden geliyorum.`;
        }
        if (playerActionInput) {
          playerActionInput.value = fallbackText;
          playerActionInput.focus();
          actionHub?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      }
    } catch (e) {
      hideLoading();
      console.error("Prayer action error:", e);
      let fallbackText = `[İlahi Ferman]: ${mortalName} adlı faninin "${prayerText}" yakarışına karar verildi.`;
      if (playerActionInput) {
        playerActionInput.value = fallbackText;
        playerActionInput.focus();
        actionHub?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  }

  if (btnTogglePrayers) {
    btnTogglePrayers.addEventListener("click", () => {
      if (godPrayersList) {
        const isHidden = godPrayersList.style.display === "none";
        godPrayersList.style.display = isHidden ? "flex" : "none";
        btnTogglePrayers.textContent = isHidden ? "▲ Gizle" : "▼ Göster";
      }
    });
  }

  // GOD SIM: CIVILIZATION EVOLUTION MODAL & PROPHET APPOINTMENT
  function openGodEraModal() {
    if (!godEraModal) return;
    godEraModal.style.display = "flex";
    renderEraCards();
  }

  function closeGodEraModal() {
    if (godEraModal) godEraModal.style.display = "none";
  }

  function renderEraCards() {
    if (!eraCardsGrid) return;
    eraCardsGrid.innerHTML = "";
    const currentEraName = lastGameState?.civilization_era || "Yaratılış ve Kabileler Çağı";
    if (modalCurrentEraPill) {
      modalCurrentEraPill.textContent = `Mevcut: ${currentEraName}`;
    }

    CIVILIZATION_ERAS.forEach(era => {
      const isCurrent = era.name.toLowerCase().trim() === currentEraName.toLowerCase().trim();
      const card = document.createElement("div");
      card.className = `era-card ${isCurrent ? "active-current-era" : ""}`;
      card.innerHTML = `
        <div class="era-card-top">
          <span class="era-card-icon">${era.icon}</span>
          <div class="era-card-title-group">
            <h4 class="era-card-name">${escapeHtml(era.name)}</h4>
            <span class="era-card-tech">${escapeHtml(era.techLevel)}</span>
          </div>
        </div>
        <p class="era-card-desc">${escapeHtml(era.desc)}</p>
        <div class="era-card-traits">
          <strong>Özellikler:</strong> ${escapeHtml(era.traits)}
        </div>
        <div class="era-card-footer">
          ${isCurrent 
            ? '<span class="current-era-indicator">✓ Şu Anki Aktif Çağ</span>'
            : `<button type="button" class="btn-select-era" data-era="${escapeHtml(era.name)}">⚡ Bu Çağa Geçiş Fermanı Ver</button>`
          }
        </div>
      `;

      if (!isCurrent) {
        const selectBtn = card.querySelector(".btn-select-era");
        if (selectBtn) {
          selectBtn.addEventListener("click", async () => {
            await decreeNewEra(era);
          });
        }
      }

      eraCardsGrid.appendChild(card);
    });
  }

  async function decreeNewEra(era) {
    try {
      showLoading("Medeniyet Çağı Değişiyor...", `Yeryüzü '${era.name}' safhasına sıçratılıyor...`);
      const res = await fetch("/api/god/set_era", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ era: era.name })
      });
      const data = await res.json();
      hideLoading();

      if (data.success && data.state) {
        renderGameState(data.state);
        closeGodEraModal();
        if (playerActionInput) {
          playerActionInput.value = `[Kozmik Çağ Fermanı]: İlahi kudretimle dünyayı '${era.name}' safhasına yükseltiyorum! İnsanlar ${era.techLevel} çağına girdi. Bu büyük kırılma ve medeniyet sıçraması yeryüzünü sarıyor.`;
          playerActionInput.focus();
          actionHub?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      } else {
        alert("Çağ güncellenirken hata oluştu: " + (data.error || "Bilinmeyen hata"));
      }
    } catch (e) {
      hideLoading();
      alert("Hata: " + e.message);
    }
  }

  async function appointNewProphet() {
    const name = prompt("Seçeceğiniz yeni Peygamberin / Faninin Adı:", "Başrahip Ogan");
    if (!name || !name.trim()) return;

    const role = prompt("Bu peygambere vereceğiniz ilahi unvan / makam:", "Gök Tanrısı Elçisi & Yüksek Rahip") || "Başpeygamber / Elçi";
    const region = prompt("Peygamberin tebliğde bulunacağı kutsal bölge:", "Kutsal Topraklar") || "Kutsal Topraklar";
    const doctrine = prompt("Peygambere bahşettiğiniz temel öğreti veya ferman:", "Tanrının kudretine boyun eğin, adaletle hükmedin.") || "";

    try {
      showLoading("İlahi Elçi Seçiliyor...", `${name} yeryüzünde seçilmiş peygamber ilan ediliyor...`);
      const res = await fetch("/api/god/appoint_prophet", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(),
          role: role.trim(),
          region: region.trim(),
          doctrine: doctrine.trim()
        })
      });
      const data = await res.json();
      hideLoading();

      if (data.success && data.state) {
        renderGameState(data.state);
        if (playerActionInput) {
          playerActionInput.value = `[İlahi Peygamber Fermanı]: Yeryüzünde ${name} adlı faniyi kendime '${role}' olarak tayin ettim! Ona '${doctrine || 'İlahi İrade'}' öğretisini yayması için kutsal işaretler verdim.`;
          playerActionInput.focus();
          actionHub?.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      } else {
        alert("Peygamber atanırken hata: " + (data.error || "Bilinmiyor"));
      }
    } catch (e) {
      hideLoading();
      alert("Hata: " + e.message);
    }
  }

  // God Sim Listeners
  if (godCivilizationEraBtn) {
    godCivilizationEraBtn.addEventListener("click", openGodEraModal);
  }
  if (btnOpenEraModal) {
    btnOpenEraModal.addEventListener("click", openGodEraModal);
  }
  if (btnCloseGodEraModal) {
    btnCloseGodEraModal.addEventListener("click", closeGodEraModal);
  }
  if (btnAppointProphetQuick) {
    btnAppointProphetQuick.addEventListener("click", appointNewProphet);
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
        item.className = `save-item ${s.is_autosave ? 'autosave-item' : ''}`;
        const autoBadge = s.is_autosave ? '<span class="badge-autosave">🔄 Otomatik Kayıt</span>' : '';
        item.innerHTML = `
          <div class="save-info">
            <h5>${escapeHtml(s.character_name)} - ${escapeHtml(s.universe_name)}${autoBadge}</h5>
            <p>Tur: ${s.turn_count} | Mod: ${escapeHtml(s.mode)} | Tarih: ${escapeHtml(s.saved_at)}</p>
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
      const activeKey = localStorage.getItem("gemini_rpg_api_key") || (apiKeyInput ? apiKeyInput.value.trim() : "");
      const res = await fetch("/api/load_game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: filename, api_key: activeKey })
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
      alert(`Sunucu ile iletişim kurulamadı (${e.message}).\nLütfen 'run.bat' dosyasının açık olduğundan emin olun.`);
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

  // Known NPCs Drawer Toggle
  const toggleKnownNpcsBtn = document.getElementById("toggleKnownNpcsBtn");
  const knownNpcsDrawer = document.getElementById("knownNpcsDrawer");
  if (toggleKnownNpcsBtn && knownNpcsDrawer) {
    toggleKnownNpcsBtn.addEventListener("click", () => {
      const isHidden = knownNpcsDrawer.style.display === "none";
      knownNpcsDrawer.style.display = isHidden ? "block" : "none";
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
