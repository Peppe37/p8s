import { useQuery } from '@tanstack/react-query'

export default function Products() {
    const { data: products, isLoading } = useQuery({
        queryKey: ['products'],
        queryFn: async () => {
            const token = localStorage.getItem('token')
            const headers: HeadersInit = {}
            if (token) headers['Authorization'] = `Bearer ${token}`

            const res = await fetch('/api/products', { headers })
            if (!res.ok) throw new Error('Failed to fetch')
            return res.json()
        },
    })

    return (
        <div style={{ padding: '2rem' }}>
            <h2>Products</h2>
            {isLoading ? (
                <p>Loading...</p>
            ) : (
                <ul style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                    {products?.map((product: any) => (
                        <li key={product.id} style={{ border: '1px solid #333', padding: '1rem', listStyle: 'none' }}>
                            <h3>{product.name}</h3>
                            <p>{product.description}</p>
                            <p>Price: ${product.price}</p>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}
