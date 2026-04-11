import { useEffect, useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''

export default function ChatSidebar({ userId, activeConversationId, onSelectConversation, onNewChat }) {
  const [conversations, setConversations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    axios
      .get(`${API}/chat/conversations`, { params: { user_id: userId } })
      .then(({ data }) => setConversations(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [userId, activeConversationId])

  async function handleNewChat() {
    try {
      const { data } = await axios.post(`${API}/chat/conversations`, { user_id: userId })
      onNewChat(data)
    } catch {
      // silently fail
    }
  }

  return (
    <aside className="w-64 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      <div className="p-3 border-b border-gray-800">
        <button
          onClick={handleNewChat}
          className="w-full bg-brand-600 hover:bg-brand-700 text-white rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {loading && (
          <p className="text-center text-gray-600 text-xs py-4 animate-pulse">Loading...</p>
        )}
        {!loading && conversations.length === 0 && (
          <p className="text-center text-gray-600 text-xs py-4">No conversations yet</p>
        )}
        {conversations.map((convo) => (
          <button
            key={convo.id}
            onClick={() => onSelectConversation(convo)}
            className={`w-full text-left px-3 py-3 text-sm transition-colors rounded-lg mx-1 ${
              convo.id === activeConversationId
                ? 'bg-gray-800 text-gray-100'
                : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200'
            }`}
            style={{ width: 'calc(100% - 8px)' }}
          >
            <div className="truncate font-medium">{convo.title}</div>
            <div className="text-xs text-gray-600 mt-0.5">
              {new Date(convo.updated_at).toLocaleDateString()}
            </div>
          </button>
        ))}
      </div>
    </aside>
  )
}
