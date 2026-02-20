import React from 'react'
import { motion } from 'framer-motion'

const LineVisualizer = ({ data }) => {
    if (!data) return null

    // Helper to render grid
    const renderGrid = (currentVins, capacity = 12) => {
        return (
            <div className="grid grid-cols-6 gap-1 w-full max-w-[200px]">
                {[...Array(capacity)].map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ scale: 0.8, opacity: 0.5 }}
                        animate={{
                            scale: i < currentVins ? 1 : 0.9,
                            opacity: i < currentVins ? 1 : 0.3,
                            backgroundColor: i < currentVins ? '#8b5cf6' : '#e5e7eb'
                        }}
                        className="h-6 rounded-sm border border-gray-300"
                    />
                ))}
            </div>
        )
    }

    // Helper to render queue
    const renderQueue = (queue) => {
        if (!queue || queue.length === 0) return <div className="text-gray-400 text-xs text-center italic">Kuyruk bos</div>

        return (
            <div className="flex space-x-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-300">
                {queue.map((item, i) => (
                    <motion.div
                        key={item.dolly_no}
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="flex-shrink-0 bg-white border border-purple-200 rounded p-2 text-center min-w-[70px] shadow-sm"
                    >
                        <div className="font-bold text-purple-700 text-sm">{item.dolly_no}</div>
                        <div className="text-[10px] text-gray-500 mt-1">
                            {new Date(item.completed_at).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}
                        </div>
                    </motion.div>
                ))}
            </div>
        )
    }

    return (
        <div className="space-y-4">
            {Object.entries(data).map(([lineName, details], index) => (
                <motion.div
                    key={lineName}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.2 }}
                    className="bg-white rounded-xl shadow-lg p-4 border-l-4 border-purple-500 flex flex-col md:flex-row items-center gap-6"
                >
                    {/* Line Name */}
                    <div className="w-full md:w-32 font-bold text-xl text-gray-800 border-b md:border-b-0 md:border-r border-gray-200 pb-2 md:pb-0 md:pr-4 text-center md:text-left">
                        {lineName.replace('-EOL', '')}
                    </div>

                    {/* Grid (Active Dolly) */}
                    <div className="flex-1 flex flex-col items-center md:items-start border-b md:border-b-0 md:border-r border-gray-200 pb-4 md:pb-0 md:pr-6 w-full md:w-auto">
                        <div className="flex justify-between w-full items-center mb-2">
                            <div className="text-xs font-bold text-gray-500 uppercase tracking-wider">AKTIF DOLLY</div>
                            <div className="text-purple-600 font-bold bg-purple-50 px-2 py-0.5 rounded text-sm">{details.active?.dolly_no || '-'}</div>
                        </div>

                        {details.active ? renderGrid(details.active.current_vins, details.active.capacity) : <div className="text-gray-400 text-sm italic py-2">Aktif dolly yok</div>}
                    </div>

                    {/* Queue */}
                    <div className="flex-[2] w-full overflow-hidden">
                        <div className="text-xs font-bold text-gray-500 mb-2 uppercase tracking-wider">KUYRUK (Bekleyen)</div>
                        {renderQueue(details.queue)}
                    </div>
                </motion.div>
            ))}
        </div>
    )
}

export default LineVisualizer
