import React from 'react'
import './ShiftSelector.css'

function ShiftSelector({ selectedShift, onShiftChange }) {
  const shifts = [
    { value: null, label: 'Tüm Vardiyalar' },
    { value: 1, label: 'Sabah (08:00-16:00)' },
    { value: 2, label: 'Akşam (16:00-00:00)' },
    { value: 3, label: 'Gece (00:00-08:00)' }
  ]

  return (
    <div className="shift-selector">
      <label>Vardiya:</label>
      <select 
        value={selectedShift || ''} 
        onChange={(e) => onShiftChange(e.target.value ? parseInt(e.target.value) : null)}
        className="shift-select"
      >
        {shifts.map((shift) => (
          <option key={shift.label} value={shift.value || ''}>
            {shift.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default ShiftSelector
