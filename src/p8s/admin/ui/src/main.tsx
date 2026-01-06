import React from 'react'
import ReactDOM from 'react-dom/client'
import { AdminPanel } from './components/admin/AdminPanel'
import './components/admin/admin.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <div style={{ height: '100vh', width: '100vw' }}>
            <AdminPanel />
        </div>
    </React.StrictMode>,
)
