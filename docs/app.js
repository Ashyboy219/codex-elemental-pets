const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const AMBIENT_DURATION_MS = 11_000;

document.querySelectorAll("[data-evolution-card]").forEach((card) => {
  const stage = card.querySelector(".evolution-stage");
  const formButtons = card.querySelectorAll("[data-form-button]");
  const ambientButton = card.querySelector(".ambient-toggle");
  const normalImage = card.querySelector(".animated-normal");
  const normalStill = card.querySelector(".normal-still");
  const ultraImage = card.querySelector(".ultra-form");
  const status = card.querySelector("[data-status]");
  const petName = stage.dataset.pet === "frostbyte" ? "Frostbyte" : "Bolt";
  let ambientTimer;

  function syncFormAccessibility() {
    const isUltra = card.dataset.form === "ultra";
    normalImage.setAttribute("aria-hidden", String(isUltra || reducedMotion.matches));
    normalStill.setAttribute("aria-hidden", String(isUltra || !reducedMotion.matches));
    ultraImage.setAttribute("aria-hidden", String(!isUltra));
  }

  function stopAmbient(announce = false) {
    window.clearTimeout(ambientTimer);
    stage.classList.remove("ambient-live");
    ambientButton.setAttribute("aria-pressed", "false");
    ambientButton.disabled = reducedMotion.matches || card.dataset.form !== "ultra";
    ambientButton.textContent = reducedMotion.matches
      ? "Ambient paused"
      : card.dataset.form === "ultra"
        ? "Play ambient"
        : "Ambient in Ultra";

    if (announce) {
      status.textContent = `${petName} ambient motion stopped.`;
    }
  }

  function startAmbient() {
    if (reducedMotion.matches || card.dataset.form !== "ultra") {
      return;
    }

    window.clearTimeout(ambientTimer);
    stage.classList.remove("ambient-live");
    void stage.offsetWidth;
    stage.classList.add("ambient-live");
    ambientButton.disabled = false;
    ambientButton.setAttribute("aria-pressed", "true");
    ambientButton.textContent = "Stop ambient";
    status.textContent = `${petName} ambient motion is playing and will stop after 11 seconds.`;
    ambientTimer = window.setTimeout(() => stopAmbient(true), AMBIENT_DURATION_MS);
  }

  function setForm(form) {
    const isUltra = form === "ultra";
    card.dataset.form = form;
    syncFormAccessibility();

    formButtons.forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.formButton === form));
    });
    ambientButton.title = reducedMotion.matches
      ? "Ambient motion is paused by your reduced-motion preference."
      : isUltra
        ? "Play ambient motion for up to 11 seconds."
        : "Choose Ultra to play ambient motion.";

    if (!reducedMotion.matches) {
      stage.classList.remove("is-evolving");
      void stage.offsetWidth;
      stage.classList.add("is-evolving");
      window.setTimeout(() => stage.classList.remove("is-evolving"), 800);
    }

    status.textContent = `${petName} is in ${isUltra ? "the proposed Ultra" : "Normal"} form.`;

    if (isUltra) {
      startAmbient();
    } else {
      stopAmbient();
    }
  }

  formButtons.forEach((button) => {
    button.addEventListener("click", () => setForm(button.dataset.formButton));
  });

  ambientButton.addEventListener("click", () => {
    if (ambientButton.getAttribute("aria-pressed") === "true") {
      stopAmbient(true);
    } else if (card.dataset.form === "ultra") {
      startAmbient();
    } else {
      status.textContent = `Choose ${petName} Ultra before playing ambient motion.`;
    }
  });

  function syncReducedMotion() {
    stopAmbient();
    syncFormAccessibility();
    ambientButton.title = reducedMotion.matches
      ? "Ambient motion is paused by your reduced-motion preference."
      : card.dataset.form === "ultra"
        ? "Play ambient motion for up to 11 seconds."
        : "Choose Ultra to play ambient motion.";
  }

  syncReducedMotion();
  reducedMotion.addEventListener("change", syncReducedMotion);
});
