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

export function loadActiveUserId() {
  return loadSession().activeUserId ?? null
}

export function saveActiveUserId(userId) {
  saveSession({ activeUserId: userId })
}
