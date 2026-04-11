import { useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'

// In a real app this would come from auth; for demo we use a fixed ID
const USER_ID = 'demo-user-1'

const INITIAL_MESSAGES = [
  {
    role: 'assistant',
    content: "Hi! I'm FitAgent, your AI health coach. Tell me your fitness goal and I'll build a personalized plan for you.",
  },
]

export default function App() {
  const [messages, setMessages] = useState(INITIAL_MESSAGES)

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
        <span className="text-brand-500 font-bold text-xl tracking-tight">FitAgent</span>
        <nav className="flex gap-4 text-sm">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              isActive ? 'text-brand-500 font-medium' : 'text-gray-400 hover:text-gray-200'
            }
          >
            Chat
          </NavLink>
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              isActive ? 'text-brand-500 font-medium' : 'text-gray-400 hover:text-gray-200'
            }
          >
            Dashboard
          </NavLink>
        </nav>
      </header>

      <main className="flex-1 flex">
        <Routes>
          <Route path="/" element={<Chat userId={USER_ID} messages={messages} setMessages={setMessages} />} />
          <Route path="/dashboard" element={<Dashboard userId={USER_ID} />} />
        </Routes>
      </main>
    </div>
  )
}
