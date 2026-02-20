import React from 'react'
import { motion } from 'framer-motion'
import { useWebSocket } from '../hooks/useWebSocket'
import QueueStatus from './QueueStatus'
import EOLDistribution from './EOLDistribution'
import LoadingStatus from './LoadingStatus'
import Statistics from './Statistics'
import RecentActivity from './RecentActivity'
import PartSummaries from './PartSummaries'
import ProcessTimeline from './ProcessTimeline'
import DollyFillingStatus from './DollyFillingStatus'
import ShiftStatistics from './ShiftStatistics'
import LineVisualizerTV from './LineVisualizerTV'

const Dashboard = () => {
  const { data, isConnected, error } = useWebSocket()

  return (
    <div className="min-h-screen bg-harmony-light">
      {/* Header */}
      <header className="bg-harmony-secondary shadow-lg">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <img
                src="/logo/logo.png"
                alt="Harmony Logo"
                className="h-12 w-auto"
                onError={(e) => {
                  e.target.style.display = 'none'
                }}
              />
              <div>
                <h1 className="text-2xl font-bold text-white">
                  HARMONY CONTROL TOWER
                </h1>
                <p className="text-sm text-gray-300">
                  Magna Dolly Logistics Dashboard
                </p>
              </div>
            </div>

            {/* Connection Status */}
            <div className="flex items-center space-x-3">
              <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${isConnected
                ? 'bg-green-500/20 text-green-400'
                : 'bg-red-500/20 text-red-400'
                }`}>
                <div className={`w-2 h-2 rounded-full ${isConnected
                  ? 'bg-green-400 animate-pulse'
                  : 'bg-red-400'
                  }`} />
                <span className="text-sm font-medium">
                  {isConnected ? 'CANLI' : 'BAGLANTI YOK'}
                </span>
              </div>

              {data?.last_updated && (
                <div className="text-sm text-gray-300">
                  Son Guncelleme: {new Date(data.last_updated).toLocaleTimeString('tr-TR')}
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        {(!data || error) && (
          <div className="fixed inset-0 z-50 bg-gray-900 flex flex-col items-center justify-center space-y-6">
            <div className="relative">
              {/* Pulse Effect */}
              <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl animate-pulse"></div>
              <img
                src="/logo/logo.png"
                alt="Logo"
                className="h-24 w-auto relative z-10 brightness-0 invert opacity-90"
              />
            </div>

            <div className="flex flex-col items-center space-y-2">
              <h2 className="text-2xl font-bold text-white tracking-widest uppercase">
                Veriler Güncelleniyor
              </h2>
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>

            {/* Optional: Show technically what's happening in small text if it takes too long */}
            {error && (
              <p className="text-gray-600 text-xs absolute bottom-10 font-mono">
                Sunucu bağlantısı bekleniyor...
              </p>
            )}
          </div>
        )}

        {data && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
            className="space-y-6"
          >
            {/* TV Dashboard - All Lines Visualization (Full Screen) */}
            {data.line_visualization && (
              <div className="h-screen w-full absolute top-0 left-0 z-50 bg-gray-900">
                <LineVisualizerTV data={data.line_visualization} />
              </div>
            )}
          </motion.div>
        )}
      </main>
    </div >
  )
}

export default Dashboard
