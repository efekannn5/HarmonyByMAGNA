import React from 'react'
import { motion } from 'framer-motion'

const ProcessTimeline = ({ timeline, metrics }) => {
  if (!timeline || timeline.length === 0) return null

  const steps = [
    { id: 'EOL_READY', label: 'EOL Cikis', icon: '🏭', color: 'bg-blue-500' },
    { id: 'SCAN_CAPTURED', label: 'Tarama', icon: '📱', color: 'bg-purple-500' },
    { id: 'WAITING_SUBMIT', label: 'Yuklendi', icon: '📦', color: 'bg-yellow-500' },
    { id: 'COMPLETED_ASN', label: 'Sevkiyat', icon: '✅', color: 'bg-green-500' }
  ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6 }}
      className="bg-white rounded-xl shadow-lg p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-harmony-text">
          SUREC PERFORMANSI
        </h2>
        
        {metrics && (
          <div className="flex items-center space-x-4 text-sm">
            <div className="bg-blue-50 px-3 py-1 rounded">
              <span className="text-gray-600">Bugun Gonderilen: </span>
              <span className="font-bold text-blue-600">{metrics.total_dollies_shipped} Dolly</span>
            </div>
            <div className="bg-green-50 px-3 py-1 rounded">
              <span className="text-gray-600">Ort. Surec: </span>
              <span className="font-bold text-green-600">{metrics.avg_processing_minutes} dk</span>
            </div>
            <div className="bg-orange-50 px-3 py-1 rounded">
              <span className="text-gray-600">Saatlik: </span>
              <span className="font-bold text-orange-600">{metrics.dollies_per_hour} Dolly/saat</span>
            </div>
          </div>
        )}
      </div>

      {/* Horizontal Timeline */}
      <div className="relative mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.id} className="flex-1 relative">
              <div className="flex flex-col items-center">
                <div className={`w-16 h-16 ${step.color} rounded-full flex items-center justify-center text-2xl shadow-lg z-10`}>
                  {step.icon}
                </div>
                <p className="mt-2 text-xs font-bold text-gray-700 text-center">
                  {step.label}
                </p>
              </div>
              
              {/* Connecting line */}
              {index < steps.length - 1 && (
                <div className="absolute top-8 left-1/2 w-full h-1 bg-gray-300" style={{ zIndex: 0 }} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent Timeline Items */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {timeline.slice(0, 8).map((item, index) => (
          <motion.div
            key={`${item.dolly_no}-${item.vin_no}-${index}`}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="flex items-center justify-between bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors"
          >
            <div className="flex items-center space-x-3">
              <div className={`w-2 h-2 rounded-full ${steps.find(s => s.id === item.status)?.color || 'bg-gray-500'}`} />
              <span className="font-bold text-sm text-gray-700">
                Dolly {item.dolly_no}
              </span>
            </div>
            
            <div className="flex items-center space-x-3">
              <span className="text-xs text-gray-500">
                {steps.find(s => s.id === item.status)?.label || item.status}
              </span>
              <span className="text-xs text-gray-400">
                {new Date(item.created_at).toLocaleTimeString('tr-TR')}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export default ProcessTimeline
