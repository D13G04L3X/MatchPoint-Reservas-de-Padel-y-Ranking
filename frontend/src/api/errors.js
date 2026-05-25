const ERROR_MESSAGES = {
  'Premium slot requires active membership.': 'Necesitas membresía activa para horario premium.',
  'Player is restricted from premium slots due to low reliability penalty.':
    'No puedes reservar horario premium por una penalización activa.',
  'Ranked player level difference exceeds 2.0.':
    'Los jugadores tienen niveles muy distintos para este tipo de partido.',
  'Booking not found.': 'No encontramos esa reserva.',
  'Court not found.': 'La cancha seleccionada no existe o está inactiva.',
  'Booking does not belong to the player.': 'Esta reserva no pertenece a ese jugador.',
  'Booking overlaps with an existing reservation.': 'Ese horario ya está ocupado.',
  'Value error, end_time must be after start_time.': 'La hora de fin debe ser posterior a la de inicio.',
}

function messageFromValidationItem(item) {
  if (!item || typeof item !== 'object') return null

  const loc = Array.isArray(item.loc) ? item.loc.join('.') : ''

  if (loc.includes('guest_player_ids') && item.type === 'too_long') {
    return 'Máximo 3 compañeros por reserva (sin contar al jugador principal).'
  }
  if (item.msg?.includes('end_time must be after start_time')) {
    return ERROR_MESSAGES['Value error, end_time must be after start_time.']
  }
  if (typeof item.msg === 'string') return item.msg

  return null
}

export function userFacingError(message) {
  if (message.includes('MS-') || message.includes('unavailable') || message.includes('503')) {
    return 'El servicio no está disponible. Verifica que Docker esté corriendo.'
  }

  if (ERROR_MESSAGES[message]) return ERROR_MESSAGES[message]

  try {
    const parsed = JSON.parse(message)
    if (Array.isArray(parsed)) {
      for (const item of parsed) {
        const friendly = messageFromValidationItem(item)
        if (friendly) return friendly
      }
    }
  } catch {
    // not JSON validation payload
  }

  return message
}
