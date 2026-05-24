const ERROR_MESSAGES = {
  'Premium slot requires active membership.': 'Necesitas membresía activa para horario premium.',
  'Ranked player level difference exceeds 2.0.':
    'Los jugadores tienen niveles muy distintos para este tipo de partido.',
  'Booking not found.': 'No encontramos esa reserva.',
  'Booking does not belong to the player.': 'Esta reserva no pertenece a ese jugador.',
  'Booking overlaps with an existing reservation.': 'Ese horario ya está ocupado.',
}

export function userFacingError(message) {
  return ERROR_MESSAGES[message] ?? message
}
