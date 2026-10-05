const phoneScreen = document.querySelector(".phone-screen");
const screens = [...document.querySelectorAll("[data-screen]")];
const tabs = [...document.querySelectorAll("[data-show-screen]")];

function showScreen(name) {
  screens.forEach((screen) => {
    screen.classList.toggle("is-active", screen.dataset.screen === name);
  });
  tabs.forEach((tab) => {
    tab.classList.toggle("is-active", tab.dataset.showScreen === name);
  });
  phoneScreen.scrollTo(0, 0);
  const url = new URL(window.location.href);
  url.searchParams.set("screen", name);
  window.history.replaceState({}, "", url);
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => showScreen(tab.dataset.showScreen));
});

document.querySelector(".menu-trigger").addEventListener("click", () => showScreen("menu"));
document.querySelector(".close-menu").addEventListener("click", () => showScreen("home"));
document.querySelector(".product-trigger").addEventListener("click", () => showScreen("product"));
document.querySelector(".category-trigger").addEventListener("click", () => showScreen("category"));
document.querySelector(".home-trigger").addEventListener("click", () => showScreen("home"));
document.querySelector(".cart-trigger").addEventListener("click", () => showScreen("checkout"));

const areaInput = document.querySelector(".area-input");
const result = document.querySelector(".calculation-result strong");

function updateCalculation(nextValue) {
  const area = Math.max(1, Number(nextValue) || 1);
  areaInput.value = area;
  result.textContent = `${Math.ceil((area * 2) / 9)} litraa`;
}

document.querySelector(".area-minus").addEventListener("click", () => {
  updateCalculation(Number(areaInput.value) - 1);
});
document.querySelector(".area-plus").addEventListener("click", () => {
  updateCalculation(Number(areaInput.value) + 1);
});
areaInput.addEventListener("input", () => updateCalculation(areaInput.value));

document.querySelectorAll(".size-picker label").forEach((label) => {
  label.addEventListener("click", () => {
    document.querySelectorAll(".size-picker label").forEach((item) => item.classList.remove("is-selected"));
    label.classList.add("is-selected");
  });
});

document.querySelectorAll(".shipping-option").forEach((label) => {
  label.addEventListener("click", () => {
    document.querySelectorAll(".shipping-option").forEach((item) => item.classList.remove("is-selected"));
    label.classList.add("is-selected");
  });
});

document.querySelector(".open-calculator").addEventListener("click", () => {
  showScreen("product");
  window.setTimeout(() => {
    document.querySelector(".inline-calculator").scrollIntoView({ behavior: "smooth", block: "center" });
  }, 50);
});

const toast = document.querySelector(".toast");
document.querySelector(".add-cart").addEventListener("click", () => {
  toast.classList.add("is-visible");
  window.setTimeout(() => toast.classList.remove("is-visible"), 1800);
});

const requestedScreen = new URLSearchParams(window.location.search).get("screen");
if (screens.some((screen) => screen.dataset.screen === requestedScreen)) {
  showScreen(requestedScreen);
}
