import React from 'react'
import './PartAnalysisTable.css'

function PartAnalysisTable({ data }) {
    if (!data || data.length === 0) {
        return (
            <div className="part-analysis-section empty-state">
                <p className="empty-icon">📦</p>
                <p>Part verisi bulunamadı</p>
                <p className="section-sub">Seçili tarih aralığında kayıt yok.</p>
            </div>
        )
    }

    // Duration'a göre renk sınıfı belirleme (dakika)
    const getDurationClass = (minutes) => {
        if (minutes === null || minutes === undefined) return ''
        if (minutes <= 30) return 'good'
        if (minutes <= 60) return 'warning'
        return 'danger'
    }

    // Toplam hesaplama
    const totals = data.reduce((acc, item) => ({
        dolly_count: acc.dolly_count + item.dolly_count,
        total_quantity: acc.total_quantity + item.total_quantity,
        avg_wait_before_scan: acc.avg_wait_before_scan + (item.avg_wait_before_scan * item.dolly_count),
        avg_loading_duration: acc.avg_loading_duration + (item.avg_loading_duration * item.dolly_count),
        avg_terminal_duration: acc.avg_terminal_duration + (item.avg_terminal_duration * item.dolly_count),
        avg_total_duration: acc.avg_total_duration + (item.avg_total_duration * item.dolly_count)
    }), {
        dolly_count: 0,
        total_quantity: 0,
        avg_wait_before_scan: 0,
        avg_loading_duration: 0,
        avg_terminal_duration: 0,
        avg_total_duration: 0
    })

    const avgWait = totals.dolly_count > 0 ? (totals.avg_wait_before_scan / totals.dolly_count).toFixed(1) : 0
    const avgLoading = totals.dolly_count > 0 ? (totals.avg_loading_duration / totals.dolly_count).toFixed(1) : 0
    const avgTerminal = totals.dolly_count > 0 ? (totals.avg_terminal_duration / totals.dolly_count).toFixed(1) : 0
    const avgTotal = totals.dolly_count > 0 ? (totals.avg_total_duration / totals.dolly_count).toFixed(1) : 0

    return (
        <div className="part-analysis-section">
            <h3>📦 Part Bazlı Süre Analizi</h3>
            <p className="section-sub">Her parça numarası için ortalama işlem süreleri (dakika)</p>

            <div className="part-table-container">
                <table className="part-table">
                    <thead>
                        <tr>
                            <th>Part Numarası</th>
                            <th>Grup</th>
                            <th>Dolly</th>
                            <th>Adet</th>
                            <th>Okutulmadan Bekleme</th>
                            <th>Yükleme Süresi</th>
                            <th>Terminal Süresi</th>
                            <th>Toplam Süre</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((item, index) => (
                            <tr key={item.part_number || index}>
                                <td className="part-number">{item.part_number}</td>
                                <td>
                                    <span className={`group-badge ${!item.group_name ? 'no-group' : ''}`}>
                                        {item.group_name || 'Grupsuz'}
                                    </span>
                                </td>
                                <td>
                                    <span className="count-badge">{item.dolly_count}</span>
                                </td>
                                <td>{item.total_quantity}</td>
                                <td className="duration-cell">
                                    <span className={`duration-value ${getDurationClass(item.avg_wait_before_scan)}`}>
                                        {item.avg_wait_before_scan} dk
                                    </span>
                                </td>
                                <td className="duration-cell">
                                    <span className={`duration-value ${getDurationClass(item.avg_loading_duration)}`}>
                                        {item.avg_loading_duration} dk
                                    </span>
                                </td>
                                <td className="duration-cell">
                                    <span className={`duration-value ${getDurationClass(item.avg_terminal_duration)}`}>
                                        {item.avg_terminal_duration} dk
                                    </span>
                                </td>
                                <td className="duration-cell">
                                    <span className={`duration-value ${getDurationClass(item.avg_total_duration)}`}>
                                        {item.avg_total_duration} dk
                                    </span>
                                </td>
                            </tr>
                        ))}
                        {/* Toplam satırı */}
                        <tr className="summary-row">
                            <td><strong>TOPLAM</strong></td>
                            <td>-</td>
                            <td><span className="count-badge">{totals.dolly_count}</span></td>
                            <td><strong>{totals.total_quantity}</strong></td>
                            <td className="duration-cell"><span className="duration-value">{avgWait} dk</span></td>
                            <td className="duration-cell"><span className="duration-value">{avgLoading} dk</span></td>
                            <td className="duration-cell"><span className="duration-value">{avgTerminal} dk</span></td>
                            <td className="duration-cell"><span className="duration-value">{avgTotal} dk</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default PartAnalysisTable
