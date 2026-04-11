import { useEffect, useState } from 'react'
import axios from 'axios'

const API = import.meta.env.VITE_API_URL || ''

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

function StatCard({ label, value, sub, color = 'text-brand-500' }) {
  return (
    <div className="bg-gray-800 rounded-2xl p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value ?? '—'}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function CalorieRing({ calories, target }) {
  const pct = target ? Math.min((calories / target) * 100, 100) : 0
  const r = 38
  const circ = 2 * Math.PI * r
  const dash = (pct / 100) * circ

  return (
    <div className="bg-gray-800 rounded-2xl p-4 flex flex-col items-center gap-2">
      <p className="text-xs text-gray-500 uppercase tracking-wide">Calories Today</p>
      <svg width="100" height="100" className="-rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#1f2937" strokeWidth="10" />
        <circle
          cx="50"
          cy="50"
          r={r}
          fill="none"
          stroke="#16a34a"
          strokeWidth="10"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
        />
      </svg>
      <div className="-mt-2 text-center">
        <p className="text-xl font-bold text-brand-500">{calories}</p>
        <p className="text-xs text-gray-500">of {target || '?'} kcal</p>
      </div>
    </div>
  )
}

export default function Dashboard({ userId }) {
  const [data, setData] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/users/${userId}/progress`),
      axios.get(`${API}/users/${userId}/logs`),
    ])
      .then(([prog, logsRes]) => {
        setData(prog.data)
        setLogs(logsRes.data)
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [userId])

  if (loading) return <div className="m-auto text-gray-500 text-sm">Loading dashboard...</div>
  if (error) return (
    <div className="m-auto text-red-400 text-sm">
      No data yet — start chatting to build your plan!
    </div>
  )

  const goal = data?.user?.goal || {}
  const today = data?.today || {}
  const summary = data?.weekly_summary || {}
  const workoutPlan = data?.current_plan?.workout_plan || {}

  return (
    <div className="w-full max-w-4xl mx-auto p-6 flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-gray-100">Dashboard</h1>
        <p className="text-sm text-gray-500">{data?.user?.name}</p>
      </div>

      {/* Goal banner */}
      {goal.description && (
        <div className="bg-brand-700/20 border border-brand-700/40 rounded-2xl p-4">
          <p className="text-sm text-brand-500 font-medium">Current Goal</p>
          <p className="text-gray-200 mt-1">{goal.description}</p>
          <div className="flex gap-4 mt-2 text-xs text-gray-400">
            {goal.timeline_weeks && <span>{goal.timeline_weeks} week program</span>}
            {goal.workouts_per_week && <span>{goal.workouts_per_week}x/week workouts</span>}
            {goal.daily_calorie_target && <span>{goal.daily_calorie_target} kcal/day target</span>}
          </div>
          {data?.goal_progress_pct != null && (
            <div className="mt-3">
              <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>Goal Progress</span>
                <span>{data.goal_progress_pct}%</span>
              </div>
              <div className="h-2 bg-gray-700 rounded-full">
                <div
                  className="h-2 bg-brand-500 rounded-full transition-all"
                  style={{ width: `${data.goal_progress_pct}%` }}
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Today's stats */}
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Today</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <CalorieRing calories={today.calories || 0} target={goal.daily_calorie_target} />
          <StatCard
            label="Protein"
            value={`${today.macros?.protein || 0}g`}
            sub={goal.daily_protein_target_g ? `of ${goal.daily_protein_target_g}g target` : null}
          />
          <StatCard label="Meals Logged" value={today.meals_logged || 0} />
          <StatCard label="Workouts Logged" value={today.workouts_logged || 0} />
        </div>
      </div>

      {/* Weekly log */}
      {logs.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
            Recent Days
          </h2>
          <div className="bg-gray-800 rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-700 text-gray-500 text-xs uppercase">
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-right px-4 py-3">Calories</th>
                  <th className="text-right px-4 py-3">Protein</th>
                  <th className="text-right px-4 py-3">Meals</th>
                  <th className="text-right px-4 py-3">Workouts</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log) => (
                  <tr key={log.date} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="px-4 py-3 text-gray-300">{log.date}</td>
                    <td className="px-4 py-3 text-right text-brand-500">{log.calories}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{log.macros?.protein || 0}g</td>
                    <td className="px-4 py-3 text-right text-gray-400">{log.meals_count}</td>
                    <td className="px-4 py-3 text-right text-gray-400">{log.workouts_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Weekly workout plan */}
      {Object.keys(workoutPlan).length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">
            This Week's Workout Plan
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {DAYS.map((day) => {
              const dayPlan = workoutPlan[day]
              if (!dayPlan) return null
              const isRest = !dayPlan.exercises || dayPlan.exercises.length === 0
              return (
                <div
                  key={day}
                  className={`rounded-2xl p-4 ${isRest ? 'bg-gray-800/50' : 'bg-gray-800'}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-gray-400 uppercase">{day}</p>
                    {!isRest && (
                      <span className="text-xs bg-brand-700/30 text-brand-500 px-2 py-0.5 rounded-full">
                        {dayPlan.exercises.length} exercises
                      </span>
                    )}
                  </div>
                  <p className={`text-sm font-medium ${isRest ? 'text-gray-600' : 'text-gray-200'}`}>
                    {dayPlan.focus}
                  </p>
                  {!isRest && (
                    <ul className="mt-2 flex flex-col gap-1">
                      {dayPlan.exercises.slice(0, 3).map((ex, i) => (
                        <li key={i} className="text-xs text-gray-500">
                          {ex.name} — {ex.sets}×{ex.reps}
                        </li>
                      ))}
                      {dayPlan.exercises.length > 3 && (
                        <li className="text-xs text-gray-600">
                          +{dayPlan.exercises.length - 3} more
                        </li>
                      )}
                    </ul>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {!goal.description && Object.keys(workoutPlan).length === 0 && (
        <div className="text-center py-16 text-gray-600">
          <p className="text-lg mb-2">No plan yet</p>
          <p className="text-sm">
            Head to the Chat tab and tell FitAgent your fitness goal to get started.
          </p>
        </div>
      )}
    </div>
  )
}
