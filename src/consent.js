const STORAGE_KEY = "site_consent_v1";

/**
 * Consent model:
 * - necessary: always true (no tracking)
 * - analytics: traffic analytics + events (GA4/Metрика)
 * - experience: UI analytics like session replay/heatmaps (Clarity)
 */
export function getConsent() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object") return null;
    return {
      necessary: true,
      analytics: !!parsed.analytics,
      experience: !!parsed.experience,
      ts: typeof parsed.ts === "number" ? parsed.ts : Date.now(),
    };
  } catch {
    return null;
  }
}

export function setConsent(next) {
  const value = {
    analytics: !!next.analytics,
    experience: !!next.experience,
    ts: Date.now(),
  };
  localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
  window.dispatchEvent(new CustomEvent("consent:changed", { detail: getConsent() }));
}

export function hasAnyOptionalConsent(consent) {
  return !!(consent && (consent.analytics || consent.experience));
}

export function openConsentModal() {
  window.dispatchEvent(new CustomEvent("consent:open"));
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else if (k === "text") node.textContent = v;
    else if (v === true) node.setAttribute(k, "");
    else if (v !== false && v != null) node.setAttribute(k, String(v));
  }
  for (const c of children) node.append(c);
  return node;
}

export function mountConsentUI({ rootId = "consent-root" } = {}) {
  const root = document.getElementById(rootId);
  if (!root) return;

  let banner = null;
  let modalBackdrop = null;

  const renderBanner = () => {
    const consent = getConsent();
    if (consent) return; // уже есть выбор

    if (banner) return;
    banner = el("div", { class: "consent", role: "region", "aria-label": "Настройки cookies" }, [
      el("div", { class: "consent__row" }, [
        el("div", {}, [
          el("p", { class: "consent__title", text: "Мы используем cookies" }),
          el("p", {
            class: "consent__text",
            text:
              "Нужны для аналитики интерфейса (клики/скролл) и улучшения UX. Вы можете отключить необязательные категории.",
          }),
          el("div", {}, [
            el("a", { class: "consent__link", href: "./privacy.html" , text: "Политика" }),
            document.createTextNode(" · "),
            el("a", { class: "consent__link", href: "./consent.html", text: "Согласие" }),
          ]),
        ]),
        el("div", { class: "consent__actions" }, [
          el("button", {
            class: "btn btn--secondary",
            type: "button",
            text: "Настроить",
            onclick: () => open(),
          }),
          el("button", {
            class: "btn btn--ghost",
            type: "button",
            text: "Только необходимые",
            onclick: () => {
              setConsent({ analytics: false, experience: false });
              cleanup();
            },
          }),
          el("button", {
            class: "btn btn--primary",
            type: "button",
            text: "Разрешить все",
            onclick: () => {
              setConsent({ analytics: true, experience: true });
              cleanup();
            },
          }),
        ]),
      ]),
    ]);

    root.append(banner);
  };

  const cleanup = () => {
    if (banner) banner.remove();
    banner = null;
  };

  const closeModal = () => {
    if (!modalBackdrop) return;
    modalBackdrop.remove();
    modalBackdrop = null;
  };

  const toggle = (current, onChange) => {
    const t = el("button", {
      class: "toggle",
      type: "button",
      role: "switch",
      "aria-checked": String(!!current),
      onclick: (e) => {
        const next = e.currentTarget.getAttribute("aria-checked") !== "true";
        e.currentTarget.setAttribute("aria-checked", String(next));
        onChange(next);
      },
    });
    return t;
  };

  const open = () => {
    const current = getConsent() || { necessary: true, analytics: false, experience: false };
    let draft = { analytics: !!current.analytics, experience: !!current.experience };

    const analyticsToggle = toggle(draft.analytics, (v) => (draft.analytics = v));
    const expToggle = toggle(draft.experience, (v) => (draft.experience = v));

    modalBackdrop = el("div", { class: "modal-backdrop", role: "dialog", "aria-modal": "true" }, [
      el("div", { class: "modal" }, [
        el("div", { class: "modal__head" }, [
          el("p", { class: "modal__title", text: "Настройки cookies" }),
          el("button", { class: "icon-btn", type: "button", "aria-label": "Закрыть", text: "×", onclick: closeModal }),
        ]),
        el("div", { class: "modal__body" }, [
          el("div", { class: "pref" }, [
            el("div", {}, [
              el("p", { class: "pref__name", text: "Необходимые" }),
              el("p", { class: "pref__desc", text: "Нужны для работы сайта. Их нельзя отключить." }),
            ]),
            el("div", { class: "toggle", role: "switch", "aria-checked": "true", tabindex: "-1" }),
          ]),
          el("div", { class: "pref" }, [
            el("div", {}, [
              el("p", { class: "pref__name", text: "Аналитика" }),
              el("p", { class: "pref__desc", text: "События (клики, скролл), источники трафика." }),
            ]),
            analyticsToggle,
          ]),
          el("div", { class: "pref" }, [
            el("div", {}, [
              el("p", { class: "pref__name", text: "Улучшение UX" }),
              el("p", { class: "pref__desc", text: "Карты кликов/скролла и записи сессий (если включено)." }),
            ]),
            expToggle,
          ]),
          el("div", { style: "display:flex; gap:10px; flex-wrap:wrap; margin-top:12px" }, [
            el("button", {
              class: "btn btn--secondary",
              type: "button",
              text: "Отклонить необязательные",
              onclick: () => {
                setConsent({ analytics: false, experience: false });
                closeModal();
                cleanup();
              },
            }),
            el("button", {
              class: "btn btn--primary",
              type: "button",
              text: "Сохранить выбор",
              onclick: () => {
                setConsent(draft);
                closeModal();
                cleanup();
              },
            }),
          ]),
          el("p", { class: "fineprint", style: "margin-top:10px" }, [
            document.createTextNode("Подробнее: "),
            el("a", { href: "./privacy.html", text: "политика" }),
            document.createTextNode(" и "),
            el("a", { href: "./consent.html", text: "согласие" }),
            document.createTextNode("."),
          ]),
        ]),
      ]),
    ]);

    root.append(modalBackdrop);
  };

  window.addEventListener("consent:open", open);
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModal();
  });

  renderBanner();

  return {
    open,
    close: closeModal,
  };
}

