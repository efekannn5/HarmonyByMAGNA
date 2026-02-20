import React from 'react'
import './EOLPerformanceTable.css'

function EOLPerformanceTable({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="eol-performance-table">
        <p className="no-data">EOL performans verisi bulunamadı</p>
      </div>
    )
  }

  return (
    <div className="eol-performance-table">
      <table>
        <thead>
          <tr>
            <th>EOL İstasyonu</th>
            <th>Toplam Dolly</th>
            <th>Toplam Parça</th>
            <th>Ort. Parça/Dolly</th>
            <th>Sefer Sayısı</th>
            <th>ASN Tamamlanma %</th>
          </tr>
        </thead>
        <tbody>
          {data.map((eol, index) => {
            const performanceLevel = 
              eol.asn_completion_rate >= 95 ? 'excellent' :
              eol.asn_completion_rate >= 85 ? 'good' :
              eol.asn_completion_rate >= 70 ? 'average' : 'poor'
            
            return (
              <tr key={index} className={`performance-${performanceLevel}`}>
                <td className="eol-name">{eol.eol_name}</td>
                <td className="text-center">{eol.dolly_count}</td>
                <td className="text-center">{eol.total_quantity}</td>
                <td className="text-center">{eol.avg_quantity_per_dolly.toFixed(1)}</td>
                <td className="text-center">{eol.sefer_count}</td>
                <td className="text-center">
                  <div className="fill-percentage">
                    <div className="fill-bar">
                      <div 
                        className="fill-progress" 
                        style={{ width: `${eol.asn_completion_rate}%` }}
                      ></div>
                    </div>
                    <span>{eol.asn_completion_rate.toFixed(1)}%</span>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default EOLPerformanceTable
