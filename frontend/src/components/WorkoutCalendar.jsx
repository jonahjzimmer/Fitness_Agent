import { useState } from 'react'

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]

function buildIso(year, month, day) {
  return `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
}

function DayDetailModal({ isoDate, workouts, onClose }) {
  return (
    <div
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div
        className="bg-gray-900 border border-gray-700 rounded-2xl p-6 w-full max-w-md mx-4 max-h-[80vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-base font-semibold text-gray-100">Workouts — {isoDate}</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-200 text-lg leading-none">✕</button>
        </div>

        {workouts.length === 0 ? (
          <p className="text-gray-500 text-sm">No workout details recorded.</p>
        ) : (
          <div className="flex flex-col gap-4">
            {workouts.map((w, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-4">
                <div className="flex justify-between items-start mb-2">
                  <p className="font-semibold text-brand-500">{w.type || 'Workout'}</p>
                  {w.duration_min && (
                    <span className="text-xs text-gray-500">{w.duration_min} min</span>
                  )}
                </div>
                {w.exercises_completed?.length > 0 && (
                  <ul className="flex flex-col gap-1 mt-1">
                    {w.exercises_completed.map((ex, j) => (
                      <li key={j} className="text-xs text-gray-400">
                        • {typeof ex === 'string' ? ex : ex.name || JSON.stringify(ex)}
                      </li>
                    ))}
                  </ul>
                )}
                {w.notes && (
                  <p className="text-xs text-gray-600 mt-2 italic">{w.notes}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function WorkoutCalendar({ calendarData, currentYear, currentMonth, onMonthChange }) {
  const [selectedDay, setSelectedDay] = useState(null)

  const now = new Date()
  const isCurrentMonth =
    currentYear > now.getFullYear() ||
    (currentYear === now.getFullYear() && currentMonth >= now.getMonth() + 1)

  const todayIso = buildIso(now.getFullYear(), now.getMonth() + 1, now.getDate())

  const firstDayOfMonth = new Date(currentYear, currentMonth - 1, 1)
  const daysInMonth = new Date(currentYear, currentMonth, 0).getDate()
  // Monday-first: getDay() Sun=0..Sat=6 → offset Mon=0..Sun=6
  const startOffset = (firstDayOfMonth.getDay() + 6) % 7

  const dataByDate = {}
  calendarData.forEach((d) => { dataByDate[d.date] = d })

  function handlePrev() {
    if (currentMonth === 1) onMonthChange(currentYear - 1, 12)
    else onMonthChange(currentYear, currentMonth - 1)
  }

  function handleNext() {
    if (isCurrentMonth) return
    if (currentMonth === 12) onMonthChange(currentYear + 1, 1)
    else onMonthChange(currentYear, currentMonth + 1)
  }

  return (
    <div className="bg-gray-800 rounded-2xl p-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={handlePrev}
          className="text-gray-400 hover:text-gray-200 px-3 py-1 rounded-lg hover:bg-gray-700 transition-colors"
        >
          ‹
        </button>
        <h3 className="text-sm font-semibold text-gray-300">
          {MONTH_NAMES[currentMonth - 1]} {currentYear}
        </h3>
        <button
          onClick={handleNext}
          disabled={isCurrentMonth}
          className="text-gray-400 hover:text-gray-200 px-3 py-1 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-30 disabled:cursor-default"
        >
          ›
        </button>
      </div>

      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 mb-1">
        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
          <div key={d} className="text-center text-xs text-gray-600 pb-1">{d}</div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {/* Leading blank cells */}
        {Array.from({ length: startOffset }).map((_, i) => (
          <div key={`blank-${i}`} />
        ))}

        {/* Day cells */}
        {Array.from({ length: daysInMonth }, (_, i) => i + 1).map((day) => {
          const iso = buildIso(currentYear, currentMonth, day)
          const dayData = dataByDate[iso]
          const isToday = iso === todayIso

          return (
            <button
              key={day}
              onClick={() => dayData && setSelectedDay({ isoDate: iso, workouts: dayData.workouts })}
              className={[
                'relative flex flex-col items-center justify-start pt-1 rounded-lg h-10 text-xs font-medium transition-colors',
                isToday ? 'ring-1 ring-brand-500' : '',
                dayData
                  ? 'bg-brand-700/20 hover:bg-brand-700/40 cursor-pointer text-brand-500'
                  : 'text-gray-600 cursor-default',
              ].join(' ')}
            >
              <span>{day}</span>
              {dayData && (
                <span className="mt-0.5 bg-brand-500 text-gray-950 text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center">
                  {dayData.workout_count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Modal */}
      {selectedDay && (
        <DayDetailModal
          isoDate={selectedDay.isoDate}
          workouts={selectedDay.workouts}
          onClose={() => setSelectedDay(null)}
        />
      )}
    </div>
  )
}
