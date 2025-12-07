import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import LabPage from './pages/LabPage'
import './index.css'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/lab" element={<LabPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
