import { useState, useRef } from 'react'
import '../index.css'

function HomePage() {
    const [userImage, setUserImage] = useState(null)
    const [modelImage, setModelImage] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    const [baselineData, setBaselineData] = useState(null)
    const [showDebug, setShowDebug] = useState(false)

    const userFileInputRef = useRef(null)
    const modelFileInputRef = useRef(null)

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
            setError("Please upload both photos!")
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

            const response = await fetch('http://localhost:8000/process-baseline', {
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

    // Helper Component for Result Card
    const ResultCard = ({ title, data }) => {
        if (!data) return null;

        return (
            <div className="card" style={{ flex: '1 1 300px', minWidth: '300px', maxWidth: '450px', border: '1px solid #475569', background: 'rgba(30, 41, 59, 0.5)' }}>
                <h3 style={{ color: '#94a3b8' }}>{title}</h3>
                <div className="preview-area" style={{ cursor: 'default', background: !data.image ? '#0f172a' : 'transparent', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {data.image ? (
                        <img src={`data:image/jpeg;base64,${data.image}`} alt={title} />
                    ) : (
                        <div style={{ textAlign: 'center', color: '#64748b', padding: '2rem' }}>
                            <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1rem' }}>🍌🚫</span>
                            <p><strong>Visual Check Failed</strong></p>
                            <p style={{ fontSize: '0.8rem' }}>Nano Banana provided text analysis only.</p>
                        </div>
                    )}
                </div>

                <div style={{ marginTop: '1rem', padding: '1rem', background: '#1e293b', borderRadius: '0.5rem' }}>
                    <h4 style={{ color: '#cbd5e1', margin: '0 0 0.5rem 0' }}>FactBomb 💣</h4>
                    <p style={{ fontSize: '0.95rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.analysis.fact_bomb}</p>

                    <hr style={{ borderColor: '#334155', margin: '1rem 0' }} />
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', color: '#e2e8f0' }}>
                        <span>🧍 You: <strong>{data.analysis.user_heads} 등신</strong></span>
                        <span>✨ Model: <strong>{data.analysis.model_heads} 등신</strong></span>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="container">
            <h1>FactBomb Fitting Room</h1>
            <p className="tagline">Shockingly Realistic. Brutally Honest.</p>

            <div className="upload-section">
                {/* User Photo Card */}
                <div className="card">
                    <h3>1. Your Real Body</h3>
                    <div className="preview-area" onClick={() => userFileInputRef.current.click()}>
                        <input
                            type="file"
                            ref={userFileInputRef}
                            onChange={(e) => handleImageUpload(e, 'user')}
                            accept="image/*"
                        />
                        {userImage ? (
                            <img src={userImage.url} alt="User" />
                        ) : (
                            <div className="preview-placeholder">
                                <span>📸</span>
                                <span>Click to Upload</span>
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Full body shot required</p>
                </div>

                {/* Model Photo Card */}
                <div className="card">
                    <h3>2. The Dream Fit</h3>
                    <div className="preview-area" onClick={() => modelFileInputRef.current.click()}>
                        <input
                            type="file"
                            ref={modelFileInputRef}
                            onChange={(e) => handleImageUpload(e, 'model')}
                            accept="image/*"
                        />
                        {modelImage ? (
                            <img src={modelImage.url} alt="Model" />
                        ) : (
                            <div className="preview-placeholder">
                                <span>👕</span>
                                <span>Click to Upload</span>
                            </div>
                        )}
                    </div>
                    <p style={{ fontSize: '0.8rem', color: '#64748b' }}>Shopping mall model shot</p>
                </div>
            </div>

            <div style={{ margin: '2rem 0' }}>
                {error && <div style={{ color: '#f43f5e', marginBottom: '1rem', fontWeight: 'bold' }}>{error}</div>}

                <button
                    className="action-btn"
                    onClick={handleProcess}
                    disabled={loading || !userImage || !modelImage}
                >
                    {loading ? 'Crunching...' : 'Reality Check! 💥'}
                </button>
            </div>

            {/* RESULT SECTION */}
            {baselineData && (
                <div className="result-section" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
                    <h2 style={{ marginBottom: '2rem' }}>Analysis Result</h2>

                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2rem', justifyContent: 'center' }}>
                        <ResultCard
                            title="📊 Result"
                            data={baselineData}
                        />
                    </div>

                    <div style={{ marginTop: '3rem' }}>
                        <button
                            onClick={() => setShowDebug(!showDebug)}
                            style={{ background: 'transparent', border: '1px solid #64748b', color: '#94a3b8', cursor: 'pointer', padding: '0.5rem 1rem', borderRadius: '4px' }}
                        >
                            {showDebug ? 'Hide Details' : 'Show Analysis Details 🕵️'}
                        </button>
                    </div>

                    {showDebug && (
                        <div className="debug-section" style={{ marginTop: '2rem', padding: '1rem', background: '#0f172a', borderRadius: '1rem', border: '1px solid #334155' }}>
                            <h3 style={{ marginBottom: '1rem' }}>Detailed Metrics 📐</h3>

                            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                                <div>
                                    <h5 style={{ color: '#cbd5e1' }}>User Skeleton</h5>
                                    <img src={`data:image/jpeg;base64,${baselineData.debug_user}`} style={{ maxHeight: '300px', borderRadius: '8px', border: '1px solid #334155' }} />
                                </div>
                                <div>
                                    <h5 style={{ color: '#cbd5e1' }}>Model Skeleton</h5>
                                    <img src={`data:image/jpeg;base64,${baselineData.debug_model}`} style={{ maxHeight: '300px', borderRadius: '8px', border: '1px solid #334155' }} />
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}

export default HomePage
