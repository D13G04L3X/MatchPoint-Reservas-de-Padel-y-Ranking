const STATUS_LABELS = {
  PENDING: 'Pendiente',
  CANCELLED_EARLY: 'Cancelada',
  CANCELLED_LATE: 'Cancelada con aviso corto',
}

export function formatDateTime(iso) {
  return new Date(iso).toLocaleString('es-CO', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

export function formatStatus(status) {
  return STATUS_LABELS[status] ?? status
}

export function formatYesNo(value) {
  return value ? 'Sí' : 'No'
}

export function formatCourtName(courtId, courtNames = null) {
  if (courtNames && courtNames[courtId]) {
    return courtNames[courtId]
  }

  const fallback = {
    'a1a1a1a1-a1a1-4111-a111-000000000001': 'Cancha 1',
    'a1a1a1a1-a1a1-4111-a111-000000000002': 'Cancha 2',
    'a1a1a1a1-a1a1-4111-a111-000000000003': 'Cancha 3',
  }

  return fallback[courtId] ?? 'Cancha no registrada'
}

export function buildCourtNameMap(courts) {
  if (!Array.isArray(courts)) return {}
  return Object.fromEntries(courts.map((court) => [court.id, court.name]))
}

export function formatTimeRange(startIso, endIso) {
  return `${formatTime(startIso)} – ${formatTime(endIso)}`
}

export function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('es-CO', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

export function toDateInputValue(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function toDatetimeLocal(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function shiftDatetimeLocalToDate(value, dateStr) {
  if (!value || !dateStr) return value
  const [year, month, day] = dateStr.split('-').map(Number)
  const current = new Date(value)
  const shifted = new Date(year, month - 1, day, current.getHours(), current.getMinutes(), 0, 0)
  return toDatetimeLocal(shifted)
}
