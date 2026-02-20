import React, { useState, useMemo } from 'react'
import { format } from 'date-fns'
import './ExpandableDollyTable.css'

function ExpandableDollyTable({ data }) {
    const [expandedParts, setExpandedParts] = useState(new Set())
    const [searchTerm, setSearchTerm] = useState('')
    const [expandAll, setExpandAll] = useState(false)

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

    // Part bazlı gruplama
    const groupedData = useMemo(() => {
        if (!data || data.length === 0) return []

        const groups = {}

        data.forEach(item => {
            const partKey = item.part_number || 'Bilinmiyor'

            if (!groups[partKey]) {
                groups[partKey] = {
                    part_number: partKey,
                    group_name: item.group_name,
                    dollies: [],
                    total_wait: 0,
                    total_loading: 0,
                    total_terminal: 0,
                    total_total: 0,
                    count_wait: 0,
                    count_loading: 0,
                    count_terminal: 0,
                    count_total: 0,
                    sefer_set: new Set(),
                    plaka_set: new Set()
                }
            }

            groups[partKey].dollies.push(item)

            if (item.wait_before_scan_min !== null) {
                groups[partKey].total_wait += item.wait_before_scan_min
                groups[partKey].count_wait++
            }
            if (item.loading_duration_min !== null) {
                groups[partKey].total_loading += item.loading_duration_min
                groups[partKey].count_loading++
            }
            if (item.terminal_duration_min !== null) {
                groups[partKey].total_terminal += item.terminal_duration_min
                groups[partKey].count_terminal++
            }
            if (item.total_minutes !== null) {
                groups[partKey].total_total += item.total_minutes
                groups[partKey].count_total++
            }

            if (item.sefer_numarasi) groups[partKey].sefer_set.add(item.sefer_numarasi)
            if (item.plaka_no) groups[partKey].plaka_set.add(item.plaka_no)
        })

        return Object.values(groups).map(g => ({
            ...g,
            avg_wait: g.count_wait > 0 ? Math.round(g.total_wait / g.count_wait) : null,
            avg_loading: g.count_loading > 0 ? Math.round(g.total_loading / g.count_loading) : null,
            avg_terminal: g.count_terminal > 0 ? Math.round(g.total_terminal / g.count_terminal) : null,
            avg_total: g.count_total > 0 ? Math.round(g.total_total / g.count_total) : null,
            sefer_count: g.sefer_set.size,
            plaka_count: g.plaka_set.size
        })).sort((a, b) => b.dollies.length - a.dollies.length)
    }, [data])

    // Filtreleme
    const filteredGroups = useMemo(() => {
        if (!searchTerm) return groupedData
        const term = searchTerm.toLowerCase()
        return groupedData.filter(g =>
            g.part_number.toLowerCase().includes(term) ||
            g.group_name?.toLowerCase().includes(term) ||
            g.dollies.some(d =>
                d.dolly_no?.toLowerCase().includes(term) ||
                d.sefer_numarasi?.toLowerCase().includes(term) ||
                d.plaka_no?.toLowerCase().includes(term)
            )
        )
    }, [groupedData, searchTerm])

    // Toggle expand
    const togglePart = (partNumber) => {
        const newExpanded = new Set(expandedParts)
        if (newExpanded.has(partNumber)) {
            newExpanded.delete(partNumber)
        } else {
            newExpanded.add(partNumber)
        }
        setExpandedParts(newExpanded)
    }

    // Expand/Collapse All
    const toggleExpandAll = () => {
        if (expandAll) {
            setExpandedParts(new Set())
        } else {
            setExpandedParts(new Set(filteredGroups.map(g => g.part_number)))
        }
        setExpandAll(!expandAll)
    }

    // İstatistikler
    const stats = useMemo(() => {
        return {
            totalParts: groupedData.length,
            totalDollies: data?.length || 0,
            avgTotal: groupedData.reduce((sum, g) => sum + (g.avg_total || 0), 0) / (groupedData.length || 1)
        }
    }, [groupedData, data])

    if (!data || data.length === 0) {
        return (
            <div className="expandable-table-section">
                <h3>📂 Part → Dolly Kırılımı</h3>
                <div className="empty-state">
                    <p className="empty-icon">📂</p>
                    <p>Veri bulunamadı</p>
                </div>
            </div>
        )
    }

    return (
        <div className="expandable-table-section">
            <h3>📂 Part → Dolly Kırılımı</h3>
            <p className="section-sub">Part numarasına göre gruplandırılmış dolly listesi. Detayları görmek için + butonuna tıklayın.</p>

            <div className="stats-summary">
                <div className="stat-chip">
                    <span className="stat-chip-label">Toplam Part:</span>
                    <span className="stat-chip-value">{stats.totalParts}</span>
                </div>
                <div className="stat-chip">
                    <span className="stat-chip-label">Toplam Dolly:</span>
                    <span className="stat-chip-value">{stats.totalDollies}</span>
                </div>
                <div className="stat-chip">
                    <span className="stat-chip-label">Ort. Süre:</span>
                    <span className="stat-chip-value">{Math.round(stats.avgTotal)} dk</span>
                </div>
            </div>

            <div className="table-header-actions">
                <input
                    type="text"
                    className="search-input"
                    placeholder="🔍 Part, Dolly, Sefer veya Plaka ara..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                <button className="expand-all-btn" onClick={toggleExpandAll}>
                    {expandAll ? '📁 Tümünü Kapat' : '📂 Tümünü Aç'}
                </button>
            </div>

            <div className="expandable-table-container">
                <table className="expandable-table">
                    <thead>
                        <tr>
                            <th style={{ width: '40px' }}></th>
                            <th>Part / Dolly No</th>
                            <th>Grup</th>
                            <th>Sefer</th>
                            <th>Plaka</th>
                            <th>EOL → Terminal</th>
                            <th>Terminal → ASN</th>
                            <th>ASN → Irsaliye</th>
                            <th>Toplam Süre</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filteredGroups.map((group) => {
                            const isExpanded = expandedParts.has(group.part_number) || expandAll

                            return (
                                <React.Fragment key={group.part_number}>
                                    {/* Part Row */}
                                    <tr className="part-row" onClick={() => togglePart(group.part_number)}>
                                        <td>
                                            <button
                                                className={`expand-btn ${isExpanded ? 'expanded' : ''}`}
                                                onClick={(e) => { e.stopPropagation(); togglePart(group.part_number) }}
                                            >
                                                {isExpanded ? '−' : '+'}
                                            </button>
                                        </td>
                                        <td>
                                            <span className="part-badge">{group.part_number}</span>
                                            <span className="dolly-count-badge" style={{ marginLeft: '10px' }}>
                                                🚛 {group.dollies.length} dolly
                                            </span>
                                        </td>
                                        <td>
                                            <span className="group-tag">{group.group_name || 'Diğer'}</span>
                                        </td>
                                        <td>
                                            <span className="sefer-tag">{group.sefer_count} sefer</span>
                                        </td>
                                        <td>
                                            <span className="plaka-tag">{group.plaka_count} plaka</span>
                                        </td>
                                        <td>
                                            {group.avg_wait !== null ? (
                                                <span className={`avg-badge ${getDurationClass(group.avg_wait)}`}>
                                                    Ø {group.avg_wait} dk
                                                </span>
                                            ) : '-'}
                                        </td>
                                        <td>
                                            {group.avg_loading !== null ? (
                                                <span className={`avg-badge ${getDurationClass(group.avg_loading)}`}>
                                                    Ø {group.avg_loading} dk
                                                </span>
                                            ) : '-'}
                                        </td>
                                        <td>
                                            {group.avg_terminal !== null ? (
                                                <span className={`avg-badge ${getDurationClass(group.avg_terminal)}`}>
                                                    Ø {group.avg_terminal} dk
                                                </span>
                                            ) : '-'}
                                        </td>
                                        <td>
                                            {group.avg_total !== null ? (
                                                <span className={`avg-badge ${getDurationClass(group.avg_total)}`}>
                                                    Ø {group.avg_total} dk
                                                </span>
                                            ) : '-'}
                                        </td>
                                    </tr>

                                    {/* Dolly Rows (expanded) */}
                                    {isExpanded && group.dollies.map((dolly, idx) => (
                                        <tr key={`${dolly.dolly_no}-${idx}`} className="dolly-row">
                                            <td></td>
                                            <td>
                                                <div className="indent-cell">
                                                    <span className="indent-line"></span>
                                                    <span style={{ fontWeight: 500, color: '#c8102e' }}>{dolly.dolly_no}</span>
                                                    <span style={{ marginLeft: '8px', color: '#888', fontSize: '0.75rem' }}>
                                                        {dolly.vin_no ? `(${dolly.vin_no.slice(-6)})` : ''}
                                                    </span>
                                                </div>
                                            </td>
                                            <td style={{ paddingLeft: '14px' }}>{dolly.eol_name || '-'}</td>
                                            <td style={{ paddingLeft: '14px' }}>
                                                {dolly.sefer_numarasi ? (
                                                    <span className="sefer-tag">{dolly.sefer_numarasi}</span>
                                                ) : '-'}
                                            </td>
                                            <td style={{ paddingLeft: '14px' }}>
                                                {dolly.plaka_no ? (
                                                    <span className="plaka-tag">{dolly.plaka_no}</span>
                                                ) : '-'}
                                            </td>
                                            <td style={{ paddingLeft: '14px' }}>
                                                {dolly.wait_before_scan_min !== null ? (
                                                    <span className={`avg-badge ${getDurationClass(dolly.wait_before_scan_min)}`}>
                                                        {dolly.wait_before_scan_min} dk
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td style={{ paddingLeft: '14px' }}>
                                                {dolly.loading_duration_min !== null ? (
                                                    <span className={`avg-badge ${getDurationClass(dolly.loading_duration_min)}`}>
                                                        {dolly.loading_duration_min} dk
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td style={{ paddingLeft: '14px' }}>
                                                {dolly.terminal_duration_min !== null ? (
                                                    <span className={`avg-badge ${getDurationClass(dolly.terminal_duration_min)}`}>
                                                        {dolly.terminal_duration_min} dk
                                                    </span>
                                                ) : '-'}
                                            </td>
                                            <td style={{ paddingLeft: '14px' }}>
                                                {dolly.total_minutes !== null ? (
                                                    <span className={`avg-badge ${getDurationClass(dolly.total_minutes)}`}>
                                                        {dolly.total_minutes} dk
                                                    </span>
                                                ) : '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </React.Fragment>
                            )
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default ExpandableDollyTable
