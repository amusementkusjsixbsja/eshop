import { useEffect, useState } from 'react'
import { adminListAfterSales, adminApproveAfterSale, adminRejectAfterSale } from '../../api/admin'
import type { AfterSaleItem } from '../../api/admin'

const statusMap: Record<string, string> = {
  pending: '待审核',
  approved: '已通过',
  rejected: '已拒绝',
  completed: '已完成',
}
const statusBadge: Record<string, string> = {
  pending: 'badge-warning',
  approved: 'badge-success',
  rejected: 'badge-danger',
  completed: 'badge-gray',
}
const typeMap: Record<string, string> = { refund: '退款', return: '退货' }

export default function AdminAfterSalePage() {
  const [items, setItems] = useState<AfterSaleItem[]>([])
  const [filter, setFilter] = useState('')
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminListAfterSales({ status: filter || undefined, page: 1, size: 50 })
      if (res.code === 0) setItems(res.data.items)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filter])

  const handleApprove = async (id: number) => {
    const res = await adminApproveAfterSale(id)
    if (res.code === 0) load()
  }

  const handleReject = async (id: number) => {
    const res = await adminRejectAfterSale(id)
    if (res.code === 0) load()
  }

  return (
    <div className="admin-content animate-in">
      <div className="page-header">
        <h1>售后管理</h1>
      </div>

      <div style={{ display: 'flex', gap: 4, marginBottom: '1.5rem', borderBottom: '2px solid var(--color-border)', paddingBottom: 0 }}>
        {['', 'pending', 'approved', 'rejected', 'completed'].map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            style={{
              padding: '8px 20px',
              background: 'none',
              border: 'none',
              borderBottom: filter === s ? '2px solid var(--color-primary)' : '2px solid transparent',
              marginBottom: '-2px',
              color: filter === s ? 'var(--color-primary)' : 'var(--gray-500)',
              fontWeight: filter === s ? 600 : 400,
              cursor: 'pointer',
              transition: 'all var(--transition)',
              fontSize: '0.9rem',
            }}
          >{s ? statusMap[s] : '全部'}</button>
        ))}
      </div>

      {loading ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="loading-dots"><span /><span /><span /></div>
        </div>
      ) : items.length === 0 ? (
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">📄</div>
          <p className="state-title">暂无售后申请</p>
          <p className="state-desc">{filter ? `没有${statusMap[filter]}的售后申请` : '系统暂无售后数据'}</p>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>用户</th>
                <th>订单号</th>
                <th>类型</th>
                <th>原因</th>
                <th>状态</th>
                <th>申请时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {items.map(a => (
                <tr key={a.id}>
                  <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>#{a.id}</td>
                  <td><span className="badge badge-gray">UID: {a.user_id}</span></td>
                  <td style={{ fontFamily: 'monospace' }}>#{a.order_id}</td>
                  <td>{typeMap[a.type] || a.type}</td>
                  <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={a.reason}>{a.reason || '-'}</td>
                  <td><span className={`badge ${statusBadge[a.status] || 'badge-gray'}`}>{statusMap[a.status] || a.status}</span></td>
                  <td className="text-sm text-muted">{a.created_at}</td>
                  <td>
                    {a.status === 'pending' ? (
                      <div style={{ display: 'flex', gap: 8 }}>
                        <button className="btn btn-sm btn-primary" onClick={() => handleApprove(a.id)}>通过</button>
                        <button className="btn btn-sm btn-danger" onClick={() => handleReject(a.id)}>拒绝</button>
                      </div>
                    ) : (
                      <span className="text-sm text-muted">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
