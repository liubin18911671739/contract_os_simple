/**
 * MainLayout Component
 * Combines Sidebar and Header with main content area
 */
import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { SettingsProvider, useSettings } from '../../contexts/SettingsContext';

interface MainLayoutProps {
  children: React.ReactNode;
}

function LayoutContent({ children }: MainLayoutProps) {
  const location = useLocation();
  const [activeItem, setActiveItem] = useState('dashboard');

  // Update active item based on current path
  useEffect(() => {
    const pathToItem: Record<string, string> = {
      '/': 'dashboard',
      '/kb': 'kb',
      '/new-task': 'upload',
      '/processing': 'tasks',
      '/results': 'tasks',
      '/review': 'tasks',
      '/evaluation': 'evaluation',
      '/settings': 'settings',
    };
    setActiveItem(pathToItem[location.pathname] || 'dashboard');
  }, [location.pathname]);

  const { settings } = useSettings();

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar activeItem={activeItem} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          notificationCount={3}
          userName={settings.user.name}
          userDepartment={settings.user.department}
        />
        <main className="flex-1 overflow-auto bg-content p-6 relative">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function MainLayout({ children }: MainLayoutProps) {
  return (
    <SettingsProvider>
      <LayoutContent>{children}</LayoutContent>
    </SettingsProvider>
  );
}
