import { useEffect, useState, useCallback } from 'react'
import { adminListReviews, adminSetReviewStatus } from '../../api/admin'
import type { Review } from '../../types'

const ratingStars = (r: number) => '★'.repeat(r) + '☆'.repeat(5 - r)

const statusMap: Record<string, string> = { visible: '可见', hidden: '已隐藏' }
const statusBadge: Record<string, string> = { visible: 'badge-success', hidden: 'badge-gray' }

export default function AdminReviewPage() {
  const [reviews, setReviews] = useState<Review[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [size] = useState(15)
  const [filterRating, setFilterRating] = useState<number | ''>('')
  const [filterProduct, setFilterProduct] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionId, setActionId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminListReviews({
        page,
        size,
        rating: filterRating || undefined,
        product_id: filterProduct ? Number(filterProduct) : undefined,
      })
      if (res.code === 0) {
        setReviews(res.data.items)
        setTotal(res.data.total)
      }
    } finally {
      setLoading(false)
    }
  }, [page, size, filterRating, filterProduct])

  useEffect(() => { load() }, [load])

  const toggleStatus = async (id: number, current: string) => {
    setActionId(id)
    try {
      const next = current === 'visible' ? 'hidden' : 'visible'
      const res = await adminSetReviewStatus(id, next)
      if (res.code === 0) load()
    } finally {
      setActionId(null)
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / size))

  return (
    <div className="admin-content animate-in">
      <div className="page-header">
        <h1>评价管理</h1>
        <span className="text-sm text-muted">共 {total} 条评价</span>
      </div>

      {/* 筛选栏 */}
      <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label className="text-sm text-muted">星级</label>
          <select
            value={filterRating}
            onChange={e => { setFilterRating(e.target.value ? Number(e.target.value) : ''); setPage(1) }}
            className="input"
            style={{ width: 'auto', padding: '6px 28px 6px 12px' }}
          >
            <option value="">全部</option>
            <option value="5">5 星</option>
            <option value="4">4 星</option>
            <option value="3">3 星</option>
            <option value="2">2 星</option>
            <option value="1">1 星</option>
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <label className="text-sm text-muted">商品ID</label>
          <input
            type="number"
            placeholder="筛选商品"
            value={filterProduct}
            onChange={e => { setFilterProduct(e.target.value); setPage(1) }}
            className="input"
            style={{ width: 120, padding: '6px 12px' }}
          />
        </div>
      </div>

      {loading ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">💬</div>
          <p className="state-title">暂无评价</p>
          <p className="state-desc">当前筛选条件下没有评价数据</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>商品</th>
                <th>用户</th>
                <th>评分</th>
                <th>内容</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map(r => (
                <tr key={r.id} style={{ opacity: r.status === 'hidden' ? 0.55 : 1 }}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>#{r.id}</td>
                  <td><span className="badge badge-gray">#{r.product_id}</span></td>
                  <td>{r.nickname || `UID:${r.user_id}`}</td>
                  <td><span style={{ color: 'var(--am-500)', letterSpacing: 1 }}>{ratingStars(r.rating)}</span></td>
                  <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.content}>{r.content || '-'}</td>
                  <td><span className={`badge ${statusBadge[r.status] || 'badge-gray'}`}>{statusMap[r.status] || r.status}</span></td>
                  <td>
                    <button
                      onClick={() => toggleStatus(r.id, r.status)}
                      disabled={actionId === r.id}
                      className={`btn btn-sm ${r.status === 'visible' ? 'btn-outline' : 'btn-primary'}`}
                    >
                      {r.status === 'visible' ? '隐藏' : '显示'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 分页 */}
      {totalPages > 1 && (
        <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: '1.5rem', alignItems: 'center' }}>
          <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="btn btn-sm btn-outline">上一页</button>
          <span className="text-sm text-muted">{page} / {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="btn btn-sm btn-outline">下一页</button>
        </div>
      )}
    </div>
  )
}
