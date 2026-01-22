import { useState, useEffect } from 'react';
import { File, Database, CheckCircle, HardDrive, Upload, Plus } from 'lucide-react';
import { createKBCollection, getKBCollections, uploadKBDocument } from '../api/kb';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
import { Card, CardHeader, CardBody } from '../components/ui/Card';
import { StatsCard } from '../components/ui/StatsCard';
import { Badge } from '../components/ui/Badge';
import {
  Table,
  TableHead,
  TableHeader,
  TableBody,
  TableRow,
  TableCell,
} from '../components/ui/Table';

interface KBCollection {
  id: string;
  name: string;
  scope: string;
  version: number;
  document_count?: number;
  chunk_count?: number;
  indexed_count?: number;
  created_at: string;
}

interface KBDocument {
  id: string;
  collection_id: string;
  title: string;
  doc_type: string;
  chunk_count: number;
  indexed_count: number;
  status: 'pending' | 'chunking' | 'indexing' | 'ready' | 'failed';
  created_at: string;
}

export default function KBAdmin() {
  const [collections, setCollections] = useState<KBCollection[]>([]);
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [showNewCollection, setShowNewCollection] = useState(false);
  const [showUploadDoc, setShowUploadDoc] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formData, setFormData] = useState({ name: '', scope: 'GLOBAL' });
  const [selectedCollectionId, setSelectedCollectionId] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [collectionsData, documentsData] = await Promise.all([
        getKBCollections(),
        fetch('/api/kb/documents').then((res) => (res.ok ? res.json() : [])),
      ]);
      setCollections(collectionsData);
      setDocuments(documentsData);
    } catch (error) {
      console.error('Failed to load KB data:', error);
    }
  }

  async function handleCreateCollection(e: React.FormEvent) {
    e.preventDefault();
    try {
      await createKBCollection({ name: formData.name, scope: formData.scope as any });
      setShowNewCollection(false);
      setFormData({ name: '', scope: 'GLOBAL' });
      loadData();
    } catch (error) {
      console.error('Failed to create collection:', error);
    }
  }

  async function handleUploadDocument(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile || !selectedCollectionId) {
      console.error('Missing file or collection:', { selectedFile: !!selectedFile, selectedCollectionId });
      return;
    }

    try {
      await uploadKBDocument(selectedCollectionId, selectedFile, selectedFile.name);
      setShowUploadDoc(false);
      setSelectedFile(null);
      setSelectedCollectionId('');
      loadData();
    } catch (error) {
      console.error('Failed to upload document:', error);
      // Don't clear state on error, let user see what they tried to upload
    }
  }

  function openUploadModal() {
    setSelectedFile(null);
    setSelectedCollectionId('');
    setShowUploadDoc(true);
  }

  // Calculate totals
  const totals = collections.reduce(
    (acc, col) => ({
      documents: acc.documents + (col.document_count || 0),
      chunks: acc.chunks + (col.chunk_count || 0),
      indexed: acc.indexed + (col.indexed_count || 0),
    }),
    { documents: 0, chunks: 0, indexed: 0 }
  );

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: 'blue' | 'emerald' | 'amber' | 'red'; label: string }> = {
      pending: { color: 'blue', label: '待处理' },
      chunking: { color: 'amber', label: '分块中' },
      indexing: { color: 'amber', label: '索引中' },
      ready: { color: 'emerald', label: '就绪' },
      failed: { color: 'red', label: '失败' },
    };
    const config = statusMap[status] || statusMap.pending;
    return <Badge color={config.color}>{config.label}</Badge>;
  };

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">知识库管理</h1>
          <p className="text-gray-600 mt-1">管理法规、案例和文档</p>
        </div>
        <Button onClick={openUploadModal}>
          <Upload className="w-4 h-4 mr-2" />
          上传文档
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatsCard
          icon={<File className="w-6 h-6 text-blue-600" />}
          label="文档总数"
          value={totals.documents}
        />
        <StatsCard
          icon={<CheckCircle className="w-6 h-6 text-emerald-600" />}
          label="已向量化"
          value={totals.indexed}
        />
        <StatsCard
          icon={<Database className="w-6 h-6 text-purple-600" />}
          label="文档片段"
          value={totals.chunks}
        />
        <StatsCard
          icon={<HardDrive className="w-6 h-6 text-amber-600" />}
          label="存储占用"
          value="3.53 MB"
        />
      </div>

      {/* Collections */}
      <Card className="mb-8">
        <CardHeader>
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold text-gray-900">集合</h2>
            <Button variant="ghost" size="sm" onClick={() => setShowNewCollection(true)}>
              <Plus className="w-4 h-4 mr-2" />
              新建集合
            </Button>
          </div>
        </CardHeader>
        <CardBody>
          <Table>
            <TableHead>
              <TableHeader>名称</TableHeader>
              <TableHeader>范围</TableHeader>
              <TableHeader>文档数</TableHeader>
              <TableHeader>片段数</TableHeader>
              <TableHeader>已索引</TableHeader>
              <TableHeader>版本</TableHeader>
              <TableHeader>创建时间</TableHeader>
            </TableHead>
            <TableBody>
              {collections.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-gray-500 py-8">
                    暂无集合
                  </TableCell>
                </TableRow>
              ) : (
                collections.map((collection) => (
                  <TableRow key={collection.id}>
                    <TableCell className="font-medium">{collection.name}</TableCell>
                    <TableCell>
                      <Badge color="blue">{collection.scope}</Badge>
                    </TableCell>
                    <TableCell>{collection.document_count || 0}</TableCell>
                    <TableCell>{collection.chunk_count || 0}</TableCell>
                    <TableCell>{collection.indexed_count || 0}</TableCell>
                    <TableCell>v{collection.version}</TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(collection.created_at).toLocaleDateString('zh-CN')}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      {/* Documents */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold text-gray-900">文档</h2>
        </CardHeader>
        <CardBody>
          <Table>
            <TableHead>
              <TableHeader>标题</TableHeader>
              <TableHeader>类型</TableHeader>
              <TableHeader>片段数</TableHeader>
              <TableHeader>已索引</TableHeader>
              <TableHeader>状态</TableHeader>
              <TableHeader>创建时间</TableHeader>
            </TableHead>
            <TableBody>
              {documents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center text-gray-500 py-8">
                    暂无文档
                  </TableCell>
                </TableRow>
              ) : (
                documents.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">{doc.title}</TableCell>
                    <TableCell>
                      <Badge color="gray">{doc.doc_type}</Badge>
                    </TableCell>
                    <TableCell>{doc.chunk_count}</TableCell>
                    <TableCell>{doc.indexed_count}</TableCell>
                    <TableCell>{getStatusBadge(doc.status)}</TableCell>
                    <TableCell className="text-sm text-gray-500">
                      {new Date(doc.created_at).toLocaleDateString('zh-CN')}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardBody>
      </Card>

      {/* New Collection Modal */}
      <Modal
        isOpen={showNewCollection}
        onClose={() => setShowNewCollection(false)}
        title="新建集合"
      >
        <form onSubmit={handleCreateCollection} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
            <Input
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              placeholder="例如：劳动法规库"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">范围</label>
            <Select
              value={formData.scope}
              onChange={(e) => setFormData({ ...formData, scope: e.target.value })}
            >
              <option value="GLOBAL">全局</option>
              <option value="TENANT">租户</option>
              <option value="PROJECT">项目</option>
              <option value="DEPT">部门</option>
            </Select>
          </div>
          <div className="flex justify-end space-x-2">
            <Button type="button" variant="secondary" onClick={() => setShowNewCollection(false)}>
              取消
            </Button>
            <Button type="submit">创建</Button>
          </div>
        </form>
      </Modal>

      {/* Upload Document Modal */}
      <Modal
        isOpen={showUploadDoc}
        onClose={() => {
          setShowUploadDoc(false);
          setSelectedFile(null);
          setSelectedCollectionId('');
        }}
        title="上传文档"
      >
        <form onSubmit={handleUploadDocument} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">集合</label>
            <Select
              value={selectedCollectionId}
              onChange={(e) => setSelectedCollectionId(e.target.value)}
              required
            >
              <option value="">选择集合</option>
              {collections.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">文件</label>
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div className="flex justify-end space-x-2">
            <Button type="button" variant="secondary" onClick={() => setShowUploadDoc(false)}>
              取消
            </Button>
            <Button type="submit">上传</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
