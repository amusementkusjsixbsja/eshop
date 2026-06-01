import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getLogistics } from '../../api/logistics'
import type { Logistics } from '../../types'

const statusMap: Record<string, string> = {
  picked_up: '已揽件', in_transit: '运输中', out_for_delivery: '派送中', delivered: '已签收',
}

export default function LogisticsPage() {
  const { orderId } = useParams()
  const navigate = useNavigate()
  const [logistics, setLogistics] = useState<Logistics | null>(null)

  useEffect(() => {
    if (orderId) getLogistics(Number(orderId)).then(res => {
      if (res.code === 0) setLogistics(res.data)
    })
  }, [orderId])

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 20 }}>
      <button onClick={() => navigate(-1)}>← 返回</button>
      <h1>物流追踪</h1>
      {logistics ? (
        <div>
          <p>承运方：{logistics.carrier} | 运单号：{logistics.tracking_number}</p>
          <p>状态：{statusMap[logistics.status] || logistics.status}</p>
          <p>当前位置：{logistics.current_location}</p>
          <p>预计送达：{logistics.estimated_delivery}</p>
          <h3>运输节点</h3>
          {logistics.timeline.map((n, i) => (
            <div key={i} style={{ padding: '8px 0', borderLeft: '2px solid #1890ff', paddingLeft: 16, marginLeft: 8 }}>
              <div style={{ fontWeight: 'bold' }}>{n.status}</div>
              <div style={{ color: '#999', fontSize: 12 }}>{n.time} - {n.location}</div>
            </div>
          ))}
        </div>
      ) : (
        <p>物流信息等待更新</p>
      )}
    </div>
  )
}
