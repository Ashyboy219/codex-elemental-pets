const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

document.querySelectorAll("[data-evolution-card]").forEach((card) => {
  const stage = card.querySelector(".evolution-stage");
  const formButtons = card.querySelectorAll("[data-form-button]");
  const normalImage = card.querySelector(".animated-normal");
  const normalStill = card.querySelector(".normal-still");
  const evolvedImage = card.querySelector(".evolved-form");
  const status = card.querySelector("[data-status]");
  const petName = stage.dataset.petName;

  function syncFormAccessibility() {
    const isEvolved = card.dataset.form === "evolved";
    normalImage.setAttribute("aria-hidden", String(isEvolved || reducedMotion.matches));
    normalStill.setAttribute("aria-hidden", String(isEvolved || !reducedMotion.matches));
    evolvedImage.setAttribute("aria-hidden", String(!isEvolved));
  }

  function setForm(form) {
    card.dataset.form = form;
    syncFormAccessibility();

    formButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.formButton === form));
    });
    status.textContent = `${petName} is in ${form === "evolved" ? "the proposed evolved" : "Normal"} form.`;
  }

  formButtons.forEach((button) => {
    button.addEventListener("click", () => setForm(button.dataset.formButton));
  });

  function syncReducedMotion() {
    syncFormAccessibility();
  }

  syncReducedMotion();
  reducedMotion.addEventListener("change", syncReducedMotion);
});
