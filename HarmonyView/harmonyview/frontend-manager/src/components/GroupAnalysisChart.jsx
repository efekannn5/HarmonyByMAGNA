import React from 'react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import './GroupAnalysisChart.css'

const COLORS = ['#c8102e', '#0077b6', '#059669', '#d97706', '#7c3aed', '#db2777', '#0891b2', '#65a30d']

function GroupAnalysisChart({ data }) {
    if (!data || data.length === 0) {
        return (
            <div className="group-analysis-section">
                <h3>🏷️ Grup Bazlı Analiz</h3>
                <div className="empty-state">
                    <p className="empty-icon">🏷️</p>
                    <p>Grup verisi bulunamadı</p>
                </div>
            </div>
        )
    }

    // Pasta grafik için veri hazırlama
    const chartData = data.map((item, index) => ({
        name: item.group_name,
        value: item.dolly_count,
        color: COLORS[index % COLORS.length]
    }))

    return (
        <div className="group-analysis-section">
            <h3>🏷️ Grup Bazlı Analiz</h3>
            <p className="section-sub">DollyGroup'lara göre dolly dağılımı ve süre ortalamaları</p>

            <div className="group-analysis-content">
                {/* Pasta Grafik */}
                <div className="group-chart-container">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={chartData}
                                cx="50%"
                                cy="50%"
                                innerRadius={50}
                                outerRadius={90}
                                paddingAngle={2}
                                dataKey="value"
                                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                                labelLine={true}
                            >
                                {chartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                formatter={(value) => [`${value} dolly`, 'Sayı']}
                                contentStyle={{
                                    borderRadius: '8px',
                                    border: '1px solid #e0e0e0',
                                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                                }}
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Grup Kartları */}
                <div className="group-cards">
                    {data.map((group, index) => (
                        <div className="group-card" key={group.group_id}>
                            <div className="group-card-header">
                                <span className="group-name" style={{ color: COLORS[index % COLORS.length] }}>
                                    {group.group_name}
                                </span>
                                <span className="group-dolly-count">{group.dolly_count} dolly</span>
                            </div>

                            <div className="group-stats">
                                <div className="group-stat">
                                    <span className="group-stat-label">Part Sayısı</span>
                                    <span className="group-stat-value">{group.part_count}</span>
                                </div>
                                <div className="group-stat">
                                    <span className="group-stat-label">Toplam Adet</span>
                                    <span className="group-stat-value">{group.total_quantity}</span>
                                </div>
                                <div className="group-stat">
                                    <span className="group-stat-label">Bekleme</span>
                                    <span className="group-stat-value">{group.avg_wait_before_scan} dk</span>
                                </div>
                                <div className="group-stat">
                                    <span className="group-stat-label">Yükleme</span>
                                    <span className="group-stat-value">{group.avg_loading_duration} dk</span>
                                </div>
                            </div>

                            <div className="group-total-time">
                                <span className="total-time-label">Ort. Toplam Süre</span>
                                <span className="total-time-value">{group.avg_total_duration} dk</span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default GroupAnalysisChart
