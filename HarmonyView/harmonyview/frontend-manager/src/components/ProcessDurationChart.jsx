import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts'
import './ProcessDurationChart.css'

function ProcessDurationChart({ data }) {
  // Veri yoksa veya dolly sayısı 0 ise kullanıcıya boş durum göster.
  const dollyCount = data?.total_process_duration?.dolly_count || 0
  if (!data || dollyCount === 0) {
    return (
      <div className="process-duration-chart empty-state">
        <div className="empty-card">
          <p className="empty-icon">🕒</p>
          <p className="empty-title">Süreç verisi bulunamadı</p>
          <p className="empty-desc">Seçili tarih/shift için kayıt yok. Tarih aralığını genişletmeyi deneyin.</p>
        </div>
      </div>
    )
  }

  const chartData = [
    {
      stage: data.production_duration.stage_name,
      'Ortalama': data.production_duration.avg_duration_minutes,
      'Minimum': data.production_duration.min_duration_minutes,
      'Maksimum': data.production_duration.max_duration_minutes
    },
    {
      stage: 'Okutulmadan\nBekleme',
      'Ortalama': data.wait_before_scan_duration.avg_duration_minutes,
      'Minimum': data.wait_before_scan_duration.min_duration_minutes,
      'Maksimum': data.wait_before_scan_duration.max_duration_minutes
    },
    {
      stage: 'Okutulma\nSüresi',
      'Ortalama': data.scanning_duration.avg_duration_minutes,
      'Minimum': data.scanning_duration.min_duration_minutes,
      'Maksimum': data.scanning_duration.max_duration_minutes
    },
    {
      stage: 'ASN/İrsaliye\nBekleme',
      'Ortalama': data.wait_after_scan_duration.avg_duration_minutes,
      'Minimum': data.wait_after_scan_duration.min_duration_minutes,
      'Maksimum': data.wait_after_scan_duration.max_duration_minutes
    },
    {
      stage: 'Toplam\nSüreç',
      'Ortalama': data.total_process_duration.avg_duration_minutes,
      'Minimum': data.total_process_duration.min_duration_minutes,
      'Maksimum': data.total_process_duration.max_duration_minutes
    }
  ]

  const items = data.items || []

  return (
    <div className="process-duration-chart">
      <header className="section-header">
        <div>
          <h3>Süreç Kırılımı</h3>
          <p className="section-sub">Ortalama/Min/Maks grafiğin altında liste halinde detay</p>
        </div>
        <div className="chip">{items.length} kayıt</div>
      </header>

      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 80 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="stage" 
            angle={-15}
            textAnchor="end"
            height={100}
            tick={{ fontSize: 13, fill: '#333', fontWeight: 500 }}
          />
          <YAxis 
            label={{ value: 'Süre (Dakika)', angle: -90, position: 'insideLeft', style: { fill: '#666', fontSize: 14 } }}
            tick={{ fontSize: 13, fill: '#666' }}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '2px solid #c8102e',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              padding: '12px'
            }}
            formatter={(value) => [`${value.toFixed(1)} dakika`, '']}
            labelStyle={{ fontWeight: 'bold', marginBottom: '8px' }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
          <Bar dataKey="Ortalama" fill="#c8102e" radius={[8, 8, 0, 0]} />
          <Bar dataKey="Minimum" fill="#2563eb" radius={[8, 8, 0, 0]} />
          <Bar dataKey="Maksimum" fill="#f59e0b" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
      
      <div className="process-summary">
        <div className="summary-item">
          <span className="summary-label">Dolly Sayısı:</span>
          <span className="summary-value">{data.total_process_duration.dolly_count}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Ortalama Toplam Süre:</span>
          <span className="summary-value">{data.total_process_duration.avg_duration_minutes.toFixed(1)} dk</span>
        </div>
      </div>

      {items.length > 0 && (
        <div className="process-table">
          <div className="table-head">
            <span>Dolly</span>
            <span>Parça</span>
            <span>Sefer No</span>
            <span>Plaka</span>
            <span>Okutulmadan Bekleme</span>
            <span>Yükleme Süresi</span>
            <span>ASN/İrsaliye Bekleme</span>
            <span>Toplam</span>
          </div>
          {items.map((row) => (
            <div className="table-row" key={row.dolly_no}>
              <span className="mono">{row.dolly_no || '-'}</span>
              <span className="mono">{row.part_number || '-'}</span>
              <span>{row.sefer_numarasi || '-'}</span>
              <span>{row.plaka_no || '-'}</span>
              <span>{row.wait_before_scan_minutes ?? '-'} dk</span>
              <span>{row.loading_duration_minutes ?? '-'} dk</span>
              <span>{row.shipment_prep_minutes ?? '-'} dk</span>
              <span className="bold">{row.total_minutes ?? '-'} dk</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default ProcessDurationChart
