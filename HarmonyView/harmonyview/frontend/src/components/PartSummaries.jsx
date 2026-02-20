import React from 'react'
import { motion } from 'framer-motion'
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

const PartSummaries = ({ data }) => {
  if (!data || data.length === 0) return null

  const COLORS = ['#dc2626', '#2563eb', '#16a34a', '#ca8a04', '#9333ea', '#ea580c', '#0891b2', '#4f46e5']

  const chartData = data.map(item => ({
    name: item.group_name || item.part_number,
    value: item.dolly_count
  }))

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="bg-white rounded-xl shadow-lg p-6"
    >
      <h2 className="text-lg font-bold text-harmony-text mb-4">
        GRUP BAZLI DOLLY DAGILIMI (TIR Icerigi)
      </h2>
      
      <div className="grid grid-cols-2 gap-4">
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                padding: '8px'
              }}
            />
          </PieChart>
        </ResponsiveContainer>

        <div className="space-y-2 overflow-y-auto max-h-64">
          {data.map((item, index) => (
            <motion.div
              key={item.group_name || item.part_number}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className="border border-gray-200 rounded-lg p-3"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <p className="font-bold text-sm text-gray-700 truncate">
                    {item.group_name || item.part_number}
                  </p>
                  {item.shipping_tag && (
                    <span className={`text-xs px-2 py-1 rounded mt-1 inline-block ${
                      item.shipping_tag === 'asn' ? 'bg-blue-100 text-blue-700' :
                      item.shipping_tag === 'irsaliye' ? 'bg-green-100 text-green-700' :
                      'bg-purple-100 text-purple-700'
                    }`}>
                      {item.shipping_tag.toUpperCase()}
                    </span>
                  )}
                </div>
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: COLORS[index % COLORS.length] }}
                />
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div>
                  <p className="text-gray-500">Dolly</p>
                  <p className="font-bold text-harmony-primary">{item.dolly_count}</p>
                </div>
                <div>
                  <p className="text-gray-500">VIN</p>
                  <p className="font-bold text-blue-600">{item.vin_count}</p>
                </div>
                <div>
                  <p className="text-gray-500">Sefer</p>
                  <p className="font-bold text-green-600">{item.sefer_count}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </motion.div>
  )
}

export default PartSummaries
