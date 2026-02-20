import React from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import { tr } from 'date-fns/locale'
import './DailyPerformanceChart.css'

function DailyPerformanceChart({ data }) {
  const chartData = data.map(day => ({
    date: format(new Date(day.date), 'dd MMM', { locale: tr }),
    fullDate: day.date,
    dollies: day.total_dollies,
    parts: day.total_parts,
    sefer: day.total_sefer,
    shifts: day.shifts
  }))

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="custom-tooltip">
          <p className="tooltip-date">{format(new Date(data.fullDate), 'dd MMMM yyyy', { locale: tr })}</p>
          <p className="tooltip-value" style={{ color: '#c8102e' }}>
            Dolly: {data.dollies}
          </p>
          <p className="tooltip-value" style={{ color: '#2563eb' }}>
            Parça: {data.parts}
          </p>
          <p className="tooltip-value" style={{ color: '#16a34a' }}>
            Sefer: {data.sefer}
          </p>
          {data.shifts && (
            <div className="tooltip-shifts">
              <p className="tooltip-subtitle">Vardiya Detayı:</p>
              {data.shifts.map((shift, idx) => (
                <p key={idx} className="tooltip-shift">
                  {shift.shift_name}: {shift.total_dollies} dolly
                </p>
              ))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  return (
    <div className="daily-performance-chart">
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <defs>
            <linearGradient id="colorDollies" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#c8102e" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#c8102e" stopOpacity={0.1}/>
            </linearGradient>
            <linearGradient id="colorParts" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#2563eb" stopOpacity={0.1}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <YAxis 
            tick={{ fontSize: 12, fill: '#666' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '10px' }}
            iconType="circle"
          />
          <Area 
            type="monotone" 
            dataKey="dollies" 
            stroke="#c8102e" 
            fillOpacity={1} 
            fill="url(#colorDollies)" 
            name="Dolly"
            strokeWidth={2}
          />
          <Area 
            type="monotone" 
            dataKey="sefer" 
            stroke="#16a34a" 
            fillOpacity={1} 
            fill="url(#colorParts)" 
            name="Sefer"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default DailyPerformanceChart
