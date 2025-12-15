import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { useState } from 'react'
import Layout from './components/Layout'
import ReportInputForm from './components/ReportInputForm'
import ReportPreview from './components/ReportPreview'
import ReportViewer from './components/ReportViewer'

function App() {
  const [darkMode, setDarkMode] = useState(false)

  const toggleDarkMode = () => {
    setDarkMode(!darkMode)
    if (!darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  return (
    <Router>
      <div className={darkMode ? 'dark' : ''}>
        <Layout darkMode={darkMode} toggleDarkMode={toggleDarkMode}>
          <Routes>
            <Route path="/" element={<ReportInputForm />} />
            <Route path="/preview/:sessionId" element={<ReportPreview />} />
            <Route path="/report/:sessionId" element={<ReportViewer />} />
          </Routes>
        </Layout>
      </div>
    </Router>
  )
}

export default App

