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
