import { CONFIG } from "./config.js";
import { getConsent } from "./consent.js";

let booted = false;

function loadScript({ src, id, async = true }) {
  return new Promise((resolve, reject) => {
    if (id && document.getElementById(id)) return resolve(true);
    const s = document.createElement("script");
    if (id) s.id = id;
    s.async = async;
    s.src = src;
    s.onload = () => resolve(true);
    s.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.head.appendChild(s);
  });
}

function bootClarity(projectId) {
  if (!projectId) return;
  if (window.clarity) return;

  // Official embed pattern (wrapped so we can gate by consent).
  (function (c, l, a, r, i, t, y) {
    c[a] =
      c[a] ||
      function () {
        (c[a].q = c[a].q || []).push(arguments);
      };
    t = l.createElement(r);
    t.async = 1;
    t.src = "https://www.clarity.ms/tag/" + i;
    y = l.getElementsByTagName(r)[0];
    y.parentNode.insertBefore(t, y);
  })(window, document, "clarity", "script", projectId);
}

function bootYandexMetrica(counterId) {
  if (!counterId) return;
  if (window.ym) return;

  // Inject loader
  (function (m, e, t, r, i, k, a) {
    m[i] =
      m[i] ||
      function () {
        (m[i].a = m[i].a || []).push(arguments);
      };
    m[i].l = 1 * new Date();
    for (let j = 0; j < document.scripts.length; j++) {
      if (document.scripts[j].src === r) return;
    }
    k = e.createElement(t);
    a = e.getElementsByTagName(t)[0];
    k.async = 1;
    k.src = r;
    a.parentNode.insertBefore(k, a);
  })(window, document, "script", "https://mc.yandex.ru/metrika/tag.js", "ym");

  window.ym(counterId, "init", {
    clickmap: true,
    trackLinks: true,
    accurateTrackBounce: true,
    webvisor: true,
  });
}

async function bootGA4(measurementId) {
  if (!measurementId) return;
  if (window.gtag) return;

  window.dataLayer = window.dataLayer || [];
  window.gtag = function () {
    window.dataLayer.push(arguments);
  };
  window.gtag("js", new Date());
  window.gtag("config", measurementId, { anonymize_ip: true });

  await loadScript({
    id: "ga4",
    src: `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(measurementId)}`,
  });
}

export async function bootAnalyticsIfConsented() {
  if (booted) return;
  const consent = getConsent();
  if (!consent) return;

  const wantTraffic = !!consent.analytics && CONFIG.enableTrafficAnalytics;
  const wantUX = !!consent.experience && CONFIG.enableClarity;

  const jobs = [];

  if (wantUX && CONFIG.clarityProjectId) {
    jobs.push(Promise.resolve().then(() => bootClarity(CONFIG.clarityProjectId)));
  }

  if (wantTraffic) {
    if (CONFIG.yandexMetricaId) jobs.push(Promise.resolve().then(() => bootYandexMetrica(CONFIG.yandexMetricaId)));
    if (CONFIG.ga4MeasurementId) jobs.push(bootGA4(CONFIG.ga4MeasurementId));
  }

  booted = true;
  await Promise.allSettled(jobs);
}

export function track(eventName, params = {}) {
  const consent = getConsent();
  if (!consent || !consent.analytics) return;

  // GA4 event
  if (window.gtag && CONFIG.ga4MeasurementId) {
    window.gtag("event", eventName, params);
  }

  // Yandex Metrica reachGoal (optional)
  if (window.ym && CONFIG.yandexMetricaId) {
    try {
      window.ym(CONFIG.yandexMetricaId, "reachGoal", eventName, params);
    } catch {
      // ignore
    }
  }
}

