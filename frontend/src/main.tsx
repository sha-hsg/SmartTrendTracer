import React from 'react'
import ReactDOM from 'react-dom/client'
import ModernApp from './ModernApp'
import { ThemeProvider } from './contexts/ThemeContext'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <ModernApp />
    </ThemeProvider>
  </React.StrictMode>,
)