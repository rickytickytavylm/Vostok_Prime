const header = document.querySelector(".header");
const productTabs = Array.from(document.querySelectorAll(".products-switcher__item"));
const productTabsIndicator = document.querySelector(".products-switcher__indicator");
const productsGrid = document.querySelector(".products-grid");
const productsPrev = document.querySelector(".products-arrow--prev");
const productsNext = document.querySelector(".products-arrow--next");
const ingredientsScene = document.querySelector(".ingredients-scene");
const berries = Array.from(document.querySelectorAll(".berry"));
const categoryLinks = Array.from(document.querySelectorAll("[data-category-link]"));
const footer = document.querySelector(".footer");

const products = {
  cakes: [
    {
      title: "Гурме",
      description: "Шоколадно-Ванильный",
      weights: [
        { label: "1 000 гр.", price: "1 100 ₽" },
        { label: "1 500 гр.", price: "1 500 ₽" },
      ],
    },
    {
      title: "Восточная Сказка",
      description: "Клубнично-Сливочный",
      weights: [{ label: "1 000 гр.", price: "850 ₽" }],
    },
    {
      title: "Красный Бархат",
      description: "Клубнично-Сливочный",
      weights: [{ label: "900 гр.", price: "960 ₽" }],
    },
    {
      title: "Прага",
      description: "Шоколадный",
      weights: [{ label: "1 000 гр.", price: "920 ₽" }],
    },
    {
      title: "Медовик",
      description: "Медово-Сливочный",
      weights: [
        { label: "900 гр.", price: "780 ₽" },
        { label: "1 300 гр.", price: "1 080 ₽" },
      ],
    },
    {
      title: "Наполеон",
      description: "Сливочный",
      weights: [{ label: "1 000 гр.", price: "890 ₽" }],
    },
  ],
  pastries: [
    {
      title: "Эклер",
      description: "Ванильный крем",
      weights: [{ label: "90 гр.", price: "120 ₽" }],
    },
    {
      title: "Картошка",
      description: "Шоколадная",
      weights: [{ label: "80 гр.", price: "95 ₽" }],
    },
    {
      title: "Корзиночка",
      description: "Ягодная",
      weights: [{ label: "100 гр.", price: "140 ₽" }],
    },
    {
      title: "Профитроли",
      description: "Сливочные",
      weights: [
        { label: "6 шт.", price: "260 ₽" },
        { label: "12 шт.", price: "490 ₽" },
      ],
    },
    {
      title: "Трубочка",
      description: "С белковым кремом",
      weights: [{ label: "75 гр.", price: "110 ₽" }],
    },
  ],
  cookies: [
    {
      title: "Овсяное",
      description: "Классическое",
      weights: [{ label: "300 гр.", price: "180 ₽" }],
    },
    {
      title: "Курабье",
      description: "С абрикосом",
      weights: [{ label: "300 гр.", price: "220 ₽" }],
    },
    {
      title: "Шоколадное",
      description: "С крошкой",
      weights: [
        { label: "250 гр.", price: "210 ₽" },
        { label: "500 гр.", price: "390 ₽" },
      ],
    },
    {
      title: "Сахарное",
      description: "Рассыпчатое",
      weights: [{ label: "300 гр.", price: "160 ₽" }],
    },
    {
      title: "Ореховое",
      description: "С арахисом",
      weights: [{ label: "250 гр.", price: "240 ₽" }],
    },
  ],
};

let activeCategory = "cakes";

const updateHeader = () => {
  if (!header) return;
  header.classList.toggle("is-compact", window.scrollY > 0);

  const distanceToBottom = document.documentElement.scrollHeight - window.innerHeight - window.scrollY;
  const isFooterVisible = distanceToBottom < 520;
  header.classList.toggle("is-hidden", isFooterVisible);
  document.body.classList.toggle("is-footer-visible", isFooterVisible);
};

const createProductCard = (product) => {
  const weights = product.weights;
  const weightMarkup =
    weights.length > 1
      ? `<div class="product-card__weights">${weights
          .map(
            (weight, index) =>
              `<button class="product-card__weight${index === 0 ? " product-card__weight--active" : ""}" type="button" data-price="${weight.price}">${weight.label}</button>`
          )
          .join("")}</div>`
      : `<p class="product-card__single-weight">${weights[0].label}</p>`;

  return `<article class="product-card">
    <div class="product-card__photo"></div>
    <div class="product-card__content">
      <h3 class="product-card__title">${product.title}</h3>
      <p class="product-card__description">${product.description}</p>
      <p class="product-card__price" data-product-price>${weights[0].price}</p>
      ${weightMarkup}
    </div>
  </article>`;
};

const updateArrowState = () => {
  if (!productsGrid || !productsPrev || !productsNext) return;

  const maxScrollLeft = productsGrid.scrollWidth - productsGrid.clientWidth;
  productsPrev.disabled = productsGrid.scrollLeft <= 1;
  productsNext.disabled = productsGrid.scrollLeft >= maxScrollLeft - 1;
};

const bindProductWeights = () => {
  document.querySelectorAll(".product-card").forEach((card) => {
    const price = card.querySelector("[data-product-price]");
    const weights = Array.from(card.querySelectorAll(".product-card__weight"));

    weights.forEach((weight) => {
      weight.addEventListener("click", () => {
        weights.forEach((item) => item.classList.remove("product-card__weight--active"));
        weight.classList.add("product-card__weight--active");

        if (price) {
          price.textContent = weight.dataset.price || "";
        }
      });
    });
  });
};

const renderProducts = () => {
  if (!productsGrid) return;
  const categoryProducts = products[activeCategory];

  productsGrid.innerHTML = categoryProducts.map(createProductCard).join("");
  productsGrid.scrollLeft = 0;
  bindProductWeights();
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
  const tabIndex = productTabs.indexOf(tab);
  activeCategory = tab.dataset.category || "cakes";

  productTabs.forEach((item) => {
    item.classList.remove("products-switcher__item--active");
    item.setAttribute("aria-selected", "false");
  });

  tab.classList.add("products-switcher__item--active");
  tab.setAttribute("aria-selected", "true");

  if (productTabsIndicator) {
    productTabsIndicator.style.transform = `translateX(${tabIndex * 126}px)`;
  }

  renderProducts();
};

updateHeader();
window.addEventListener("scroll", updateHeader, { passive: true });

productTabs.forEach((tab) => {
  tab.addEventListener("click", () => setActiveCategory(tab));
});

categoryLinks.forEach((link) => {
  link.addEventListener("click", (event) => {
    const category = link.dataset.categoryLink;
    const tab = productTabs.find((item) => item.dataset.category === category);

    if (!tab) return;

    event.preventDefault();
    setActiveCategory(tab);
    document.querySelector("#products")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

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
  window.addEventListener("resize", updateArrowState);
}

if (ingredientsScene && berries.length && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  let parallaxFrame = null;
  let pointerX = 0;
  let pointerY = 0;

  const updateBerryParallax = () => {
    const rect = ingredientsScene.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const rawProgress = Math.min(Math.max((viewportHeight - rect.top) / (viewportHeight + rect.height), 0), 1);
    const easedProgress = rawProgress * rawProgress * (3 - 2 * rawProgress);
    const flow = easedProgress * 2 - 1;

    berries.forEach((berry) => {
      const depth = Number(berry.dataset.depth) || 0;
      const drift = Number(berry.dataset.drift) || 0;
      const rotate = Number(berry.dataset.rotate) || 0;
      const phase = Number(berry.dataset.phase) || 0;
      const curve = Number(berry.dataset.curve) || 0;
      const speed = Number(berry.dataset.speed) || 1;
      const individualProgress = Math.min(Math.max(rawProgress * speed + phase, 0), 1);
      const berryProgress = individualProgress * individualProgress * (3 - 2 * individualProgress);
      const berryFlow = berryProgress * 2 - 1;
      const z = depth * 180;
      const x = berryFlow * drift * 0.45 + Math.sin(berryProgress * Math.PI) * curve + pointerX * 90 * depth;
      const y = berryFlow * depth * 620 + pointerY * 140 * Math.abs(depth);
      const rotation = berryFlow * rotate;

      berry.style.transform = `translate3d(${x}px, ${y}px, ${z}px) rotate(${rotation}deg)`;
    });

    parallaxFrame = null;
  };

  const requestBerryParallax = () => {
    if (parallaxFrame) return;
    parallaxFrame = window.requestAnimationFrame(updateBerryParallax);
  };

  window.addEventListener("scroll", requestBerryParallax, { passive: true });
  window.addEventListener("resize", requestBerryParallax);
  ingredientsScene.addEventListener("pointermove", (event) => {
    const rect = ingredientsScene.getBoundingClientRect();
    pointerX = (event.clientX - rect.left) / rect.width - 0.5;
    pointerY = (event.clientY - rect.top) / rect.height - 0.5;
    requestBerryParallax();
  });
  ingredientsScene.addEventListener("pointerleave", () => {
    pointerX = 0;
    pointerY = 0;
    requestBerryParallax();
  });
  requestBerryParallax();
}

renderProducts();
