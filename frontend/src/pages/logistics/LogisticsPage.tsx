import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getLogistics } from '../../api/logistics'
import type { Logistics } from '../../types'

const STATUS_CN: Record<string, string> = {
  picked_up: '已揽件', in_transit: '运输中',
  out_for_delivery: '派送中', delivered: '已签收',
}

const STATUS_ICON: Record<string, string> = {
  '已揽件': '📦', '运输中': '🚚', '派送中': '📬', '已签收': '✅',
}

export default function LogisticsPage() {
  const { orderId } = useParams()
  const navigate = useNavigate()
  const [logistics, setLogistics] = useState<Logistics | null>(null)
  const [loading, setLoading] = useState(true)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchLogistics = async () => {
    if (!orderId) return
    try {
      const res = await getLogistics(Number(orderId))
      if (res.code === 0) setLogistics(res.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogistics()
    // 每 15 秒轮询一次，自动更新物流状态
    timerRef.current = setInterval(fetchLogistics, 15000)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [orderId])

  if (!logistics) {
    if (loading) {
      return (
        <div className="page">
          <div className="state" style={{ minHeight: 300 }}>
            <div className="loading-dots"><span /><span /><span /></div>
          </div>
        </div>
      )
    }
    return (
      <div className="page">
        <div className="state" style={{ minHeight: 300 }}>
          <div className="state-icon">📦</div>
          <p className="state-title">物流信息等待更新</p>
          <p className="state-desc">订单尚未发货，请稍后再查看</p>
        </div>
      </div>
    )
  }

  const currentStatusCn = STATUS_CN[logistics.status] || logistics.status
  const timeline = logistics.timeline || []
  const currentIdx = timeline.findIndex(n => n.status === currentStatusCn)
  // 只取到当前节点为止（已完成 + 当前），隐藏未来节点
  const visibleNodes = currentIdx >= 0 ? timeline.slice(0, currentIdx + 1) : timeline
  const isDelivered = logistics.status === 'delivered'

  return (
    <div className="page animate-in">
      <button className="btn btn-ghost btn-sm" onClick={() => navigate(-1)} style={{ marginBottom: '1rem' }}>
        ← 返回
      </button>

      <div className="page-header">
        <h1>🚚 物流追踪</h1>
        <span className="text-sm text-muted">订单 #{orderId}</span>
      </div>

      {/* 物流信息卡 */}
      <div className="card card-sm" style={{
        marginBottom: '1.5rem',
        background: 'linear-gradient(135deg, var(--em-50), #fff)',
        border: '1px solid var(--em-200)',
      }}>
        <div className="flex items-center justify-between" style={{ marginBottom: 8 }}>
          <span style={{ fontWeight: 600 }}>{logistics.carrier}</span>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: 4,
            padding: '4px 12px', borderRadius: 'var(--radius-full)',
            background: isDelivered ? '#D1FAE5' : '#FEF3C7',
            color: isDelivered ? 'var(--em-700)' : '#92400E',
            fontWeight: 600, fontSize: '0.85rem',
          }}>
            {STATUS_ICON[currentStatusCn] || '📦'} {currentStatusCn}
          </span>
        </div>
        <div className="flex gap-lg flex-wrap">
          <div className="text-sm">
            <span className="text-muted">运单号：</span>
            <span style={{ fontWeight: 500, fontFamily: 'monospace' }}>{logistics.tracking_number}</span>
          </div>
          <div className="text-sm">
            <span className="text-muted">当前位置：</span>
            <span style={{ fontWeight: 500 }}>{logistics.current_location}</span>
          </div>
        </div>
        <div style={{ marginTop: 8 }}>
          <span className="badge badge-warning" style={{ fontSize: '0.8rem' }}>
            ⚡ 预计 5 分钟极速送达
          </span>
        </div>
      </div>

      {/* 配送进度 — 只显示到当前节点 */}
      <h3 style={{ marginBottom: '1rem' }}>配送进度</h3>
      <div className="card" style={{ padding: '1.5rem' }}>
        <div className="timeline">
          {visibleNodes.map((n, i) => {
            const isCurrent = i === visibleNodes.length - 1
            const showTime = !isDelivered && isCurrent && timeline.length > currentIdx + 1
            return (
              <div key={i} className="timeline-item">
                <div className="timeline-dot" style={{
                  background: isCurrent && !isDelivered ? 'var(--color-bg)' : 'var(--color-primary)',
                  borderColor: isCurrent && !isDelivered ? 'var(--color-primary)' : 'var(--color-primary-light)',
                  boxShadow: isCurrent && !isDelivered ? '0 0 0 4px rgba(5, 150, 105, 0.15)' : 'none',
                }} />
                <div className="timeline-content">
                  <div className="timeline-status" style={{
                    fontWeight: isCurrent ? 700 : 500,
                  }}>
                    {STATUS_ICON[n.status] && <span style={{ marginRight: 4 }}>{STATUS_ICON[n.status]}</span>}
                    {n.status}
                    {isCurrent && !isDelivered && (
                      <span style={{
                        marginLeft: 8, fontSize: '0.75rem',
                        color: 'var(--color-primary)', fontWeight: 600,
                      }}>进行中</span>
                    )}
                    {isDelivered && (
                      <span style={{
                        marginLeft: 8, fontSize: '0.75rem',
                        color: 'var(--em-700)', fontWeight: 600,
                      }}>✅ 已送达</span>
                    )}
                  </div>
                  <div className="timeline-meta">{n.time} — {n.location}</div>
                </div>
              </div>
            )
          })}
        </div>

        {/* 下一个节点的预告 */}
        {!isDelivered && currentIdx >= 0 && currentIdx < timeline.length - 1 && (
          <div style={{
            marginTop: '1.5rem', padding: '12px 16px',
            background: 'var(--gray-50)', borderRadius: 'var(--radius-sm)',
            border: '1px dashed var(--color-border)',
            textAlign: 'center', fontSize: '0.85rem',
            color: 'var(--color-text-secondary)',
          }}>
            ⏳ 下一站：{timeline[currentIdx + 1].status} @ {timeline[currentIdx + 1].location}
          </div>
        )}
      </div>
    </div>
  )
}
