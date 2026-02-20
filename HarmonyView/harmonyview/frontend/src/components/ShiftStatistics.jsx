import React from 'react'
import { motion } from 'framer-motion'

const ShiftStatistics = ({ data }) => {
  if (!data) return null

  const { current_shift, previous_shift } = data

  const comparison = {
    dolly: current_shift.dolly_count - previous_shift.dolly_count,
    part: current_shift.part_count - previous_shift.part_count,
    sefer: current_shift.sefer_count - previous_shift.sefer_count
  }

  const getComparisonColor = (value) => {
    if (value > 0) return 'text-green-600'
    if (value < 0) return 'text-red-600'
    return 'text-gray-600'
  }

  const getComparisonIcon = (value) => {
    if (value > 0) return '↑'
    if (value < 0) return '↓'
    return '='
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-orange-500"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        VARDIYA PERFORMANSI
      </h2>

      <div className="mb-4 bg-orange-50 rounded-lg p-3">
        <p className="text-sm text-gray-600">Aktif Vardiya</p>
        <p className="text-2xl font-bold text-orange-600">
          {current_shift.name.replace('Shift_', 'Vardiya ')}
        </p>
        <p className="text-xs text-gray-500">
          {current_shift.start_time} - {current_shift.end_time}
        </p>
      </div>

      <div className="space-y-3">
        {/* Dolly Count */}
        <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
          <div>
            <p className="text-xs text-gray-600">Gonderilen Dolly</p>
            <p className="text-2xl font-bold text-harmony-primary">
              {current_shift.dolly_count}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Onceki Vardiya</p>
            <p className="text-sm text-gray-600">{previous_shift.dolly_count}</p>
            <p className={`text-sm font-bold ${getComparisonColor(comparison.dolly)}`}>
              {getComparisonIcon(comparison.dolly)} {Math.abs(comparison.dolly)}
            </p>
          </div>
        </div>

        {/* Part Count */}
        <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
          <div>
            <p className="text-xs text-gray-600">Gonderilen Part</p>
            <p className="text-2xl font-bold text-blue-600">
              {current_shift.part_count}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Onceki Vardiya</p>
            <p className="text-sm text-gray-600">{previous_shift.part_count}</p>
            <p className={`text-sm font-bold ${getComparisonColor(comparison.part)}`}>
              {getComparisonIcon(comparison.part)} {Math.abs(comparison.part)}
            </p>
          </div>
        </div>

        {/* Sefer Count */}
        <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
          <div>
            <p className="text-xs text-gray-600">Toplam Sefer</p>
            <p className="text-2xl font-bold text-green-600">
              {current_shift.sefer_count}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500">Onceki Vardiya</p>
            <p className="text-sm text-gray-600">{previous_shift.sefer_count}</p>
            <p className={`text-sm font-bold ${getComparisonColor(comparison.sefer)}`}>
              {getComparisonIcon(comparison.sefer)} {Math.abs(comparison.sefer)}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export default ShiftStatistics
