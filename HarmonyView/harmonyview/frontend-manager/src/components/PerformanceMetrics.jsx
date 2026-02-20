import React from 'react'
import { motion } from 'framer-motion'
import './PerformanceMetrics.css'

function PerformanceMetrics({ data }) {
  const metrics = [
    {
      label: 'Toplam Parça',
      value: data.total_quantity || 0,
      icon: '📦',
      color: '#c8102e',
      description: 'Toplam üretilen parça adedi'
    },
    {
      label: 'Farklı Part',
      value: data.unique_part_count || 0,
      icon: '🔢',
      color: '#2563eb',
      description: 'Kaç farklı part numarası'
    },
    {
      label: 'Toplam Dolly',
      value: data.total_dollies || 0,
      icon: '🛒',
      color: '#16a34a',
      description: 'Kullanılan dolly sayısı'
    },
    {
      label: 'Toplam Sefer',
      value: data.total_sefer || 0,
      icon: '🚚',
      color: '#9333ea',
      description: 'Tamamlanan sefer sayısı'
    }
  ]

  return (
    <div className="performance-metrics">
      {metrics.map((metric, index) => (
        <motion.div
          key={metric.label}
          className="metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.1 }}
          style={{ borderTopColor: metric.color }}
        >
          <div className="metric-icon" style={{ backgroundColor: `${metric.color}20` }}>
            {metric.icon}
          </div>
          <div className="metric-content">
            <p className="metric-label">{metric.label}</p>
            <p className="metric-value" style={{ color: metric.color }}>
              {typeof metric.value === 'number' ? metric.value.toLocaleString('tr-TR') : metric.value}
            </p>
            <p className="metric-description">{metric.description}</p>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

export default PerformanceMetrics
