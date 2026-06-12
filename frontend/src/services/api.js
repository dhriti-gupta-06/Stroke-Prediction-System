import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const getDashboard        = ()       => api.get('/dashboard').then(r => r.data)
export const getMetrics          = ()       => api.get('/metrics').then(r => r.data)
export const getModelPerformance = ()       => api.get('/model-performance').then(r => r.data)
export const getAnalyticsMetrics = ()       => api.get('/advanced-metrics').then(r => r.data)

export const predict = (data) => api.post('/predict', data).then(r => r.data)

export const batchPredict = (file) => {
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

export const savePrediction = (payload) =>
  api.post('/save-prediction', payload).then(r => r.data)

export const saveBatchPredictions = (results) =>
  api.post('/save-batch-predictions', { results }).then(r => r.data)

export const getPredictions = ({ page = 1, per_page = 20, search = '', prediction = '' } = {}) =>
  api.get('/predictions', { params: { page, per_page, search, prediction } }).then(r => r.data)

// ── NEW ──────────────────────────────────────────────────────────────────────

export const checkPatient = (patient_id) =>
  api.post('/check-patient', { patient_id }).then(r => r.data)

export const getPatient = (patient_id) =>
  api.get(`/patient/${encodeURIComponent(patient_id)}`).then(r => r.data)

export const generatePatientId = () =>
  api.get('/generate-patient-id').then(r => r.data)