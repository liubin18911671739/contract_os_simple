/**
 * Sidebar Component
 * Left navigation sidebar with dark navy background
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  FileText,
  Book,
  BarChart3,
  Settings,
  ChevronLeft,
  Shield,
} from 'lucide-react';

interface SidebarProps {
  activeItem: string;
}

export function Sidebar({ activeItem }: SidebarProps) {
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  const menuItems = [
    { id: 'dashboard', label: '控制台', path: '/', icon: LayoutDashboard },
    { id: 'upload', label: '合同上传', path: '/new-task', icon: Upload },
    { id: 'tasks', label: '分析任务', path: '/processing', icon: FileText },
    { id: 'kb', label: '知识库', path: '/kb', icon: Book },
    { id: 'evaluation', label: '评测面板', path: '/evaluation', icon: BarChart3 },
    { id: 'settings', label: '设置', path: '/settings', icon: Settings },
  ];

  return (
    <aside
      className={`flex-shrink-0 flex flex-col bg-sidebar text-white transition-all duration-300 ${
        collapsed ? 'w-20' : 'w-64'
      }`}
    >
      {/* Logo Section */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        {!collapsed && (
          <div>
            <h1 className="text-xl font-bold">LegalOS</h1>
            <p className="text-xs text-slate-400">智能合同法律分析系统</p>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          aria-label="Toggle sidebar"
        >
          <ChevronLeft
            className={`w-5 h-5 transition-transform ${
              collapsed ? 'rotate-180' : ''
            }`}
          />
        </button>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 p-4 space-y-2">
        {menuItems.map((item) => {
          const isActive = activeItem === item.id;
          return (
            <button
              key={item.id}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                isActive
                  ? 'bg-accent text-white shadow-lg'
                  : 'text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {!collapsed && (
                <span className="font-medium">{item.label}</span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Enterprise Badge */}
      {!collapsed && (
        <div className="p-4 m-4 bg-slate-800 rounded-lg border border-slate-700">
          <div className="flex items-center gap-2 mb-2">
            <Shield className="w-4 h-4 text-accent" />
            <span className="text-sm font-semibold">企业版</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            多Agent协作 · 混合检索 · 幻觉检测
          </p>
        </div>
      )}
    </aside>
  );
}
