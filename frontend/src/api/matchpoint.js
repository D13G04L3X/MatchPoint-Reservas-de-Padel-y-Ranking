async function parseResponse(response) {
  const text = await response.text()
  const data = text ? JSON.parse(text) : null
  if (!response.ok) {
    const message = data?.detail ?? response.statusText
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data
}

export async function createBooking(payload) {
  const response = await fetch('/bookings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
