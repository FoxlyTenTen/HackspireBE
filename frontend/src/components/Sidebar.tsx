import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { NavLink } from 'react-router-dom'

export interface SidebarItem {
  to: string
  label: string
  icon: ReactNode
  /** Only match this exact path, not sub-routes (use for root-ish paths). */
  end?: boolean
}

interface SidebarProps {
  brand: string
  badge?: ReactNode
  items: SidebarItem[]
  storageKey: string
  variant?: 'admin'
}

export default function Sidebar({ brand, badge, items, storageKey, variant }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem(storageKey) === '1')

  useEffect(() => {
    localStorage.setItem(storageKey, collapsed ? '1' : '0')
  }, [collapsed, storageKey])

  return (
    <aside className={`app-sidebar${variant ? ` ${variant}` : ''}${collapsed ? ' collapsed' : ''}`}>
      <div className="sidebar-header">
        <span className="brand">
          {brand}
          {badge}
        </span>
        <button
          type="button"
          className="sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? '»' : '«'}
        </button>
      </div>
      <nav>
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}
            title={item.label}
          >
            <span className="sidebar-icon">{item.icon}</span>
            <span className="sidebar-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
