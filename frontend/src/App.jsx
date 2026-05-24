import { useState } from 'react'
import BookingForm from './components/BookingForm'
import BookingDetail from './components/BookingDetail'
import RankingList from './components/RankingList'
import './App.css'

const TABS = [
  { id: 'booking', label: 'Reservar' },
  { id: 'my-bookings', label: 'Mis reservas' },
  { id: 'ranking', label: 'Ranking' },
]

export default function App() {
  const [tab, setTab] = useState('booking')

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

      <main>
        {tab === 'booking' && <BookingForm />}
        {tab === 'my-bookings' && <BookingDetail />}
        {tab === 'ranking' && <RankingList />}
      </main>
    </div>
  )
}
