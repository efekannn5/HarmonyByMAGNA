import React from 'react'
import { motion } from 'framer-motion'

const QueueStatus = ({ data }) => {
  if (!data) return null

  const stats = [
    {
      label: 'Kuyrukta Bekleyen Dolly',
      value: data.total_dollies,
      color: 'text-harmony-primary',
      bgColor: 'bg-red-50'
    },
    {
      label: 'Toplam Parca',
      value: data.total_parts,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      label: 'Toplam VIN',
      value: data.unique_vins,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-harmony-primary"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        ANLIK KUYRUK DURUMU
      </h2>
      
      <div className="space-y-4">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className={`${stat.bgColor} rounded-lg p-4`}
          >
            <p className="text-sm text-gray-600 mb-1">{stat.label}</p>
            <p className={`text-3xl font-bold ${stat.color}`}>
              {stat.value.toLocaleString('tr-TR')}
            </p>
          </motion.div>
        ))}
      </div>

      {data.oldest_dolly_date && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            En Eski Dolly: {new Date(data.oldest_dolly_date).toLocaleString('tr-TR')}
          </p>
        </div>
      )}
    </motion.div>
  )
}

export default QueueStatus
