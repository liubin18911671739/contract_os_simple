import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Shield, Users, Zap } from 'lucide-react';
import { createContract, uploadContractVersion } from '../api/contracts';
import { createTask } from '../api/tasks';
import { getKBCollections } from '../api/kb';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';
import { Alert } from '../components/ui/Alert';
import { Card, CardBody } from '../components/ui/Card';

export default function NewTaskUpload() {
  const navigate = useNavigate();
  const [collections, setCollections] = useState<any[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [formData, setFormData] = useState({
    contract_name: '',
    counterparty: '',
    contract_type: 'SERVICE',
    kb_mode: 'STRICT',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadCollections();
  }, []);

  async function loadCollections() {
    try {
      const data = await getKBCollections();
      setCollections(data);
    } catch (error) {
      console.error('Failed to load collections:', error);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!selectedFile || selectedCollections.length === 0) {
      setError('请选择文件并至少选择一个知识库集合');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create contract
      const contract = await createContract({
        contract_name: formData.contract_name,
        counterparty: formData.counterparty || undefined,
        contract_type: formData.contract_type,
      });

      // Upload file
      const version = await uploadContractVersion(contract.id, selectedFile);

      // Create task
      const task = await createTask({
        contract_version_id: version.id,
        kb_collection_ids: selectedCollections,
        kb_mode: formData.kb_mode as any,
      });

      navigate(`/processing/${task.id}`);
    } catch (err: any) {
      setError(err.message || '创建任务失败');
    } finally {
      setLoading(false);
    }
  }

  function toggleCollection(collectionId: string) {
    setSelectedCollections((prev) =>
      prev.includes(collectionId)
        ? prev.filter((id) => id !== collectionId)
        : [...prev, collectionId]
    );
  }

  function handleDrag(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">合同上传</h1>
        <p className="text-gray-600 mt-1">上传合同文件进行智能法律风险分析</p>
      </div>

      {error && (
        <Alert type="error" className="mb-6">
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* File Upload Section */}
        <Card>
          <CardBody>
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                dragActive
                  ? 'border-accent bg-blue-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                id="file-upload"
                className="hidden"
                onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                required
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="w-16 h-16 mx-auto text-gray-400 mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">
                  点击或拖拽文件到此处上传
                </p>
                <p className="text-sm text-gray-500">
                  支持 TXT、PDF、DOCX 格式，最大 100MB
                </p>
              </label>
              {selectedFile && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg inline-block">
                  <p className="text-sm font-medium text-gray-700">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              )}
            </div>
          </CardBody>
        </Card>

        {/* Contract Details */}
        <Card>
          <CardBody>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">合同信息</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  合同名称 <span className="text-red-500">*</span>
                </label>
                <Input
                  value={formData.contract_name}
                  onChange={(e) => setFormData({ ...formData, contract_name: e.target.value })}
                  placeholder="例如：技术服务合同"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">对方当事人</label>
                <Input
                  value={formData.counterparty}
                  onChange={(e) => setFormData({ ...formData, counterparty: e.target.value })}
                  placeholder="例如：某某科技有限公司"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">合同类型</label>
                <Select
                  value={formData.contract_type}
                  onChange={(e) => setFormData({ ...formData, contract_type: e.target.value })}
                >
                  <option value="SERVICE">服务合同</option>
                  <option value="SALES">销售合同</option>
                  <option value="NDA">保密协议</option>
                  <option value="EMPLOYMENT">劳动合同</option>
                  <option value="OTHER">其他</option>
                </Select>
              </div>
            </div>
          </CardBody>
        </Card>

        {/* KB Collections */}
        <Card>
          <CardBody>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              知识库集合 <span className="text-red-500">*</span>
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto border rounded-lg p-4">
              {collections.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">暂无知识库集合</p>
              ) : (
                collections.map((collection) => (
                  <label
                    key={collection.id}
                    className="flex items-center space-x-3 cursor-pointer p-2 hover:bg-gray-50 rounded"
                  >
                    <input
                      type="checkbox"
                      checked={selectedCollections.includes(collection.id)}
                      onChange={() => toggleCollection(collection.id)}
                      className="rounded"
                    />
                    <span className="flex-1 font-medium">{collection.name}</span>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {collection.scope}
                    </span>
                  </label>
                ))
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">
              已选择 {selectedCollections.length} 个集合
            </p>
          </CardBody>
        </Card>

        {/* Analysis Mode */}
        <Card>
          <CardBody>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">分析模式</h3>
            <div className="space-y-3">
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="kb_mode"
                  value="STRICT"
                  checked={formData.kb_mode === 'STRICT'}
                  onChange={(e) => setFormData({ ...formData, kb_mode: e.target.value })}
                  className="text-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-gray-900">严格模式</p>
                  <p className="text-sm text-gray-500">必须基于知识库进行分析，确保合规性</p>
                </div>
              </label>
              <label className="flex items-center space-x-3 cursor-pointer">
                <input
                  type="radio"
                  name="kb_mode"
                  value="RELAXED"
                  checked={formData.kb_mode === 'RELAXED'}
                  onChange={(e) => setFormData({ ...formData, kb_mode: e.target.value })}
                  className="text-accent"
                />
                <div className="flex-1">
                  <p className="font-medium text-gray-900">宽松模式</p>
                  <p className="text-sm text-gray-500">知识库仅供参考，可进行自由分析</p>
                </div>
              </label>
            </div>
          </CardBody>
        </Card>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="border-l-4 border-l-accent">
            <CardBody>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-blue-50 rounded-lg">
                  <Users className="w-6 h-6 text-accent" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">多Agent协作分析</h4>
                  <p className="text-sm text-gray-600">
                    协调Agent、检索Agent、分析Agent协同工作，全面分析合同风险
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card className="border-l-4 border-l-emerald-500">
            <CardBody>
              <div className="flex items-start gap-4">
                <div className="p-3 bg-emerald-50 rounded-lg">
                  <Shield className="w-6 h-6 text-emerald-600" />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-1">幻觉检测机制</h4>
                  <p className="text-sm text-gray-600">
                    实时检测AI生成内容的准确性，确保分析结果可靠可信
                  </p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Submit Buttons */}
        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="secondary"
            onClick={() => navigate('/')}
            disabled={loading}
          >
            取消
          </Button>
          <Button type="submit" disabled={loading} className="min-w-[120px]">
            {loading ? (
              <span className="flex items-center">
                <Zap className="w-4 h-4 mr-2 animate-pulse" />
                创建中...
              </span>
            ) : (
              '开始分析'
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
