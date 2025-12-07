import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import LabPage from './pages/LabPage'
import './index.css'
import { API_BASE_URL, APP_VERSION } from './config'

function App() {
  const [versionStatus, setVersionStatus] = useState({ match: true, remoteVersion: null });

  useEffect(() => {
    const checkVersion = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/version`);
        if (response.ok) {
          const data = await response.json();
          if (data.version !== APP_VERSION) {
            setVersionStatus({ match: false, remoteVersion: data.version });
          }
        }
      } catch (error) {
        console.error("Failed to check version:", error);
      }
    };
    checkVersion();
  }, []);

  return (
    <>
      {!versionStatus.match && (
        <div style={{
          backgroundColor: '#ef4444',
          color: 'white',
          textAlign: 'center',
          padding: '10px',
          fontWeight: 'bold',
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          zIndex: 9999
        }}>
          ⚠️ Version Mismatch! Frontend: v{APP_VERSION} / Backend: v{versionStatus.remoteVersion || 'Unknown'}
          <br />
          <span style={{ fontSize: '0.8rem', fontWeight: 'normal' }}>Some features may not work as expected. Please refresh or redeploy.</span>
        </div>
      )}
      <BrowserRouter>
        <div style={{ paddingTop: !versionStatus.match ? '60px' : '0' }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/lab" element={<LabPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </>
  )
}

export default App
