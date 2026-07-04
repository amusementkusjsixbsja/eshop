/**
 * ProductImage — 本地生成的商品占位图（零网络请求，秒加载，图文相符）
 *
 * 按商品分类（category_id）渲染对应图标 + 渐变背景 + 商品名。
 * 替代此前 picsum.photos 随机图（慢 + 不对版）。
 */

interface ProductImageProps {
  name: string
  categoryId?: number
  className?: string
  style?: React.CSSProperties
  size?: number
}

// 分类 → 图标 + 渐变色
const CATEGORY_META: Record<number, { icon: string; from: string; to: string }> = {
  // 智能家居
  1: { icon: '🏠', from: '#059669', to: '#047857' },
  10: { icon: '🔐', from: '#10B981', to: '#059669' },
  11: { icon: '💡', from: '#FBBF24', to: '#F59E0B' },
  12: { icon: '🪟', from: '#60A5FA', to: '#3B82F6' },
  13: { icon: '🤖', from: '#34D399', to: '#10B981' },
  // 数码配件
  2: { icon: '🎧', from: '#6366F1', to: '#4F46E5' },
  20: { icon: '🎧', from: '#818CF8', to: '#6366F1' },
  21: { icon: '🔌', from: '#F59E0B', to: '#D97706' },
  22: { icon: '🔋', from: '#22C55E', to: '#16A34A' },
  23: { icon: '🔗', from: '#94A3B8', to: '#64748B' },
  // 安防设备
  3: { icon: '🛡️', from: '#EF4444', to: '#DC2626' },
  30: { icon: '📷', from: '#F87171', to: '#EF4444' },
  31: { icon: '🔔', from: '#FB923C', to: '#F97316' },
  32: { icon: '👁️', from: '#A78BFA', to: '#8B5CF6' },
  // 家用电器
  4: { icon: '🍳', from: '#F472B6', to: '#EC4899' },
  40: { icon: '🍳', from: '#FB7185', to: '#F43F5E' },
  41: { icon: '🌀', from: '#38BDF8', to: '#0EA5E9' },
  // 运动户外
  5: { icon: '🏋️', from: '#FACC15', to: '#EAB308' },
  50: { icon: '🏋️', from: '#FDE047', to: '#FACC15' },
  51: { icon: '🎒', from: '#4ADE80', to: '#22C55E' },
  // 个护健康
  6: { icon: '💆', from: '#F0ABFC', to: '#E879F9' },
  60: { icon: '💆', from: '#F5D0FE', to: '#F0ABFC' },
  61: { icon: '⌚', from: '#5EEAD4', to: '#2DD4BF' },
}

const DEFAULT_META = { icon: '📦', from: '#94A3B8', to: '#64748B' }

export default function ProductImage({ name, categoryId, className, style, size = 400 }: ProductImageProps) {
  const meta = (categoryId && CATEGORY_META[categoryId]) || DEFAULT_META
  const gradId = `g${categoryId || 0}`

  // 商品名截断（最多显示 8 字）
  const displayName = name.length > 10 ? name.slice(0, 9) + '…' : name

  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}">
      <defs>
        <linearGradient id="${gradId}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="${meta.from}"/>
          <stop offset="100%" stop-color="${meta.to}"/>
        </linearGradient>
      </defs>
      <rect width="${size}" height="${size}" fill="url(#${gradId})"/>
      <text x="50%" y="42%" font-size="${size * 0.28}" text-anchor="middle" dominant-baseline="central">${meta.icon}</text>
      <text x="50%" y="72%" font-size="${size * 0.075}" fill="rgba(255,255,255,0.95)" text-anchor="middle" dominant-baseline="central" font-family="system-ui, sans-serif" font-weight="600">${escapeXml(displayName)}</text>
    </svg>
  `.trim()

  const dataUri = `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`

  return (
    <img
      src={dataUri}
      alt={name}
      className={className}
      style={style}
      loading="lazy"
      decoding="async"
    />
  )
}

function escapeXml(s: string): string {
  return s.replace(/[<>&'"]/g, c => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' }[c] || c))
}
