import React from 'react'

interface StarRatingProps {
  rating: number
  maxRating?: number
  size?: 'sm' | 'md' | 'lg'
  interactive?: boolean
  onChange?: (rating: number) => void
  showValue?: boolean
}

/** 星级评分组件 — 支持展示模式（只读）与交互模式（可点击选择） */
const StarRating: React.FC<StarRatingProps> = ({
  rating,
  maxRating = 5,
  size = 'md',
  interactive = false,
  onChange,
  showValue = false,
}) => {
  const [hoverRating, setHoverRating] = React.useState(0)
  const displayRating = hoverRating || rating

  const sizeMap = { sm: '16px', md: '20px', lg: '28px' }
  const starSize = sizeMap[size]

  const stars = []
  for (let i = 1; i <= maxRating; i++) {
    const filled = i <= displayRating
    const halfFilled = !filled && i - 0.5 <= displayRating

    stars.push(
      <span
        key={i}
        style={{
          cursor: interactive ? 'pointer' : 'default',
          fontSize: starSize,
          color: filled ? '#f59e0b' : halfFilled ? '#fcd34d' : '#d1d5db',
          transition: 'color 0.15s',
          userSelect: 'none',
          lineHeight: 1,
        }}
        onClick={() => interactive && onChange?.(i)}
        onMouseEnter={() => interactive && setHoverRating(i)}
        onMouseLeave={() => interactive && setHoverRating(0)}
        role={interactive ? 'button' : 'img'}
        aria-label={`${i} 星`}
      >
        ★
      </span>,
    )
  }

  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
      {stars}
      {showValue && (
        <span style={{ marginLeft: '4px', fontSize: starSize, color: '#6b7280' }}>
          {rating.toFixed(1)}
        </span>
      )}
    </span>
  )
}

export default StarRating
