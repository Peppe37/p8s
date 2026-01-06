// Moved logic to main.tsx for simplicity, but cleaner to keep App separate.
// For now, main.tsx handles routing.
// Actually, I should probably keep `App` in `App.tsx` and import it in `main.tsx`.
// But I replaced `main.tsx` content with `App` component definition which is wrong.
// `main.tsx` should render `App`.
// Let's fix `App.tsx` first.

import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import Login from './pages/Login'
import Products from './pages/Products'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header>
          <h1>🔥 p8s_test_site</h1>
          <nav style={{ display: 'flex', gap: '1rem', justifyContent: 'center', marginTop: '1rem' }}>
            <Link to="/" style={{ color: 'white' }}>Home</Link>
            <Link to="/products" style={{ color: 'white' }}>Products</Link>
            <Link to="/login" style={{ color: 'white' }}>Login</Link>
            <a href="/admin" target="_blank" style={{ color: '#fbbf24' }}>Admin Panel</a>
          </nav>
        </header>
        <main>
          <Routes>
            <Route path="/" element={<div style={{ textAlign: 'center' }}><h2>Welcome to P8s Test Site</h2></div>} />
            <Route path="/login" element={<Login />} />
            <Route path="/products" element={<Products />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
