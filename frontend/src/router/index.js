import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/',                component: () => import('../views/item/ItemList.vue') },
  { path: '/login',           component: () => import('../views/user/Login.vue') },
  { path: '/item/:id',        component: () => import('../views/item/ItemDetail.vue') },
  { path: '/publish',         component: () => import('../views/item/ItemPublish.vue'), meta: { auth: true } },
  { path: '/orders/buy',      component: () => import('../views/order/MyBuyOrders.vue'), meta: { auth: true } },
  { path: '/orders/sell',     component: () => import('../views/order/MySellOrders.vue'), meta: { auth: true } },
  { path: '/messages',        component: () => import('../views/message/Inbox.vue'), meta: { auth: true } },
  { path: '/messages/:other', component: () => import('../views/message/Conversation.vue'), meta: { auth: true } }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  if (to.meta.auth && !localStorage.getItem('token')) next('/login')
  else next()
})

export default router
