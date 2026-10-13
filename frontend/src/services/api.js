import axios from 'axios'

export const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? '/api' : 'https://stroke-prediction-system-lihd.onrender.com/api')

const api = axios.create({ baseURL: API_BASE_URL })

// Attach JWT to every request automatically
api.interceptors.request.use(config => {
  const token = localStorage.getItem('ns_token')
  if (token) config.headers['Authorization'] = `Bearer ${token}`
  return config
})

// Redirect to login on 401
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('ns_token')
      localStorage.removeItem('ns_username')
      localStorage.removeItem('ns_role')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export const getDashboard        = ()       => api.get('/dashboard').then(r => r.data)
export const getMetrics          = ()       => api.get('/metrics').then(r => r.data)
export const getModelPerformance = ()       => api.get('/model-performance').then(r => r.data)
export const getAnalyticsMetrics = (params = {}) =>
  api.get('/advanced-metrics', { params }).then(r => r.data)

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
  window.location.href = `${API_BASE_URL}/sample-template`
}

export const savePrediction = (payload) =>
  api.post('/save-prediction', payload).then(r => r.data)

export const saveBatchPredictions = (results) =>
  api.post('/save-batch-predictions', { results }).then(r => r.data)

export const getPredictions = ({ page = 1, per_page = 20, search = '', prediction = '', user = '' } = {}) => {
  const params = { page, per_page, search, prediction }
  if (user) params.user = user
  return api.get('/predictions', { params }).then(r => r.data)
}

export const checkPatient    = (patient_id) => api.post('/check-patient', { patient_id }).then(r => r.data)
export const getPatient      = (patient_id) => api.get(`/patient/${encodeURIComponent(patient_id)}`).then(r => r.data)
export const generatePatientId = ()         => api.get('/generate-patient-id').then(r => r.data)
export const getMe           = ()           => api.get('/me').then(r => r.data)
export const getUserStats    = ()           => api.get('/user-stats').then(r => r.data)