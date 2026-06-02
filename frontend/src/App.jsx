import { useEffect, useState } from 'react'
import BookingForm from './components/BookingForm'
import BookingDetail from './components/BookingDetail'
import RankingList from './components/RankingList'
import { getPlayers } from './api/matchpoint'
import { loadActiveUserId, saveActiveUserId } from './utils/session'
import './App.css'

const TABS = [
  { id: 'booking', label: 'Reservar' },
  { id: 'my-bookings', label: 'Reservas del día' },
  { id: 'ranking', label: 'Ranking' },
]

export default function App() {
  const [tab, setTab] = useState('booking')
  const [players, setPlayers] = useState([])
  const [playersLoading, setPlayersLoading] = useState(true)
  const [activeUserId, setActiveUserId] = useState(null)

  const playerMap = {}
  for (const p of players) playerMap[p.id] = p.username

  useEffect(() => {
    getPlayers()
      .then((data) => {
        setPlayers(data)
        const stored = loadActiveUserId()
        if (stored && data.some((p) => p.id === stored)) {
          setActiveUserId(stored)
        } else if (data.length > 0) {
          setActiveUserId(data[0].id)
        }
      })
      .catch(() => {})
      .finally(() => setPlayersLoading(false))
  }, [])

  useEffect(() => {
    if (activeUserId) saveActiveUserId(activeUserId)
  }, [activeUserId])

  function goToMyBookings() {
    setTab('my-bookings')
  }

  const noPlayers = !playersLoading && players.length === 0

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">MatchPoint</p>
          <h1>Reservas de pádel</h1>
        </div>
        <nav className="tabs">
          {TABS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={tab === item.id ? 'tab active' : 'tab'}
              onClick={() => setTab(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </header>

      <div className="seeder-bar">
        <span className="seeder-label">Jugador activo:</span>
        {playersLoading && <span className="hint">Cargando jugadores…</span>}
        {noPlayers && <span className="hint">No hay jugadores disponibles.</span>}
        {!playersLoading &&
          players.map((player) => (
            <button
              key={player.id}
              type="button"
              className={
                player.id === activeUserId ? 'seeder-btn active' : 'seeder-btn'
              }
              onClick={() => setActiveUserId(player.id)}
            >
              {player.username}
            </button>
          ))}
      </div>

      <main>
        {tab === 'booking' && (
          <BookingForm
            players={players}
            activeUserId={activeUserId}
            onViewBooking={goToMyBookings}
          />
        )}
        {tab === 'my-bookings' && (
          <BookingDetail activeUserId={activeUserId} playerMap={playerMap} />
        )}
        {tab === 'ranking' && <RankingList />}
      </main>
    </div>
  )
}
