import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDashboard   = ()       => api.get('/dashboard').then(r => r.data)
export const getMetrics     = ()       => api.get('/metrics').then(r => r.data)
export const predict        = (data)   => api.post('/predict', data).then(r => r.data)
export const batchPredict   = (file)   => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/batch-predict', form, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data)
}
export const downloadResults = (results) =>
  api.post('/batch-download', { results }, { responseType: 'blob' }).then(r => {
    const url = window.URL.createObjectURL(new Blob([r.data]))
    const a   = document.createElement('a')
    a.href    = url
    a.download = 'stroke_predictions.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
  })

export const downloadTemplate = () => {
  window.location.href = '/api/sample-template'
}
