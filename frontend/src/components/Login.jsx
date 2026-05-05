import { useState, useEffect } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''

export default function Login({ onLogin }) {
  const [users, setUsers] = useState([])
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [fetchError, setFetchError] = useState(null)

  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [createError, setCreateError] = useState(null)

  useEffect(() => {
    axios
      .get(`${API}/users`)
      .then(({ data }) => setUsers(data))
      .catch(() => setFetchError('Could not load profiles. Is the backend running?'))
      .finally(() => setLoadingUsers(false))
  }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setCreateError(null)
    setSubmitting(true)
    try {
      const { data } = await axios.post(`${API}/users`, { name: name.trim(), email: email.trim() })
      onLogin(data.id, data.name)
    } catch (err) {
      const detail = err.response?.data?.detail
      setCreateError(detail === 'Email already in use' ? 'That email is already taken.' : 'Something went wrong. Try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (showCreate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <span className="text-brand-500 font-bold text-3xl tracking-tight">FitAgent</span>
            <p className="text-gray-500 mt-2 text-sm">Create an account</p>
          </div>

          <form onSubmit={handleCreate} className="flex flex-col gap-4">
            <input
              type="text"
              placeholder="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-brand-500 transition-colors"
            />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-brand-500 transition-colors"
            />
            {createError && <p className="text-red-500 text-sm">{createError}</p>}
            <button
              type="submit"
              disabled={submitting || !name.trim() || !email.trim()}
              className="bg-brand-600 hover:bg-brand-700 disabled:bg-gray-200 disabled:text-gray-400 text-white rounded-xl px-5 py-3 text-sm font-medium transition-colors"
            >
              {submitting ? 'Creating…' : 'Create account'}
            </button>
          </form>

          <button
            onClick={() => { setShowCreate(false); setCreateError(null) }}
            className="mt-5 w-full text-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            ← Back to profiles
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <span className="text-brand-500 font-bold text-3xl tracking-tight">FitAgent</span>
          <p className="text-gray-500 mt-2 text-sm">Select a profile to continue</p>
        </div>

        {loadingUsers && (
          <p className="text-center text-gray-400 text-sm animate-pulse">Loading profiles...</p>
        )}

        {fetchError && (
          <p className="text-center text-red-500 text-sm">{fetchError}</p>
        )}

        {!loadingUsers && !fetchError && (
          <>
            {users.length === 0 ? (
              <p className="text-center text-gray-400 text-sm mb-6">No profiles yet. Create one below.</p>
            ) : (
              <div className="flex flex-col gap-3 mb-6">
                {users.map((user) => (
                  <button
                    key={user.id}
                    onClick={() => onLogin(user.id, user.name)}
                    className="w-full bg-white hover:bg-gray-50 border border-gray-200 hover:border-brand-600 rounded-xl px-5 py-4 text-left transition-colors group"
                  >
                    <div className="font-medium text-gray-900 group-hover:text-brand-500 transition-colors">
                      {user.name}
                    </div>
                    <div className="text-sm text-gray-500 mt-0.5">{user.email}</div>
                  </button>
                ))}
              </div>
            )}

            <button
              onClick={() => setShowCreate(true)}
              className="w-full text-center text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              + Create account
            </button>
          </>
        )}
      </div>
    </div>
  )
}
