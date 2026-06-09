const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost'

const API_PORTS = {
  auth: '8001',
  users: '8001',
  places: '8002',
  reports: '8003',
  bookings: '8004',
  'booking-slots': '8004',
  shop: '8005',
  orders: '8005',
  email: '8006',
}

function getApiUrl(path: string): string {
  const match = path.match(/^\/api\/v1\/([^\/]+)/)
  if (!match) {
    return path
  }

  const service = match[1]
  const port = API_PORTS[service as keyof typeof API_PORTS]

  if (port) {
    return `${API_BASE_URL}:${port}${path}`
  }

  return path
}

export async function apiRequest(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const url = getApiUrl(path)

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }

  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  return fetch(url, {
    ...options,
    headers,
  })
}
