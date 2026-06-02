async function parseResponse(response) {
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    const message = data?.detail ?? response.statusText
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data
}

function headers(xUserId) {
  const h = { 'Content-Type': 'application/json' }
  if (xUserId) h['X-User-Id'] = xUserId
  return h
}

export async function getPlayers() {
  const response = await fetch('/identity/players')
  return parseResponse(response)
}

export async function createBooking(payload, xUserId) {
  const response = await fetch('/bookings', {
    method: 'POST',
    headers: headers(xUserId),
    body: JSON.stringify(payload),
  })
  return parseResponse(response)
}

export async function getBooking(bookingId) {
  const response = await fetch(`/bookings/${bookingId}`)
  return parseResponse(response)
}

export async function cancelBooking(bookingId, playerId) {
  const response = await fetch(
    `/bookings/${bookingId}?player_id=${encodeURIComponent(playerId)}`,
    { method: 'DELETE' },
  )
  return parseResponse(response)
}

export async function getCourts() {
  const response = await fetch('/courts')
  return parseResponse(response)
}

export async function listBookingsByDate(date, { playerId, includeCancelled = false } = {}) {
  const params = new URLSearchParams({ date })
  if (playerId) {
    params.set('player_id', playerId)
  }
  if (includeCancelled) {
    params.set('include_cancelled', 'true')
  }
  const response = await fetch(`/bookings/by-date?${params}`)
  return parseResponse(response)
}

export async function getCourtsAvailability(date) {
  const params = new URLSearchParams({ date })
  const response = await fetch(`/courts/availability?${params}`)
  return parseResponse(response)
}

export async function getCourtAvailability(courtId, date) {
  const params = new URLSearchParams({ date })
  const response = await fetch(`/courts/${courtId}/availability?${params}`)
  return parseResponse(response)
}

export async function getRanking() {
  const response = await fetch('/penalty/ranking')
  return parseResponse(response)
}

export async function getPlayerRank(playerId) {
  const response = await fetch(`/penalty/internal/rank/${playerId}`)
  return parseResponse(response)
}

export async function getPlayerBookings(playerId) {
  const response = await fetch(`/internal/bookings/player/${playerId}`)
  return parseResponse(response)
}

export async function getPlayerPenalties(playerId) {
  const response = await fetch(`/penalty/penalties/${playerId}`)
  return parseResponse(response)
}
