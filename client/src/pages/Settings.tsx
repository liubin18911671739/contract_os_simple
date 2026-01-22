/**
 * Settings Page
 * Main settings page with tabbed interface
 */

import { Tabs } from '../components/ui/Tabs';
import AccountSettings from '../components/settings/AccountSettings';
import SystemSettings from '../components/settings/SystemSettings';
import KBSettings from '../components/settings/KBSettings';
import UISettings from '../components/settings/UISettings';

export default function Settings() {
  const tabs = [
    { id: 'account', label: '账户设置' },
    { id: 'system', label: '系统配置' },
    { id: 'kb', label: '知识库设置' },
    { id: 'ui', label: '界面设置' }
  ];

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">设置</h1>
        <p className="text-gray-600 mt-1">管理系统配置和偏好设置</p>
      </div>

      <Tabs tabs={tabs}>
        {(activeTab) => {
          switch (activeTab) {
            case 'account':
              return <AccountSettings />;
            case 'system':
              return <SystemSettings />;
            case 'kb':
              return <KBSettings />;
            case 'ui':
              return <UISettings />;
            default:
              return <div>未知标签页</div>;
          }
        }}
      </Tabs>
    </div>
  );
}
