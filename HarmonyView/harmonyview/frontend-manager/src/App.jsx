import { useState, useEffect, useCallback } from 'react'
import './App.css'
import ChatWidget from './components/ChatWidget'

// Removed Recharts due to React 19 incompatibility - using CSS-based charts instead

const API_URL = import.meta.env.VITE_MANAGER_API_URL || 'http://localhost:8001'

// Format helpers
const formatNumber = (n) => n?.toLocaleString('tr-TR') || '0'
const formatDuration = (min) => {
  if (min === null || min === undefined) return '-'
  // Round to 1 decimal place to handle repeating decimals
  const roundedMin = Math.round(min * 10) / 10
  if (roundedMin < 60) return `${roundedMin} dk`
  const h = Math.floor(roundedMin / 60)
  const m = Math.round(roundedMin % 60)
  return `${h}s ${m}dk`
}

const getDurationClass = (min) => {
  if (min === null || min === undefined) return ''
  if (min <= 10) return 'fast'
  if (min <= 30) return 'normal'
  return 'slow'
}

// Color palette for charts
const COLORS = ['#e74c3c', '#00b894', '#0984e3', '#fdcb6e', '#6c5ce7', '#fd79a8', '#00cec9', '#fab1a0', '#74b9ff', '#a29bfe']

function App() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [data, setData] = useState(null)

  // Filters
  const [startDate, setStartDate] = useState(() => {
    const d = new Date()
    d.setDate(d.getDate() - 7)
    return d.toISOString().split('T')[0]
  })
  const [endDate, setEndDate] = useState(() => new Date().toISOString().split('T')[0])
  const [shift, setShift] = useState('')
  const [minVin, setMinVin] = useState('')
  const [hat, setHat] = useState('')
  const [hoveredSlice, setHoveredSlice] = useState(null) // { chart: 'adet'|'dolly', index, eol, value, pct }
  const [hoveredHour, setHoveredHour] = useState(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate
      })
      if (shift) params.append('shift', shift)
      if (minVin) params.append('min_vin', minVin)
      if (hat) params.append('hat', hat)

      const res = await fetch(`${API_URL}/api/dashboard?${params}`)
      if (!res.ok) throw new Error(`API Error: ${res.status}`)

      const json = await res.json()
      setData(json)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, shift, hat, minVin])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 60000) // Auto refresh every 60s
    return () => clearInterval(interval)
  }, [fetchData])

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="header-logo">
            <img src="/img/logo.png" alt="Logo" style={{ height: 32, marginRight: 8 }} onError={(e) => { e.target.style.display = 'none' }} />
            <span>MAGNA<span className="brand-sub">Harmony</span></span>
          </div>

          <nav className="header-nav">
            <button className="active">Manager Dashboard</button>
          </nav>

          <div className="header-user">
            <span className="status-dot"></span>

          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="main-content">
        {/* Error */}
        {error && (
          <div className="error-message">
            <strong>Hata:</strong> {error}
            <button onClick={fetchData} style={{ marginLeft: 16 }}>Yeniden Dene</button>
          </div>
        )}

        {/* Filters */}
        <div className="filters-bar">
          <div className="filter-group">
            <label>Başlangıç</label>
            <input
              type="date"
              value={startDate}
              onChange={e => setStartDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Bitiş</label>
            <input
              type="date"
              value={endDate}
              onChange={e => setEndDate(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label>Vardiya</label>
            <select value={shift} onChange={e => setShift(e.target.value)}>
              <option value="">Tümü</option>
              <option value="1">1. Vardiya (00-08)</option>
              <option value="2">2. Vardiya (08-16)</option>
              <option value="3">3. Vardiya (16-24)</option>
            </select>
          </div>
          <div className="filter-group">
            <label>Hat</label>
            <select value={hat} onChange={e => setHat(e.target.value)}>
              <option value="">Tümü</option>
              <option value="J74 FR BUMPER SEQUENCING EOL">J74 Bumper</option>
              <option value="J74 HEADLAMP FINISHER SIRALAMA EOL">J74 Headlamp</option>
              <option value="J74 LLS SIRALAMA EOL">J74 LLS</option>
              <option value="J74-MR-EOL">J74 MR</option>
              <option value="V710-LLS-EOL">V710 LLS</option>
              <option value="V710-MR-EOL">V710 MR</option>
              <option value="V710-FR-EOL">V710 Bumper</option>
            </select>
          </div>
          <button className="filter-button" onClick={fetchData} disabled={loading}>
            {loading ? 'Yükleniyor...' : 'Filtrele'}
          </button>
        </div>

        {/* Loading */}
        {loading && !data && (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
          </div>
        )}

        {/* Dashboard Content */}
        {data && (
          <>
            <div className="stats-grid" style={{ marginBottom: 24, gridTemplateColumns: 'repeat(3, 1fr)' }}>
              <div className="stat-card primary">
                <div className="stat-icon"></div>
                <div className="stat-value">{formatNumber(data.summary.total_sefer)}</div>
                <div className="stat-label">Toplam Sefer</div>
              </div>
              <div className="stat-card success">
                <div className="stat-icon"></div>
                <div className="stat-value">{formatNumber(data.summary.total_dolly)}</div>
                <div className="stat-label">Toplam Dolly(Kasa)</div>
              </div>
              <div className="stat-card info">
                <div className="stat-icon"></div>
                <div className="stat-value">{formatNumber(data.summary.total_adet)}</div>
                <div className="stat-label">Toplam Parça Adet</div>
              </div>
            </div>

            {/* Sevkıyat Detayları Listesi */}
            <div className="dashboard-card col-12" style={{ marginBottom: 24 }}>
              <div className="card-header">
                <h3>Sevkıyat Detayları</h3>
                <span className="badge">{data.shipment_details?.length || 0} kayıt</span>
              </div>
              <div className="card-content" style={{ maxHeight: 400, overflow: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Vrd</th>
                      <th>Gonderim Tarihi</th>
                      <th>Dolly Adet</th>
                      <th>Part No</th>
                      <th>Grup (Hatlar)</th>
                      <th>Plaka</th>
                      <th>Sefer No</th>
                      <th>Okutma Başl.</th>
                      <th>Submit</th>
                      <th>ASN/Irsaliye</th>
                      <th>Yükleme Süre</th>
                      <th>İşlem Süre</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.shipment_details?.length > 0 ? (
                      data.shipment_details.map((s, i) => (
                        <tr key={i}>
                          <td className="number" style={{ fontWeight: 'bold', color: '#636e72' }}>{s.vardiya}</td>
                          <td><strong>{s.gonderim_tarihi}</strong></td>
                          <td className="number">{s.dolly_count}</td>
                          <td>{s.part_number}</td>
                          <td>
                            <div>{s.group_name}</div>
                            <div style={{ fontSize: '10px', color: '#636e72' }}>{s.eol_names}</div>
                          </td>
                          <td>{s.plaka_no}</td>
                          <td><strong>{s.sefer_no || ''}</strong></td>
                          <td>{s.loading_start}</td>
                          <td><strong style={{ color: '#0984e3' }}>{s.submit_date}</strong></td>
                          <td>{s.doc_date}</td>
                          <td className="number">
                            <span className={`duration ${getDurationClass(s.loading_duration_min)}`}>
                              {s.loading_duration_min !== null ? `${s.loading_duration_min.toFixed(0)} dk` : '-'}
                            </span>
                          </td>
                          <td className="number">
                            <span className={`duration ${getDurationClass(s.process_duration_min)}`}>
                              {s.process_duration_min !== null ? `${s.process_duration_min.toFixed(0)} dk` : '-'}
                            </span>
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="12" style={{ textAlign: 'center', color: '#636e72', padding: 20 }}>
                          Sevkıyat verisi bulunamadı
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Dashboard Grid */}
            <div className="dashboard-grid">
              {/* EOL Distribution - Pie Chart */}
              <div className="dashboard-card col-6">
                <div className="card-header">
                  <h3>EOL Bazlı Dağılım</h3>
                  <span className="badge">{data.eol_distribution?.length || 0} EOL</span>
                </div>
                <div className="card-content" style={{ minHeight: 380, padding: '20px 24px' }}>
                  {data.eol_distribution && data.eol_distribution.length > 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                      {/* İki pasta grafik yan yana */}
                      <div style={{ display: 'flex', justifyContent: 'center', gap: 48, flexWrap: 'wrap' }}>

                        {/* ADET Bazlı Pasta */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                          <div style={{ fontSize: 12, fontWeight: 700, color: '#636e72', textTransform: 'uppercase' }}>Adet Bazlı</div>
                          {(() => {
                            const total = data.eol_distribution.reduce((s, e) => s + e.total_adet, 0);
                            let cumulativePct = 0;
                            const slices = data.eol_distribution.map((eol, i) => {
                              const pct = total > 0 ? (eol.total_adet / total * 100) : 0;
                              const startAngle = cumulativePct * 3.6; // 360/100
                              cumulativePct += pct;
                              const endAngle = cumulativePct * 3.6;
                              return { eol, pct, startAngle, endAngle, color: COLORS[i % COLORS.length], index: i };
                            });
                            const gradientParts = slices.map(s => `${s.color} ${s.startAngle / 3.6}% ${s.endAngle / 3.6}%`);
                            const gradient = `conic-gradient(${gradientParts.join(', ')})`;

                            return (
                              <div style={{ position: 'relative' }}
                                onMouseLeave={() => setHoveredSlice(null)}
                              >
                                <div style={{
                                  width: 'clamp(100px, 12vw, 140px)',
                                  aspectRatio: '1 / 1',
                                  borderRadius: '50%',
                                  background: gradient,
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  position: 'relative',
                                  cursor: 'pointer'
                                }}>
                                  {/* Invisible slice overlays for hover detection */}
                                  {slices.map((slice, i) => {
                                    const midAngle = (slice.startAngle + slice.endAngle) / 2;
                                    const rad = (midAngle - 90) * Math.PI / 180;
                                    const x = 70 + 50 * Math.cos(rad);
                                    const y = 70 + 50 * Math.sin(rad);
                                    return (
                                      <div
                                        key={i}
                                        style={{
                                          position: 'absolute',
                                          left: x - 15,
                                          top: y - 15,
                                          width: 30,
                                          height: 30,
                                          borderRadius: '50%',
                                          cursor: 'pointer',
                                          zIndex: 10
                                        }}
                                        onMouseEnter={() => setHoveredSlice({
                                          chart: 'adet',
                                          index: i,
                                          eol: slice.eol.eol_name,
                                          value: slice.eol.total_adet,
                                          pct: slice.pct.toFixed(1)
                                        })}
                                      />
                                    );
                                  })}
                                </div>
                                {/* Tooltip */}
                                {hoveredSlice && hoveredSlice.chart === 'adet' && (
                                  <div style={{
                                    position: 'absolute',
                                    top: -40,
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    background: '#2d3436',
                                    color: '#fff',
                                    padding: '6px 12px',
                                    borderRadius: 6,
                                    fontSize: 11,
                                    whiteSpace: 'nowrap',
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                                    zIndex: 100
                                  }}>
                                    <strong>{hoveredSlice.eol}</strong><br />
                                    {formatNumber(hoveredSlice.value)} adet ({hoveredSlice.pct}%)
                                  </div>
                                )}
                                <div style={{
                                  position: 'absolute',
                                  top: '50%',
                                  left: '50%',
                                  transform: 'translate(-50%, -50%)',
                                  width: '50%',
                                  aspectRatio: '1 / 1',
                                  borderRadius: '50%',
                                  background: '#fff',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.05)',
                                  pointerEvents: 'none'
                                }}>
                                  <div style={{ fontSize: 'clamp(12px, 1.5vw, 16px)', fontWeight: 700, color: '#2d3436' }}>
                                    {formatNumber(total)}
                                  </div>
                                  <div style={{ fontSize: 'clamp(7px, 1vw, 9px)', color: '#636e72' }}>ADET</div>
                                </div>
                              </div>
                            );
                          })()}
                        </div>

                        {/* DOLLY Bazlı Pasta */}
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
                          <div style={{ fontSize: 12, fontWeight: 700, color: '#636e72', textTransform: 'uppercase' }}>Dolly Bazlı</div>
                          {(() => {
                            const total = data.eol_distribution.reduce((s, e) => s + e.dolly_count, 0);
                            let cumulativePct = 0;
                            const slices = data.eol_distribution.map((eol, i) => {
                              const pct = total > 0 ? (eol.dolly_count / total * 100) : 0;
                              const startAngle = cumulativePct * 3.6;
                              cumulativePct += pct;
                              const endAngle = cumulativePct * 3.6;
                              return { eol, pct, startAngle, endAngle, color: COLORS[i % COLORS.length], index: i };
                            });
                            const gradientParts = slices.map(s => `${s.color} ${s.startAngle / 3.6}% ${s.endAngle / 3.6}%`);
                            const gradient = `conic-gradient(${gradientParts.join(', ')})`;

                            return (
                              <div style={{ position: 'relative' }}
                                onMouseLeave={() => setHoveredSlice(null)}
                              >
                                <div style={{
                                  width: 'clamp(100px, 12vw, 140px)',
                                  aspectRatio: '1 / 1',
                                  borderRadius: '50%',
                                  background: gradient,
                                  boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                  position: 'relative',
                                  cursor: 'pointer'
                                }}>
                                  {/* Invisible slice overlays for hover detection */}
                                  {slices.map((slice, i) => {
                                    const midAngle = (slice.startAngle + slice.endAngle) / 2;
                                    const rad = (midAngle - 90) * Math.PI / 180;
                                    const x = 70 + 50 * Math.cos(rad);
                                    const y = 70 + 50 * Math.sin(rad);
                                    return (
                                      <div
                                        key={i}
                                        style={{
                                          position: 'absolute',
                                          left: x - 15,
                                          top: y - 15,
                                          width: 30,
                                          height: 30,
                                          borderRadius: '50%',
                                          cursor: 'pointer',
                                          zIndex: 10
                                        }}
                                        onMouseEnter={() => setHoveredSlice({
                                          chart: 'dolly',
                                          index: i,
                                          eol: slice.eol.eol_name,
                                          value: slice.eol.dolly_count,
                                          pct: slice.pct.toFixed(1)
                                        })}
                                      />
                                    );
                                  })}
                                </div>
                                {/* Tooltip */}
                                {hoveredSlice && hoveredSlice.chart === 'dolly' && (
                                  <div style={{
                                    position: 'absolute',
                                    top: -40,
                                    left: '50%',
                                    transform: 'translateX(-50%)',
                                    background: '#2d3436',
                                    color: '#fff',
                                    padding: '6px 12px',
                                    borderRadius: 6,
                                    fontSize: 11,
                                    whiteSpace: 'nowrap',
                                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                                    zIndex: 100
                                  }}>
                                    <strong>{hoveredSlice.eol}</strong><br />
                                    {formatNumber(hoveredSlice.value)} dolly ({hoveredSlice.pct}%)
                                  </div>
                                )}
                                <div style={{
                                  position: 'absolute',
                                  top: '50%',
                                  left: '50%',
                                  transform: 'translate(-50%, -50%)',
                                  width: '50%',
                                  aspectRatio: '1 / 1',
                                  borderRadius: '50%',
                                  background: '#fff',
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.05)',
                                  pointerEvents: 'none'
                                }}>
                                  <div style={{ fontSize: 'clamp(12px, 1.5vw, 16px)', fontWeight: 700, color: '#2d3436' }}>
                                    {formatNumber(total)}
                                  </div>
                                  <div style={{ fontSize: 'clamp(7px, 1vw, 9px)', color: '#636e72' }}>DOLLY</div>
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                      </div>

                      {/* Ortak Legend */}
                      <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                        gap: 8,
                        padding: '12px 16px',
                        background: '#f8f9fa',
                        borderRadius: 8
                      }}>
                        {data.eol_distribution.slice(0, 8).map((eol, i) => (
                          <div key={`legend-${i}`} style={{
                            display: 'flex',
                            alignItems: 'center',
                            fontSize: 11,
                            gap: 6
                          }}>
                            <div style={{
                              width: 10,
                              height: 10,
                              borderRadius: 2,
                              background: COLORS[i % COLORS.length],
                              flexShrink: 0
                            }} />
                            <span style={{
                              flex: 1,
                              color: '#2d3436',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }} title={eol.eol_name}>
                              {eol.eol_name}
                            </span>
                            <span style={{ fontWeight: 600, color: '#2d3436' }}>
                              {formatNumber(eol.total_adet)}
                            </span>
                            <span style={{ color: '#636e72', fontSize: 10 }}>
                              ({eol.dolly_count})
                            </span>
                          </div>
                        ))}
                      </div>

                      {/* EOL Süre Analizi Tablosu */}
                      <div style={{ marginTop: 16 }}>
                        <div style={{
                          fontSize: 12,
                          fontWeight: 700,
                          color: '#636e72',
                          marginBottom: 8,
                          textTransform: 'uppercase'
                        }}>
                          Hat Bazlı Süre Analizi
                        </div>
                        <table style={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          fontSize: 'clamp(10px, 1.2vw, 12px)'
                        }}>
                          <thead>
                            <tr style={{ background: '#f1f3f4', textAlign: 'left' }}>
                              <th style={{ padding: '8px 12px', fontWeight: 600 }}>Üretim Hattı</th>
                              <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'center' }}>VIN/Dolly</th>
                              <th style={{ padding: '8px 12px', fontWeight: 600, textAlign: 'right' }}>Ort. Süre</th>
                            </tr>
                          </thead>
                          <tbody>
                            {data.eol_distribution.map((eol, i) => {
                              const vinsPerDolly = eol.dolly_count > 0
                                ? (eol.vin_count / eol.dolly_count).toFixed(1)
                                : '-';
                              const maxDuration = Math.max(...data.eol_distribution.map(e => e.avg_duration_min || 0));
                              const duration = eol.avg_duration_min || 0;
                              // Color: green for fast, red for slow
                              const hue = maxDuration > 0 ? Math.max(0, 120 - (duration / maxDuration * 120)) : 120;
                              const barColor = `hsl(${hue}, 70%, 50%)`;

                              return (
                                <tr key={`eol-row-${i}`} style={{
                                  borderBottom: '1px solid #eee',
                                  background: i % 2 === 0 ? '#fff' : '#fafafa'
                                }}>
                                  <td style={{ padding: '8px 12px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                      <div style={{
                                        width: 8,
                                        height: 8,
                                        borderRadius: 2,
                                        background: COLORS[i % COLORS.length],
                                        flexShrink: 0
                                      }} />
                                      <span style={{
                                        whiteSpace: 'nowrap',
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                        maxWidth: 'clamp(80px, 15vw, 150px)'
                                      }} title={eol.eol_name}>
                                        {eol.eol_name}
                                      </span>
                                    </div>
                                  </td>
                                  <td style={{ padding: '8px 12px', textAlign: 'center' }}>
                                    <span style={{
                                      background: parseFloat(vinsPerDolly) >= 2 ? '#e8f5e9' : '#fff3e0',
                                      color: parseFloat(vinsPerDolly) >= 2 ? '#2e7d32' : '#ef6c00',
                                      padding: '2px 8px',
                                      borderRadius: 12,
                                      fontWeight: 600,
                                      fontSize: 11
                                    }}>
                                      {vinsPerDolly}
                                    </span>
                                  </td>
                                  <td style={{ padding: '8px 12px', textAlign: 'right' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 8 }}>
                                      <div style={{
                                        width: 40,
                                        height: 6,
                                        background: '#eee',
                                        borderRadius: 3,
                                        overflow: 'hidden'
                                      }}>
                                        <div style={{
                                          width: `${maxDuration > 0 ? (duration / maxDuration * 100) : 0}%`,
                                          height: '100%',
                                          background: barColor,
                                          borderRadius: 3
                                        }} />
                                      </div>
                                      <span style={{ fontWeight: 600, color: barColor, minWidth: 50 }}>
                                        {duration ? `${duration} dk` : '-'}
                                      </span>
                                    </div>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <p>EOL verisi bulunamadı</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Group Duration Analysis - Süre bazlı karşılaştırma */}
              <div className="dashboard-card col-6">
                <div className="card-header">
                  <h3>Grup Ortalama Süreleri</h3>
                  <span className="badge">{data.group_performance?.length || 0} grup</span>
                </div>
                <div className="card-content" style={{ minHeight: 300, padding: 16 }}>
                  {data.group_performance && data.group_performance.length > 0 ? (
                    <div className="group-duration-chart">
                      {(() => {
                        // Maksimum süreyi bul (bar genişliği için referans)
                        const maxDuration = Math.max(...data.group_performance.map(g => g.avg_duration_min || 0));
                        return data.group_performance.map((grp, i) => {
                          const duration = grp.avg_duration_min || 0;
                          const barWidth = maxDuration > 0 ? (duration / maxDuration * 100) : 0;
                          // Renk: Düşük süre = yeşil, yüksek süre = kırmızı
                          const hue = Math.max(0, 120 - (duration / maxDuration * 120));
                          const barColor = `hsl(${hue}, 70%, 50%)`;

                          return (
                            <div key={`grp-${i}`} style={{ marginBottom: 14 }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                                <span style={{ fontSize: 13, fontWeight: 500, color: '#2d3436' }}>
                                  {grp.group_name.length > 22 ? grp.group_name.substring(0, 22) + '...' : grp.group_name}
                                </span>
                                <span style={{ fontSize: 13, fontWeight: 600, color: barColor }}>
                                  {duration.toFixed(0)} dk
                                </span>
                              </div>
                              <div style={{ height: 22, background: '#dfe6e9', borderRadius: 4, overflow: 'hidden' }}>
                                <div style={{
                                  width: `${barWidth}%`,
                                  height: '100%',
                                  background: barColor,
                                  borderRadius: 4,
                                  transition: 'width 0.3s'
                                }} />
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2, fontSize: 10, color: '#636e72' }}>
                                <span>{formatNumber(grp.total_adet)} adet</span>
                                <span>Min: {grp.min_duration_min || 0}dk | Max: {grp.max_duration_min || 0}dk</span>
                              </div>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <p>Grup verisi bulunamadı</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Forklift Operators */}
              <div className="dashboard-card col-6">
                <div className="card-header">
                  <h3>Forklift Operatörleri</h3>
                  <span className="badge">Top 10</span>
                </div>
                <div className="card-content" style={{ maxHeight: 300, overflow: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Operatör</th>
                        <th>Sefer</th>
                        <th>Dolly</th>
                        <th>Adet</th>
                        <th>Ort. Taşıma</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.forklift_operators?.slice(0, 10).map((op, i) => (
                        <tr key={i}>
                          <td><strong>{op.operator_name}</strong></td>
                          <td className="number">{op.sefer_count}</td>
                          <td className="number">{op.dolly_count}</td>
                          <td className="number">{formatNumber(op.total_adet)}</td>
                          <td>
                            <span className={`duration ${getDurationClass(op.avg_duration_min)}`}>
                              {formatDuration(op.avg_duration_min)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Data Entry Operators */}
              <div className="dashboard-card col-6">
                <div className="card-header">
                  <h3>Veri Girişçileri</h3>
                  <span className="badge">Top 10</span>
                </div>
                <div className="card-content" style={{ maxHeight: 300, overflow: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Operatör</th>
                        <th>Sefer</th>
                        <th>Dolly</th>
                        <th>Adet</th>
                        <th>Ort. İşlem</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.data_entry_operators?.length > 0 ? (
                        data.data_entry_operators.slice(0, 10).map((op, i) => (
                          <tr key={i}>
                            <td><strong>{op.operator_name}</strong></td>
                            <td className="number">{op.sefer_count}</td>
                            <td className="number">{op.dolly_count}</td>
                            <td className="number">{formatNumber(op.total_adet)}</td>
                            <td>
                              <span className={`duration ${getDurationClass(op.avg_duration_min)}`}>
                                {formatDuration(op.avg_duration_min)}
                              </span>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" style={{ textAlign: 'center', color: '#636e72' }}>
                            Veri girişçi bilgisi bulunamadı
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Sefer List */}
              <div className="dashboard-card col-12">
                <div className="card-header">
                  <h3>Son Seferler</h3>
                  <span className="badge">{data.sefer_list?.length || 0} sefer</span>
                </div>
                <div className="card-content" style={{ maxHeight: 350, overflow: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Sefer No</th>
                        <th>Plaka</th>
                        <th>Operatör</th>
                        <th>Dolly</th>
                        <th>Adet</th>
                        <th>Süre</th>
                        <th>Tarih</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.sefer_list?.map((s, i) => (
                        <tr key={i}>
                          <td><strong>{s.sefer_numarasi || ''}</strong></td>
                          <td>{s.plaka_no || '-'}</td>
                          <td>{s.forklift_operator || '-'}</td>
                          <td className="number">{s.dolly_count}</td>
                          <td className="number">{s.total_adet}</td>
                          <td>
                            <span className={`duration ${getDurationClass(s.toplam_sure_min)}`}>
                              {formatDuration(s.toplam_sure_min)}
                            </span>
                          </td>
                          <td>{s.islem_tarihi}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Hourly Activity Wave Chart */}
              <div className="dashboard-card col-12">
                <div className="card-header">
                  <h3>Saatlik Aktivite Grafiği (24 Saat)</h3>
                </div>
                <div className="card-content" style={{ minHeight: 400, padding: 20 }}>
                  {data.hourly_throughput && data.hourly_throughput.length > 0 ? (
                    <div className="activity-wave-chart">
                      {(() => {
                        const hours = data.hourly_throughput;
                        const maxVal = Math.max(...hours.map(h => h.total_adet));
                        const minVal = Math.min(...hours.map(h => h.total_adet));
                        const peakHour = hours.reduce((max, hr) => hr.total_adet > max.total_adet ? hr : max);

                        // Larger dimensions for col-12
                        const chartWidth = 1000;
                        const chartHeight = 300;
                        const padding = { top: 30, right: 30, bottom: 40, left: 60 };
                        const innerWidth = chartWidth - padding.left - padding.right;
                        const innerHeight = chartHeight - padding.top - padding.bottom;

                        // Calculate points
                        const points = hours.map((hr, i) => ({
                          x: padding.left + (i / (hours.length - 1)) * innerWidth,
                          y: padding.top + innerHeight - ((hr.total_adet - minVal) / (maxVal - minVal || 1)) * innerHeight,
                          value: hr.total_adet,
                          hour: hr.saat
                        }));

                        // Create smooth curve path
                        const linePath = points.reduce((path, p, i) => {
                          if (i === 0) return `M ${p.x} ${p.y}`;
                          const prev = points[i - 1];
                          const cp1x = prev.x + (p.x - prev.x) / 3;
                          const cp2x = prev.x + 2 * (p.x - prev.x) / 3;
                          return `${path} C ${cp1x} ${prev.y}, ${cp2x} ${p.y}, ${p.x} ${p.y}`;
                        }, '');

                        // Area path (filled)
                        const areaPath = `${linePath} L ${points[points.length - 1].x} ${chartHeight - padding.bottom} L ${points[0].x} ${chartHeight - padding.bottom} Z`;

                        return (
                          <div style={{ position: 'relative' }}>
                            <svg width="100%" viewBox={`0 0 ${chartWidth} ${chartHeight + 20}`} style={{ overflow: 'visible' }}>
                              {/* Gradient definitions */}
                              <defs>
                                <linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                                  <stop offset="0%" stopColor="#ef4444" stopOpacity="0.8" />
                                  <stop offset="40%" stopColor="#f97316" stopOpacity="0.6" />
                                  <stop offset="70%" stopColor="#22c55e" stopOpacity="0.4" />
                                  <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.2" />
                                </linearGradient>
                                <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                  <stop offset="0%" stopColor="#3b82f6" />
                                  <stop offset="50%" stopColor="#f97316" />
                                  <stop offset="100%" stopColor="#ef4444" />
                                </linearGradient>
                                <filter id="glow">
                                  <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                                  <feMerge>
                                    <feMergeNode in="coloredBlur" />
                                    <feMergeNode in="SourceGraphic" />
                                  </feMerge>
                                </filter>
                              </defs>

                              {/* Grid lines */}
                              {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => (
                                <line
                                  key={`grid-${i}`}
                                  x1={padding.left}
                                  y1={padding.top + innerHeight * (1 - ratio)}
                                  x2={chartWidth - padding.right}
                                  y2={padding.top + innerHeight * (1 - ratio)}
                                  stroke="#e5e7eb"
                                  strokeDasharray="3,3"
                                />
                              ))}

                              {/* Area fill */}
                              <path d={areaPath} fill="url(#waveGradient)" />

                              {/* Line */}
                              <path
                                d={linePath}
                                fill="none"
                                stroke="url(#lineGradient)"
                                strokeWidth="3"
                                strokeLinecap="round"
                                filter="url(#glow)"
                              />

                              {/* Data points */}
                              {points.map((p, i) => (
                                <g
                                  key={`point-${i}`}
                                  onMouseEnter={() => setHoveredHour(p)}
                                  onMouseLeave={() => setHoveredHour(null)}
                                >
                                  <circle
                                    cx={p.x}
                                    cy={p.y}
                                    r={hoveredHour?.hour === p.hour ? 8 : (p.hour === peakHour.saat ? 6 : 4)}
                                    fill={p.hour === peakHour.saat ? '#ef4444' : '#fff'}
                                    stroke={p.hour === peakHour.saat ? '#ef4444' : '#f97316'}
                                    strokeWidth={hoveredHour?.hour === p.hour ? "3" : "2"}
                                    style={{ cursor: 'pointer', transition: 'all 0.2s' }}
                                  />
                                </g>
                              ))}

                              {/* X-axis labels - Show every 4 hours for 24h view */}
                              {points.filter((_, i) => i % 4 === 0 || i === points.length - 1).map((p, i) => (
                                <text
                                  key={`label-${i}`}
                                  x={p.x}
                                  y={chartHeight - 5}
                                  textAnchor="middle"
                                  fontSize="10"
                                  fill="#6b7280"
                                  fontWeight="500"
                                >
                                  {p.hour}:00
                                </text>
                              ))}

                              {/* Y-axis labels */}
                              <text x={padding.left - 5} y={padding.top} textAnchor="end" fontSize="8" fill="#9ca3af">
                                {formatNumber(maxVal)}
                              </text>
                              <text x={padding.left - 5} y={chartHeight - padding.bottom} textAnchor="end" fontSize="8" fill="#9ca3af">
                                {formatNumber(minVal)}
                              </text>
                            </svg>

                            {/* Custom Tooltip */}
                            {hoveredHour && (
                              <div style={{
                                position: 'absolute',
                                left: hoveredHour.x > chartWidth / 2 ? hoveredHour.x - 120 : hoveredHour.x + 10,
                                top: hoveredHour.y - 60,
                                background: 'rgba(255, 255, 255, 0.95)',
                                padding: '8px 12px',
                                border: '1px solid #dfe6e9',
                                borderRadius: 8,
                                boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                                pointerEvents: 'none',
                                zIndex: 10,
                                animation: 'fadeIn 0.2s'
                              }}>
                                <div style={{ fontSize: 12, fontWeight: 700, color: '#2d3436' }}>{hoveredHour.hour}:00</div>
                                <div style={{ fontSize: 14, color: '#e17055' }}><strong>{formatNumber(hoveredHour.value)}</strong> adet</div>
                              </div>
                            )}
                          </div>
                        );
                      })()}

                      {/* Summary bar */}
                      <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        marginTop: 12,
                        padding: '10px 12px',
                        background: 'linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)',
                        borderRadius: 8,
                        boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
                      }}>
                        <span style={{ fontSize: 11, color: '#92400e' }}>
                          En yoğun: <strong>{data.hourly_throughput.reduce((max, hr) => hr.total_adet > max.total_adet ? hr : max).saat}:00</strong>
                        </span>
                        <span style={{ fontSize: 11, color: '#166534' }}>
                          Toplam: <strong>{formatNumber(data.hourly_throughput.reduce((sum, hr) => sum + hr.total_adet, 0))}</strong>
                        </span>
                      </div>
                    </div>
                  ) : (
                    <div className="empty-state">
                      <p>Saatlik veri bulunamadı</p>
                    </div>
                  )}
                </div>
              </div>



              {/* Part Analysis */}
              <div className="dashboard-card col-12">
                <div className="card-header">
                  <h3>Parça Analizi</h3>
                  <span className="badge">{data.part_analysis?.length || 0} parça</span>
                </div>
                <div className="card-content" style={{ maxHeight: 400, overflow: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Parça No</th>
                        <th>Grup</th>
                        <th>EOL</th>
                        <th>Dolly</th>
                        <th>Adet</th>
                        <th>Ort. Süre</th>
                        <th>Min</th>
                        <th>Max</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.part_analysis?.map((p, i) => (
                        <tr key={i}>
                          <td><strong>{p.part_number}</strong></td>
                          <td>{p.group_name || '-'}</td>
                          <td style={{ fontSize: 11 }}>{p.eol_name || '-'}</td>
                          <td className="number">{p.dolly_count}</td>
                          <td className="number">{formatNumber(p.total_adet)}</td>
                          <td>
                            <span className={`duration ${getDurationClass(p.avg_duration_min)}`}>
                              {formatDuration(p.avg_duration_min)}
                            </span>
                          </td>
                          <td className="number">{formatDuration(p.min_duration_min)}</td>
                          <td className="number">{formatDuration(p.max_duration_min)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </>
        )}
      </main>
      <ChatWidget />
    </div>
  )
}

export default App
