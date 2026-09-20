import { ApiError, leadKaydet, sohbetGonder } from "./api-client.js";

const HISTORY_LIMIT = 20;
const LEAD_IDLE_LABEL = "İletişim talebi oluştur →";
const SLIDE_LABELS = ["Sohbet ekranı", "İletişim ekranı"];

const state = {
  activeSlide: 0,
  chatBusy: false,
  leadBusy: false,
  history: [],
};

document.addEventListener("DOMContentLoaded", initializePage);

function initializePage() {
  const elements = getElements();
  elements.chatForm.addEventListener("submit", (event) => handleChatSubmit(event, elements));
  elements.messageInput.addEventListener("keydown", (event) => handleMessageKeydown(event, elements));
  elements.leadForm.addEventListener("submit", (event) => handleLeadSubmit(event, elements));
  initializeSlider(elements);
}

function getElements() {
  return {
    landingSlider: document.querySelector("#landingSlider"),
    slides: Array.from(document.querySelectorAll(".landing-slider__slide")),
    slideButtons: Array.from(document.querySelectorAll("[data-slide-target]")),
    prevSlideButton: document.querySelector("#prevSlideButton"),
    nextSlideButton: document.querySelector("#nextSlideButton"),
    slideStatus: document.querySelector("#slideStatus"),
    chatForm: document.querySelector("#chatForm"),
    messageInput: document.querySelector("#messageInput"),
    askButton: document.querySelector("#askButton"),
    answerText: document.querySelector("#answerText"),
    chatMessages: document.querySelector("#chatMessages"),
    leadForm: document.querySelector("#leadForm"),
    nameInput: document.querySelector("#nameInput"),
    phoneInput: document.querySelector("#phoneInput"),
    leadMessageInput: document.querySelector("#leadMessageInput"),
    saveLeadButton: document.querySelector("#saveLeadButton"),
    statusText: document.querySelector("#statusText"),
  };
}

function handleMessageKeydown(event, elements) {
  if (event.key !== "Enter" || event.isComposing) return;
  event.preventDefault();
  elements.chatForm.requestSubmit();
}

function initializeSlider(elements) {
  elements.prevSlideButton.addEventListener("click", () => {
    setActiveSlide(state.activeSlide - 1, elements);
  });
  elements.nextSlideButton.addEventListener("click", () => {
    setActiveSlide(state.activeSlide + 1, elements);
  });
  elements.slideButtons.forEach((button) => {
    button.addEventListener("click", () => {
      setActiveSlide(Number(button.dataset.slideTarget), elements);
    });
  });

  setActiveSlide(0, elements);
}

function setActiveSlide(nextSlide, elements) {
  const lastSlide = elements.slides.length - 1;
  state.activeSlide = Math.max(0, Math.min(nextSlide, lastSlide));
  elements.landingSlider.dataset.slide = String(state.activeSlide);
  elements.prevSlideButton.disabled = state.activeSlide === 0;
  elements.nextSlideButton.disabled = state.activeSlide === lastSlide;

  elements.slides.forEach((slide, index) => {
    const isActive = index === state.activeSlide;
    slide.setAttribute("aria-hidden", String(!isActive));
    slide.toggleAttribute("inert", !isActive);
  });

  elements.slideButtons.forEach((button, index) => {
    button.setAttribute("aria-current", String(index === state.activeSlide));
  });

  elements.slideStatus.textContent = `${SLIDE_LABELS[state.activeSlide]} gösteriliyor`;
}

async function handleChatSubmit(event, elements) {
  event.preventDefault();
  if (state.chatBusy) return;

  const message = elements.messageInput.value.trim();
  if (!message) {
    const validationMessage = "Lütfen bir soru yazın.";
    appendChatMessage(elements.chatMessages, validationMessage, "assistant", "error");
    showStatus(elements.answerText, validationMessage, "error");
    elements.messageInput.setAttribute("aria-invalid", "true");
    elements.messageInput.focus();
    return;
  }

  elements.messageInput.removeAttribute("aria-invalid");
  appendChatMessage(elements.chatMessages, message, "user");
  const pendingAnswer = appendChatMessage(
    elements.chatMessages,
    "Yosuun AI yanıt hazırlıyor...",
    "assistant",
    "loading",
  );
  elements.messageInput.value = "";
  setChatBusy(elements, true);

  try {
    const answer = await sohbetGonder(message, state.history);
    rememberConversation(message, answer);
    updateChatMessage(pendingAnswer, answer, "success");
    showStatus(elements.answerText, answer, "success");
  } catch (error) {
    const publicError = getPublicError(error);
    updateChatMessage(pendingAnswer, publicError, "error");
    showStatus(elements.answerText, publicError, "error");
  } finally {
    setChatBusy(elements, false);
    scrollToLatestMessage(elements.chatMessages);
    if (state.activeSlide === 0) elements.messageInput.focus();
  }
}

function appendChatMessage(container, message, role, status = "success") {
  const bubble = document.createElement("div");
  bubble.classList.add("chat-bubble", `chat-bubble--${role}`);
  bubble.dataset.state = status;
  bubble.textContent = message;
  container.append(bubble);
  scrollToLatestMessage(container);
  return bubble;
}

function updateChatMessage(bubble, message, status) {
  bubble.textContent = message;
  bubble.dataset.state = status;
}

function scrollToLatestMessage(container) {
  container.scrollTop = container.scrollHeight;
}

async function handleLeadSubmit(event, elements) {
  event.preventDefault();
  if (state.leadBusy) return;

  const lead = {
    isim: elements.nameInput.value.trim(),
    telefon: elements.phoneInput.value.trim(),
    mesaj: elements.leadMessageInput.value.trim(),
  };

  const validationMessage = validateLead(lead);
  if (validationMessage) {
    showStatus(elements.statusText, validationMessage, "error");
    focusFirstInvalidLeadField(lead, elements);
    return;
  }

  setLeadBusy(elements, true);
  showStatus(elements.statusText, "Bilgileriniz kaydediliyor...", "loading");

  try {
    await leadKaydet(lead);
    elements.leadForm.reset();
    showStatus(
      elements.statusText,
      "Talebiniz alındı. Yosuun ekibi en kısa sürede sizinle iletişime geçecek.",
      "success",
    );
  } catch (error) {
    showStatus(elements.statusText, getPublicError(error), "error");
  } finally {
    setLeadBusy(elements, false);
  }
}

function validateLead(lead) {
  if (!lead.isim) return "Lütfen adınızı ve soyadınızı yazın.";
  if (!lead.telefon) return "Lütfen telefon numaranızı yazın.";
  if (lead.isim.length > 100) return "Ad soyad en fazla 100 karakter olabilir.";
  if (lead.telefon.length > 50) return "Telefon en fazla 50 karakter olabilir.";
  if (lead.mesaj.length > 2000) return "Mesaj en fazla 2000 karakter olabilir.";
  return null;
}

function focusFirstInvalidLeadField(lead, elements) {
  if (!lead.isim) {
    elements.nameInput.focus();
    return;
  }
  if (!lead.telefon) elements.phoneInput.focus();
}

function rememberConversation(message, answer) {
  state.history.push(
    { role: "user", content: message },
    { role: "assistant", content: answer },
  );
  state.history = state.history.slice(-HISTORY_LIMIT);
}

function showStatus(element, message, status) {
  element.textContent = message;
  element.dataset.state = status;
  element.hidden = false;
}

function setChatBusy(elements, isBusy) {
  state.chatBusy = isBusy;
  elements.messageInput.disabled = isBusy;
  elements.askButton.disabled = isBusy;
  elements.askButton.dataset.loading = String(isBusy);
  elements.askButton.setAttribute("aria-label", isBusy ? "Yanıt hazırlanıyor" : "Mesajı gönder");
}

function setLeadBusy(elements, isBusy) {
  state.leadBusy = isBusy;
  elements.nameInput.disabled = isBusy;
  elements.phoneInput.disabled = isBusy;
  elements.leadMessageInput.disabled = isBusy;
  elements.saveLeadButton.disabled = isBusy;
  elements.saveLeadButton.textContent = isBusy ? "Kaydediliyor…" : LEAD_IDLE_LABEL;
}

function getPublicError(error) {
  if (error instanceof ApiError) return error.message;
  return "Beklenmeyen bir hata oluştu. Lütfen tekrar deneyin.";
}
