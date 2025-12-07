import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { API_BASE_URL } from '../config'
import '../index.css'

function HomePage() {
    const { t, i18n } = useTranslation()
    const [userImage, setUserImage] = useState(null)
    const [modelImage, setModelImage] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const [baselineData, setBaselineData] = useState(null)
    const [showDebug, setShowDebug] = useState(false)
    const [theme, setTheme] = useState('dark') // Default theme

    // Server Health Check State
    const [serverStatus, setServerStatus] = useState('checking') // 'checking', 'online', 'offline'
    const [retryCount, setRetryCount] = useState(0)
    const [lastChecked, setLastChecked] = useState(null)

    const userFileInputRef = useRef(null)
    const modelFileInputRef = useRef(null)

    // Health Check Logic
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

    // Initial Check
    useEffect(() => {
        checkServerStatus()
    }, [])

    // Interval Logic
    useEffect(() => {
        let intervalId;

        if (serverStatus === 'online') {
            // If online, check every 5 minutes
            intervalId = setInterval(() => {
                checkServerStatus()
            }, 5 * 60 * 1000)
        } else if (serverStatus === 'offline' && retryCount < 10) {
            // If offline, retry every 5 seconds
            intervalId = setInterval(() => {
                checkServerStatus()
            }, 5000)
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
        setError(null)
    }

    const handleProcess = async () => {
        if (!userImage || !modelImage) {
            setError(t('upload.error_both_photos'))
            return
        }

        if (serverStatus !== 'online') {
            setError(t('upload.error_server_offline'))
            return
        }

        setLoading(true)
        setError(null)
        setBaselineData(null)

        // STAGE 1: Baseline (Standard) Only
        try {
            const formData = new FormData()
            formData.append('user_image', userImage.file)
            formData.append('model_image', modelImage.file)
            formData.append('language', i18n.language) // Send current language

            const response = await fetch(`${API_BASE_URL}/process-baseline`, {
                method: 'POST',
                body: formData,
            })
            if (!response.ok) throw new Error('Baseline process failed')

            const data = await response.json()
            setBaselineData(data.baseline)
            setLoading(false)

        } catch (err) {
            console.error(err)
            setError(err.message)
            setLoading(false)
            return
        }
    }

    // Helper Function for Downloading Image
    const handleDownload = (base64Image, fileName) => {
        const link = document.createElement('a');
        link.href = `data:image/jpeg;base64,${base64Image}`;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // Helper Component for Result Card
    const ResultCard = ({ title, data }) => {
        if (!data) return null;

        return (
            <div className="card" style={{ maxWidth: '800px' }}>
                <h3 style={{ color: '#94a3b8' }}>{title}</h3>
                <div className="preview-area" style={{ height: 'auto', minHeight: '300px', cursor: 'default', background: !data.image ? '#0f172a' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {data.image ? (
                        <img src={`data:image/jpeg;base64,${data.image}`} alt={title} style={{ width: '100%', height: 'auto', maxHeight: '600px', objectFit: 'contain' }} />
                    ) : (
                        <div style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                            <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🍌🚫</span>
                            <p><strong>{t('result.visual_check_failed')}</strong></p>
                            <p style={{ fontSize: '0.8rem' }}>{t('result.nano_banana')}</p>
                        </div>
                    )}
                </div>

                {data.image && (
                    <div style={{ display: 'flex', justifyContent: 'center', margin: '1rem 0' }}>
                        <button
                            className="secondary-btn"
                            onClick={() => {
                                const date = new Date();
                                const yymmdd = date.toISOString().slice(2, 10).replace(/-/g, '');
                                const hhmm = date.toTimeString().slice(0, 5).replace(':', '');
                                const ss = date.toTimeString().slice(6, 8);
                                const filename = `factbomb-fitting-room-${yymmdd}-${hhmm}-${ss}.jpg`;
                                handleDownload(data.image, filename);
                            }}
                        >
                            {t('result.download')}
                        </button>
                    </div>
                )}

                <div style={{ marginTop: '1rem', padding: '1rem', background: '#1e293b', borderRadius: '0.5rem' }}>
                    <h4 style={{ color: '#cbd5e1', margin: '0 0 0.5rem 0' }}>{t('result.fact_bomb_title')}</h4>
                    <p style={{ fontSize: '0.95rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.analysis.fact_bomb}</p>

                    <hr style={{ borderColor: '#334155', margin: '1rem 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#e2e8f0', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <span>{t('result.you')} <strong>{data.analysis.user_heads} {t('result.ratio_unit')}</strong></span>
                        <span>{t('result.model')} <strong>{data.analysis.model_heads} {t('result.ratio_unit')}</strong></span>
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
                <h1>{t('title')}</h1>

                <p className="tagline">{t('tagline')}</p>
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
                        {serverStatus === 'checking' && t('server.checking')}
                        {serverStatus === 'online' && t('server.online')}
                        {serverStatus === 'offline' && t('server.offline')}
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
                            {t('server.refresh')}
                        </button>
                    )}
                </div>
                {serverStatus === 'offline' && retryCount > 0 && retryCount < 10 && (
                    <div style={{ fontSize: '0.8rem', marginTop: '4px', opacity: 0.8 }}>
                        {t('server.retrying', { count: retryCount })}
                    </div>
                )}
                {serverStatus === 'online' && lastChecked && (
                    <div style={{ fontSize: '0.7rem', marginTop: '4px', opacity: 0.7 }}>
                        {t('server.lastChecked', { time: lastChecked.toLocaleTimeString() })}
                    </div>
                )}
            </div>

            <section className="upload-section">
                {/* User Photo Card */}
                <div className="card">
                    <h3>{t('upload.user_title')}</h3>
                    <div className="preview-area" onClick={() => userFileInputRef.current.click()}>
                        <input
                            type="file"
                            ref={userFileInputRef}
                            onChange={(e) => handleImageUpload(e, 'user')}
                            accept="image/*"
                            aria-label={t('upload.user_title')}
                        />
                        {userImage ? (
                            <img src={userImage.url} alt="User" />
                        ) : (
                            <div className="preview-placeholder">
                                <span aria-hidden="true">📸</span>
                                <span style={{ textAlign: 'center', whiteSpace: 'pre-line' }}>{t('upload.user_placeholder')}</span>
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>{t('upload.user_helper')}</p>
                </div>

                {/* Model Photo Card */}
                <div className="card">
                    <h3>{t('upload.model_title')}</h3>
                    <div className="preview-area" onClick={() => modelFileInputRef.current.click()}>
                        <input
                            type="file"
                            ref={modelFileInputRef}
                            onChange={(e) => handleImageUpload(e, 'model')}
                            accept="image/*"
                            aria-label={t('upload.model_title')}
                        />
                        {modelImage ? (
                            <img src={modelImage.url} alt="Model" />
                        ) : (
                            <div className="preview-placeholder">
                                <span aria-hidden="true">👕</span>
                                <span style={{ textAlign: 'center', whiteSpace: 'pre-line' }}>{t('upload.model_placeholder')}</span>
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>{t('upload.model_helper')}</p>
                </div>
            </section>

            <section style={{ margin: '2rem 0', width: '100%', display: 'flex', justifyContent: 'center' }}>
                {error && <div role="alert" style={{ color: '#f43f5e', marginBottom: '1rem', fontWeight: 'bold', width: '100%', textAlign: 'center' }}>{error}</div>}

                <button
                    className="action-btn"
                    onClick={handleProcess}
                    disabled={loading || !userImage || !modelImage || serverStatus !== 'online'}
                    style={{ opacity: (serverStatus !== 'online') ? 0.5 : 1, cursor: (serverStatus !== 'online') ? 'not-allowed' : 'pointer' }}
                >
                    {loading ? t('action.crunching') : t('action.button')}
                </button>
            </section>

            {/* RESULT SECTION */}
            {baselineData && (

                <section className="result-section">
                    <h2 style={{ marginBottom: '2rem', color: 'var(--text-primary)' }}>{t('result.title')}</h2>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', justifyContent: 'center', width: '100%' }}>
                        <ResultCard
                            title={t('result.card_title')}
                            data={baselineData}
                        />
                    </div>

                    <div style={{ marginTop: '3rem' }}>
                        <button
                            className="secondary-btn"
                            onClick={() => setShowDebug(!showDebug)}
                        >
                            {showDebug ? t('result.hide_details') : t('result.show_details')}
                        </button>
                    </div>

                    {showDebug && (
                        <div className="debug-section" style={{ marginTop: '2rem', padding: '1rem', background: '#0f172a', borderRadius: '1rem', border: '1px solid #334155', width: '100%', maxWidth: '800px', boxSizing: 'border-box' }}>
                            <h3 style={{ marginBottom: '1rem' }}>{t('result.detailed_metrics')}</h3>

                            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                                <div style={{ maxWidth: '100%' }}>
                                    <h5 style={{ color: '#cbd5e1' }}>{t('result.user_skeleton')}</h5>
                                    <img src={`data:image/jpeg;base64,${baselineData.debug_user}`} alt="User detailed skeleton analysis" style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px', border: '1px solid #334155', objectFit: 'contain' }} />
                                </div>
                                <div style={{ maxWidth: '100%' }}>
                                    <h5 style={{ color: '#cbd5e1' }}>{t('result.model_skeleton')}</h5>
                                    <img src={`data:image/jpeg;base64,${baselineData.debug_model}`} alt="Model detailed skeleton analysis" style={{ maxWidth: '100%', maxHeight: '300px', borderRadius: '8px', border: '1px solid #334155', objectFit: 'contain' }} />
                                </div>
                            </div>
                        </div>
                    )}
                </section>
            )}
        </main>
    )
}

export default HomePage
