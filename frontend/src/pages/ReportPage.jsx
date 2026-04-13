import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Download, Shield, Activity,Cpu, FileJson } from 'lucide-react';
import api from '../services/apiClient';

export default function ReportPage() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [reportRaw, setReportRaw] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get(`/report/${id}`)
            .then(r => setReportRaw(r.data))
            .catch(() => {})
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <div style={{ display: 'grid', placeItems: 'center', minHeight: '60vh', color: '#fff' }}>Loading the Report...</div>;
    if (!reportRaw) return <div style={{color: '#fff', textAlign: 'center'}}>Error loading the report data.</div>;

    // Use merged report if available; fallback intelligently for older reports.
    const isV2 = !!reportRaw.merged_report;
    const merged = isV2 ? reportRaw.merged_report : reportRaw;
    const report1 = isV2 ? reportRaw : {};
    const report2 = isV2 ? (reportRaw.report2 || {}) : {}; 
    
    // Safety destructures
    const finalScore = merged.final_score || report1.score || 0;
    const layerScores = merged.category_details || report1.layer_scores || {};
    const risks = merged.consolidated_risks || merged.risks || report1.risks || [];
    const roadmap = merged.action_roadmap || report1.why_not_80 || [];

    return (
        <motion.div style={{ display: 'flex', flexDirection: 'column', gap: 24, padding: 16 }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <button onClick={() => navigate('/dashboard')} className="btn-jarvis" style={{ padding: '8px 16px', background: 'transparent' }}>
                    <ArrowLeft size={16} /> Back
                </button>
                <h1 style={{ color: '#fff', margin: 0, fontFamily: 'Orbitron' }}>AI Readiness Assessment Report</h1>
                <a href={`http://localhost:8000/api/report/${id}/download/json`} className="chip chip-cyan" style={{ textDecoration: 'none' }}>
                    <Download size={14} /> Export JSON
                </a>
            </div>

            {/* Top Overview Panel */}
            <div className="glass-panel" style={{ padding: '32px', display: 'flex', gap: 32, alignItems: 'center', position: 'relative', overflow: 'hidden' }}>
                <div style={{ width: 140, height: 140, borderRadius: '50%', background: `conic-gradient(#22d3ee ${finalScore}%, #1e293b 0)`, display: 'grid', placeItems: 'center' }}>
                    <div style={{ width: 120, height: 120, borderRadius: '50%', background: '#0d0520', display: 'grid', placeItems: 'center' }}>
                        <h1 style={{ color: '#22d3ee', margin: 0, fontSize: '3rem', fontFamily: 'Orbitron' }}>{finalScore}</h1>
                    </div>
                </div>
                
                <div style={{ flex: 1 }}>
                    <span className="chip chip-violet" style={{ marginBottom: 12 }}>Dual Engine Final Verdict (Z)</span>
                    <p style={{ color: '#cbd5e1', fontSize: '1.05rem', lineHeight: 1.6, marginTop: 12 }}>
                        {merged.executive_summary || report1.executive_summary || "Automated analysis complete."}
                    </p>
                    
                    {report2 && report2.executive_summary && (
                        <div style={{ marginTop: 16, padding: 16, background: 'rgba(168, 85, 247, 0.1)', border: '1px solid rgba(168, 85, 247, 0.3)', borderRadius: 8 }}>
                            <strong style={{ color: '#a855f7', display: 'flex', alignItems: 'center', gap: 8 }}><Cpu size={14}/> LLM Descriptive Analysis:</strong>
                            <p style={{ color: '#e2e8f0', fontSize: '0.95rem', marginTop: 8, lineHeight: 1.5 }}>{report2.executive_summary}</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Combined Dimensions & Categories */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
                {Object.keys(layerScores).map(cat => {
                    const detail = layerScores[cat];
                    const isSemantic = ["semantic_maintainability", "generative_ai_mapping", "data_processing_pipelines", "business_logic_modeling"].includes(cat);
                    const tagType = isSemantic ? "Y (LLM Only Semantic)" : "X (Static Checked)";
                    
                    return (
                        <div key={cat} className="glass-panel" style={{ padding: 20, borderLeft: `4px solid ${isSemantic ? '#a855f7' : '#00e5ff'}` }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div>
                                    <h3 style={{ color: isSemantic ? '#a855f7' : '#00e5ff', textTransform: 'uppercase', margin: 0, fontSize: '1rem' }}>{cat.replace(/_/g, ' ')}</h3>
                                    <span style={{ fontSize: '0.7rem', color: '#64748b', fontWeight: 'bold' }}>{tagType}</span>
                                </div>
                                <span style={{ padding: '4px 10px', background: 'rgba(255,255,255,0.1)', borderRadius: 20, color: '#fff', fontWeight: 'bold' }}>
                                    {detail.score}/100
                                </span>
                            </div>
                            
                            <div style={{ marginTop: 16, background: '#0a0f1d', padding: 12, borderRadius: 8, border: '1px solid #1e293b' }}>
                                <strong style={{ color: '#e2e8f0', fontSize: '0.85rem' }}>AI Merged Conclusion:</strong>
                                <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: 6, lineHeight: 1.5 }}>
                                    {typeof detail === 'object' ? detail.merged_conclusion || detail.report2_view || "No deep analysis provided." : "Category parsed natively."}
                                </p>
                            </div>
                        </div>
                    )
                })}
            </div>

            {/* Action Roadmap */}
            <div className="glass-panel" style={{ padding: 24, marginTop: 12 }}>
                <h3 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Activity size={20} color="#22c55e" /> Actionable AI Roadmap
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {roadmap.map((step, i) => (
                        <div key={i} style={{ display: 'flex', gap: 16, padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: 8, border: '1px solid #1e293b' }}>
                            <div style={{ width: 32, height: 32, borderRadius: 8, background: '#22c55e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', color: '#000', flexShrink: 0 }}>
                                {step.step || i + 1}
                            </div>
                            <div>
                                <p style={{ color: '#f8fafc', fontWeight: 'bold', margin: '0 0 6px 0', fontSize: '1rem' }}>
                                    {typeof step === 'object' ? (step.action || step.title || 'Action Required') : step}
                                </p>
                                {step.impact && <span style={{ fontSize: '0.75rem', color: '#22d3ee', background: 'rgba(34,211,238,0.1)', padding: '2px 8px', borderRadius: 4 }}>Impact: {step.impact}</span>}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
            
            {/* Risks Panel */}
            <div className="glass-panel" style={{ padding: 24 }}>
                <h3 style={{ color: '#fff', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10 }}>
                    <Shield size={20} color="#f43f5e" /> Identified Risks
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                    {risks.map((r, i) => {
                        const isObj = typeof r === 'object';
                        const sev = isObj ? (r.severity || '').toLowerCase() : 'medium';
                        const c = sev === 'critical' ? '#f43f5e' : sev === 'high' ? '#f97316' : sev === 'low' ? '#22c55e' : '#fbbf24';
                        return (
                            <div key={i} style={{ borderLeft: `4px solid ${c}`, background: 'rgba(0,0,0,0.2)', padding: 16, borderRadius: '0 8px 8px 0' }}>
                                <p style={{ color: '#fff', fontWeight: 'bold', margin: 0 }}>{isObj ? (r.issue || r.name || 'Risk') : r}</p>
                                {isObj && r.recommendation && <p style={{ fontSize: '0.8rem', color: '#38bdf8', marginTop: 8, lineHeight: 1.4 }}>{r.recommendation}</p>}
                            </div>
                        )
                    })}
                </div>
            </div>

        </motion.div>
    );
}
