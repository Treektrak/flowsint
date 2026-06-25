import { useAuthStore } from '@/stores/auth-store'
import { fetchWithAuth } from './api'

const API_URL = import.meta.env.VITE_API_URL ?? ''

export interface AgentExpert {
  key: string
  name: string
  emoji: string
}

export function listExperts(): Promise<AgentExpert[]> {
  return fetchWithAuth('/api/agents/experts')
}

export interface ModelOption {
  id: string
  label: string
}

export interface ProviderModels {
  provider: string
  label: string
  models: ModelOption[]
  has_key: boolean
}

export function listModels(): Promise<ProviderModels[]> {
  return fetchWithAuth('/api/agents/models')
}

/**
 * Запускает панель ИИ-экспертов над графом и скачивает PDF-отчёт.
 * Возвращает имя скачанного файла.
 */
export async function downloadAgentReport(
  sketchId: string,
  investigationName: string = '',
  opts: { expertKeys?: string[]; provider?: string; model?: string } = {}
): Promise<string> {
  const token = useAuthStore.getState().token
  const res = await fetch(`${API_URL}/api/agents/sketch/${sketchId}/report`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify({
      investigation_name: investigationName,
      expert_keys: opts.expertKeys ?? null,
      provider: opts.provider ?? null,
      model: opts.model ?? null
    })
  })

  if (res.status === 401) {
    useAuthStore.getState().logout()
    window.location.href = '/login'
    throw new Error('Сессия истекла, войдите снова.')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Ошибка ${res.status}`)
  }

  const blob = await res.blob()
  const safeName = (investigationName || 'отчёт')
    .replace(/[^\p{L}\p{N}\-_ ]/gu, '')
    .trim()
    .slice(0, 60)
  const filename = `Traceon-отчёт-${safeName || 'расследование'}.pdf`

  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
  return filename
}
