import React from 'react'
import './DateRangePicker.css'

function DateRangePicker({ startDate, endDate, onStartDateChange, onEndDateChange }) {
  const formatDate = (date) => {
    if (!date) return ''
    const d = new Date(date)
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    return `${year}-${month}-${day}`
  }

  const handleStartChange = (e) => {
    onStartDateChange(new Date(e.target.value))
  }

  const handleEndChange = (e) => {
    onEndDateChange(new Date(e.target.value))
  }

  return (
    <div className="date-range-picker">
      <div className="date-input-group">
        <label>Başlangıç:</label>
        <input
          type="date"
          value={formatDate(startDate)}
          onChange={handleStartChange}
          max={formatDate(endDate)}
          className="date-input"
        />
      </div>
      <div className="date-input-group">
        <label>Bitiş:</label>
        <input
          type="date"
          value={formatDate(endDate)}
          onChange={handleEndChange}
          min={formatDate(startDate)}
          max={formatDate(new Date())}
          className="date-input"
        />
      </div>
    </div>
  )
}

export default DateRangePicker
