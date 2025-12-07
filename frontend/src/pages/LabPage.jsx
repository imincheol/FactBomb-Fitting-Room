import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE_URL } from '../config'
import '../index.css'

function LabPage() {
    const { t, i18n } = useTranslation()

    // -- Lab Specific State --
    const [userImage, setUserImage] = useState(null)
    const [modelImage, setModelImage] = useState(null)
    // resultImage is not strictly used in lead logic but kept for consistency if needed, though baselineData covers it.
    // I'll leave it out if unused, or keep it if I see it used. It was declared in original but not used in view_file output.

    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [mode, setMode] = useState('legacy') // 'legacy' | 'lab' | 'full_ai'
    const [labFlow, setLabFlow] = useState('exp_a') // 'exp_a' | 'exp_b'

    const [baselineData, setBaselineData] = useState(null)
    const [activeData, setActiveData] = useState(null)
    const [isAiLoading, setIsAiLoading] = useState(false)
    const [showDebug, setShowDebug] = useState(false)

    // -- Home Shared State --
    const [theme, setTheme] = useState('dark')
    const [serverStatus, setServerStatus] = useState('checking') // 'checking', 'online', 'offline'
    const [retryCount, setRetryCount] = useState(0)
    const [lastChecked, setLastChecked] = useState(null)

    const userFileInputRef = useRef(null)
    const modelFileInputRef = useRef(null)

    // -- Server Health Check Logic --
    const checkServerStatus = async (isManual = false) => {
        if (!isManual && serverStatus === 'offline' && retryCount >= 10) {
            return; // Stop retrying after 10 failed attempts
        }

        if (isManual) {
            setRetryCount(0); // Reset retry count on manual check
            setServerStatus('checking');
        }

        try {
            const response = await fetch(`${API_BASE_URL}/health`)
            if (response.ok) {
                setServerStatus('online')
                setRetryCount(0)
                setLastChecked(new Date())
            } else {
                throw new Error('Server not ready')
            }
        } catch (err) {
            console.error("Server Check Failed:", err)
            setServerStatus('offline')
            if (!isManual) {
                setRetryCount(prev => prev + 1)
            }
        }
    }

    // Initial Check & Interval
    useEffect(() => {
        checkServerStatus()
        let intervalId;

        if (serverStatus === 'online') {
            intervalId = setInterval(() => checkServerStatus(), 5 * 60 * 1000)
        } else if (serverStatus === 'offline' && retryCount < 10) {
            intervalId = setInterval(() => checkServerStatus(), 60 * 1000)
        }

        return () => {
            if (intervalId) clearInterval(intervalId)
        }
    }, [serverStatus, retryCount])

    // Theme Effect
    useEffect(() => {
        document.body.className = theme === 'light' ? 'light-mode' : '';
    }, [theme]);

    const toggleTheme = () => {
        setTheme(prev => prev === 'dark' ? 'light' : 'dark');
    };

    const handleImageUpload = (e, type) => {
        const file = e.target.files[0]
        if (!file) return

        const imageUrl = URL.createObjectURL(file)
        if (type === 'user') {
            setUserImage({ file, url: imageUrl })
        } else {
            setModelImage({ file, url: imageUrl })
        }
        // Clear result if inputs change
        setBaselineData(null)
        setActiveData(null)
        setError(null)
    }

    const handleProcess = async () => {
        if (!userImage || !modelImage) {
            setError(t('upload.error_both_photos') || "Please upload both photos!")
            return
        }

        if (serverStatus !== 'online') {
            setError(t('upload.error_server_offline') || "Server is offline")
            return
        }

        setLoading(true)
        setError(null)
        setBaselineData(null)
        setActiveData(null)
        setIsAiLoading(false)

        // STAGE 1: Baseline (Standard)
        let currentBaseline = null;
        try {
            const formData = new FormData()
            formData.append('user_image', userImage.file)
            formData.append('model_image', modelImage.file)
            formData.append('language', i18n.language)

            const response = await fetch(`${API_BASE_URL}/process-baseline`, {
                method: 'POST',
                body: formData,
            })
            if (!response.ok) throw new Error('Baseline process failed')

            const data = await response.json()
            setBaselineData(data.baseline)
            currentBaseline = data;
            setLoading(false)

        } catch (err) {
            console.error(err)
            setError(err.message)
            setLoading(false)
            return
        }

        // STAGE 2: AI Analysis (If applicable)
        if (mode === 'legacy') {
            setActiveData(currentBaseline.baseline)
        } else {
            setIsAiLoading(true)
            try {
                const aiFormData = new FormData()
                aiFormData.append('user_image', userImage.file)
                aiFormData.append('model_image', modelImage.file)
                aiFormData.append('mode', mode)
                if (mode === 'lab') aiFormData.append('lab_flow', labFlow)
                aiFormData.append('language', i18n.language)

                // Pass meta data
                aiFormData.append('user_ratios_json', JSON.stringify(currentBaseline.meta.user_ratios))
                aiFormData.append('model_ratios_json', JSON.stringify(currentBaseline.meta.model_ratios))

                const aiRes = await fetch(`${API_BASE_URL}/process-ai`, {
                    method: 'POST',
                    body: aiFormData
                })
                if (!aiRes.ok) throw new Error('AI process failed')

                const aiData = await aiRes.json()

                // Explicitly set null if no image generated (Honest Mode)
                const finalActive = {
                    ...aiData.active,
                    image: aiData.active.image || null
                }
                setActiveData(finalActive)

            } catch (err) {
                console.error("AI Error", err)
                // We can optionally set error state for right card here
            } finally {
                setIsAiLoading(false)
            }
        }
    }

    // Helper Component for Comparison Cards
    const ResultCard = ({ title, data, isBaseline, isLoading }) => {
        if (isLoading) {
            return (
                <div className="card" style={{ flex: '1 1 300px', minWidth: '300px', maxWidth: '450px', border: '2px dashed #64748b', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '400px', background: 'rgba(30, 41, 59, 0.3)' }}>
                    <div className="spinner" style={{ width: '40px', height: '40px', border: '4px solid #f3f3f3', borderTop: '4px solid #a78bfa', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '1rem' }}></div>
                    <p style={{ color: '#94a3b8', textAlign: 'center' }}>Nano Banana Analyzing... 🍌<br /><span style={{ fontSize: '0.8em' }}>(AI Generation)</span></p>
                    <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
                </div>
            )
        }
        if (!data) return null;

        return (
            <div className="card" style={{ flex: '1 1 300px', minWidth: '300px', maxWidth: '450px', border: isBaseline ? '1px solid #475569' : '2px solid #a78bfa', background: isBaseline ? 'rgba(30, 41, 59, 0.5)' : 'rgba(46, 16, 101, 0.5)' }}>
                <h3 style={{ color: isBaseline ? '#94a3b8' : '#a78bfa' }}>{title}</h3>

                {/* Updated Image Display: Fill/Fit Fix */}
                <div className="preview-area" style={{ height: 'auto', minHeight: '300px', cursor: 'default', background: !data.image ? '#0f172a' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {data.image ? (
                        <img src={`data:image/jpeg;base64,${data.image}`} alt={title} style={{ width: '100%', height: 'auto', maxHeight: '600px', objectFit: 'contain' }} />
                    ) : (
                        <div style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                            <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🍌🚫</span>
                            <p><strong>{t('result.visual_check_failed') || "Visual Check Failed"}</strong></p>
                            <p style={{ fontSize: '0.8rem' }}>Nano Banana provided text analysis only.</p>
                        </div>
                    )}
                </div>

                <div style={{ marginTop: '1rem', padding: '1rem', background: isBaseline ? '#1e293b' : '#4c1d95', borderRadius: '0.5rem' }}>
                    <h4 style={{ color: isBaseline ? '#cbd5e1' : '#d8b4fe', margin: '0 0 0.5rem 0' }}>{t('result.fact_bomb_title') || "FactBomb 💣"}</h4>
                    <p style={{ fontSize: '0.95rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.analysis.fact_bomb}</p>

                    <hr style={{ borderColor: isBaseline ? '#334155' : '#6d28d9', margin: '1rem 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#e2e8f0', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <span>{t('result.you') || "You"} <strong>{data.analysis.user_heads} {t('result.ratio_unit') || "heads"}</strong></span>
                        <span>{t('result.model') || "Model"} <strong>{data.analysis.model_heads} {t('result.ratio_unit') || "heads"}</strong></span>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <main className="container">
            <header style={{ marginBottom: '2rem', position: 'relative' }}>
                <div className="header-controls">
                    <button className="theme-toggle-btn" onClick={toggleTheme} aria-label="Toggle Theme">
                        {theme === 'dark' ? '☀️' : '🌙'}
                    </button>
                    <div style={{ display: 'flex', gap: '5px' }}>
                        <button onClick={() => i18n.changeLanguage('ko')} style={{ opacity: i18n.language === 'ko' ? 1 : 0.5 }}>🇰🇷</button>
                        <button onClick={() => i18n.changeLanguage('vi')} style={{ opacity: i18n.language === 'vi' ? 1 : 0.5 }}>🇻🇳</button>
                        <button onClick={() => i18n.changeLanguage('en')} style={{ opacity: i18n.language === 'en' ? 1 : 0.5 }}>🇺🇸</button>
                    </div>
                </div>

                <h1>
                    {t('title') || "FactBomb Fitting Room"}
                    <span style={{ fontSize: '0.4em', color: '#f472b6', border: '1px solid #f472b6', padding: '2px 8px', borderRadius: '10px', verticalAlign: 'middle', marginLeft: '10px' }}>LAB</span>
                </h1>

                {i18n.language !== 'en' && (
                    <h2 style={{
                        fontSize: '1rem',
                        color: 'var(--text-secondary)',
                        marginTop: '-0.5rem',
                        marginBottom: '0.5rem',
                        fontWeight: 'normal',
                        textTransform: 'uppercase',
                        letterSpacing: '0.05em'
                    }}>
                        (FactBomb Fitting Room)
                    </h2>
                )}

                <p className="tagline" style={{ marginTop: '0.5rem' }}>
                    {t('tagline') || "Shockingly Realistic. Brutally Honest."} (Experimental Build)
                </p>

                <div style={{ marginTop: '0.5rem', textAlign: 'center' }}>
                    <a href="/" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem', borderBottom: '1px dashed currentColor' }}>
                        &larr; {t('back_to_basic') || "Go to Basic Version"}
                    </a>
                </div>
            </header>

            {/* Server Status Banner */}
            <div role="status" aria-live="polite" style={{
                margin: '0 auto 2rem auto',
                padding: '0.75rem',
                borderRadius: '8px',
                width: '100%',
                maxWidth: '600px',
                textAlign: 'center',
                backgroundColor: serverStatus === 'online' ? 'rgba(16, 185, 129, 0.2)' :
                    serverStatus === 'checking' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                border: `1px solid ${serverStatus === 'online' ? '#059669' :
                    serverStatus === 'checking' ? '#3b82f6' : '#b91c1c'}`,
                color: serverStatus === 'online' ? '#34d399' :
                    serverStatus === 'checking' ? '#60a5fa' : '#fca5a5',
                boxSizing: 'border-box'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', flexWrap: 'wrap' }}>
                    <span>
                        {serverStatus === 'checking' && (t('server.checking') || "Checking Server...")}
                        {serverStatus === 'online' && (t('server.online') || "Server Online")}
                        {serverStatus === 'offline' && (t('server.offline') || "Server Offline")}
                    </span>
                    {serverStatus !== 'online' && (
                        <button
                            onClick={() => checkServerStatus(true)}
                            aria-label="Refresh connection"
                            style={{
                                padding: '4px 8px',
                                fontSize: '0.8rem',
                                background: '#334155',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer'
                            }}
                        >
                            {t('server.refresh') || "Refresh"}
                        </button>
                    )}
                </div>
                {serverStatus === 'offline' && retryCount > 0 && retryCount < 10 && (
                    <div style={{ fontSize: '0.8rem', marginTop: '4px', opacity: 0.8 }}>
                        {t('server.retrying', { count: retryCount }) || `Retrying... (${retryCount})`}
                    </div>
                )}
            </div>

            <section className="upload-section">
                {/* User Photo Card */}
                <div className="card">
                    <h3>{t('upload.user_title') || "1. Your Real Body"}</h3>
                    <div className="preview-area" onClick={() => userFileInputRef.current.click()}>
                        <input
                            type="file"
                            ref={userFileInputRef}
                            onChange={(e) => handleImageUpload(e, 'user')}
                            accept="image/*"
                            aria-label="Upload your full body photo"
                        />
                        {userImage ? (
                            <img src={userImage.url} alt="User" />
                        ) : (
                            <div className="preview-placeholder">
                                <span aria-hidden="true">📸</span>
                                <span style={{ textAlign: 'center', whiteSpace: 'pre-line' }}>{t('upload.user_placeholder') || "Click to Upload"}</span>
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>{t('upload.user_helper') || "Full body shot required"}</p>
                </div>

                {/* Model Photo Card */}
                <div className="card">
                    <h3>{t('upload.model_title') || "2. The Dream Fit"}</h3>
                    <div className="preview-area" onClick={() => modelFileInputRef.current.click()}>
                        <input
                            type="file"
                            ref={modelFileInputRef}
                            onChange={(e) => handleImageUpload(e, 'model')}
                            accept="image/*"
                            aria-label="Upload model photo"
                        />
                        {modelImage ? (
                            <img src={modelImage.url} alt="Model" />
                        ) : (
                            <div className="preview-placeholder">
                                <span aria-hidden="true">👕</span>
                                <span style={{ textAlign: 'center', whiteSpace: 'pre-line' }}>{t('upload.model_placeholder') || "Click to Upload"}</span>
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>{t('upload.model_helper') || "Shopping mall model shot"}</p>
                </div>
            </section>

            <section style={{ margin: '2rem 0' }}>
                {error && <div role="alert" style={{ color: '#f43f5e', marginBottom: '1rem', fontWeight: 'bold' }}>{error}</div>}

                {/* Mode Selector */}
                <div className="mode-selector" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }} role="radiogroup" aria-label="Analysis Mode Selection">

                    {/* 1. Legacy */}
                    <label style={{
                        cursor: 'pointer',
                        padding: '0.5rem 1rem',
                        borderRadius: '2rem',
                        background: mode === 'legacy' ? '#f472b6' : 'transparent',
                        border: '1px solid #f472b6',
                        color: mode === 'legacy' ? '#fff' : '#f472b6',
                        transition: 'all 0.3s ease'
                    }}>
                        <input
                            type="radio"
                            name="mode"
                            value="legacy"
                            checked={mode === 'legacy'}
                            onChange={(e) => setMode(e.target.value)}
                            style={{ display: 'none' }}
                        />
                        📊 Standard
                    </label>

                    {/* 2. Lab Mode (Experiment) */}
                    <label style={{
                        cursor: 'pointer',
                        padding: '0.5rem 1rem',
                        borderRadius: '2rem',
                        background: mode === 'lab' ? '#818cf8' : 'transparent',
                        border: '1px solid #818cf8',
                        color: mode === 'lab' ? '#fff' : '#818cf8',
                        transition: 'all 0.3s ease'
                    }}>
                        <input
                            type="radio"
                            name="mode"
                            value="lab"
                            checked={mode === 'lab'}
                            onChange={(e) => setMode(e.target.value)}
                            style={{ display: 'none' }}
                        />
                        🧪 Lab Mode
                    </label>

                    {/* 3. Full AI (Generation) */}
                    <label style={{
                        cursor: 'pointer',
                        padding: '0.5rem 1rem',
                        borderRadius: '2rem',
                        background: mode === 'full_ai' ? '#a78bfa' : 'transparent',
                        border: '1px solid #a78bfa',
                        color: mode === 'full_ai' ? '#fff' : '#a78bfa',
                        transition: 'all 0.3s ease'
                    }}>
                        <input
                            type="radio"
                            name="mode"
                            value="full_ai"
                            checked={mode === 'full_ai'}
                            onChange={(e) => setMode(e.target.value)}
                            style={{ display: 'none' }}
                        />
                        🤖 Full AI (Pure Gen)
                    </label>
                </div>

                {/* Lab Experiment Selector (Only visible in Lab Mode) */}
                {mode === 'lab' && (
                    <div className="lab-options" style={{ marginBottom: '2rem', background: '#1e293b', padding: '1rem', borderRadius: '0.5rem', border: '1px dashed #818cf8' }}>
                        <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1rem' }}>🔬 Select Experiment Flow:</p>
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }} role="radiogroup" aria-label="Lab Experiment Flow">
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: '#cbd5e1' }}>
                                <input
                                    type="radio"
                                    name="labFlow"
                                    value="exp_a"
                                    checked={labFlow === 'exp_a'}
                                    onChange={(e) => setLabFlow(e.target.value)}
                                />
                                <strong>Flow A:</strong> Body Data Driven <br /><span style={{ fontSize: '0.8em', color: '#64748b' }}>(내 몸 수치로 변형해줘)</span>
                            </label>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', color: '#cbd5e1' }}>
                                <input
                                    type="radio"
                                    name="labFlow"
                                    value="exp_b"
                                    checked={labFlow === 'exp_b'}
                                    onChange={(e) => setLabFlow(e.target.value)}
                                />
                                <strong>Flow B:</strong> Cloth Data Driven <br /><span style={{ fontSize: '0.8em', color: '#64748b' }}>(옷 데이터만 가져와서 입혀줘)</span>
                            </label>
                        </div>
                    </div>
                )}

                <button
                    className="action-btn"
                    onClick={handleProcess}
                    disabled={loading || !userImage || !modelImage || serverStatus !== 'online'}
                    style={{ opacity: (serverStatus !== 'online') ? 0.5 : 1, cursor: (serverStatus !== 'online') ? 'not-allowed' : 'pointer' }}
                >
                    {loading ? (t('action.crunching') || 'Crunching Baseline...') : (isAiLoading ? 'Analyzing AI...' : (t('action.button') || 'Reality Check! 💥'))}
                </button>
            </section>

            {/* RESULT SECTION (Comparison View) */}
            {(baselineData || isAiLoading) && (
                <section className="result-section" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
                    <h2 style={{ marginBottom: '2rem' }}>Comparison Result 🆚</h2>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', justifyContent: 'center' }}>
                        {/* Left: Baseline (always visible) */}
                        <ResultCard
                            title="📊 Standard (Baseline)"
                            data={baselineData}
                            isBaseline={true}
                        />

                        {/* Right: Active Mode (only if different from baseline) */}
                        {mode !== 'legacy' && (
                            <ResultCard
                                title={`✨ Active: ${mode === 'lab' ? 'Lab Mode' : 'Full AI'}`}
                                data={activeData}
                                isBaseline={false}
                                isLoading={isAiLoading}
                            />
                        )}

                        {/* If Legacy mode, we can show it twice or just once. Let's show duplicate for layout balance as requested */}
                        {mode === 'legacy' && baselineData && (
                            <ResultCard
                                title="📊 Standard (Same)"
                                data={baselineData}
                                isBaseline={true}
                            />
                        )}
                    </div>

                    {(baselineData) && (
                        <>
                            <div style={{ marginTop: '3rem' }}>
                                <button
                                    onClick={() => setShowDebug(!showDebug)}
                                    style={{ background: 'transparent', border: '1px solid #64748b', color: '#94a3b8', cursor: 'pointer', padding: '0.5rem 1rem', borderRadius: '4px' }}
                                >
                                    {showDebug ? 'Hide Details' : 'Show Debug Details 🕵️'}
                                </button>
                            </div>

                            {showDebug && (
                                <div className="debug-section" style={{ marginTop: '2rem', padding: '1rem', background: '#0f172a', borderRadius: '1rem', border: '1px solid #334155' }}>
                                    <h3 style={{ marginBottom: '1rem' }}>Detailed Metrics 📐</h3>

                                    {/* AI Debug Info */}
                                    {activeData && activeData.analysis && (activeData.analysis.debug_user_info || activeData.analysis.debug_model_info) && (
                                        <div style={{ marginBottom: '2rem', padding: '1rem', background: 'rgba(167, 139, 250, 0.1)', borderRadius: '8px', border: '1px solid #a78bfa' }}>
                                            <h4 style={{ color: '#d8b4fe', marginTop: 0 }}>🤖 AI Analysis Log</h4>

                                            {activeData.analysis.debug_user_info && (
                                                <div style={{ marginBottom: '1rem' }}>
                                                    <strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '0.3rem' }}>[Step 1] User Analysis:</strong>
                                                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#cbd5e1', fontSize: '0.85rem', fontFamily: 'monospace' }}>
                                                        {activeData.analysis.debug_user_info}
                                                    </pre>
                                                </div>
                                            )}

                                            {activeData.analysis.debug_model_info && (
                                                <div>
                                                    <strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '0.3rem' }}>[Step 2] Model Analysis:</strong>
                                                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#cbd5e1', fontSize: '0.85rem', fontFamily: 'monospace' }}>
                                                        {activeData.analysis.debug_model_info}
                                                    </pre>
                                                </div>
                                            )}

                                            {activeData.analysis.gen_prompt && (
                                                <div style={{ marginTop: '1rem', borderTop: '1px solid #4c1d95', paddingTop: '1rem' }}>
                                                    <strong style={{ color: '#e2e8f0', display: 'block', marginBottom: '0.3rem' }}>[Step 4] Generated Prompt (To Nano Banana):</strong>
                                                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', color: '#86efac', fontSize: '0.85rem', fontFamily: 'monospace', background: '#022c22', padding: '0.5rem', borderRadius: '4px' }}>
                                                        {activeData.analysis.gen_prompt}
                                                    </pre>
                                                </div>
                                            )}

                                            <div style={{ marginTop: '1rem', borderTop: '1px solid #4c1d95', paddingTop: '1rem' }}>
                                                <strong style={{ color: '#a78bfa', fontSize: '0.8rem' }}>RAW DATA DUMP:</strong>
                                                <pre style={{ background: '#000', padding: '10px', borderRadius: '4px', overflowX: 'auto', fontSize: '0.7rem', color: '#0f0' }}>
                                                    {JSON.stringify(activeData.analysis, null, 2)}
                                                </pre>
                                            </div>
                                        </div>
                                    )}

                                    <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>Visualizing the warping engine skeletal tracking (Shared Engine).</p>

                                    <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                                        <div>
                                            <h5 style={{ color: '#cbd5e1' }}>User Skeleton</h5>
                                            <img src={`data:image/jpeg;base64,${baselineData.debug_user}`} alt="User Skeleton Debug View" style={{ maxHeight: '300px', borderRadius: '8px', border: '1px solid #334155' }} />
                                        </div>
                                        <div>
                                            <h5 style={{ color: '#cbd5e1' }}>Model Skeleton</h5>
                                            <img src={`data:image/jpeg;base64,${baselineData.debug_model}`} alt="Model Skeleton Debug View" style={{ maxHeight: '300px', borderRadius: '8px', border: '1px solid #334155' }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </section>
            )}
        </main>
    )
}

export default LabPage
