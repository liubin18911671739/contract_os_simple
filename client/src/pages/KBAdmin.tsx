/**
 * KB Admin Page with Tabbed Interface
 * Knowledge Base Management - Collections, Documents, Search
 */
import { useState, useEffect } from 'react';
import {
  File,
  Database,
  CheckCircle,
  HardDrive,
  Upload,
  Plus,
  Search,
  Trash2,
  Eye,
} from 'lucide-react';
import {
  createKBCollection,
  getKBCollections,
  uploadKBDocument,
  deleteKBDocument,
  getKBDocuments,
  getKBDocumentChunks,
  getKBCollectionStats,
  searchKB,
  KBCollection,
  KBDocument,
  KBSearchResult,
  KBChunk,
  KBCollectionStats,
} from '../api/kb';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Modal } from '../components/ui/Modal';
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
import { SearchResults } from '../components/kb/SearchResults';
import { DocumentChunks } from '../components/kb/DocumentChunks';
import { CollectionDetail } from '../components/kb/CollectionDetail';
import { KBSearchBar } from '../components/kb/KBSearchBar';

type TabType = 'collections' | 'documents' | 'search';

export default function KBAdmin() {
  const [activeTab, setActiveTab] = useState<TabType>('collections');
  const [collections, setCollections] = useState<KBCollection[]>([]);
  const [documents, setDocuments] = useState<KBDocument[]>([]);
  const [searchResults, setSearchResults] = useState<KBSearchResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Modals
  const [showNewCollection, setShowNewCollection] = useState(false);
  const [showUploadDoc, setShowUploadDoc] = useState(false);
  const [showCollectionDetail, setShowCollectionDetail] = useState(false);
  const [showDocumentChunks, setShowDocumentChunks] = useState(false);

  // Form data
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [formData, setFormData] = useState({ name: '', scope: 'GLOBAL' });
  const [selectedCollectionId, setSelectedCollectionId] = useState('');

  // Detail data
  const [selectedCollection, setSelectedCollection] = useState<KBCollection | null>(null);
  const [selectedCollectionStats, setSelectedCollectionStats] = useState<KBCollectionStats | null>(null);
  const [selectedDocumentChunks, setSelectedDocumentChunks] = useState<KBChunk[]>([]);
  const [selectedDocumentTitle, setSelectedDocumentTitle] = useState('');

  // Filters
  const [documentCollectionFilter, setDocumentCollectionFilter] = useState<string>('');

  useEffect(() => {
    loadData();
  }, []);

  // Auto-refresh documents with processing status
  useEffect(() => {
    const hasProcessing = documents.some(
      d => d.status === 'pending' || d.status === 'chunking' || d.status === 'indexing'
    );

    if (hasProcessing) {
      const interval = setInterval(loadData, 3000);
      return () => clearInterval(interval);
    }
  }, [documents]);

  async function loadData(): Promise<void> {
    try {
      const [collectionsData, documentsData] = await Promise.all([
        getKBCollections(),
        getKBDocuments(),
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
      await createKBCollection({ name: formData.name, scope: formData.scope as 'GLOBAL' | 'TENANT' | 'PROJECT' | 'DEPT' });
      setShowNewCollection(false);
      setFormData({ name: '', scope: 'GLOBAL' });
      loadData();
    } catch (error) {
      console.error('Failed to create collection:', error);
      alert('创建集合失败：' + (error as Error).message);
    }
  }

  async function handleUploadDocument(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile || !selectedCollectionId) {
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
      alert('上传失败：' + (error as Error).message);
    }
  }

  async function handleDeleteDocument(docId: string, docTitle: string) {
    if (!confirm(`确定要删除文档"${docTitle}"吗？此操作不可撤销。`)) {
      return;
    }

    try {
      await deleteKBDocument(docId);
      await loadData();
    } catch (error) {
      console.error('Failed to delete document:', error);
      alert('删除失败：' + (error as Error).message);
    }
  }

  async function handleViewChunks(docId: string, docTitle: string) {
    try {
      const chunks = await getKBDocumentChunks(docId);
      setSelectedDocumentChunks(chunks);
      setSelectedDocumentTitle(docTitle);
      setShowDocumentChunks(true);
    } catch (error) {
      console.error('Failed to load chunks:', error);
      alert('加载片段失败：' + (error as Error).message);
    }
  }

  async function handleViewCollection(collection: KBCollection) {
    setSelectedCollection(collection);
    try {
      const stats = await getKBCollectionStats(collection.id);
      setSelectedCollectionStats(stats);
      setShowCollectionDetail(true);
    } catch (error) {
      console.error('Failed to load collection stats:', error);
      // Show modal without stats
      setShowCollectionDetail(true);
    }
  }

  async function handleSearch(params: { query: string; collectionIds: string[]; topK: number }) {
    setSearchLoading(true);
    try {
      const results = await searchKB(params);
      setSearchResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      alert('搜索失败：' + (error as Error).message);
    } finally {
      setSearchLoading(false);
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

  const scopeLabels: Record<string, string> = {
    GLOBAL: '全局',
    TENANT: '租户',
    PROJECT: '项目',
    DEPT: '部门',
  };

  // Filter documents by collection
  const filteredDocuments = documentCollectionFilter
    ? documents.filter((d: KBDocument) => d.collection_id === documentCollectionFilter)
    : documents;

  return (
    <div>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatsCard
          icon={<File className="w-5 h-5 text-blue-600" />}
          label="文档总数"
          value={totals.documents}
        />
        <StatsCard
          icon={<CheckCircle className="w-5 h-5 text-emerald-600" />}
          label="已向量化"
          value={totals.indexed}
        />
        <StatsCard
          icon={<Database className="w-5 h-5 text-purple-600" />}
          label="文档片段"
          value={totals.chunks}
        />
        <StatsCard
          icon={<HardDrive className="w-5 h-5 text-amber-600" />}
          label="存储占用"
          value={((totals.chunks * 500) / (1024 * 1024)).toFixed(2) + ' MB'}
        />
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex -mb-px space-x-8">
          {[
            { id: 'collections', label: '集合', icon: Database },
            { id: 'documents', label: '文档', icon: File },
            { id: 'search', label: '搜索', icon: Search },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-1 py-4 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-accent text-accent'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow">
        {/* Collections Tab */}
        {activeTab === 'collections' && (
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">知识库集合</h2>
              <Button variant="secondary" size="sm" onClick={() => setShowNewCollection(true)}>
                <Plus className="w-4 h-4 mr-2" />
                新建集合
              </Button>
            </div>

            <Table>
              <TableHead>
                <TableHeader>名称</TableHeader>
                <TableHeader>范围</TableHeader>
                <TableHeader>文档数</TableHeader>
                <TableHeader>片段数</TableHeader>
                <TableHeader>已索引</TableHeader>
                <TableHeader>版本</TableHeader>
                <TableHeader>创建时间</TableHeader>
                <TableHeader>操作</TableHeader>
              </TableHead>
              <TableBody>
                {collections.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} className="text-center text-gray-500 py-8">
                      暂无集合，点击"新建集合"创建
                    </TableCell>
                  </TableRow>
                ) : (
                  collections.map((collection) => (
                    <TableRow key={collection.id}>
                      <TableCell className="font-medium">{collection.name}</TableCell>
                      <TableCell>
                        <Badge color="blue">{scopeLabels[collection.scope] || collection.scope}</Badge>
                      </TableCell>
                      <TableCell>{collection.document_count || 0}</TableCell>
                      <TableCell>{collection.chunk_count || 0}</TableCell>
                      <TableCell>{collection.indexed_count || 0}</TableCell>
                      <TableCell>v{collection.version}</TableCell>
                      <TableCell className="text-sm text-gray-500">
                        {new Date(collection.created_at).toLocaleDateString('zh-CN')}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleViewCollection(collection)}
                            className="text-accent hover:underline text-sm"
                          >
                            详情
                          </button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Documents Tab */}
        {activeTab === 'documents' && (
          <div className="p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold text-gray-900">文档列表</h2>
              <Select
                value={documentCollectionFilter}
                onChange={(e) => setDocumentCollectionFilter(e.target.value)}
                className="max-w-xs"
              >
                <option value="">全部集合</option>
                {collections.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </Select>
            </div>

            <Table>
              <TableHead>
                <TableHeader>标题</TableHeader>
                <TableHeader>类型</TableHeader>
                <TableHeader>集合</TableHeader>
                <TableHeader>片段数</TableHeader>
                <TableHeader>已索引</TableHeader>
                <TableHeader>状态</TableHeader>
                <TableHeader>创建时间</TableHeader>
                <TableHeader>操作</TableHeader>
              </TableHead>
              <TableBody>
                {filteredDocuments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center text-gray-500 py-8">
                      {documents.length === 0 ? '暂无文档，点击"上传文档"添加' : '该集合暂无文档'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredDocuments.map((doc: KBDocument) => {
                    const collection = collections.find(c => c.id === doc.collection_id);
                    return (
                      <TableRow key={doc.id}>
                        <TableCell className="font-medium">{doc.title}</TableCell>
                        <TableCell>
                          <Badge color="gray">{doc.doc_type}</Badge>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-gray-600">
                            {collection?.name || '-'}
                          </span>
                        </TableCell>
                        <TableCell>{doc.chunk_count}</TableCell>
                        <TableCell>{doc.indexed_count}</TableCell>
                        <TableCell>{getStatusBadge(doc.status)}</TableCell>
                        <TableCell className="text-sm text-gray-500">
                          {new Date(doc.created_at).toLocaleDateString('zh-CN')}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <button
                              onClick={() => handleViewChunks(doc.id, doc.title)}
                              className="text-accent hover:underline text-sm"
                              title="查看片段"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(doc.id, doc.title)}
                              className="text-red-600 hover:underline text-sm"
                              title="删除"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="p-6">
            <KBSearchBar collections={collections} onSearch={handleSearch} loading={searchLoading} />
            <div className="mt-6">
              <SearchResults results={searchResults} query={searchResults.length > 0 ? searchResults[0].doc_title : ''} loading={searchLoading} />
            </div>
          </div>
        )}
      </div>

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
          <div className="flex justify-end gap-2">
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
            <label className="block text-sm font-medium text-gray-700 mb-1">选择集合</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">选择文件</label>
            <input
              type="file"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div className="text-sm text-gray-500">
            支持格式：.txt, .md, .pdf, .docx
          </div>
          <div className="flex justify-end gap-2">
            <Button type="button" variant="secondary" onClick={() => setShowUploadDoc(false)}>
              取消
            </Button>
            <Button type="submit">上传</Button>
          </div>
        </form>
      </Modal>

      {/* Collection Detail Modal */}
      <CollectionDetail
        collection={selectedCollection}
        stats={selectedCollectionStats}
        isOpen={showCollectionDetail}
        onClose={() => setShowCollectionDetail(false)}
        onUpdate={loadData}
      />

      {/* Document Chunks Modal */}
      <DocumentChunks
        chunks={selectedDocumentChunks}
        documentTitle={selectedDocumentTitle}
        isOpen={showDocumentChunks}
        onClose={() => setShowDocumentChunks(false)}
      />
    </div>
  );
}
