import React from 'react'
import { motion } from 'framer-motion'

const LoadingStatus = ({ sessions }) => {
  if (!sessions) return null

  const getStatusColor = (status) => {
    switch (status) {
      case 'loading_completed':
        return 'bg-green-100 text-green-700 border-green-300'
      case 'scanned':
        return 'bg-blue-100 text-blue-700 border-blue-300'
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'loading_completed':
        return 'Yukleme Tamamlandi'
      case 'scanned':
        return 'Taranmis'
      case 'pending':
        return 'Bekliyor'
      default:
        return status
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="bg-white rounded-xl shadow-lg p-6 border-t-4 border-blue-500"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        AKTIF YUKLEME SEANSLAR
      </h2>
      
      {sessions.length === 0 ? (
        <div className="text-center py-8 text-gray-400">
          <div className="text-4xl mb-2">📦</div>
          <p>Aktif yukleme yok</p>
        </div>
      ) : (
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {sessions.map((session, index) => (
            <motion.div
              key={session.session_id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`border rounded-lg p-4 ${getStatusColor(session.status)}`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="font-bold text-sm">{session.operator_name}</p>
                  <p className="text-xs opacity-75">
                    {new Date(session.created_at).toLocaleTimeString('tr-TR')}
                  </p>
                </div>
                <span className="px-2 py-1 rounded text-xs font-bold">
                  {getStatusText(session.status)}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="text-center">
                    <p className="text-2xl font-bold">{session.dolly_count}</p>
                    <p className="text-xs opacity-75">Dolly</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold">{session.scan_order_max}</p>
                    <p className="text-xs opacity-75">Max Sira</p>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </motion.div>
  )
}

export default LoadingStatus
