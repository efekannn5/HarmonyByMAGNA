import React from 'react'
import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const EOLDistribution = ({ data }) => {
  if (!data || data.length === 0) return null

  const COLORS = [
    '#dc2626', // Red
    '#2563eb', // Blue
    '#16a34a', // Green
    '#ca8a04', // Yellow
    '#9333ea', // Purple
    '#ea580c', // Orange
    '#0891b2', // Cyan
    '#4f46e5', // Indigo
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-white rounded-xl shadow-lg p-6"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        EOL ISTASYON DAGILIMI
      </h2>
      
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="eol_name" 
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 11, fill: '#374151' }}
          />
          <YAxis tick={{ fontSize: 12, fill: '#374151' }} />
          <Tooltip 
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              padding: '8px'
            }}
            formatter={(value, name) => {
              if (name === 'dolly_count') return [value, 'Dolly Sayisi']
              if (name === 'part_count') return [value, 'Parca Sayisi']
              return [value, name]
            }}
          />
          <Bar dataKey="dolly_count" radius={[8, 8, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-2 gap-2">
        {data.slice(0, 4).map((item, index) => (
          <div key={item.eol_name} className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded"
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <div className="flex-1">
              <p className="text-xs font-medium text-gray-700 truncate">
                {item.eol_name}
              </p>
              <p className="text-xs text-gray-500">
                {item.dolly_count} adet ({item.percentage}%)
              </p>
            </div>
          </div>
        ))}
      </div>
    </motion.div>
  )
}

export default EOLDistribution
