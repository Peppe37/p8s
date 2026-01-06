import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// API Types
interface Product {
  id: string
  name: string
  description: string
  price: number
  stock: number
  is_active: boolean
  created_at: string
}

interface Category {
  id: string
  name: string
  description: string | null
}

interface User {
  id: string
  email: string
  username: string | null
  full_name: string
  role: string
}

interface AuthState {
  authenticated: boolean
  user: User | null
}

// API Functions
const api = {
  getHealth: () => fetch('/api/health').then(r => r.json()),
  getProducts: () => fetch('/api/products').then(r => r.json()),
  getCategories: () => fetch('/api/categories').then(r => r.json()),
  getMe: () => fetch('/api/me').then(r => r.json()),
  
  login: (email: string, password: string) => 
    fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(r => r.json()),
    
  register: (email: string, password: string) =>
    fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(r => r.json()),
}

function App() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'home' | 'products' | 'auth'>('home')
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  
  // Queries
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  })
  
  const { data: products, isLoading: productsLoading } = useQuery({
    queryKey: ['products'],
    queryFn: api.getProducts,
    enabled: activeTab === 'products',
  })
  
  const { data: authState } = useQuery<AuthState>({
    queryKey: ['me'],
    queryFn: api.getMe,
  })

  // Auth Form State
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isRegister, setIsRegister] = useState(false)
  const [authError, setAuthError] = useState('')

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault()
    setAuthError('')
    
    try {
      if (isRegister) {
        await api.register(email, password)
        setIsRegister(false)
        setAuthError('Registration successful! Please login.')
      } else {
        const result = await api.login(email, password)
        if (result.access_token) {
          localStorage.setItem('token', result.access_token)
          setToken(result.access_token)
          queryClient.invalidateQueries({ queryKey: ['me'] })
        } else {
          setAuthError(result.detail || 'Login failed')
        }
      }
    } catch (err) {
      setAuthError('An error occurred')
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
    queryClient.invalidateQueries({ queryKey: ['me'] })
  }

  return (
    <div className="app">
      {/* Header */}
      <header>
        <div className="logo">
          <h1>🔥 P8s Demo</h1>
          <span className="badge">v0.1.0</span>
        </div>
        <nav>
          <button 
            className={activeTab === 'home' ? 'active' : ''} 
            onClick={() => setActiveTab('home')}
          >
            Home
          </button>
          <button 
            className={activeTab === 'products' ? 'active' : ''} 
            onClick={() => setActiveTab('products')}
          >
            Products
          </button>
          <button 
            className={activeTab === 'auth' ? 'active' : ''} 
            onClick={() => setActiveTab('auth')}
          >
            {authState?.authenticated ? 'Profile' : 'Login'}
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <main>
        {activeTab === 'home' && (
          <section className="home">
            <div className="hero">
              <h2>Welcome to P8s Demo</h2>
              <p>A full-stack application built with the P8s framework</p>
            </div>
            
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-icon">⚡</div>
                <div className="stat-info">
                  <span className="stat-value">{health?.status || '...'}</span>
                  <span className="stat-label">API Status</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">🔥</div>
                <div className="stat-info">
                  <span className="stat-value">{health?.framework || '...'}</span>
                  <span className="stat-label">Framework</span>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">👤</div>
                <div className="stat-info">
                  <span className="stat-value">
                    {authState?.authenticated ? 'Yes' : 'No'}
                  </span>
                  <span className="stat-label">Logged In</span>
                </div>
              </div>
            </div>

            <div className="features">
              <h3>Framework Features</h3>
              <ul>
                <li>✅ FastAPI async backend</li>
                <li>✅ SQLModel ORM with UUID & timestamps</li>
                <li>✅ JWT Authentication</li>
                <li>✅ Auto-generated Admin API</li>
                <li>✅ React + Vite frontend</li>
                <li>✅ AI-powered fields (optional)</li>
              </ul>
            </div>
          </section>
        )}

        {activeTab === 'products' && (
          <section className="products">
            <h2>Products</h2>
            {productsLoading ? (
              <p className="loading">Loading products...</p>
            ) : products?.length === 0 ? (
              <div className="empty-state">
                <p>No products yet. Create one via the API!</p>
                <code>POST /api/products</code>
              </div>
            ) : (
              <div className="products-grid">
                {products?.map((product: Product) => (
                  <div key={product.id} className="product-card">
                    <h3>{product.name}</h3>
                    <p>{product.description}</p>
                    <div className="product-meta">
                      <span className="price">${product.price.toFixed(2)}</span>
                      <span className="stock">Stock: {product.stock}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {activeTab === 'auth' && (
          <section className="auth">
            {authState?.authenticated ? (
              <div className="profile">
                <h2>Welcome, {authState.user?.full_name || authState.user?.email}</h2>
                <div className="profile-card">
                  <div className="profile-field">
                    <label>Email</label>
                    <span>{authState.user?.email}</span>
                  </div>
                  <div className="profile-field">
                    <label>Role</label>
                    <span className="role-badge">{authState.user?.role}</span>
                  </div>
                  <div className="profile-field">
                    <label>ID</label>
                    <span className="id">{authState.user?.id}</span>
                  </div>
                </div>
                <button className="logout-btn" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            ) : (
              <div className="auth-form-container">
                <h2>{isRegister ? 'Register' : 'Login'}</h2>
                <form onSubmit={handleAuth} className="auth-form">
                  <div className="form-group">
                    <label>Email</label>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@example.com"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label>Password</label>
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      required
                      minLength={8}
                    />
                  </div>
                  {authError && <p className="error">{authError}</p>}
                  <button type="submit" className="submit-btn">
                    {isRegister ? 'Create Account' : 'Sign In'}
                  </button>
                </form>
                <p className="switch-auth">
                  {isRegister ? 'Already have an account?' : "Don't have an account?"}{' '}
                  <button onClick={() => setIsRegister(!isRegister)}>
                    {isRegister ? 'Login' : 'Register'}
                  </button>
                </p>
              </div>
            )}
          </section>
        )}
      </main>

      {/* Footer */}
      <footer>
        <p>Built with 🔥 P8s Framework</p>
        <p>
          <a href="/docs" target="_blank">API Docs</a>
          {' • '}
          <a href="/admin" target="_blank">Admin Panel</a>
        </p>
      </footer>
    </div>
  )
}

export default App
