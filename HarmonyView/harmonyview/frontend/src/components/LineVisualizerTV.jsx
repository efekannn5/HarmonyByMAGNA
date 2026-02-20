import React, { useRef, useEffect, useState } from 'react'
import { motion, AnimatePresence, useAnimationControls } from 'framer-motion'

// --- CONSTANTS ---
const MIN_CAPACITY = 12

const LINE_PRIORITY = [
    'V710 MR',
    'V710 LLS',
    'J74 FR',
    'J74 LLS',
    'J74 MR',
    'J74 HEADLAMP',
    'J74 HLF'
]

const LINE_DISPLAY_NAMES = {
    'J74 FR BUMPER SEQUENCING': 'J74 FR',
    'J74 HEADLAMP FINISHER SIRALAMA': 'J74 HLF',
    'J74 HEADLAMP': 'J74 HLF',
    'J74 LLS SIRALAMA': 'J74 LLS'
}

// Note: Keys in data might be like 'J74-FR-EOL' or 'V710_MR'. 
// We normalize both the priority keys and the data keys for comparison.
const normalize = (str) => str.replace(/[^a-zA-Z0-9]/g, '').toUpperCase()

const getLineRank = (lineName) => {
    const normName = normalize(lineName)
    const index = LINE_PRIORITY.findIndex(p => normName.includes(normalize(p)))
    return index === -1 ? 999 : index
}

// --- SUB-COMPONENTS ---

// 0. Header Clock
const HeaderClock = () => {
    const [time, setTime] = useState(new Date())

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000)
        return () => clearInterval(timer)
    }, [])

    return (
        <div className="flex flex-col items-center justify-center -space-y-1">
            <span className="text-[1.8vh] font-bold text-gray-200 tracking-widest uppercase">
                {time.toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' })}
            </span>
            <span className="text-[2.5vh] font-black text-white tracking-widest leading-none font-mono">
                {time.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
        </div>
    )
}

// 1. Line Name (Compact)
const LineHeader = ({ lineName }) => {
    // 1. Try exact match in map
    // 2. Try normalized match
    // 3. Fallback to cleaning
    let displayName = LINE_DISPLAY_NAMES[lineName]

    if (!displayName) {
        // Check partial matches or cleaning
        const cleanName = lineName.replace(/-?EOL/g, '').replace(/-/g, ' ').trim()

        // Check if any key in map is contained in cleanName
        const mapKey = Object.keys(LINE_DISPLAY_NAMES).find(k => cleanName.includes(k) || k.includes(cleanName))
        if (mapKey) {
            displayName = LINE_DISPLAY_NAMES[mapKey]
        } else {
            displayName = cleanName
        }
    }

    return (
        <div className="w-[10%] h-full bg-gray-800 border-r border-gray-700 flex items-center justify-center px-1 relative z-20">
            <div className="flex flex-col items-center justify-center w-full">
                <h2 className="text-[1.1vw] font-bold text-white text-center leading-tight break-words w-full">
                    {displayName}
                </h2>
            </div>
            {/* Metric Dot */}
            <div className="absolute right-0 top-1/2 w-1.5 h-1.5 bg-gray-500 rounded-full translate-x-1/2"></div>
        </div>
    )
}

// 2. Active Dolly (Responsive Grid with High Density Support)
const ActiveDollyDisplay = ({ active }) => {
    if (!active) {
        return (
            <div className="w-full h-[85%] mx-2 bg-gray-800/20 border-2 border-dashed border-gray-600/50 rounded flex items-center justify-center">
                <span className="text-gray-500 text-[0.8vw] font-bold tracking-wider">HAT BEKLEMEDE</span>
            </div>
        )
    }

    const { dolly_no, dolly_order_no, current_vins, capacity } = active
    const safeCap = Math.max(1, capacity || MIN_CAPACITY)

    // Check for high density (many VINs)
    const isHighDensity = safeCap > 30

    // Dynamic Grid Calculation (Custom Layouts)
    let rows = 1;
    let cols = 1;

    if (safeCap <= 18) {
        // User Preference: Small capacities should be 2 rows (e.g. 8->4x2, 14->7x2)
        rows = 2;
        cols = Math.ceil(safeCap / rows);
    } else if (safeCap >= 36 && safeCap <= 60) {
        // User Preference: Large capacities (e.g. 48) should be ~6 rows
        rows = 6;
        cols = Math.ceil(safeCap / rows);
    } else {
        // Intermediate/Other: Square-ish
        const sqrt = Math.sqrt(safeCap);
        cols = Math.ceil(sqrt);
        rows = Math.ceil(safeCap / cols);
    }

    return (
        <motion.div
            layoutId={`active-${dolly_no}`}
            className="w-full h-[90%] px-1 bg-white rounded-lg shadow-lg border-l-[6px] border-emerald-600 flex flex-col overflow-hidden relative"
        >
            {/* Header - Condensed if High Density */}
            <div className={`bg-emerald-600 flex justify-between items-center shrink-0 ${isHighDensity ? 'px-1.5 py-0.5' : 'px-2 py-1'}`}>
                <span className="text-[0.6vw] text-white/90 font-bold uppercase tracking-wider">Dolly No</span>
                <span className="text-[1.1vw] font-black text-white tracking-widest leading-none font-mono">
                    {dolly_order_no || dolly_no}
                </span>
            </div>

            {/* Grid Container */}
            <div className="flex-1 p-1 bg-gray-100 flex items-center justify-center min-h-0">
                <div
                    className={`grid w-full h-full ${isHighDensity ? 'gap-px' : 'gap-0.5'}`}
                    style={{
                        gridTemplateColumns: `repeat(${cols}, 1fr)`,
                        gridTemplateRows: `repeat(${rows}, 1fr)`
                    }}
                >
                    {[...Array(safeCap)].map((_, i) => {
                        const isFilled = i < current_vins
                        const isLastFilled = i === current_vins - 1

                        return (
                            <motion.div
                                key={i}
                                initial={{ scale: 0.5, opacity: 0 }}
                                animate={{
                                    scale: 1,
                                    opacity: 1,
                                    backgroundColor: isLastFilled
                                        ? ['#eab308', '#f97316', '#16a34a', '#059669'] // Yellow -> Orange -> Green -> Emerald
                                        : (isFilled ? '#059669' : '#e5e7eb'),
                                    borderColor: isFilled ? 'transparent' : '#d1d5db'
                                }}
                                transition={{
                                    duration: isLastFilled ? 5 : 0.3,
                                    repeat: 0, // Run once
                                    ease: "linear"
                                }}
                                className={`
                                    rounded-[1px] border flex items-center justify-center relative shadow-sm min-h-0 min-w-0
                                    ${!isFilled && 'bg-gray-200'}
                                `}
                            >
                                <span className={`
                                    font-bold z-10 leading-none
                                    ${isFilled ? 'text-white' : 'text-gray-400'}
                                    ${isHighDensity ? 'text-[0.55vw]' : 'text-[0.7vw]'}
                                `}>
                                    {i + 1}
                                </span>
                            </motion.div>
                        )
                    })}
                </div>
            </div>
        </motion.div>
    )
}

// 3. Ready Queue (Scrollable Stream)
const ReadyQueue = ({ queue }) => {
    const containerRef = useRef(null);
    const contentRef = useRef(null);
    const controls = useAnimationControls();

    // Stable dependency for effect
    const queueIds = queue.map(i => i.dolly_no).join(',');

    // Auto-scroll logic: Ping-Pong if overflow
    useEffect(() => {
        let isCancelled = false;

        const scroll = async () => {
            if (isCancelled || !containerRef.current || !contentRef.current) return;

            const containerWidth = containerRef.current.offsetWidth;
            const contentWidth = contentRef.current.scrollWidth;

            // If content fits, reset
            if (contentWidth <= containerWidth) {
                controls.set({ x: 0 });
                return;
            }

            const distance = contentWidth - containerWidth + 20; // +20 for padding buffer

            // Loop: Wait -> Slide Left -> Wait -> Slide Right
            try {
                if (isCancelled) return;
                await controls.start({ x: 0, transition: { duration: 2 } }); // Initial delay

                if (isCancelled) return;
                await controls.start({
                    x: -distance,
                    transition: { duration: Math.max(2, distance * 0.05), ease: "linear" } // Speed dependent on distance (min 2s)
                });

                if (isCancelled) return;
                await controls.start({ x: -distance, transition: { duration: 2 } }); // Pause at end

                if (isCancelled) return;
                await controls.start({
                    x: 0,
                    transition: { duration: Math.max(2, distance * 0.05), ease: "linear" }
                });

                if (!isCancelled) scroll(); // Recurse
            } catch (e) {
                // Animation interrupted (unmount), ignore
            }
        };

        scroll();
        return () => {
            isCancelled = true;
            controls.stop();
        };
    }, [queueIds, controls]); // Re-run only when content changes

    return (
        // Container ref is needed for scroll logic. 
        // We utilize the passed scroll logic. 
        // I will keep the ref here but remove the formatting classes that conflict with the parent wrapper I added.
        <div ref={containerRef} className="w-full h-full flex items-center overflow-hidden relative">
            <motion.div
                ref={contentRef}
                animate={controls}
                className="flex items-center space-x-2 h-full py-2 pl-2" // Added pl-2 for start padding
            >
                <AnimatePresence>
                    {queue.map((item) => {
                        // Server stores time in local TRT already - extract HH:MM directly from ISO string
                        const completedTime = (item.completed_at || '').substring(11, 16);

                        return (
                            <motion.div
                                key={item.dolly_no}
                                layoutId={`ready-${item.dolly_no}`}
                                initial={{ opacity: 0, scale: 0.5 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0 }}
                                className="h-[90%] aspect-[1/1.1] bg-white border border-gray-300 rounded shadow-sm flex flex-col flex-shrink-0 relative overflow-hidden"
                            >
                                {/* Time Header */}
                                <div className="bg-gray-100 text-[0.6vw] text-center text-gray-500 font-bold border-b border-gray-200 py-0.5">
                                    {completedTime}
                                </div>

                                <div className="flex-1 flex flex-col items-center justify-center p-1">
                                    <span className="text-[1.2vw] font-bold text-gray-800 leading-none">
                                        {item.dolly_order_no || item.dolly_no}
                                    </span>
                                    {/* Duration Tag - Compact */}
                                    {item.duration !== undefined && (
                                        <span className="mt-1 px-1.5 py-0.5 bg-gray-200 text-gray-600 text-[0.5vw] rounded font-bold whitespace-nowrap">
                                            {(() => {
                                                const h = Math.floor(item.duration / 60);
                                                const m = item.duration % 60;
                                                return h > 0 ? `${h} sa ${m} dk` : `${m} dk`;
                                            })()}
                                        </span>
                                    )}
                                </div>
                            </motion.div>
                        )
                    })}
                </AnimatePresence>
            </motion.div>
        </div>
    )
}

// 4. Scanned Queue (Right Side - Auto-Scrolling & Status Logic)
const ScannedQueue = ({ scanned }) => {
    const containerRef = useRef(null);
    const contentRef = useRef(null);
    const controls = useAnimationControls();

    // Stable dependency for effect
    const scannedIds = scanned.map(i => i.dolly_no).join(',');

    // Auto-scroll logic: Ping-Pong if overflow
    useEffect(() => {
        let isCancelled = false;

        const scroll = async () => {
            if (isCancelled || !containerRef.current || !contentRef.current) return;

            const containerWidth = containerRef.current.offsetWidth;
            const contentWidth = contentRef.current.scrollWidth;

            // If content fits, reset
            if (contentWidth <= containerWidth) {
                controls.set({ x: 0 });
                return;
            }

            const distance = contentWidth - containerWidth + 20;

            try {
                if (isCancelled) return;
                await controls.start({ x: 0, transition: { duration: 2 } });

                if (isCancelled) return;
                await controls.start({
                    x: -distance,
                    transition: { duration: Math.max(2, distance * 0.05), ease: "linear" }
                });

                if (isCancelled) return;
                await controls.start({ x: -distance, transition: { duration: 2 } });

                if (isCancelled) return;
                await controls.start({
                    x: 0,
                    transition: { duration: Math.max(2, distance * 0.05), ease: "linear" }
                });

                if (!isCancelled) scroll();
            } catch (e) { }
        };

        scroll();
        return () => {
            isCancelled = true;
            controls.stop();
        };
    }, [scannedIds, controls]);

    // Check if list is empty
    if (!scanned || scanned.length === 0) {
        return (
            <div className="w-full h-[90%] mx-2 bg-gray-900 border-2 border-green-600/50 rounded-xl flex items-center justify-center relative overflow-hidden px-2 shadow-2xl z-30">
                {/* Label Badge */}
                <div className="absolute top-0 right-0 bg-gray-700 text-white text-[0.6vw] font-bold px-2 py-0.5 rounded-bl-lg z-40 border-l border-b border-gray-600 shadow-md">
                    SEVK ALANI
                </div>
                <div className="text-gray-500 text-[0.8vw] italic opacity-50">
                    BEKLEYEN YOK
                </div>
            </div>
        )
    }

    return (
        <div ref={containerRef} className="w-full h-[90%] mx-2 bg-gray-900 border-2 border-green-600/50 rounded-xl flex items-center relative overflow-hidden px-2 shadow-2xl z-30 mask-linear-fade">
            {/* Label Badge */}
            <div className="absolute top-0 right-0 bg-gray-700 text-white text-[0.6vw] font-bold px-2 py-0.5 rounded-bl-lg z-40 border-l border-b border-gray-600 shadow-md">
                SEVK ALANI
            </div>

            <motion.div
                ref={contentRef}
                animate={controls}
                className="flex items-center space-x-2 h-full py-2 z-30"
            >
                <AnimatePresence>
                    {scanned.map((item) => {
                        // Logic: 
                        // Green/Scanned: 'scanned' ONLY
                        // Red/Submitted: 'pending', 'loading_completed', 'completed', 'submitted', 'irsaliye_ready'
                        const isScanned = item.status === 'scanned';
                        const isSubmitted = !isScanned;

                        // Server stores time in local TRT already - extract HH:MM directly from ISO string
                        const completedTime = (item.completed_at || item.sort_date || '').substring(11, 16);

                        return (
                            <motion.div
                                key={item.dolly_no}
                                layoutId={`scanned-${item.dolly_no}`}
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                className={`
                                    h-[80%] aspect-square rounded-lg shadow-lg flex flex-col items-center justify-between border-2 relative py-1 flex-shrink-0
                                    ${isSubmitted ? 'bg-red-600 border-red-400' : 'bg-green-600 border-green-400'}
                                `}
                            >
                                {/* Top: Time */}
                                <span className={`text-[0.6vw] font-bold ${isSubmitted ? 'text-red-100' : 'text-green-100'}`}>
                                    {completedTime}
                                </span>

                                {/* Center: OrderNo */}
                                <span className="text-[1.2vw] font-black text-white leading-none tracking-tight">
                                    {item.dolly_order_no || item.dolly_no}
                                </span>

                                {/* Bottom: Label */}
                                <div className="flex flex-col items-center w-full">
                                    <span className={`
                                        text-[0.4vw] uppercase opacity-90 font-bold tracking-tighter w-full text-center py-0.5
                                        ${isSubmitted ? 'bg-red-700/50' : 'bg-green-700/50'}
                                     `}>
                                        {isSubmitted ? 'ASN/İRSALİYE HAZIR' : 'OKUTULDU'}
                                    </span>
                                </div>
                            </motion.div>
                        )
                    })}
                </AnimatePresence>
            </motion.div>
        </div>
    )
}


// --- MAIN COMPONENT ---
const LineVisualizerTV = ({ data }) => {
    if (!data) return null

    // Sort lines based on priority
    const lines = Object.entries(data).sort((a, b) => {
        return getLineRank(a[0]) - getLineRank(b[0])
    })

    return (
        <div className="h-screen w-full bg-gray-900 text-white flex flex-col overflow-hidden font-sans selection:bg-none cursor-default">
            {/* HEADER (Fixed Height) */}
            <div className="h-[6vh] bg-gray-950 border-b border-gray-800 flex items-center justify-between px-6 shadow-md shrink-0 z-50">
                <div className="flex items-center space-x-3 w-[25%]">
                    <div className="w-2.5 h-2.5 bg-red-500 rounded-full animate-pulse"></div>
                    <h1 className="text-[2vh] font-bold tracking-widest text-gray-100 uppercase">
                        YMC CANLI ÜRETİM ve SEVKİYAT AKIŞI
                    </h1>
                </div>

                {/* Center: Clock */}
                <HeaderClock />

                {/* Right: MAGNA Harmony Logo */}
                <div className="flex items-center justify-end w-[25%] space-x-3">
                    <img
                        src="/logo/logo.png"
                        alt="Magna Logo"
                        className="h-[4vh] w-auto object-contain brightness-0 invert"
                        onError={(e) => e.target.style.display = 'none'}
                    />
                    <div className="flex flex-col items-start justify-center leading-none">
                        <span className="text-[1vh] tracking-[0.3em] font-medium text-gray-400 uppercase mb-0.5">MAGNA</span>
                        <span className="text-[2vh] font-bold text-white tracking-wide">Harmony</span>
                    </div>
                </div>
            </div>

            {/* COLUMN HEADERS */}
            <div className="flex items-center w-full px-0 py-1 bg-gray-900 border-b border-gray-800">
                {/* 1. HAT */}
                <div className="w-[10%] text-center border-r border-gray-700 h-full flex items-center justify-center">
                    <span className="text-[1vh] font-bold text-gray-500 tracking-wider uppercase">HAT</span>
                </div>
                {/* Spacer for Arrow */}
                <div className="w-[2%] border-r border-gray-700 h-full"></div>
                {/* 2. AKTİF */}
                <div className="w-[14%] text-center border-r border-gray-700 h-full flex items-center justify-center">
                    <span className="text-[1vh] font-bold text-gray-500 tracking-wider uppercase">AKTİF</span>
                </div>
                {/* 3. TAMAMLANAN (HAZIR) */}
                <div className="flex-1 pl-2 text-left border-r border-gray-700 h-full flex items-center">
                    <span className="text-[1vh] font-bold text-gray-500 tracking-wider uppercase">TAMAMLANAN / HAZIR</span>
                </div>
                {/* 4. SEVK */}
                <div className="w-[22%] text-center h-full flex items-center justify-center">
                    <span className="text-[1vh] font-bold text-gray-500 tracking-wider uppercase">SEVK ALANI</span>
                </div>
            </div>

            {/* LINES CONTAINER */}
            <div className="flex-1 flex flex-col w-full bg-gray-900">
                {lines.map(([lineName, details], index) => (
                    <div
                        key={lineName}
                        className={`
                            flex-1 flex w-full relative min-h-0 items-center
                            border-b-[3px] border-gray-950 
                            ${index % 2 === 0 ? 'bg-gray-900' : 'bg-gray-800/20'}
                        `}
                    >

                        {/* 1. Line Name Box */}
                        <LineHeader lineName={lineName} />

                        {/* 2. Arrow Connector */}
                        <div className="w-[2%] h-full flex items-center justify-center text-gray-600 relative border-r border-gray-700">
                            <span className="text-[1.2vw]">›</span>
                        </div>

                        {/* 3. Active Workstation - Wrapped for Border */}
                        <div className="w-[14%] h-full flex items-center justify-center px-1 border-r border-gray-700">
                            <ActiveDollyDisplay active={details.active} />
                        </div>

                        {/* 4. Ready Queue Stream - Wrapped for Border */}
                        <div className="flex-1 h-full flex items-center px-2 space-x-2 bg-gray-800/40 overflow-hidden mr-0 relative z-10 mask-linear-fade border-r border-gray-700">
                            <ReadyQueue queue={details.queue || []} />
                        </div>

                        {/* 5. Scanned Queue (End) - Wrapped for Layout Consistency */}
                        <div className="w-[22%] h-full flex items-center justify-center px-2">
                            <ScannedQueue scanned={details.scanned || []} />
                        </div>

                    </div>
                ))}
            </div>
        </div>
    )
}

export default LineVisualizerTV
