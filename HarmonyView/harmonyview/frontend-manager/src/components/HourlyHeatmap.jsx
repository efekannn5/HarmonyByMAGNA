import React from 'react'
import './HourlyHeatmap.css'

function HourlyHeatmap({ data }) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <div className="hourly-heatmap">
        <p className="no-data">Saatlik aktivite verisi bulunamadı</p>
      </div>
    )
  }

  const hours = Array.from({ length: 24 }, (_, i) => i)
  const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi']
  
  // Create a map for quick lookup
  const dataMap = new Map()
  data.forEach(cell => {
    const key = `${cell.day_of_week}-${cell.hour_of_day}`
    dataMap.set(key, cell.dolly_count)
  })
  
  // Find max for intensity calculation
  const maxCount = Math.max(...data.map(d => d.dolly_count), 1)
  const minCount = Math.min(...data.map(d => d.dolly_count), 0)
  const avgCount = data.length > 0 ? data.reduce((sum, d) => sum + d.dolly_count, 0) / data.length : 0
  
  const getIntensityColor = (intensity) => {
    if (intensity === 0) return '#f0f0f0'
    if (intensity < 20) return '#fee2e2'
    if (intensity < 40) return '#fecaca'
    if (intensity < 60) return '#fca5a5'
    if (intensity < 80) return '#f87171'
    return '#dc2626'
  }
  
  return (
    <div className="hourly-heatmap">
      <div className="heatmap-container">
        <div className="heatmap-grid">
          {/* Header row with hours */}
          <div className="heatmap-row header-row">
            <div className="heatmap-cell header-cell corner-cell">Gün/Saat</div>
            {hours.map(hour => (
              <div key={hour} className="heatmap-cell header-cell hour-cell">
                {hour.toString().padStart(2, '0')}
              </div>
            ))}
          </div>
          
          {/* Data rows */}
          {[0, 1, 2, 3, 4, 5, 6].map(dayOfWeek => (
            <div key={dayOfWeek} className="heatmap-row">
              <div className="heatmap-cell header-cell day-cell">
                {days[dayOfWeek]}
              </div>
              {hours.map(hour => {
                const key = `${dayOfWeek}-${hour}`
                const dollyCount = dataMap.get(key) || 0
                const intensity = maxCount > 0 ? (dollyCount / maxCount) * 100 : 0
                
                return (
                  <div
                    key={hour}
                    className="heatmap-cell data-cell"
                    style={{ backgroundColor: getIntensityColor(intensity) }}
                    title={`${days[dayOfWeek]}, ${hour}:00 - ${dollyCount} dolly (${intensity.toFixed(0)}% yoğunluk)`}
                  >
                    {dollyCount > 0 ? dollyCount : ''}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
      
      <div className="heatmap-legend">
        <div className="legend-title">Yoğunluk Göstergesi:</div>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f0f0f0' }}></div>
            <span>Veri Yok</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#fee2e2' }}></div>
            <span>Çok Düşük</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#fca5a5' }}></div>
            <span>Düşük</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#f87171' }}></div>
            <span>Orta</span>
          </div>
          <div className="legend-item">
            <div className="legend-color" style={{ backgroundColor: '#dc2626' }}></div>
            <span>Yüksek</span>
          </div>
        </div>
        <div className="heatmap-stats">
          <div>Maks: {maxCount} dolly</div>
          <div>Min: {minCount} dolly</div>
          <div>Ort: {avgCount.toFixed(1)} dolly</div>
        </div>
      </div>
    </div>
  )
}

export default HourlyHeatmap
