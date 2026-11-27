let activeToken = null
if (typeof window !== "undefined") {
  try { activeToken = window.localStorage.getItem("strokespeak_access_token") } catch {}
}

export function getAuthToken() {
  return activeToken
}

export function setAuthToken(token) {
  activeToken = token
  if (typeof window !== "undefined") {
    try {
      if (token) window.localStorage.setItem("strokespeak_access_token", token)
      else window.localStorage.removeItem("strokespeak_access_token")
    } catch {}
  }
}

export function clearAuthToken() {
  setAuthToken(null)
}

const API_BASE_URL = (import.meta.env?.VITE_API_BASE_URL || "").replace(/\/+$/, "")

function resolveApiInput(input) {
  if (typeof input === "string" && API_BASE_URL && input.startsWith("/")) {
    return `${API_BASE_URL}${input}`
  }
  return input
}

export async function apiFetch(input, options = {}) {
  const headers = new Headers(options.headers || {})
  const token = getAuthToken()
  if (token) headers.set("Authorization", `Bearer ${token}`)
  const target = resolveApiInput(input)
  const response = await fetch(target, { ...options, headers })
  const path = typeof input === "string" ? input : input.url
  if (response.status === 401 && token && !path.includes("/auth/")) {
    clearAuthToken()
    if (typeof window !== "undefined") window.dispatchEvent(new Event("strokespeak:unauthorized"))
  }
  return response
}
