import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

const api = axios.create({ baseURL: '', timeout: 15000 })

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers.Authorization = 'Bearer ' + token
  return cfg
})

api.interceptors.response.use(
  resp => {
    const body = resp.data
    if (body && typeof body === 'object' && 'code' in body) {
      if (body.code !== 0) {
        if (body.code === 1002) {
          // 未登录,清空并跳登录
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          ElMessage.warning('登录已过期,请重新登录')
          router.push('/login')
        } else {
          ElMessage.error(body.msg || '请求失败')
        }
        return Promise.reject(body)
      }
      return body  // {code, msg, data}
    }
    return resp
  },
  err => {
    if (err.response && err.response.status === 401) {
      localStorage.removeItem('token')
      router.push('/login')
    } else {
      ElMessage.error(err.message || '网络错误')
    }
    return Promise.reject(err)
  }
)

export default api
