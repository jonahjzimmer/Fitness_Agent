import { useState } from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import Chat from './components/Chat'
import Dashboard from './components/Dashboard'
import Login from './components/Login'
import ChatSidebar from './components/ChatSidebar'

export default function App() {
  const [userId, setUserId] = useState(() => localStorage.getItem('userId'))
  const [userName, setUserName] = useState(() => localStorage.getItem('userName') || '')
  const [activeConversationId, setActiveConversationId] = useState(null)

  function handleLogin(id, name) {
    localStorage.setItem('userId', id)
    localStorage.setItem('userName', name)
    setUserId(id)
    setUserName(name)
    setActiveConversationId(null)
  }

  function handleLogout() {
    localStorage.removeItem('userId')
    localStorage.removeItem('userName')
    setUserId(null)
    setUserName('')
    setActiveConversationId(null)
  }

  if (!userId) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3 flex items-center gap-6">
        <span className="text-brand-500 font-bold text-xl tracking-tight">FitAgent</span>
        <nav className="flex gap-4 text-sm flex-1">
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
        <div className="flex items-center gap-3 text-sm">
          <span className="text-gray-400">{userName}</span>
          <button
            onClick={handleLogout}
            className="text-gray-500 hover:text-gray-200 transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="flex-1 flex overflow-hidden">
        <Routes>
          <Route
            path="/"
            element={
              <div className="flex flex-1 overflow-hidden">
                <ChatSidebar
                  userId={userId}
                  activeConversationId={activeConversationId}
                  onSelectConversation={(convo) => setActiveConversationId(convo.id)}
                  onNewChat={(convo) => setActiveConversationId(convo.id)}
                />
                <Chat
                  userId={userId}
                  userName={userName}
                  conversationId={activeConversationId}
                  onConversationCreated={(id) => setActiveConversationId(id)}
                />
              </div>
            }
          />
          <Route path="/dashboard" element={<Dashboard userId={userId} />} />
        </Routes>
      </main>
    </div>
  )
}
