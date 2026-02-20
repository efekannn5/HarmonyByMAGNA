import React, { useState, useMemo } from 'react'
import { format } from 'date-fns'
import './DollyDetailTable.css'

function DollyDetailTable({ data }) {
    const [searchTerm, setSearchTerm] = useState('')
    const [currentPage, setCurrentPage] = useState(1)
    const itemsPerPage = 20

    // Filtreleme
    const filteredData = useMemo(() => {
        if (!data) return []
        if (!searchTerm) return data

        const term = searchTerm.toLowerCase()
        return data.filter(item =>
            item.dolly_no?.toLowerCase().includes(term) ||
            item.part_number?.toLowerCase().includes(term) ||
            item.group_name?.toLowerCase().includes(term) ||
            item.sefer_numarasi?.toLowerCase().includes(term) ||
            item.plaka_no?.toLowerCase().includes(term)
        )
    }, [data, searchTerm])

    // Sayfalama
    const totalPages = Math.ceil(filteredData.length / itemsPerPage)
    const paginatedData = filteredData.slice(
        (currentPage - 1) * itemsPerPage,
        currentPage * itemsPerPage
    )

    // Duration badge sınıfı
    const getDurationClass = (minutes) => {
        if (minutes === null || minutes === undefined) return ''
        if (minutes <= 30) return 'fast'
        if (minutes <= 60) return 'normal'
        return 'slow'
    }

    // Tarih formatlama
    const formatTime = (dateStr) => {
        if (!dateStr) return '-'
        try {
            return format(new Date(dateStr), 'dd.MM HH:mm')
        } catch {
            return '-'
        }
    }

    // VIN kısaltma
    const shortVin = (vin) => {
        if (!vin || vin.length < 8) return vin || '-'
        return `...${vin.slice(-6)}`
    }

    if (!data || data.length === 0) {
        return (
            <div className="dolly-detail-section">
                <h3>📋 Detaylı Dolly Listesi</h3>
                <div className="empty-state">
                    <p className="empty-icon">📋</p>
                    <p>Dolly verisi bulunamadı</p>
                </div>
            </div>
        )
    }

    return (
        <div className="dolly-detail-section">
            <div className="detail-header">
                <div>
                    <h3>📋 Detaylı Dolly Listesi</h3>
                    <span className="detail-count">Toplam {filteredData.length} kayıt</span>
                </div>
                <div className="detail-search">
                    <input
                        type="text"
                        placeholder="🔍 Dolly, Part, Sefer veya Plaka ara..."
                        value={searchTerm}
                        onChange={(e) => {
                            setSearchTerm(e.target.value)
                            setCurrentPage(1)
                        }}
                    />
                </div>
            </div>

            <div className="detail-table-container">
                <table className="detail-table">
                    <thead>
                        <tr>
                            <th>Dolly No</th>
                            <th>VIN</th>
                            <th>Part</th>
                            <th>Grup</th>
                            <th>EOL</th>
                            <th>Sefer</th>
                            <th>Plaka</th>
                            <th>EOL Çıkış</th>
                            <th>Okutma</th>
                            <th>Yükleme</th>
                            <th>Terminal</th>
                            <th>Bekleme</th>
                            <th>Yükleme</th>
                            <th>Terminal</th>
                            <th>Toplam</th>
                        </tr>
                    </thead>
                    <tbody>
                        {paginatedData.map((row, index) => (
                            <tr key={`${row.dolly_no}-${index}`}>
                                <td className="dolly-id">{row.dolly_no}</td>
                                <td className="vin-short" title={row.vin_no}>{shortVin(row.vin_no)}</td>
                                <td>{row.part_number || '-'}</td>
                                <td>{row.group_name || '-'}</td>
                                <td>{row.eol_name || '-'}</td>
                                <td>
                                    {row.sefer_numarasi ? (
                                        <span className="sefer-badge">{row.sefer_numarasi}</span>
                                    ) : '-'}
                                </td>
                                <td>
                                    {row.plaka_no ? (
                                        <span className="plaka-badge">{row.plaka_no}</span>
                                    ) : '-'}
                                </td>
                                <td className="time-cell">{formatTime(row.eol_date)}</td>
                                <td className="time-cell">{formatTime(row.scan_time)}</td>
                                <td className="time-cell">{formatTime(row.loading_completed)}</td>
                                <td className="time-cell">{formatTime(row.terminal_time)}</td>
                                <td>
                                    {row.wait_before_scan_min !== null ? (
                                        <span className={`duration-badge ${getDurationClass(row.wait_before_scan_min)}`}>
                                            {row.wait_before_scan_min}dk
                                        </span>
                                    ) : '-'}
                                </td>
                                <td>
                                    {row.loading_duration_min !== null ? (
                                        <span className={`duration-badge ${getDurationClass(row.loading_duration_min)}`}>
                                            {row.loading_duration_min}dk
                                        </span>
                                    ) : '-'}
                                </td>
                                <td>
                                    {row.terminal_duration_min !== null ? (
                                        <span className={`duration-badge ${getDurationClass(row.terminal_duration_min)}`}>
                                            {row.terminal_duration_min}dk
                                        </span>
                                    ) : '-'}
                                </td>
                                <td>
                                    {row.total_minutes !== null ? (
                                        <span className={`duration-badge ${getDurationClass(row.total_minutes)}`}>
                                            {row.total_minutes}dk
                                        </span>
                                    ) : '-'}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        onClick={() => setCurrentPage(1)}
                        disabled={currentPage === 1}
                    >
                        ⏮️ İlk
                    </button>
                    <button
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                    >
                        ◀️ Önceki
                    </button>
                    <span className="pagination-info">
                        Sayfa {currentPage} / {totalPages}
                    </span>
                    <button
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                    >
                        Sonraki ▶️
                    </button>
                    <button
                        onClick={() => setCurrentPage(totalPages)}
                        disabled={currentPage === totalPages}
                    >
                        Son ⏭️
                    </button>
                </div>
            )}
        </div>
    )
}

export default DollyDetailTable
