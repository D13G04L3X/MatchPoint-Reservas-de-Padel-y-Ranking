const ERROR_MESSAGES = {
  'Value error, start_time must be in the future.': 'No puedes reservar en una fecha u hora pasada.',
  'start_time must be in the future.': 'No puedes reservar en una fecha u hora pasada.',
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

  if (item.msg?.includes('start_time must be in the future')) {
    return 'No puedes reservar en una fecha u hora pasada.'
  }
  if (loc.includes('team_local_ids') && item.type === 'missing') {
    return 'Debes ingresar el equipo local.'
  }
  if (item.msg?.includes('Local team must have exactly 2 players')) {
    return 'El equipo local debe tener exactamente 2 jugadores.'
  }
  if (item.msg?.includes('Organizer must be in local team')) {
    return 'El organizador debe estar en el equipo local.'
  }
  if (item.msg?.includes('Local team has duplicate players')) {
    return 'El equipo local no puede tener jugadores repetidos.'
  }
  if (item.msg?.includes('Ranked bookings require a visiting team')) {
    return 'En ranking debes agregar el equipo visita.'
  }
  if (item.msg?.includes('Visiting team must have exactly 2 players')) {
    return 'El equipo visita debe tener exactamente 2 jugadores.'
  }
  if (item.msg?.includes('Visiting team has duplicate players')) {
    return 'El equipo visita no puede tener jugadores repetidos.'
  }
  if (item.msg?.includes('Players cannot be in both teams')) {
    return 'Un jugador no puede estar en ambos equipos.'
  }
  if (item.msg?.includes('Casual bookings must not include a visiting team')) {
    return 'En casual no debes enviar equipo visita.'
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
