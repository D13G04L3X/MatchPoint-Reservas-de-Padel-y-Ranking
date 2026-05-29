const KEY = 'matchpoint'

export function loadSession() {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function saveSession(partial) {
  sessionStorage.setItem(KEY, JSON.stringify({ ...loadSession(), ...partial }))
}
