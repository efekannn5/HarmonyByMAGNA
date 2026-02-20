import React from 'react'
import { motion, AnimatePresence } from 'framer-motion'

const RecentActivity = ({ activities }) => {
  if (!activities || activities.length === 0) return null

  const getActivityIcon = (type) => {
    switch (type) {
      case 'EOL_READY':
        return { icon: '🏭', color: 'bg-blue-500', text: 'EOL\'den Cikti' }
      case 'SCAN_CAPTURED':
        return { icon: '📱', color: 'bg-purple-500', text: 'Forklift Tarandi' }
      case 'COMPLETED_ASN':
        return { icon: '✅', color: 'bg-green-500', text: 'ASN Gonderildi' }
      case 'COMPLETED_IRSALIYE':
        return { icon: '📄', color: 'bg-orange-500', text: 'Irsaliye Gonderildi' }
      default:
        return { icon: '📦', color: 'bg-gray-500', text: type }
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="bg-white rounded-xl shadow-lg p-6"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        CANLI AKTIVITE AKISI
      </h2>
      
      <div className="space-y-2 max-h-96 overflow-y-auto">
        <AnimatePresence>
          {activities.map((activity, index) => {
            const activityStyle = getActivityIcon(activity.activity_type)
            
            return (
              <motion.div
                key={`${activity.dolly_no}-${activity.timestamp}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ delay: index * 0.03 }}
                className="flex items-center space-x-4 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <div className={`w-10 h-10 ${activityStyle.color} rounded-lg flex items-center justify-center text-lg flex-shrink-0`}>
                  {activityStyle.icon}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="font-bold text-sm text-gray-700 truncate">
                      {activity.dolly_no}
                    </p>
                    <span className="text-xs text-gray-500 ml-2 flex-shrink-0">
                      {new Date(activity.timestamp).toLocaleTimeString('tr-TR')}
                    </span>
                  </div>
                  
                  <div className="flex items-center space-x-2 text-xs text-gray-600 mt-1">
                    <span className="truncate">VIN: {activity.vin_no.slice(-8)}</span>
                    {activity.eol_name && (
                      <>
                        <span>•</span>
                        <span className="truncate">{activity.eol_name}</span>
                      </>
                    )}
                    {activity.operator && (
                      <>
                        <span>•</span>
                        <span className="truncate">{activity.operator}</span>
                      </>
                    )}
                  </div>
                  
                  <p className="text-xs text-gray-500 mt-1">
                    {activityStyle.text}
                  </p>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

export default RecentActivity
