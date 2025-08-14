import React from 'react'
import ReactDOM from 'react-dom/client'
import axios from 'axios'
import ModernApp from './ModernApp'
import './index.css'

// Configure axios defaults
axios.defaults.baseURL = 'http://localhost:8000'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ModernApp />
  </React.StrictMode>,
)