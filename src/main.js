const header = document.querySelector(".header");
const tabbar = document.querySelector("[data-tabbar]");
const productsSwitcher = document.querySelector(".products-switcher");
const productTabsIndicator = document.querySelector(".products-switcher__indicator");
const productsGrid = document.querySelector(".products-grid");
const productsPrev = document.querySelector(".products-arrow--prev");
const productsNext = document.querySelector(".products-arrow--next");
const productsMore = document.querySelector("[data-open-catalog]");

const views = {
  home: document.querySelector('[data-view="home"]'),
  catalog: document.querySelector('[data-view="catalog"]'),
  product: document.querySelector('[data-view="product"]'),
};
const catalogTitleEl = document.querySelector("[data-catalog-title]");
const catalogListEl = document.querySelector("[data-catalog-list]");
const productBodyEl = document.querySelector("[data-product-body]");

const catalog = window.PRODUCTS_DATA || { sections: [], products: {} };
const productTabs = [];

let activeCategory = catalog.sections[0]?.id || "classic";
let currentView = "home";
// Куда возвращает кнопка «назад» на странице торта: последняя открытая
// «список»-страница (главная или каталог категории).
let backHash = "#/";
// Была ли навигация внутри приложения (чтобы использовать history.back и
// сохранять позицию скролла списка, а не прыгать наверх).
let userNavigated = false;

const sectionLabel = (id) => catalog.sections.find((s) => s.id === id)?.label || id;

const productKey = (product, index) => product.slug || String(index);

const findProduct = (categoryId, key) => {
  const items = catalog.products[categoryId] || [];
  let index = items.findIndex((p) => p.slug === key);
  if (index < 0 && /^\d+$/.test(key)) index = Number(key);
  return { items, product: items[index], index };
};

const getProductImages = (product) => {
  const hasWhole = Boolean(product.hasWhole && product.slug);
  const hasCut = Boolean(product.hasCut && product.slug);
  const imageWhole = hasWhole ? `./assets/webp/cakes/${product.slug}-whole.webp` : "";
  const imageCut = hasCut ? `./assets/webp/cakes/${product.slug}-cut.webp` : "";
  return {
    hasWhole,
    hasCut,
    imageWhole,
    imageCut,
    imageMain: imageWhole || imageCut,
    showSwitcher: hasWhole && hasCut,
  };
};

const updateHeader = () => {
  const distanceToBottom = document.documentElement.scrollHeight - window.innerHeight - window.scrollY;
  const isMobile = window.matchMedia("(max-width: 640px)").matches;
  const isFooterVisible = currentView === "home" && distanceToBottom < 520;

  if (header) {
    const scrolled = currentView !== "home" || window.scrollY > 40;
    header.classList.toggle("is-scrolled", scrolled);

    // В мобе шапка видна только в самом верху главной; при начале скролла
    // (и на подстраницах) — прячется, навигацию берёт нижний таббар.
    let hideHeader = isFooterVisible;
    if (isMobile) {
      hideHeader = hideHeader || currentView !== "home" || window.scrollY > 8;
    }
    header.classList.toggle("is-hidden", hideHeader);
    document.body.classList.toggle("is-footer-visible", isFooterVisible);
  }

  if (tabbar) {
    // Таббар появляется при начале скролла и прячется у самого низа (чтобы не закрывать футер).
    const nearBottom = distanceToBottom < 96;
    const show = (currentView !== "home" || window.scrollY > 8) && !nearBottom;
    tabbar.classList.toggle("is-visible", show);
  }
};

const setActiveTab = () => {
  if (!tabbar) return;
  const hash = window.location.hash;
  let active = "home";
  if (currentView === "catalog" || currentView === "product" || hash.startsWith("#catalog") || hash.startsWith("#/c/") || hash.startsWith("#/p/")) {
    active = "catalog";
  } else if (hash.startsWith("#products")) {
    active = "products";
  } else if (hash.startsWith("#factory")) {
    active = "factory";
  }
  tabbar.querySelectorAll(".tabbar__item").forEach((item) => {
    item.classList.toggle("is-active", item.dataset.tab === active);
  });
};

tabbar?.querySelectorAll(".tabbar__item").forEach((item) => {
  item.addEventListener("click", () => {
    tabbar.querySelectorAll(".tabbar__item").forEach((el) => el.classList.remove("is-active"));
    item.classList.add("is-active");
  });
});

const createProductCard = (product, index) => {
  const weights = product.weights;
  const weightMarkup =
    weights.length > 1
      ? `<div class="product-card__weights">${weights
          .map(
            (weight, weightIndex) =>
              `<button class="product-card__weight${weightIndex === 0 ? " product-card__weight--active" : ""}" type="button" data-price="${weight.price}">${weight.label}</button>`
          )
          .join("")}</div>`
      : `<p class="product-card__single-weight">${weights[0].label}</p>`;

  const { imageMain } = getProductImages(product);
  const photoMarkup = imageMain
    ? `<div class="product-card__photo">
         <img class="product-card__img is-active" src="${imageMain}" alt="${product.title}" loading="lazy" />
       </div>`
    : `<div class="product-card__photo product-card__photo--empty" aria-hidden="true"></div>`;

  return `<article class="product-card" data-product-index="${index}" tabindex="0" role="link" aria-label="Подробнее о ${product.title}">
    ${photoMarkup}
    <div class="product-card__content">
      <h3 class="product-card__title">${product.title}</h3>
      <p class="product-card__description">${product.description}</p>
      <p class="product-card__price" data-product-price>${weights[0].price}</p>
      ${weightMarkup}
    </div>
  </article>`;
};

const buildProductDetail = (product, categoryId) => {
  const { imageWhole, imageCut, hasWhole, hasCut, imageMain } = getProductImages(product);
  const weights = product.weights;

  const images = [];
  if (hasWhole) images.push({ src: imageWhole, label: "Целый", cut: false });
  if (hasCut) images.push({ src: imageCut, label: "В разрезе", cut: true });

  const stageMarkup = imageMain
    ? `<div class="product-gallery__stage">
         ${images
           .map(
             (image, index) =>
               `<img class="product-gallery__img${index === 0 ? " is-active" : ""}" src="${image.src}" alt="${product.title}${image.cut ? " в разрезе" : ""}" data-gallery-img="${index}" />`
           )
           .join("")}
       </div>`
    : `<div class="product-gallery__stage product-gallery__stage--empty" aria-hidden="true"></div>`;

  const thumbsMarkup =
    images.length > 1
      ? `<div class="product-gallery__thumbs">
           ${images
             .map(
               (image, index) =>
                 `<button class="product-gallery__thumb${index === 0 ? " is-active" : ""}" type="button" data-gallery-thumb="${index}" aria-label="${image.label}">
                    <img src="${image.src}" alt="" loading="lazy" />
                  </button>`
             )
             .join("")}
         </div>`
      : "";

  const buyMarkup =
    weights.length > 1
      ? `<div class="product-weights" data-weights>
           ${weights
             .map(
               (weight, index) =>
                 `<button class="product-weight${index === 0 ? " is-active" : ""}" type="button" data-price="${weight.price}" data-label="${weight.label}">${weight.label}</button>`
             )
             .join("")}
         </div>
         <div class="product-price">
           <span class="product-price__value" data-price-value>${weights[0].price}</span>
           <span class="product-price__weight" data-price-weight>за ${weights[0].label}</span>
         </div>`
      : `<div class="product-price">
           <span class="product-price__value">${weights[0].price}</span>
           <span class="product-price__weight">за ${weights[0].label}</span>
         </div>`;

  return `
    <div class="product-hero">
      <div class="product-hero__media">
        <a class="product-hero__back" href="${backHash}" data-back aria-label="Назад">
          <svg class="product-hero__back-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M15 5 8 12l7 7" />
          </svg>
        </a>
        ${stageMarkup}
        ${thumbsMarkup}
      </div>
      <div class="product-hero__panel">
        <div class="product-hero__panel-inner">
          <p class="product-page__eyebrow">${sectionLabel(categoryId)}</p>
          <h1 class="product-page__title">${product.title}</h1>
          <p class="product-page__desc">${product.description}</p>
          <div class="product-page__buy">
            <p class="product-page__buy-label">Фасовка и цена</p>
            ${buyMarkup}
          </div>
          <p class="product-page__note">Всегда в наличии в нашем фирменном магазине</p>
        </div>
      </div>
    </div>`;
};

const buildCatalogTile = (product, categoryId, index) => {
  const { imageMain } = getProductImages(product);
  const media = imageMain
    ? `<img class="catalog-tile__img" src="${imageMain}" alt="${product.title}" loading="lazy" />`
    : `<span class="catalog-tile__img catalog-tile__img--empty" aria-hidden="true"></span>`;

  return `
    <a class="catalog-tile" href="#/p/${categoryId}/${productKey(product, index)}">
      <span class="catalog-tile__media">${media}</span>
      <span class="catalog-tile__title">${product.title}</span>
      <span class="catalog-tile__price">${product.weights[0].price}</span>
    </a>`;
};

const bindProductDetailInteractions = (container) => {
  if (!container) return;

  const back = container.querySelector("[data-back]");
  back?.addEventListener("click", (event) => {
    // Если пришли навигацией внутри сайта — возвращаемся назад по истории,
    // это сохраняет позицию скролла списка (главная/каталог).
    if (userNavigated && window.history.length > 1) {
      event.preventDefault();
      window.history.back();
    }
  });

  const thumbs = Array.from(container.querySelectorAll("[data-gallery-thumb]"));
  const images = Array.from(container.querySelectorAll("[data-gallery-img]"));

  thumbs.forEach((thumb) => {
    thumb.addEventListener("click", () => {
      const index = thumb.dataset.galleryThumb;
      thumbs.forEach((item) => item.classList.toggle("is-active", item === thumb));
      images.forEach((image) => image.classList.toggle("is-active", image.dataset.galleryImg === index));
    });
  });

  const weightButtons = Array.from(container.querySelectorAll("[data-weights] .product-weight"));
  const priceValue = container.querySelector("[data-price-value]");
  const priceWeight = container.querySelector("[data-price-weight]");

  weightButtons.forEach((button) => {
    button.addEventListener("click", () => {
      weightButtons.forEach((item) => item.classList.remove("is-active"));
      button.classList.add("is-active");
      if (priceValue) priceValue.textContent = button.dataset.price || "";
      if (priceWeight) priceWeight.textContent = `за ${button.dataset.label || ""}`;
    });
  });
};

const updateArrowState = () => {
  if (!productsGrid || !productsPrev || !productsNext) return;

  const maxScrollLeft = productsGrid.scrollWidth - productsGrid.clientWidth;
  productsPrev.disabled = productsGrid.scrollLeft <= 1;
  productsNext.disabled = productsGrid.scrollLeft >= maxScrollLeft - 1;
};

const bindProductInteractions = () => {
  const categoryProducts = catalog.products[activeCategory] || [];

  document.querySelectorAll(".product-card").forEach((card) => {
    const index = Number(card.dataset.productIndex);
    const product = categoryProducts[index];
    const price = card.querySelector("[data-product-price]");
    const weights = Array.from(card.querySelectorAll(".product-card__weight"));

    const openFromCard = () => {
      if (product) location.hash = `#/p/${activeCategory}/${productKey(product, index)}`;
    };

    card.addEventListener("click", openFromCard);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openFromCard();
      }
    });

    weights.forEach((weight) => {
      weight.addEventListener("click", (event) => {
        event.stopPropagation();
        weights.forEach((item) => item.classList.remove("product-card__weight--active"));
        weight.classList.add("product-card__weight--active");
        if (price) price.textContent = weight.dataset.price || "";
      });
    });
  });
};

const updateProductTabsIndicator = (tab = productTabs.find((item) => item.classList.contains("products-switcher__item--active"))) => {
  if (!productTabsIndicator || !tab) return;

  productTabsIndicator.style.width = `${tab.offsetWidth}px`;
  productTabsIndicator.style.transform = `translateX(${tab.offsetLeft - productTabsIndicator.offsetLeft}px)`;
};

const renderProducts = () => {
  if (!productsGrid) return;
  const categoryProducts = catalog.products[activeCategory] || [];

  productsGrid.innerHTML = categoryProducts.map(createProductCard).join("");
  productsGrid.scrollLeft = 0;
  if (productsMore) productsMore.setAttribute("href", `#/c/${activeCategory}`);
  bindProductInteractions();
  updateArrowState();
};

const getProductScrollStep = () => {
  if (!productsGrid) return 0;
  const firstCard = productsGrid.querySelector(".product-card");
  if (!firstCard) return productsGrid.clientWidth;
  const gridStyles = window.getComputedStyle(productsGrid);
  const gap = Number.parseFloat(gridStyles.columnGap || gridStyles.gap) || 0;
  return firstCard.getBoundingClientRect().width + gap;
};

const setActiveCategory = (tab) => {
  activeCategory = tab.dataset.category || catalog.sections[0]?.id || "classic";

  productTabs.forEach((item) => {
    item.classList.remove("products-switcher__item--active");
    item.setAttribute("aria-selected", "false");
  });

  tab.classList.add("products-switcher__item--active");
  tab.setAttribute("aria-selected", "true");
  updateProductTabsIndicator(tab);

  renderProducts();
};

const buildProductTabs = () => {
  if (!productsSwitcher) return;

  catalog.sections.forEach((section, index) => {
    const tab = document.createElement("button");
    tab.className = `products-switcher__item${index === 0 ? " products-switcher__item--active" : ""}`;
    tab.type = "button";
    tab.role = "tab";
    tab.dataset.category = section.id;
    tab.textContent = section.label;
    tab.setAttribute("aria-selected", index === 0 ? "true" : "false");
    tab.addEventListener("click", () => setActiveCategory(tab));
    productsSwitcher.appendChild(tab);
    productTabs.push(tab);
  });
};

/* --- Бургер + мобильное меню --- */
const burger = document.querySelector("[data-burger]");
const navDrawer = document.querySelector("[data-nav-drawer]");

const openMenu = () => {
  if (!navDrawer) return;
  navDrawer.removeAttribute("hidden");
  requestAnimationFrame(() => navDrawer.classList.add("is-open"));
  document.body.classList.add("is-sheet-open");
  burger?.setAttribute("aria-expanded", "true");
};

const closeMenu = () => {
  if (!navDrawer || navDrawer.hasAttribute("hidden")) return;
  navDrawer.classList.remove("is-open");
  burger?.setAttribute("aria-expanded", "false");
  document.body.classList.remove("is-sheet-open");
  setTimeout(() => navDrawer.setAttribute("hidden", ""), 340);
};

burger?.addEventListener("click", openMenu);
navDrawer?.querySelectorAll("[data-nav-close]").forEach((el) => {
  el.addEventListener("click", closeMenu);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMenu();
});

/* --- Роутинг по страницам --- */
const showView = (name) => {
  currentView = name;
  Object.entries(views).forEach(([key, el]) => {
    if (el) el.hidden = key !== name;
  });
  document.body.classList.toggle("is-subpage", name !== "home");
  document.body.classList.toggle("is-product-view", name === "product");
  updateHeader();
  setActiveTab();
};

const renderCatalogPage = (categoryId) => {
  const section = catalog.sections.find((s) => s.id === categoryId);
  if (!section) return false;

  const items = catalog.products[categoryId] || [];
  if (catalogTitleEl) catalogTitleEl.textContent = section.label;
  if (catalogListEl) {
    catalogListEl.innerHTML = `<div class="catalog-grid">${items
      .map((product, index) => buildCatalogTile(product, categoryId, index))
      .join("")}</div>`;
  }
  return true;
};

const renderProductPage = (categoryId, key) => {
  const { product } = findProduct(categoryId, key);
  if (!product) return false;

  if (productBodyEl) {
    productBodyEl.innerHTML = buildProductDetail(product, categoryId);
    bindProductDetailInteractions(productBodyEl);
  }
  return true;
};

const scrollTop = () => {
  // Мгновенно наверх, игнорируя scroll-behavior: smooth, чтобы внутренние
  // страницы всегда открывались с верха, а не «снизу».
  window.scrollTo({ top: 0, left: 0, behavior: "instant" });
};

const DEFAULT_TITLE = "Кондитерская фабрика «Восток» - торты и пирожные в Чите с 1910 года";
const setTitle = (part) => {
  document.title = part ? `${part} - Кондитерская фабрика «Восток»` : DEFAULT_TITLE;
};

const router = () => {
  closeMenu();

  const raw = location.hash.replace(/^#\/?/, "");
  const parts = raw.split("/").filter(Boolean);

  if (parts[0] === "c" && parts[1] && renderCatalogPage(parts[1])) {
    showView("catalog");
    backHash = location.hash;
    const section = catalog.sections.find((s) => s.id === parts[1]);
    setTitle(section ? section.label : "Каталог");
    scrollTop();
    return;
  }

  if (parts[0] === "p" && parts[1] && parts[2] && renderProductPage(parts[1], parts[2])) {
    showView("product");
    const { product } = findProduct(parts[1], parts[2]);
    setTitle(product ? product.title : "");
    scrollTop();
    return;
  }

  showView("home");
  setTitle("");
  backHash = location.hash || "#/";

  if (parts[0]) {
    const target = document.getElementById(parts[0]);
    if (target) requestAnimationFrame(() => target.scrollIntoView());
  } else {
    scrollTop();
  }
};

window.addEventListener("hashchange", () => {
  userNavigated = true;
});
window.addEventListener("hashchange", router);
window.addEventListener("hashchange", setActiveTab);
window.addEventListener("scroll", updateHeader, { passive: true });

buildProductTabs();

if (productsPrev) {
  productsPrev.addEventListener("click", () => {
    if (!productsGrid) return;
    productsGrid.scrollBy({ left: -getProductScrollStep(), behavior: "smooth" });
  });
}

if (productsNext) {
  productsNext.addEventListener("click", () => {
    if (!productsGrid) return;
    productsGrid.scrollBy({ left: getProductScrollStep(), behavior: "smooth" });
  });
}

if (productsGrid) {
  productsGrid.addEventListener("scroll", updateArrowState, { passive: true });
  window.addEventListener("resize", () => {
    updateArrowState();
    updateProductTabsIndicator();
  });
}

updateProductTabsIndicator();
renderProducts();
router();
initStoreMap();
initReveal();

function initReveal() {
  const selector = [
    ".page-title",
    ".hero-eyebrow",
    ".hero-title",
    ".hero-button",
    ".factory-brief__eyebrow",
    ".factory-brief__title",
    ".factory-brief__text",
    ".factory-brief__stat",
    ".factory-title",
    ".factory-text",
    ".factory-stat-item",
    ".factory-link",
    ".advantage-card",
    ".purchase-order__item",
    ".feed__intro",
    ".footer__top",
    ".footer__col",
    ".footer__bottom",
  ].join(",");

  const els = Array.from(document.querySelectorAll(selector));
  if (!els.length) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduceMotion || !("IntersectionObserver" in window)) {
    els.forEach((el) => el.classList.add("reveal", "is-visible"));
    return;
  }

  // Ступенчатая задержка для соседних элементов одного родителя.
  const perParent = new Map();
  els.forEach((el) => {
    el.classList.add("reveal");
    const parent = el.parentElement;
    const index = perParent.get(parent) || 0;
    perParent.set(parent, index + 1);
    el.style.setProperty("--reveal-delay", `${Math.min(index, 6) * 70}ms`);
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  els.forEach((el) => observer.observe(el));
}

async function initStoreMap() {
  const frame = document.querySelector("[data-map-frame]");
  const fallback = document.querySelector("[data-map-fallback]");
  const src = frame?.dataset.src;
  if (!frame || !fallback || !src) return;

  const showFallback = () => {
    frame.hidden = true;
    fallback.hidden = false;
  };

  let timeout;
  try {
    const controller = new AbortController();
    timeout = window.setTimeout(() => controller.abort(), 4500);
    await fetch(src, { mode: "no-cors", signal: controller.signal });
    frame.src = src;
    frame.hidden = false;
    fallback.hidden = true;
  } catch {
    showFallback();
  } finally {
    window.clearTimeout(timeout);
  }
}
