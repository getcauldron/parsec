import { invoke } from "@tauri-apps/api/core";
import { load, type Store } from "@tauri-apps/plugin-store";

// --- Types ---

interface Language {
  display_name: string;
  short_code: string;
  tesseract_code: string;
  script_group: string;
}

interface LanguagesResponse {
  status: string;
  languages: Language[];
}

// --- State ---

const STORE_FILE = "settings.json";
const STORE_KEY_LANGUAGE = "language";
const DEFAULT_LANGUAGE = "en";

/** English-only fallback when sidecar is unavailable */
const FALLBACK_LANGUAGES: Language[] = [
  { display_name: "English", short_code: "en", tesseract_code: "eng", script_group: "Latin" },
];

let store: Store | null = null;
let selectedLanguage = DEFAULT_LANGUAGE;
let languages: Language[] = [];
let panelOpen = false;

// --- DOM ---

let settingsBtn: HTMLButtonElement;
let settingsPanel: HTMLDivElement;
let languageSelect: HTMLSelectElement;

// --- Public API ---

/** Get the currently selected language short code. */
export function getSelectedLanguage(): string {
  return selectedLanguage;
}

/** Initialize the settings module: load store, fetch languages, build UI. */
export async function initSettings(): Promise<void> {
  buildSettingsDOM();
  await loadStore();
  await fetchLanguages();
  populateLanguagePicker();
}

// --- Store ---

async function loadStore(): Promise<void> {
  try {
    store = await load(STORE_FILE, {
      defaults: { [STORE_KEY_LANGUAGE]: DEFAULT_LANGUAGE },
      autoSave: true,
    });
    const saved = await store.get<string>(STORE_KEY_LANGUAGE);
    if (saved) {
      selectedLanguage = saved;
      console.log(`[parsec-settings] loaded language from store: ${saved}`);
    } else {
      console.log(`[parsec-settings] no saved language, using default: ${DEFAULT_LANGUAGE}`);
    }
  } catch (err) {
    console.warn("[parsec-settings] failed to load store, using defaults:", err);
  }
}

async function saveLanguage(code: string): Promise<void> {
  selectedLanguage = code;
  if (store) {
    try {
      await store.set(STORE_KEY_LANGUAGE, code);
      console.log(`[parsec-settings] saved language: ${code}`);
    } catch (err) {
      console.warn("[parsec-settings] failed to save language:", err);
    }
  }
}

// --- Language fetching ---

async function fetchLanguages(): Promise<void> {
  try {
    const response = await invoke<LanguagesResponse>("get_languages");
    if (response.status === "ok" && Array.isArray(response.languages)) {
      languages = response.languages;
      console.log(`[parsec-settings] loaded ${languages.length} languages from sidecar`);
    } else {
      console.error("[parsec-settings] unexpected get_languages response:", response);
      languages = FALLBACK_LANGUAGES;
    }
  } catch (err) {
    console.error("[parsec-settings] failed to fetch languages, using fallback:", err);
    languages = FALLBACK_LANGUAGES;
  }
}

// --- DOM construction ---

function buildSettingsDOM(): void {
  const header = document.getElementById("app-header")!;
  const headerRight = document.createElement("div");
  headerRight.className = "header-right";

  // Move sidecar status into header-right
  const sidecarStatus = document.getElementById("sidecar-status")!;
  headerRight.appendChild(sidecarStatus);

  // Gear button
  settingsBtn = document.createElement("button");
  settingsBtn.className = "settings-btn";
  settingsBtn.setAttribute("aria-label", "Settings");
  settingsBtn.setAttribute("title", "Settings");
  settingsBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M7.5 2.25h3l.375 1.875.75.375 1.75-.875 2.125 2.125-.875 1.75.375.75L16.875 8.625v3l-1.875.375-.375.75.875 1.75-2.125 2.125-1.75-.875-.75.375L10.5 17.25h-3l-.375-1.875-.75-.375-1.75.875L2.5 13.75l.875-1.75-.375-.75L1.125 10.875v-3L3 7.5l.375-.75L2.5 5l2.125-2.125 1.75.875.75-.375L7.5 2.25z" stroke="currentColor" stroke-width="1.25" stroke-linejoin="round"/>
    <circle cx="9" cy="9.75" r="2.25" stroke="currentColor" stroke-width="1.25"/>
  </svg>`;
  settingsBtn.addEventListener("click", togglePanel);
  headerRight.appendChild(settingsBtn);

  header.appendChild(headerRight);

  // Settings panel (collapsed by default)
  settingsPanel = document.createElement("div");
  settingsPanel.className = "settings-panel";
  settingsPanel.setAttribute("aria-hidden", "true");
  settingsPanel.innerHTML = `
    <div class="settings-panel-inner">
      <div class="settings-group">
        <label class="settings-label" for="language-select">
          <span class="settings-label-text">OCR Language</span>
          <span class="settings-label-hint">Recognition language for dropped files</span>
        </label>
        <select id="language-select" class="settings-select">
          <option value="en">English</option>
        </select>
      </div>
    </div>
  `;

  // Insert panel after header, before main
  const app = document.getElementById("app")!;
  const main = document.getElementById("main-area")!;
  app.insertBefore(settingsPanel, main);

  languageSelect = document.getElementById("language-select") as HTMLSelectElement;
  languageSelect.addEventListener("change", () => {
    const code = languageSelect.value;
    console.log(`[parsec-settings] language changed to: ${code}`);
    saveLanguage(code);
  });
}

function populateLanguagePicker(): void {
  // Group languages by script group
  const groups = new Map<string, Language[]>();
  for (const lang of languages) {
    const group = lang.script_group;
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group)!.push(lang);
  }

  languageSelect.innerHTML = "";

  for (const [groupName, langs] of groups) {
    const optgroup = document.createElement("optgroup");
    optgroup.label = groupName;
    for (const lang of langs) {
      const option = document.createElement("option");
      option.value = lang.short_code;
      option.textContent = lang.display_name;
      if (lang.short_code === selectedLanguage) {
        option.selected = true;
      }
      optgroup.appendChild(option);
    }
    languageSelect.appendChild(optgroup);
  }

  // If saved language wasn't found in the list, select English
  if (!languageSelect.value || languageSelect.value !== selectedLanguage) {
    const found = languages.find(l => l.short_code === selectedLanguage);
    if (!found) {
      console.warn(`[parsec-settings] saved language "${selectedLanguage}" not in registry, falling back to ${DEFAULT_LANGUAGE}`);
      selectedLanguage = DEFAULT_LANGUAGE;
      languageSelect.value = DEFAULT_LANGUAGE;
    }
  }
}

function togglePanel(): void {
  panelOpen = !panelOpen;
  settingsPanel.classList.toggle("settings-panel--open", panelOpen);
  settingsPanel.setAttribute("aria-hidden", String(!panelOpen));
  settingsBtn.classList.toggle("settings-btn--active", panelOpen);
}
