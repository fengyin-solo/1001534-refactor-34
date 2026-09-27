/** 统一请求封装：拼后端地址、抛网络错误、给页脚留一句可读的说明。 */
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class RequestError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'RequestError'
  }
}

export function request(path: string, init?: RequestInit): Promise<Response> {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`
  return fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  }).catch((error: unknown) => {
    const detail = error instanceof Error ? error.message : '请求未送达'
    throw new RequestError(`接口请求失败：${detail}（后端可能未启动或网络不可达，请稍后重试）`)
  })
}

/** 读取接口 JSON；非 2xx 或网络失败时抛出带可读说明的 RequestError，不返回任何假数据。 */
export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await request(path, init)
  } catch (error) {
    throw error instanceof RequestError ? error : new RequestError('接口请求失败，请稍后重试')
  }
  if (!response.ok) {
    throw new RequestError(`接口返回 ${response.status}，数据未更新，请稍后重试`)
  }
  return (await response.json()) as T
}
