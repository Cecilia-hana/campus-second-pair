// Socket.IO 客户端封装(对应后端 Flask-SocketIO,path=/ws/socket.io)
import { io } from 'socket.io-client'

let socket = null

export function connectWS(userId, onMessage) {
  closeWS()
  socket = io('/', {
    path: '/ws/socket.io',
    transports: ['websocket', 'polling'],
    reconnection: true,
    reconnectionDelay: 2000,
    reconnectionAttempts: Infinity
  })
  socket.on('connect', () => {
    // 上线后绑定 userId,后端依此把 sid 写入 _USER_SIDS
    socket.emit('register', { userId })
  })
  socket.on('message', (msg) => {
    try { onMessage(msg) } catch { /* ignore */ }
  })
}

export function closeWS() {
  if (socket) {
    try { socket.disconnect() } catch { /* ignore */ }
    socket = null
  }
}
