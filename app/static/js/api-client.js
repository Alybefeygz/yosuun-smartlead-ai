const API_ROOT = "/api";

export class ApiError extends Error {
  constructor(message, { status = 0, code = "REQUEST_FAILED" } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_ROOT}${path}`, {
      ...options,
      headers: {
        Accept: "application/json",
        ...options.headers,
      },
    });
  } catch (_error) {
    throw new ApiError("Sunucuya ulaşılamıyor. Lütfen bağlantınızı kontrol edin.", {
      code: "NETWORK_ERROR",
    });
  }

  const payload = await parseJson(response);
  if (!response.ok || payload.basari !== true) {
    throw new ApiError(
      payload?.hata?.mesaj || "İşlem şu anda tamamlanamadı. Lütfen tekrar deneyin.",
      {
        status: response.status,
        code: payload?.hata?.kod || "REQUEST_FAILED",
      },
    );
  }

  return payload;
}

async function parseJson(response) {
  try {
    return await response.json();
  } catch (_error) {
    throw new ApiError("Sunucu geçerli bir cevap döndürmedi.", {
      status: response.status,
      code: "INVALID_RESPONSE",
    });
  }
}

function jsonRequest(method, body) {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

export async function sohbetGonder(mesaj, gecmis) {
  const payload = await request(
    "/sohbet",
    jsonRequest("POST", { mesaj, gecmis }),
  );
  return payload.cevap;
}

export async function leadKaydet({ isim, telefon, mesaj }) {
  return request(
    "/leads",
    jsonRequest("POST", { isim, telefon, mesaj }),
  );
}

export async function leadleriGetir() {
  const payload = await request("/leads");
  return payload.leads;
}
