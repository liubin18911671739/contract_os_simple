/**
 * Collection Detail Modal
 * Shows detailed stats and allows editing collection properties
 */
import { useState, useEffect } from 'react';
import { KBCollection, KBCollectionStats, deleteKBCollection } from '../../api/kb';
import { Modal } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Badge } from '../ui/Badge';
import { File, Database, HardDrive, CheckCircle, Trash2, Edit2, Save } from 'lucide-react';

interface CollectionDetailProps {
  collection: KBCollection | null;
  stats?: KBCollectionStats | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

export function CollectionDetail({
  collection,
  stats,
  isOpen,
  onClose,
  onUpdate,
}: CollectionDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    name: collection?.name || '',
    scope: collection?.scope || 'GLOBAL',
  });
  const [deleting, setDeleting] = useState(false);

  // Update form when collection changes
  useEffect(() => {
    if (collection) {
      setEditForm({
        name: collection.name,
        scope: collection.scope,
      });
    }
  }, [collection]);

  // Don't render content if collection is not available
  if (!collection) {
    return (
      <Modal isOpen={isOpen} onClose={onClose} title="集合详情">
        <div className="text-center py-8 text-gray-500">加载中...</div>
      </Modal>
    );
  }

  const handleSave = async () => {
    // In a real implementation, this would call an update API
    setIsEditing(false);
    onUpdate();
    onClose();
  };

  const handleDelete = async () => {
    if (!confirm(`确定要删除集合"${collection.name}"吗？这将同时删除所有关联的文档和片段。`)) {
      return;
    }

    setDeleting(true);
    try {
      await deleteKBCollection(collection.id);
      onUpdate();
      onClose();
    } catch (error) {
      console.error('Failed to delete collection:', error);
      alert('删除失败：' + (error as Error).message);
    } finally {
      setDeleting(false);
    }
  };

  const scopeLabels: Record<string, string> = {
    GLOBAL: '全局',
    TENANT: '租户',
    PROJECT: '项目',
    DEPT: '部门',
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEditing ? '编辑集合' : '集合详情'}>
      <div className="space-y-6">
        {/* Basic Info */}
        {isEditing ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
              <Input
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                placeholder="集合名称"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">范围</label>
              <Select
                value={editForm.scope}
                onChange={(e) => setEditForm({ ...editForm, scope: e.target.value as 'GLOBAL' | 'TENANT' | 'PROJECT' | 'DEPT' })}
              >
                <option value="GLOBAL">全局</option>
                <option value="TENANT">租户</option>
                <option value="PROJECT">项目</option>
                <option value="DEPT">部门</option>
              </Select>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setIsEditing(false)}>
                取消
              </Button>
              <Button onClick={handleSave}>
                <Save className="w-4 h-4 mr-2" />
                保存
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{collection.name}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <Badge color="blue">{scopeLabels[collection.scope] || collection.scope}</Badge>
                  <span className="text-sm text-gray-500">v{collection.version}</span>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsEditing(true)}
              >
                <Edit2 className="w-4 h-4" />
              </Button>
            </div>

            {/* Stats Grid */}
            {stats && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-4">
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <File className="w-6 h-6 text-blue-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-900">{stats.document_count}</div>
                  <div className="text-xs text-gray-500">文档数</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <Database className="w-6 h-6 text-purple-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-900">{stats.chunk_count}</div>
                  <div className="text-xs text-gray-500">片段数</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <CheckCircle className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-900">{stats.indexed_count}</div>
                  <div className="text-xs text-gray-500">已索引</div>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 text-center">
                  <HardDrive className="w-6 h-6 text-amber-600 mx-auto mb-2" />
                  <div className="text-2xl font-bold text-gray-900">{stats.total_storage_mb}</div>
                  <div className="text-xs text-gray-500">MB</div>
                </div>
              </div>
            )}

            {/* Additional Info */}
            <div className="text-sm text-gray-600 space-y-1">
              <p>平均片段大小: {stats?.avg_chunk_size.toFixed(0) || 'N/A'} 字符</p>
              <p>创建时间: {new Date(collection.created_at).toLocaleString('zh-CN')}</p>
              <p>
                索引率:{' '}
                {stats && stats.chunk_count > 0
                  ? `${((stats.indexed_count / stats.chunk_count) * 100).toFixed(1)}%`
                  : '0%'}
              </p>
            </div>
          </div>
        )}

        {/* Delete Section */}
        {!isEditing && (
          <div className="pt-4 border-t border-gray-200">
            <Button
              variant="danger"
              className="w-full"
              onClick={handleDelete}
              disabled={deleting}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              {deleting ? '删除中...' : '删除集合'}
            </Button>
            <p className="text-xs text-red-600 mt-2 text-center">
              警告：删除集合将同时删除所有关联的文档和片段，此操作不可撤销
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}
