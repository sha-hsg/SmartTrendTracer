import React from 'react'
import ReactDOM from 'react-dom/client'
import axios from 'axios'
import ModernApp from './ModernApp'
import { ThemeProvider } from './contexts/ThemeContext'
import { API_BASE_URL } from './config/api'
import './index.css'

// Configure axios defaults
axios.defaults.baseURL = API_BASE_URL

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ThemeProvider>
      <ModernApp />
    </ThemeProvider>
  </React.StrictMode>,
)