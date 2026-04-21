import axios from 'axios'

export const api = axios.create({ baseURL: '/api' })

export async function fetchStats() {
  return (await api.get('/dashboard/stats')).data
}
export async function fetchDeposits(limit = 50) {
  return (await api.get(`/transactions/deposits?limit=${limit}`)).data
}
export async function fetchWithdrawals(limit = 50) {
  return (await api.get(`/transactions/withdrawals?limit=${limit}`)).data
}
export async function fetchPlayers() {
  return (await api.get('/players/')).data
}
export async function fetchPlayer(id: string) {
  return (await api.get(`/players/${id}`)).data
}
export async function fetchPlayerTransactions(id: string) {
  return (await api.get(`/players/${id}/transactions`)).data
}
export async function fetchPlayerAlerts(id: string) {
  return (await api.get(`/players/${id}/alerts`)).data
}
export async function fetchPlayerGraph(id: string) {
  return (await api.get(`/players/${id}/graph`)).data
}
export async function fetchRules() {
  return (await api.get('/rules/')).data
}
export async function fetchAlerts() {
  return (await api.get('/alerts/')).data
}
export async function updateTxStatus(id: string, status: string) {
  return (await api.patch(`/transactions/${id}/status?status=${status}`)).data
}
export async function updateAlert(id: string, data: object) {
  return (await api.patch(`/alerts/${id}`, data)).data
}
export async function createRule(data: object) {
  return (await api.post('/rules/', data)).data
}
export async function updateRule(id: string, data: object) {
  return (await api.patch(`/rules/${id}`, data)).data
}
export async function publishRule(id: string) {
  return (await api.post(`/rules/${id}/publish`)).data
}
export async function deleteRule(id: string) {
  return (await api.delete(`/rules/${id}`)).data
}
