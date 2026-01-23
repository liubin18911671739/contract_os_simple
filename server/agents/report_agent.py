"""
Report Agent - Generate HTML analysis report
"""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.connection import fetch_all_sql
from server.database.models import (Clause, Contract, ContractVersion,
                                     Evidence, KBHitTemp, PrecheckTask, Risk)
from server.services.file_service import FileService
from server.agents.base import BaseAgent

logger = logging.getLogger(__name__)


class ReportAgent(BaseAgent):
    """Generate comprehensive HTML report for task analysis"""

    stage_name = "DONE"

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.file_service = FileService()

    async def execute(self, task_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate HTML report and mark task as complete

        Args:
            task_id: Task ID
            payload: Data from previous stages

        Returns:
            Dict with report path
        """
        logger.info(f"Task {task_id}: Generating HTML report")

        # Gather all data for the report
        report_data = await self._gather_report_data(task_id)

        # Generate HTML content
        html_content = self._generate_html_report(report_data)

        # Save report file
        report_filename = (
            f"report_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        )
        object_key = self.file_service.save_file(
            "reports",
            report_filename,
            html_content.encode("utf-8"),
        )

        logger.info(f"Task {task_id}: Report saved to {object_key}")

        # Cleanup temp KB hits
        await self.session.execute(
            delete(KBHitTemp).where(KBHitTemp.task_id == task_id)
        )
        await self.session.commit()

        await self.update_progress(task_id, 100, status="COMPLETED")

        await self.log_event(task_id, "info", f"Report generated: {object_key}")

        return {
            "status": "completed",
            "report_path": object_key,
            "report_filename": report_filename,
        }

    async def _gather_report_data(self, task_id: str) -> Dict[str, Any]:
        """Gather all data needed for the report"""
        # Get task info
        task_query = select(PrecheckTask).where(PrecheckTask.id == task_id)
        task_result = await self.session.execute(task_query)
        task = task_result.scalar_one_or_none()

        if not task:
            logger.warning(f"Task {task_id} not found")
            return {}

        # Get contract info
        contract_query = (
            select(Contract, ContractVersion)
            .join(ContractVersion, ContractVersion.contract_id == Contract.id)
            .where(ContractVersion.id == task.contract_version_id)
        )
        contract_result = await self.session.execute(contract_query)
        contract_data = contract_result.first()

        # Get clauses with risks
        clauses_with_risks = await fetch_all_sql(
            """
            SELECT
                c.clause_id,
                c.order_no,
                c.text,
                c.type,
                c.page_ref,
                COUNT(r.id) as risk_count,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'HIGH') as high_risk_count,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'MEDIUM') as medium_risk_count,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'LOW') as low_risk_count,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'INFO') as info_risk_count
            FROM clauses c
            LEFT JOIN risks r ON r.clause_id = c.clause_id
            WHERE c.task_id = ?
            GROUP BY c.clause_id
            ORDER BY c.order_no
            """,
            (task_id,),
        )

        # Get all risks with details
        all_risks = await fetch_all_sql(
            """
            SELECT
                r.id,
                r.risk_level,
                r.risk_type,
                r.confidence,
                r.summary,
                r.status,
                r.clause_id,
                c.order_no,
                c.text as clause_text,
                COUNT(DISTINCT ev.id) as evidence_count,
                COUNT(DISTINCT kb.id) as kb_citation_count
            FROM risks r
            JOIN clauses c ON c.clause_id = r.clause_id
            LEFT JOIN evidences ev ON ev.risk_id = r.id
            LEFT JOIN kb_citations kb ON kb.risk_id = r.id
            WHERE r.task_id = ?
            GROUP BY r.id, c.order_no
            ORDER BY c.order_no, r.risk_level DESC
            """,
            (task_id,),
        )

        # Get risk statistics
        stats = await fetch_one_sql(
            """
            SELECT
                COUNT(DISTINCT c.id) as total_clauses,
                COUNT(r.id) as total_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'HIGH') as high_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'MEDIUM') as medium_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'LOW') as low_risks,
                COUNT(r.id) FILTER (WHERE r.risk_level = 'INFO') as info_risks,
                COUNT(DISTINCT r.risk_type) as risk_types_count
            FROM clauses c
            LEFT JOIN risks r ON r.task_id = ? AND r.clause_id = c.clause_id
            WHERE c.task_id = ?
            """,
            (task_id, task_id),
        )

        # Get rule hits
        rule_hits = await fetch_all_sql(
            """
            SELECT
                rh.rule_id,
                rh.rule_name,
                rh.matched_text,
                COUNT(r.id) as linked_risks
            FROM rule_hits rh
            LEFT JOIN risks r ON r.risk_id = rh.id
            JOIN clauses c ON c.clause_id = rh.clause_id
            WHERE c.task_id = ?
            GROUP BY rh.id
            ORDER BY linked_risks DESC
            """,
            (task_id,),
        )

        return {
            "task": {
                "id": task.id,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "kb_mode": task.kb_mode,
            },
            "contract": (
                {
                    "id": contract_data[0].id if contract_data else None,
                    "title": contract_data[0].title if contract_data else "Unknown",
                    "version": contract_data[1].version_number if contract_data else 1,
                }
                if contract_data
                else None
            ),
            "clauses": clauses_with_risks,
            "risks": all_risks,
            "stats": stats or {},
            "rule_hits": rule_hits,
        }

    def _generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML report content"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>合同风险分析报告 - {data.get('contract', {}).get('title', 'N/A')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
                'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
        }}

        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header .meta {{
            opacity: 0.9;
            font-size: 14px;
        }}

        .section {{
            padding: 30px;
            border-bottom: 1px solid #eee;
        }}

        .section:last-child {{
            border-bottom: none;
        }}

        .section-title {{
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            color: #2d3748;
            display: flex;
            align-items: center;
        }}

        .section-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: #667eea;
            margin-right: 10px;
            border-radius: 2px;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .stat-card {{
            background: #f7fafc;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}

        .stat-value {{
            font-size: 32px;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 14px;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .risk-high {{ color: #f56565; }}
        .risk-medium {{ color: #ed8936; }}
        .risk-low {{ color: #48bb78; }}
        .risk-info {{ color: #4299e1; }}

        .risk-list {{
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .risk-item {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            background: #fff;
            transition: all 0.2s;
        }}

        .risk-item:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }}

        .risk-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .risk-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-high {{
            background: #fed7d7;
            color: #c53030;
        }}

        .badge-medium {{
            background: #feebc8;
            color: #c05621;
        }}

        .badge-low {{
            background: #c6f6d5;
            color: #2f855a;
        }}

        .badge-info {{
            background: #bee3f8;
            color: #2b6cb0;
        }}

        .risk-type {{
            font-size: 14px;
            color: #718096;
            font-weight: 500;
        }}

        .risk-summary {{
            font-size: 15px;
            color: #2d3748;
            margin-bottom: 10px;
            line-height: 1.6;
        }}

        .risk-meta {{
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #718096;
        }}

        .clause-item {{
            background: #f7fafc;
            border-left: 3px solid #cbd5e0;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 4px;
        }}

        .clause-text {{
            font-size: 14px;
            color: #4a5568;
            font-style: italic;
            margin-bottom: 8px;
        }}

        .rule-hit {{
            background: #fffaf0;
            border-left: 3px solid #ed8936;
            padding: 12px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 14px;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #718096;
            font-size: 14px;
            background: #f7fafc;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #a0aec0;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📋 合同风险分析报告</h1>
            <div class="meta">
                <p><strong>合同名称：</strong>{data.get('contract', {}).get('title', 'N/A')}</p>
                <p><strong>版本：</strong>v{data.get('contract', {}).get('version', 1)}</p>
                <p><strong>任务ID：</strong>{data.get('task', {}).get('id', 'N/A')}</p>
                <p><strong>生成时间：</strong>{data.get('task', {}).get('created_at', 'N/A')[:19]}</p>
            </div>
        </div>

        <!-- Statistics Section -->
        <div class="section">
            <h2 class="section-title">📊 分析统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">{data.get('stats', {}).get('total_clauses', 0)}</div>
                    <div class="stat-label">条款总数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value risk-high">{data.get('stats', {}).get('high_risks', 0)}</div>
                    <div class="stat-label">高风险</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value risk-medium">{data.get('stats', {}).get('medium_risks', 0)}</div>
                    <div class="stat-label">中风险</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value risk-low">{data.get('stats', {}).get('low_risks', 0)}</div>
                    <div class="stat-label">低风险</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value risk-info">{data.get('stats', {}).get('info_risks', 0)}</div>
                    <div class="stat-label">信息</div>
                </div>
            </div>
        </div>

        <!-- Risks Section -->
        <div class="section">
            <h2 class="section-title">⚠️ 风险详情 ({len(data.get('risks', []))} 项)</h2>
            {self._generate_risks_html(data.get('risks', []))}
        </div>

        <!-- Rule Hits Section -->
        <div class="section">
            <h2 class="section-title">🔍 规则匹配 ({len(data.get('rule_hits', []))} 项)</h2>
            {self._generate_rule_hits_html(data.get('rule_hits', []))}
        </div>

        <!-- Footer -->
        <div class="footer">
            <p>本报告由 Contract OS Simple 自动生成</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _generate_risks_html(self, risks: list) -> str:
        """Generate HTML for risks list"""
        if not risks:
            return '<div class="empty-state">暂无风险项</div>'

        risk_items = []
        for risk in risks:
            risk_level = risk.get("risk_level", "INFO")
            risk_class = f"badge-{risk_level.lower()}"

            risk_items.append(f"""
            <div class="risk-item">
                <div class="risk-header">
                    <div>
                        <span class="risk-badge {risk_class}">{risk_level}</span>
                        <span class="risk-type">{risk.get('risk_type', 'GENERAL')}</span>
                    </div>
                    <div class="risk-meta">
                        <span>置信度: {risk.get('confidence', 0):.1%}</span>
                        <span>证据: {risk.get('evidence_count', 0)}</span>
                        <span>KB引用: {risk.get('kb_citation_count', 0)}</span>
                    </div>
                </div>
                <div class="risk-summary">{risk.get('summary', 'No summary')}</div>
                <div class="clause-item">
                    <div class="clause-text">"{risk.get('clause_text', '')[:200]}..."</div>
                </div>
            </div>
            """)

        return f'<div class="risk-list">{"".join(risk_items)}</div>'

    def _generate_rule_hits_html(self, rule_hits: list) -> str:
        """Generate HTML for rule hits"""
        if not rule_hits:
            return '<div class="empty-state">暂无规则匹配</div>'

        rule_items = []
        for hit in rule_hits:
            rule_items.append(f"""
            <div class="rule-hit">
                <strong>{hit.get('rule_name', 'Unknown Rule')}</strong>
                <p style="margin-top: 8px; color: #4a5568;">{hit.get('matched_text', '')[:200]}</p>
                {f'<p style="margin-top: 5px; font-size: 12px; color: #718096;">关联风险: {hit.get("linked_risks", 0)} 项</p>' if hit.get('linked_risks', 0) > 0 else ''}
            </div>
            """)

        return f'<div class="clauses-list">{"".join(rule_items)}</div>'
