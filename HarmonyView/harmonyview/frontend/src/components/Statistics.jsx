import React from 'react'
import { motion } from 'framer-motion'

const Statistics = ({ data }) => {
  if (!data) return null

  const stats = [
    {
      label: 'Bugun Gonderilen',
      value: data.total_shipped,
      color: 'text-green-600',
      icon: '✓'
    },
    {
      label: 'Toplam Sefer',
      value: data.unique_sefers,
      color: 'text-blue-600',
      icon: '🚛'
    },
    {
      label: 'ASN Gonderim',
      value: data.asn_count,
      color: 'text-purple-600',
      icon: '📄'
    },
    {
      label: 'Ort. Dolly/Sefer',
      value: data.avg_dollies_per_sefer.toFixed(1),
      color: 'text-orange-600',
      icon: '📊'
    }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 }}
      className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-green-500"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        GUNLUK ISTATISTIKLER
      </h2>
      
      <div className="grid grid-cols-2 gap-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            className="bg-gray-50 rounded-lg p-4 text-center"
          >
            <div className="text-2xl mb-2">{stat.icon}</div>
            <p className={`text-2xl font-bold ${stat.color} mb-1`}>
              {typeof stat.value === 'number' ? stat.value.toLocaleString('tr-TR') : stat.value}
            </p>
            <p className="text-xs text-gray-600">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-200">
        <div className="flex justify-between text-xs text-gray-500">
          <span>Irsaliye: {data.irsaliye_count}</span>
          <span>Toplam Parca: {data.total_parts}</span>
        </div>
      </div>
    </motion.div>
  )
}

export default Statistics
