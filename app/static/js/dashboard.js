import { ApiError, leadleriGetir } from "./api-client.js";

const dateFormatter = new Intl.DateTimeFormat("tr-TR", {
  dateStyle: "medium",
  timeStyle: "short",
});

let requestInProgress = false;

document.addEventListener("DOMContentLoaded", initializeDashboard);

function initializeDashboard() {
  const elements = getElements();
  elements.refreshButton.addEventListener("click", () => loadLeads(elements));
  loadLeads(elements);
}

function getElements() {
  return {
    leadList: document.querySelector("#leadList"),
    leadRowTemplate: document.querySelector("#leadRowTemplate"),
    leadCount: document.querySelector("#leadCount"),
    refreshButton: document.querySelector("#refreshButton"),
    dashboardStatus: document.querySelector("#dashboardStatus"),
  };
}

async function loadLeads(elements) {
  if (requestInProgress) return;

  setLoading(elements, true);
  showStatus(elements.dashboardStatus, "Lead'ler yükleniyor...", "loading");

  try {
    const leads = await leadleriGetir();
    renderLeads(leads, elements);
  } catch (error) {
    elements.leadList.replaceChildren();
    elements.leadCount.textContent = "Liste alınamadı";
    showStatus(elements.dashboardStatus, getPublicError(error), "error");
  } finally {
    setLoading(elements, false);
  }
}

function renderLeads(leads, elements) {
  elements.leadList.replaceChildren();
  elements.leadCount.textContent = `${leads.length} kayıt`;

  if (leads.length === 0) {
    showStatus(elements.dashboardStatus, "Henüz bir iletişim talebi bulunmuyor.", "success");
    return;
  }

  const fragment = document.createDocumentFragment();
  leads.forEach((lead) => fragment.append(createLeadCard(lead, elements.leadRowTemplate)));
  elements.leadList.append(fragment);
  showStatus(elements.dashboardStatus, `${leads.length} iletişim talebi listelendi.`, "success");
}

function createLeadCard(lead, template) {
  const card = template.content.firstElementChild.cloneNode(true);
  const name = normalizeText(lead.isim, "İsimsiz");
  const phone = normalizeText(lead.telefon, "Telefon belirtilmedi");
  const message = normalizeText(lead.mesaj, "Mesaj bırakılmadı.");

  setText(card, "initial", getInitial(name));
  setText(card, "name", name);
  setText(card, "phone", phone);
  setText(card, "message", message);

  const phoneLink = card.querySelector('[data-field="phone"]');
  phoneLink.href = `tel:${toTelephoneHref(phone)}`;

  const time = card.querySelector('[data-field="date"]');
  time.textContent = formatDate(lead.tarih);
  time.dateTime = normalizeText(lead.tarih, "");

  return card;
}

function setText(container, field, value) {
  container.querySelector(`[data-field="${field}"]`).textContent = value;
}

function normalizeText(value, fallback) {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function getInitial(name) {
  return name.charAt(0).toLocaleUpperCase("tr-TR");
}

function toTelephoneHref(phone) {
  return phone.replace(/[^+\d]/g, "");
}

function formatDate(rawDate) {
  if (typeof rawDate !== "string" || !rawDate.trim()) return "Tarih yok";
  const normalized = rawDate.includes("T") ? rawDate : `${rawDate.replace(" ", "T")}Z`;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? rawDate : dateFormatter.format(date);
}

function showStatus(element, message, status) {
  element.textContent = message;
  element.dataset.state = status;
  element.hidden = false;
}

function setLoading(elements, isLoading) {
  requestInProgress = isLoading;
  elements.leadList.setAttribute("aria-busy", String(isLoading));
  elements.refreshButton.disabled = isLoading;
  elements.refreshButton.classList.toggle("is-loading", isLoading);
}

function getPublicError(error) {
  if (error instanceof ApiError) return error.message;
  return "Lead listesi alınamadı. Lütfen tekrar deneyin.";
}
