import React from 'react'
import { motion } from 'framer-motion'

const DollyFillingStatus = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-purple-500"
      >
        <h2 className="text-lg font-bold text-harmony-text mb-4">
          AKTIF DOLLY DOLMA DURUMU
        </h2>
        <div className="text-center py-8 text-gray-400">
          <p>Aktif dolly yok</p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-purple-500"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        AKTIF DOLLY DOLMA DURUMU (Hat Bazli)
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-96 overflow-y-auto">
        {data.map((dolly, index) => (
          <motion.div
            key={dolly.eol_name}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className="border border-purple-200 rounded-lg p-4 bg-purple-50"
          >
            {/* EOL Name */}
            <div className="mb-3">
              <p className="text-xs text-gray-600 mb-1">Hat / EOL</p>
              <p className="text-sm font-bold text-purple-600 truncate" title={dolly.eol_name}>
                {dolly.eol_name}
              </p>
            </div>

            {/* Dolly Number */}
            <div className="text-center bg-white rounded-lg p-3 mb-3">
              <p className="text-xs text-gray-600 mb-1">Aktif Dolly</p>
              <p className="text-2xl font-bold text-harmony-primary">{dolly.active_dolly}</p>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>{dolly.current_vins} VIN</span>
                <span>{dolly.remaining_vins} Kaldi</span>
              </div>
              
              <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-purple-500 to-purple-600 flex items-center justify-center"
                  initial={{ width: 0 }}
                  animate={{ width: `${dolly.fill_percentage}%` }}
                  transition={{ duration: 0.5 }}
                >
                  <span className="text-white text-xs font-bold">
                    {dolly.fill_percentage}%
                  </span>
                </motion.div>
              </div>
            </div>

            {/* Details */}
            <div className="grid grid-cols-2 gap-2">
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Yuklenen</p>
                <p className="text-lg font-bold text-purple-600">{dolly.current_vins}</p>
              </div>
              <div className="bg-white rounded p-2">
                <p className="text-xs text-gray-600">Kapasite</p>
                <p className="text-lg font-bold text-blue-600">{dolly.estimated_capacity}</p>
              </div>
            </div>

            {dolly.last_update && (
              <div className="text-xs text-gray-500 text-center pt-2 border-t border-purple-200 mt-2">
                {new Date(dolly.last_update).toLocaleTimeString('tr-TR')}
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export default DollyFillingStatus
