import React, { useState, useEffect, useCallback } from 'react'

const API_URL = `${window.location.protocol}//${window.location.hostname}:8001`

// ─── Vardiya Bilgilerini Hesapla ─────────────────────────────────────
function getShiftInfo() {
  const now = new Date()
  const h = now.getHours()
  const today = now.toISOString().split('T')[0]

  let current, previous;

  if (h >= 0 && h < 8) {
    current = { shift: 1, date: today, label: '1. Vardiya (Gece 00-08)' }
    const yesterday = new Date(now)
    yesterday.setDate(now.getDate() - 1)
    const yDay = yesterday.toISOString().split('T')[0]
    previous = { shift: 3, date: yDay, label: '3. Vardiya (Önceki Gün Akşam)' }
  } else if (h >= 8 && h < 16) {
    current = { shift: 2, date: today, label: '2. Vardiya (Sabah 08-16)' }
    previous = { shift: 1, date: today, label: '1. Vardiya (Gece)' }
  } else {
    current = { shift: 3, date: today, label: '3. Vardiya (Akşam 16-00)' }
    previous = { shift: 2, date: today, label: '2. Vardiya (Sabah)' }
  }
  return { current, previous }
}

// ─── Format yardımcıları ──────────────────────────────────────────────
function fmtDuration(min) {
  if (min === null || min === undefined) return '-'
  const m = Math.round(min)
  if (m < 60) return `${m} dk`
  return `${Math.floor(m / 60)}s ${m % 60}dk`
}

function durationColor(min) {
  if (!min) return 'text-gray-400'
  if (min <= 10) return 'text-emerald-400 font-bold'
  if (min <= 30) return 'text-yellow-400'
  return 'text-red-400 font-bold'
}

// ─── HeaderClock ──────────────────────────────────────────────────────
function HeaderClock() {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <div className="flex flex-col items-center justify-center -space-y-1">
      <span className="text-[1.6vh] font-bold text-gray-300 tracking-wider uppercase">
        {time.toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' })}
      </span>
      <span className="text-[2.6vh] font-black text-white tracking-widest leading-none font-mono">
        {time.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
      </span>
    </div>
  )
}

// ─── Özet Kartı Bileşeni (Kullanıcının gönderdiği görsele uygun) ──────────
function SummaryCard({ title, value, prevValue, colorClass }) {
  const isIncrease = value > prevValue;
  const isDecrease = value < prevValue;

  return (
    <div className="flex-1 summary-card overflow-hidden flex flex-col p-5 relative min-w-[200px]">
      {/* Sol Kenar Çubuğu - Daha parlak accent */}
      <div className={`absolute left-0 top-0 bottom-0 w-1.5 ${colorClass} shadow-[0_0_10px_current]`} style={{ backgroundColor: 'currentColor' }} />

      <div className="flex flex-col">
        <span className="text-white font-black text-[4vh] leading-tight mb-1 drop-shadow-md">
          {value?.toLocaleString('tr-TR') || '0'}
        </span>
        <span className="text-gray-400 font-bold text-[1.4vh] uppercase tracking-[0.1em]">
          {title}
        </span>
      </div>

      {/* Önceki Vardiya Karşılaştırması */}
      <div className="mt-5 pt-4 border-t border-white/5 flex items-center justify-between">
        <div className="flex flex-col">
          <span className="text-gray-500 text-[1.1vh] font-black uppercase tracking-wider">Önceki Vardiya</span>
          <span className="text-gray-300 font-bold text-[2vh]">{prevValue?.toLocaleString('tr-TR') || '0'}</span>
        </div>
        {prevValue > 0 && (
          <div className={`px-2 py-1 rounded-md bg-opacity-10 flex items-center gap-1 ${isIncrease ? 'bg-emerald-500 text-emerald-400' : isDecrease ? 'bg-red-500 text-red-400' : 'bg-gray-500 text-gray-400'}`}>
            <span className="text-[1.3vh] font-black uppercase">
              {isIncrease ? '↑' : isDecrease ? '↓' : '•'}
              %{Math.abs(Math.round(((value - prevValue) / prevValue) * 100))}
            </span>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Sevkıyat Detayları Tablosu (Auto-scroll) ─────────────────────────
function ShipmentTable({ rows, shiftLabel }) {
  const scrollRef = React.useRef(null)

  useEffect(() => {
    const el = scrollRef.current
    if (!el || rows.length === 0) return

    let scrollInterval;
    let pauseTimeout;

    const startScrolling = () => {
      if (scrollInterval) clearInterval(scrollInterval);

      scrollInterval = setInterval(() => {
        if (!el) return

        const currentScroll = Math.ceil(el.scrollTop)
        const maxScroll = el.scrollHeight - el.clientHeight

        // Sona ulaşıldı mı? (2px tolerans)
        if (currentScroll >= maxScroll - 2) {
          clearInterval(scrollInterval);

          pauseTimeout = setTimeout(() => {
            if (!el) return
            el.scrollTo({ top: 0, behavior: 'smooth' });

            // Başa dönme işleminin tamamlanmasını bekle
            pauseTimeout = setTimeout(startScrolling, 2000);
          }, 3000); // Sonda 3 saniye bekle
        } else {
          el.scrollTop += 1;
        }
      }, 40); // 40ms akıcı bir kayma sağlar
    }

    // Veri render edildikten sonra başlat
    const initTimeout = setTimeout(startScrolling, 1500);

    return () => {
      clearInterval(scrollInterval);
      clearTimeout(pauseTimeout);
      clearTimeout(initTimeout);
    }
  }, [rows])

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-auto px-4 pb-4 no-scrollbar"
    >
      <table className="w-full border-collapse text-[1.4vh]">
        <thead className="sticky top-0 z-10">
          <tr className="bg-gray-950 border-b-2 border-gray-800">
            <th className="px-3 py-3 text-left text-gray-500 font-black uppercase tracking-tighter text-[1.1vh] w-12">Vrd</th>
            <th className="px-3 py-3 text-left text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Gönderim Tarihi</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Dolly</th>
            <th className="px-3 py-3 text-left text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Part No</th>
            <th className="px-3 py-3 text-left text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Grup / Hatlar</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Plaka</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Sefer No</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Başl.</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Submit</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">ASN/İrs.</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">Yükleme</th>
            <th className="px-3 py-3 text-center text-gray-500 font-black uppercase tracking-tighter text-[1.1vh]">İşlem</th>
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan="12" className="py-20 text-center text-gray-600 italic text-[2vh]">
                {shiftLabel} için henüz kayıt bulunmamaktadır.
              </td>
            </tr>
          ) : (
            rows.map((s, i) => (
              <tr
                key={i}
                className={`
                  border-b border-gray-800 transition-colors
                  ${i % 2 === 0 ? 'bg-gray-900/40' : 'bg-gray-800/20'}
                  hover:bg-gray-700/30
                `}
              >
                <td className="px-3 py-2 text-center">
                  <span className={`
                    inline-block w-6 h-6 rounded-full text-[1.1vh] font-black flex items-center justify-center
                    ${s.vardiya === 1 ? 'bg-blue-600 text-white' : s.vardiya === 2 ? 'bg-amber-500 text-gray-900' : 'bg-purple-600 text-white'}
                  `}>
                    {s.vardiya}
                  </span>
                </td>
                <td className="px-3 py-2 text-gray-200 font-bold whitespace-nowrap">{s.gonderim_tarihi}</td>
                <td className="px-3 py-2 text-center">
                  <span className="bg-indigo-950 text-indigo-400 font-black px-2 py-0.5 rounded border border-indigo-900/50">
                    {s.dolly_count}
                  </span>
                </td>
                <td className="px-3 py-2 text-gray-400 font-mono text-[1.2vh]">{s.part_number}</td>
                <td className="px-3 py-2">
                  <div className="text-gray-100 font-bold text-[1.3vh]">{s.group_name}</div>
                  <div className="text-gray-500 text-[1.1vh] truncate max-w-[200px]">{s.eol_names}</div>
                </td>
                <td className="px-3 py-2 text-center text-gray-300 font-bold tracking-tight">{s.plaka_no && s.plaka_no !== '-' ? s.plaka_no : '-'}</td>
                <td className="px-3 py-2 text-center">
                  <span className="text-amber-400 font-black text-[1.5vh] whitespace-nowrap">{s.sefer_no || '-'}</span>
                </td>
                <td className="px-3 py-2 text-center text-gray-500 font-mono">{s.loading_start}</td>
                <td className="px-3 py-2 text-center text-sky-500 font-black">{s.submit_date}</td>
                <td className="px-3 py-2 text-center text-emerald-500 font-black">{s.doc_date}</td>
                <td className="px-3 py-2 text-center">
                  <span className={durationColor(s.loading_duration_min)}>{fmtDuration(s.loading_duration_min)}</span>
                </td>
                <td className="px-3 py-2 text-center">
                  <span className={durationColor(s.process_duration_min)}>{fmtDuration(s.process_duration_min)}</span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}

// ─── Ana Uygulama ─────────────────────────────────────────────────────
export default function App() {
  const [data, setData] = useState({ current: null, previous: null })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState('')
  const [shiftInfo, setShiftInfo] = useState(getShiftInfo())

  const fetchData = useCallback(async () => {
    try {
      const info = getShiftInfo()
      setShiftInfo(info)

      const fetchSet = async (s) => {
        const params = new URLSearchParams({
          start_date: s.date,
          end_date: s.date,
          shift: s.shift
        })
        const res = await fetch(`${API_URL}/api/dashboard?${params}`)
        if (!res.ok) throw new Error(`API ${res.status}`)
        return res.json()
      }

      const [curr, prev] = await Promise.all([
        fetchSet(info.current),
        fetchSet(info.previous)
      ])

      setData({ current: curr, previous: prev })
      setError(null)
      setLastUpdated(new Date().toLocaleTimeString('tr-TR'))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const t = setInterval(fetchData, 15000)
    return () => clearInterval(t)
  }, [fetchData])


  return (
    <div className="h-screen w-full bg-gray-900 text-white flex flex-col overflow-hidden font-sans select-none cursor-default">

      {/* ── HEADER ─────────────────────────────────────────── */}
      <div className="h-[6.5vh] bg-gray-950 border-b border-gray-800 flex items-center justify-between px-6 shrink-0 z-50">
        <div className="flex items-center space-x-3 w-[1/3]">
          <div className="w-2.5 h-2.5 bg-red-600 rounded-full animate-pulse shadow-[0_0_10px_rgba(220,38,38,0.5)]" />
          <h1 className="text-[2vh] font-black tracking-widest text-gray-100 uppercase">
            YMC SEVKİYAT EKRANI
          </h1>
        </div>
        <HeaderClock />
        <div className="flex items-center justify-end w-[1/3] space-x-3">
          <img src="/logo/logo.png" alt="Logo" className="h-[4vh] brightness-0 invert" />
          <div className="flex flex-col items-start leading-none">
            <span className="text-[1vh] font-black text-gray-500 tracking-[0.2em] uppercase">MAGNA</span>
            <span className="text-[2vh] font-bold text-white tracking-wide">Harmony</span>
          </div>
        </div>
      </div>

      {/* ── ÖZET KARTLAR (Row) ────────────────────────────────── */}
      <div className="px-6 py-4 bg-gray-900 flex gap-6 shrink-0 border-b border-gray-800">
        <SummaryCard
          title="Toplam Sefer"
          value={data.current?.summary?.total_sefer}
          prevValue={data.previous?.summary?.total_sefer}
          colorClass="bg-red-500"
        />
        <SummaryCard
          title="Toplam Dolly (Kasa)"
          value={data.current?.summary?.total_dolly}
          prevValue={data.previous?.summary?.total_dolly}
          colorClass="bg-emerald-500"
        />
        <SummaryCard
          title="Toplam Parça Adet"
          value={data.current?.summary?.total_adet}
          prevValue={data.previous?.summary?.total_adet}
          colorClass="bg-sky-500"
        />
      </div>

      {/* ── BÖLÜM BAŞLIĞI ─────────────────────────────────────────── */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-gray-800 bg-gray-950/40 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-1 h-5 bg-red-600 rounded-full" />
          <h2 className="text-[1.8vh] font-black text-white tracking-widest uppercase">
            GÜNCEL VARDİYA SEVKİYATLARI
          </h2>
          <span className="bg-gray-800 text-gray-400 text-[1.2vh] font-bold px-3 py-0.5 rounded-full border border-gray-700">
            {data.current?.shipment_details?.length || 0} SEVKİYAT
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-gray-500 text-[1.2vh] font-bold uppercase tracking-widest">Aktif Vardiya:</span>
            <span className="bg-red-900/40 text-red-500 border border-red-900/60 px-3 py-0.5 rounded-full text-[1.2vh] font-black">
              {shiftInfo.current.label}
            </span>
          </div>
          <div className="w-px h-4 bg-gray-700" />
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
            <span className="text-emerald-500 text-[1.2vh] font-black tracking-widest leading-none">CANLI</span>
          </div>
        </div>
      </div>

      {/* ── İÇERİK ─────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-h-0 bg-[#0b0e14]">
        {loading && !data.current ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="flex flex-col items-center gap-4">
              <div className="w-12 h-12 border-4 border-gray-800 border-t-red-600 rounded-full animate-spin" />
              <span className="text-gray-500 text-[1.6vh] font-bold tracking-widest">VERİLER ÇEKİLİYOR...</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="bg-red-950/20 border border-red-900/30 rounded-2xl px-12 py-8 text-center max-w-lg">
              <div className="text-red-500 text-[2.5vh] font-black mb-4 uppercase tracking-tighter">Bağlantı Sorunu</div>
              <div className="text-gray-400 text-[1.6vh] leading-relaxed mb-6">{error}</div>
              <button onClick={fetchData} className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-8 rounded-full transition-all">Tekrar Dene</button>
            </div>
          </div>
        ) : (
          <ShipmentTable
            rows={data.current?.shipment_details || []}
            shiftLabel={shiftInfo.current.label}
          />
        )}
      </div>

      {/* ── FOOTER ─────────────────────────────────────────────────── */}
      <div className="h-[3.5vh] bg-gray-950 border-t border-gray-900 flex items-center justify-between px-6 shrink-0">
        <div className="flex items-center gap-4">
          <span className="text-gray-600 text-[1.1vh] font-bold tracking-widest uppercase">HARMONY ECOSYSTEM</span>
          <div className="w-1 h-1 bg-gray-800 rounded-full" />
          <span className="text-gray-600 text-[1.1vh] font-bold uppercase tracking-widest">Update: {lastUpdated}</span>
        </div>
        <span className="text-gray-700 text-[1.1vh] font-black italic tracking-[0.2em]">MAGNA HARMONY</span>
      </div>
    </div>
  )
}
