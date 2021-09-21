/** When your routing table is too long, you can split it into small modules **/

import Layout from '@/layout'

const pocRouter = {
  path: '/poc',
  name: 'poc',
  redirect: '/poc/index',
  component: Layout,
  meta: { title: 'PocManager', icon: 'el-icon-s-grid', noCache: true },
  children: [
    {
      path: 'index',
      name: 'PocList',
      component: () => import('@/views/poc/index'),
      meta: { title: 'PocList', icon: 'el-icon-s-grid', noCache: true }
    }
  ]
}
export default pocRouter
