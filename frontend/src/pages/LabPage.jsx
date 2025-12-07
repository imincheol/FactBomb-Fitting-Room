import { useState, useRef } from 'react'
import '../index.css'

function LabPage() {
    const [userImage, setUserImage] = useState(null)
    const [modelImage, setModelImage] = useState(null)
    const [resultImage, setResultImage] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [mode, setMode] = useState('legacy') // 'legacy' | 'lab' | 'full_ai'
    const [labFlow, setLabFlow] = useState('exp_a') // 'exp_a' | 'exp_b'

    const [baselineData, setBaselineData] = useState(null)
    const [activeData, setActiveData] = useState(null)
    const [isAiLoading, setIsAiLoading] = useState(false)
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
        setActiveData(null)
        setResultImage(null)
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
        setActiveData(null)
        setIsAiLoading(false)

        // STAGE 1: Baseline (Standard)
        let currentBaseline = null;
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

                // Pass meta data
                aiFormData.append('user_ratios_json', JSON.stringify(currentBaseline.meta.user_ratios))
                aiFormData.append('model_ratios_json', JSON.stringify(currentBaseline.meta.model_ratios))

                const aiRes = await fetch('http://localhost:8000/process-ai', {
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

                <div style={{ marginTop: '1rem', padding: '1rem', background: isBaseline ? '#1e293b' : '#4c1d95', borderRadius: '0.5rem' }}>
                    <h4 style={{ color: isBaseline ? '#cbd5e1' : '#d8b4fe', margin: '0 0 0.5rem 0' }}>FactBomb 💣</h4>
                    <p style={{ fontSize: '0.95rem', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{data.analysis.fact_bomb}</p>

                    <hr style={{ borderColor: isBaseline ? '#334155' : '#6d28d9', margin: '1rem 0' }} />
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
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h1>FactBomb Fitting Room <span style={{ fontSize: '0.5em', color: '#f472b6', border: '1px solid #f472b6', padding: '2px 8px', borderRadius: '10px', verticalAlign: 'middle' }}>LAB</span></h1>
                <a href="/" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.9rem' }}>Go to Basic &rarr;</a>
            </div>
            <p className="tagline">Shockingly Realistic. Brutally Honest. (Experimental Build)</p>

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

                {/* Mode Selector */}
                <div className="mode-selector" style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>

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
                        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
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
                    disabled={loading || !userImage || !modelImage}
                >
                    {loading ? 'Crunching Baseline...' : (isAiLoading ? 'Analyzing AI...' : 'Reality Check! 💥')}
                </button>
            </div>

            {/* RESULT SECTION (Comparison View) */}
            {(baselineData || isAiLoading) && (
                <div className="result-section" style={{ width: '100%', maxWidth: '1200px', margin: '0 auto' }}>
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
                                    <p style={{ color: '#94a3b8', marginBottom: '1rem' }}>Visualizing the warping engine skeletal tracking (Shared Engine).</p>

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
                        </>
                    )}
                </div>
            )}
        </div>
    )
}

export default LabPage
