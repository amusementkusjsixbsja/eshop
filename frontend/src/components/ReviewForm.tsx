import React, { useState } from 'react'
import StarRating from './StarRating'

interface ReviewFormProps {
  productId: number
  orderId: number
  productName: string
  onSubmit: (data: { product_id: number; order_id: number; rating: number; content: string }) => Promise<void>
  onClose: () => void
}

/** 评价表单 — 星级选择 + 文本框 + 提交 */
const ReviewForm: React.FC<ReviewFormProps> = ({ productId, orderId, productName, onSubmit, onClose }) => {
  const [rating, setRating] = useState(0)
  const [content, setContent] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (rating === 0) {
      alert('请选择评分')
      return
    }
    setSubmitting(true)
    try {
      await onSubmit({ product_id: productId, order_id: orderId, rating, content })
      alert('评价提交成功！')
      onClose()
    } catch {
      alert('评价提交失败，请重试')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '400px', width: '100%' }}>
      <h3 style={{ marginTop: 0 }}>评价 {productName}</h3>
      <div style={{ margin: '16px 0' }}>
        <div style={{ marginBottom: '8px', color: '#374151' }}>评分：</div>
        {rating === 0 && (
          <div style={{ fontSize: '12px', color: '#ef4444', marginBottom: '4px' }}>请选择评分</div>
        )}
        <StarRating rating={rating} size="lg" interactive onChange={setRating} />
      </div>
      <textarea
        placeholder="分享你的使用体验..."
        value={content}
        onChange={e => setContent(e.target.value)}
        maxLength={2000}
        rows={4}
        style={{
          width: '100%',
          padding: '8px',
          border: '1px solid #d1d5db',
          borderRadius: '6px',
          resize: 'vertical',
          boxSizing: 'border-box',
        }}
      />
      <div style={{ textAlign: 'right', fontSize: '12px', color: '#9ca3af', marginTop: '4px' }}>
        {content.length}/2000
      </div>
      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end', marginTop: '16px' }}>
        <button
          onClick={onClose}
          disabled={submitting}
          style={{ padding: '8px 16px', borderRadius: '6px', border: '1px solid #d1d5db', cursor: 'pointer', background: '#fff' }}
        >
          取消
        </button>
        <button
          onClick={handleSubmit}
          disabled={submitting || rating === 0}
          style={{
            padding: '8px 16px',
            borderRadius: '6px',
            border: 'none',
            backgroundColor: rating > 0 ? '#3b82f6' : '#9ca3af',
            color: '#fff',
            cursor: rating > 0 ? 'pointer' : 'not-allowed',
          }}
        >
          {submitting ? '提交中...' : '提交评价'}
        </button>
      </div>
    </div>
  )
}

export default ReviewForm
