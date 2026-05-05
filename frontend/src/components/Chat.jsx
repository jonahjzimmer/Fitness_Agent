import { useState, useRef, useEffect } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''

const INITIAL_MESSAGE = {
  role: 'assistant',
  content: "Hi! I'm FitAgent, your AI health coach. Tell me your fitness goal and I'll build a personalized plan for you.",
}

const SUGGESTIONS = [
  'I want to lose 10 lbs in 3 months, I can work out 4x a week',
  'I had grilled chicken and rice for dinner',
  'Skip leg day today, my knee hurts',
  'How am I tracking toward my goal?',
]

export default function Chat({ userId, userName, conversationId, onConversationCreated }) {
  const [messages, setMessages] = useState([INITIAL_MESSAGE])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    if (!conversationId) {
      setMessages([INITIAL_MESSAGE])
      return
    }

    setHistoryLoading(true)
    axios
      .get(`${API}/chat/conversations/${conversationId}/messages`)
      .then(({ data }) => {
        if (data.length === 0) {
          setMessages([INITIAL_MESSAGE])
        } else {
          setMessages(
            data.map((m) => ({
              role: m.role === 'human' ? 'user' : 'assistant',
              content: m.content,
            }))
          )
        }
      })
      .catch(() => setMessages([INITIAL_MESSAGE]))
      .finally(() => setHistoryLoading(false))
  }, [conversationId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text) {
    const userMsg = text || input.trim()
    if (!userMsg || loading) return
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }])
    setLoading(true)

    try {
      const { data } = await axios.post(`${API}/chat`, {
        user_id: userId,
        message: userMsg,
        name: userName || 'User',
        conversation_id: conversationId || undefined,
      })

      if (!conversationId && data.conversation_id) {
        onConversationCreated(data.conversation_id)
      }

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: data.response, node: data.next_node },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Something went wrong. Please try again.', error: true },
      ])
    } finally {
      setLoading(false)
    }
  }

  if (historyLoading) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-400 text-sm">
        Loading conversation...
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 p-4 gap-4 h-[calc(100vh-57px)] overflow-hidden">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto flex flex-col gap-3 pr-1">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                msg.role === 'user'
                  ? 'bg-brand-600 text-white rounded-br-sm'
                  : msg.error
                  ? 'bg-red-50 text-red-600 rounded-bl-sm'
                  : 'bg-gray-100 text-gray-900 rounded-bl-sm'
              }`}
            >
              {msg.content}
              {msg.node && (
                <span className="block mt-1 text-xs text-gray-400">
                  [{msg.node}]
                </span>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-gray-500">
              <span className="animate-pulse">Thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestion chips — only show at start */}
      {messages.length === 1 && (
        <div className="flex flex-wrap gap-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => sendMessage(s)}
              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full px-3 py-1.5 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault()
          sendMessage()
        }}
        className="flex gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message FitAgent..."
          className="flex-1 bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-brand-500 transition-colors"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="bg-brand-600 hover:bg-brand-700 disabled:bg-gray-200 disabled:text-gray-400 text-white rounded-xl px-5 py-3 text-sm font-medium transition-colors"
        >
          Send
        </button>
      </form>
    </div>
  )
}
