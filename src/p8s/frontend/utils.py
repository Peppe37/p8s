"""
P8s Frontend Utilities.
"""


def get_vite_config(
    backend_port: int = 8000,
    frontend_port: int = 5173,
) -> str:
    """
    Generate Vite config with proxy to backend.

    Args:
        backend_port: Backend server port.
        frontend_port: Frontend dev server port.

    Returns:
        Vite config content as string.
    """
    return f"""import {{ defineConfig }} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({{
  plugins: [react()],
  server: {{
    port: {frontend_port},
    proxy: {{
      '/api': {{
        target: 'http://localhost:{backend_port}',
        changeOrigin: true,
      }},
      '/admin': {{
        target: 'http://localhost:{backend_port}',
        changeOrigin: true,
      }},
      '/auth': {{
        target: 'http://localhost:{backend_port}',
        changeOrigin: true,
      }},
    }},
  }},
}})
"""


def get_tsconfig() -> str:
    """
    Get default TypeScript config for P8s projects.

    Returns:
        tsconfig.json content as string.
    """
    return """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/types/*": ["./src/types/*"],
      "@/components/*": ["./src/components/*"],
      "@/pages/*": ["./src/pages/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"""


def create_react_hook(
    endpoint: str,
    method: str = "GET",
    name: str | None = None,
) -> str:
    """
    Generate a React Query hook for an endpoint.

    Args:
        endpoint: API endpoint path.
        method: HTTP method.
        name: Hook name (auto-generated if None).

    Returns:
        React hook code as string.
    """
    if name is None:
        # Generate name from endpoint
        parts = endpoint.strip("/").split("/")
        name = "use" + "".join(p.title() for p in parts if not p.startswith("{"))

    if method.upper() == "GET":
        return f"""import {{ useQuery }} from '@tanstack/react-query';

export function {name}() {{
  return useQuery({{
    queryKey: ['{endpoint}'],
    queryFn: async () => {{
      const response = await fetch('{endpoint}');
      if (!response.ok) throw new Error('Failed to fetch');
      return response.json();
    }},
  }});
}}
"""
    else:
        return f"""import {{ useMutation, useQueryClient }} from '@tanstack/react-query';

export function {name}() {{
  const queryClient = useQueryClient();

  return useMutation({{
    mutationFn: async (data: unknown) => {{
      const response = await fetch('{endpoint}', {{
        method: '{method.upper()}',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify(data),
      }});
      if (!response.ok) throw new Error('Failed to submit');
      return response.json();
    }},
    onSuccess: () => {{
      queryClient.invalidateQueries({{ queryKey: ['{endpoint}'] }});
    }},
  }});
}}
"""
