import React from 'react'
import { motion } from 'framer-motion'

const DollyDetails = ({ dollies }) => {
  if (!dollies || dollies.length === 0) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.7 }}
      className="bg-white rounded-xl shadow-lg p-6"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        DOLLY DETAYLARI (VIN Gruplanmis)
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {dollies.map((dolly, index) => (
          <motion.div
            key={dolly.dolly_no}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.05 }}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-bold text-harmony-primary text-lg">
                  {dolly.dolly_no}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(dolly.inserted_at).toLocaleString('tr-TR')}
                </p>
              </div>
              
              <div className="bg-harmony-primary text-white rounded-full w-12 h-12 flex items-center justify-center">
                <div className="text-center">
                  <p className="text-lg font-bold">{dolly.vin_count}</p>
                  <p className="text-xs">VIN</p>
                </div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">EOL:</span>
                <span className="font-medium text-gray-800 truncate ml-2" title={dolly.eol_name}>
                  {dolly.eol_name ? dolly.eol_name.substring(0, 20) + '...' : 'N/A'}
                </span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Ilk VIN:</span>
                <span className="font-mono text-xs text-gray-800">
                  {dolly.first_vin}
                </span>
              </div>
              
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Toplam Parca:</span>
                <span className="font-bold text-blue-600">
                  {dolly.total_parts}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export default DollyDetails
