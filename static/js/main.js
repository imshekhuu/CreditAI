/**
 * AI Credit Underwriting System — Frontend Controller
 * ====================================================
 * Handles all UI interactions, API calls, and dynamic rendering
 * for the credit underwriting dashboard.
 */

// ===================================================================
//  STATE
// ===================================================================
let selectedFile = null;
let analysisData = {
    companyInfo: {},
    financialData: {},
    riskResult: {},
    reasoning: {},
    report: {},
};

// ===================================================================
//  INITIALIZATION
// ===================================================================
document.addEventListener('DOMContentLoaded', () => {
    initUploadZone();
    initNavLinks();
});

// ===================================================================
//  UPLOAD ZONE — Drag & Drop + Click
// ===================================================================
function initUploadZone() {
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('pdf_file');
    const uploadInfo = document.getElementById('upload-info');

    // Click to browse
    zone.addEventListener('click', () => fileInput.click());

    // Drag events
    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('dragover');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('dragover');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type === 'application/pdf') {
            handleFileSelect(files[0]);
        } else {
            showToast('Please upload a PDF file.', 'error');
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Remove file button
    document.getElementById('remove-file').addEventListener('click', (e) => {
        e.stopPropagation();
        removeFile();
    });
}

function handleFileSelect(file) {
    selectedFile = file;
    const uploadInfo = document.getElementById('upload-info');
    const uploadZone = document.getElementById('upload-zone');

    document.getElementById('uploaded-filename').textContent = file.name;
    document.getElementById('uploaded-size').textContent = formatFileSize(file.size);

    uploadInfo.style.display = 'flex';
    uploadZone.style.display = 'none';

    showToast(`File "${file.name}" selected.`, 'success');
}

function removeFile() {
    selectedFile = null;
    document.getElementById('pdf_file').value = '';
    document.getElementById('upload-info').style.display = 'none';
    document.getElementById('upload-zone').style.display = 'block';
}

// ===================================================================
//  NAV LINKS
// ===================================================================
function initNavLinks() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = link.getAttribute('data-section') + '-section';
            const section = document.getElementById(sectionId);
            if (section && !section.classList.contains('hidden')) {
                section.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// ===================================================================
//  MAIN PIPELINE — Submit & Analyze
// ===================================================================
async function submitAndAnalyze() {
    // Validate form
    const form = document.getElementById('company-form');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }

    const companyName = document.getElementById('company_name').value;
    const sector = document.getElementById('sector').value;
    const loanAmount = document.getElementById('loan_amount').value;
    const loanPurpose = document.getElementById('loan_purpose').value;
    const companyAge = document.getElementById('company_age').value;

    // Show loading overlay
    showLoading('Uploading & Processing', 'Sending company data and PDF to the server...');
    updateProgress(10);
    updateStep(1, 'done');
    updateStep(2, 'active');

    try {
        // ---- Step 1: Upload ----
        const formData = new FormData();
        formData.append('company_name', companyName);
        formData.append('sector', sector);
        formData.append('loan_amount', loanAmount);
        formData.append('loan_purpose', loanPurpose);
        formData.append('company_age', companyAge);

        if (selectedFile) {
            formData.append('pdf_file', selectedFile);
        }

        const uploadRes = await fetch('/upload', { method: 'POST', body: formData });
        const uploadData = await uploadRes.json();

        if (uploadData.status === 'error') throw new Error(uploadData.message);

        analysisData.companyInfo = uploadData.company_info;
        updateProgress(25);
        updateStep(2, 'done');
        showToast(uploadData.message, 'success');

        // ---- Step 2: Extract ----
        updateStep(3, 'active');
        updateLoadingText('Extracting Financial Data', 'Parsing document for key financial metrics...');
        updateProgress(40);

        const extractRes = await fetch('/extract', { method: 'POST' });
        const extractData = await extractRes.json();

        if (extractData.status === 'error') throw new Error(extractData.message);

        analysisData.financialData = extractData.financial_data;
        updateStep(3, 'done');
        showToast('Financial data extracted successfully.', 'success');

        // ---- Step 3: Predict ----
        updateStep(4, 'active');
        updateLoadingText('Running ML Risk Model', 'Predicting credit risk using Random Forest...');
        updateProgress(60);

        const predictRes = await fetch('/predict', { method: 'POST' });
        const predictData = await predictRes.json();

        if (predictData.status === 'error') throw new Error(predictData.message);

        analysisData.riskResult = predictData.risk_result;
        updateStep(4, 'done');
        showToast(`Risk Level: ${predictData.risk_result.risk_level}`, 'info');

        // ---- Step 4: LLM Reasoning ----
        updateStep(5, 'active');
        updateLoadingText('Generating AI Analysis', 'Building credit reasoning and SWOT analysis...');
        updateProgress(80);

        const reasonRes = await fetch('/reason', { method: 'POST' });
        const reasonData = await reasonRes.json();

        if (reasonData.status === 'error') throw new Error(reasonData.message);

        analysisData.reasoning = reasonData.reasoning;
        updateStep(5, 'done');

        // ---- Step 5: Generate Report ----
        updateStep(6, 'active');
        updateLoadingText('Compiling Report', 'Assembling final underwriting report...');
        updateProgress(95);

        const reportRes = await fetch('/report', { method: 'POST' });
        const reportData = await reportRes.json();

        if (reportData.status === 'error') throw new Error(reportData.message);

        analysisData.report = reportData.report;
        updateStep(6, 'done');
        updateProgress(100);

        // ---- Render All Results ----
        setTimeout(() => {
            hideLoading();
            renderResults();
            showToast('Analysis complete! Review your results below.', 'success');
            updatePipelineStatus('Complete', '#22c55e');
        }, 600);

    } catch (error) {
        hideLoading();
        showToast(`Error: ${error.message}`, 'error');
        updatePipelineStatus('Error', '#ef4444');
        console.error('Pipeline error:', error);
        console.error('Error stack:', error.stack);
    }
}

// ===================================================================
//  RENDER RESULTS
// ===================================================================
function renderResults() {
    // Show results & report sections
    document.getElementById('results-section').classList.remove('hidden');
    document.getElementById('report-section').classList.remove('hidden');

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector('.nav-link[data-section="results"]').classList.add('active');

    // Update section subtitle
    const name = analysisData.companyInfo.company_name || 'Company';
    document.getElementById('analysis-company-name').textContent =
        `Analysis results for ${name} — ${analysisData.companyInfo.sector || 'N/A'} sector`;

    renderFinancialMetrics();
    renderRiskGauge();
    renderProbabilityBars();
    renderFeatureImportance();
    renderAnalysisTabs();
    renderReport();

    // Scroll to results
    document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

// ---- Financial Metrics Grid ----
function renderFinancialMetrics() {
    const grid = document.getElementById('financial-metrics-grid');
    const data = analysisData.financialData;

    const metrics = [
        { key: 'revenue', label: 'Revenue', icon: 'trending_up', theme: 'blue', unit: 'Cr' },
        { key: 'profit', label: 'Net Profit', icon: 'savings', theme: 'green', unit: 'Cr' },
        { key: 'debt', label: 'Total Debt', icon: 'account_balance', theme: 'orange', unit: 'Cr' },
        { key: 'assets', label: 'Total Assets', icon: 'domain', theme: 'purple', unit: 'Cr' },
        { key: 'liabilities', label: 'Liabilities', icon: 'warning', theme: 'red', unit: 'Cr' },
        { key: 'cashflow', label: 'Cash Flow', icon: 'payments', theme: 'teal', unit: 'Cr' },
    ];

    grid.innerHTML = metrics.map(m => `
        <div class="card metric-card" data-theme="${m.theme}">
            <div class="card-header">
                <span class="material-symbols-rounded metric-icon">${m.icon}</span>
                <h3 class="card-title">${m.label}</h3>
            </div>
            <div class="metric-value">₹${formatNumber(data[m.key] || 0)}<span class="metric-unit">${m.unit}</span></div>
            <div class="metric-label">${m.label}</div>
        </div>
    `).join('');
}

// ---- Risk Gauge ----
function renderRiskGauge() {
    const risk = analysisData.riskResult;
    const gaugeFill = document.getElementById('gauge-fill');
    const gaugeValue = document.getElementById('gauge-value');
    const gaugeLabel = document.getElementById('gauge-label');
    const riskDetails = document.getElementById('risk-details');

    // Calculate gauge fill (0 = Low, 1 = Medium, 2 = High)
    // Arc length is ~251 units
    const arcLength = 251;
    let fillPercent = 0;
    let color = '';

    switch (risk.risk_level) {
        case 'Low':
            fillPercent = 0.25;
            color = 'var(--risk-low)';
            break;
        case 'Medium':
            fillPercent = 0.55;
            color = 'var(--risk-medium)';
            break;
        case 'High':
            fillPercent = 0.85;
            color = 'var(--risk-high)';
            break;
    }

    const offset = arcLength * (1 - fillPercent);
    setTimeout(() => {
        gaugeFill.style.strokeDashoffset = offset;
    }, 100);

    gaugeValue.textContent = risk.risk_level;
    gaugeValue.style.color = color;
    gaugeLabel.textContent = `Confidence: ${risk.confidence}%`;

    // Risk details
    riskDetails.innerHTML = `
        <div class="risk-detail-row">
            <span class="risk-detail-label">Risk Level</span>
            <span class="risk-detail-value" style="color:${color}">${risk.risk_level}</span>
        </div>
        <div class="risk-detail-row">
            <span class="risk-detail-label">Confidence</span>
            <span class="risk-detail-value">${risk.confidence}%</span>
        </div>
        <div class="risk-detail-row">
            <span class="risk-detail-label">Risk Probability</span>
            <span class="risk-detail-value">${(risk.risk_probability * 100).toFixed(1)}%</span>
        </div>
        <div class="risk-detail-row">
            <span class="risk-detail-label">Model Accuracy</span>
            <span class="risk-detail-value">${risk.model_accuracy}%</span>
        </div>
    `;
}

// ---- Probability Bars ----
function renderProbabilityBars() {
    const probs = analysisData.riskResult.all_probabilities || {};
    const container = document.getElementById('prob-bars');

    const levels = [
        { key: 'Low', color: 'var(--risk-low)' },
        { key: 'Medium', color: 'var(--risk-medium)' },
        { key: 'High', color: 'var(--risk-high)' },
    ];

    container.innerHTML = levels.map(l => {
        const val = ((probs[l.key] || 0) * 100).toFixed(1);
        return `
            <div class="prob-bar-item">
                <div class="prob-bar-header">
                    <span class="prob-bar-label">${l.key} Risk</span>
                    <span class="prob-bar-value" style="color:${l.color}">${val}%</span>
                </div>
                <div class="prob-bar-track">
                    <div class="prob-bar-fill" style="width:0%;background:${l.color}" data-width="${val}%"></div>
                </div>
            </div>
        `;
    }).join('');

    // Animate bars
    setTimeout(() => {
        container.querySelectorAll('.prob-bar-fill').forEach(bar => {
            bar.style.width = bar.dataset.width;
        });
    }, 200);
}

// ---- Feature Importance ----
function renderFeatureImportance() {
    const fi = analysisData.riskResult.feature_importance || {};
    const container = document.getElementById('feature-importance');

    const maxVal = Math.max(...Object.values(fi), 0.01);

    container.innerHTML = `
        <h4>Feature Importance</h4>
        ${Object.entries(fi).map(([name, value]) => {
            const pct = ((value / maxVal) * 100).toFixed(0);
            return `
                <div class="feature-bar-item">
                    <span class="feature-bar-name">${name}</span>
                    <div class="feature-bar-track">
                        <div class="feature-bar-fill" style="width:0%" data-width="${pct}%"></div>
                    </div>
                    <span class="feature-bar-value">${(value * 100).toFixed(1)}%</span>
                </div>
            `;
        }).join('')}
    `;

    // Animate
    setTimeout(() => {
        container.querySelectorAll('.feature-bar-fill').forEach(bar => {
            bar.style.width = bar.dataset.width;
        });
    }, 400);
}

// ---- Analysis Tabs Content ----
function renderAnalysisTabs() {
    const r = analysisData.reasoning;

    document.getElementById('financial-summary-tab').innerHTML = renderMarkdown(r.financial_summary || 'No data available.');
    document.getElementById('risk-explanation-tab').innerHTML = renderMarkdown(r.risk_explanation || 'No data available.');
    document.getElementById('swot-tab').innerHTML = renderMarkdown(r.swot_analysis || 'No data available.');
    document.getElementById('recommendation-tab').innerHTML = renderMarkdown(r.loan_recommendation || 'No data available.');
}

// ---- Report ----
function renderReport() {
    const report = analysisData.report;

    // Report header
    const meta = report.report_metadata || {};
    document.getElementById('report-id').textContent = `Report #${meta.report_id || '—'}`;
    document.getElementById('report-date').textContent = meta.generated_at
        ? new Date(meta.generated_at).toLocaleString()
        : '—';

    // Decision banner
    const decision = (report.final_recommendation || {}).decision || 'Pending';
    const decisionBanner = document.getElementById('report-decision-banner');
    const decisionIcon = document.getElementById('report-decision-icon');
    const decisionText = document.getElementById('report-decision-text');

    decisionText.textContent = decision;
    decisionBanner.className = 'report-decision-banner';

    if (decision === 'APPROVE') {
        decisionBanner.classList.add('approve');
        decisionIcon.textContent = 'check_circle';
    } else if (decision.includes('CONDITIONAL')) {
        decisionBanner.classList.add('conditional');
        decisionIcon.textContent = 'help';
    } else {
        decisionBanner.classList.add('reject');
        decisionIcon.textContent = 'cancel';
    }

    // Report body cards
    const body = document.getElementById('report-body');
    const co = report.company_overview || {};
    const fs = report.financial_summary || {};
    const ra = report.risk_assessment || {};
    const ai = report.ai_analysis || {};
    const fr = report.final_recommendation || {};
    const healthScore = fs.health_score || 0;
    const healthClass = healthScore >= 70 ? 'good' : healthScore >= 40 ? 'moderate' : 'poor';

    body.innerHTML = `
        <!-- Company Overview -->
        <div class="report-card">
            <div class="report-card-title">
                <span class="material-symbols-rounded">domain</span>
                Company Overview
            </div>
            <div class="report-card-body">
                <strong>Company:</strong> ${co.company_name || 'N/A'}<br>
                <strong>Sector:</strong> ${co.sector || 'N/A'}<br>
                <strong>Loan Amount:</strong> ₹${co.loan_amount || 0} Cr<br>
                <strong>Purpose:</strong> ${co.loan_purpose || 'N/A'}<br>
                <strong>Company Age:</strong> ${co.company_age || 'N/A'} years
            </div>
        </div>

        <!-- Financial Health -->
        <div class="report-card">
            <div class="report-card-title">
                <span class="material-symbols-rounded">monitoring</span>
                Financial Health Score
            </div>
            <div class="report-card-body">
                <div class="health-score-wrap">
                    <div class="health-score-circle ${healthClass}">${healthScore}</div>
                    <div class="health-score-desc">
                        <strong>Overall Financial Health: ${healthScore}/100</strong><br>
                        ${healthScore >= 70 ? 'The company demonstrates strong financial fundamentals with manageable risk levels.' :
                          healthScore >= 40 ? 'The company shows moderate financial health with some areas of concern.' :
                          'The company has significant financial weaknesses that pose substantial risk.'}
                    </div>
                </div>
            </div>
        </div>

        <!-- Key Ratios -->
        <div class="report-card">
            <div class="report-card-title">
                <span class="material-symbols-rounded">calculate</span>
                Key Financial Ratios
            </div>
            <div class="report-card-body">
                <table>
                    <thead>
                        <tr><th>Ratio</th><th>Value</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Profit Margin</td><td>${(fs.ratios || {}).profit_margin || 0}%</td></tr>
                        <tr><td>Debt-to-Asset</td><td>${(fs.ratios || {}).debt_to_asset || 0}%</td></tr>
                        <tr><td>Debt-to-Equity</td><td>${(fs.ratios || {}).debt_to_equity || 0}%</td></tr>
                        <tr><td>Current Ratio</td><td>${(fs.ratios || {}).current_ratio || 0}x</td></tr>
                        <tr><td>Return on Assets</td><td>${(fs.ratios || {}).return_on_assets || 0}%</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Risk Assessment -->
        <div class="report-card">
            <div class="report-card-title">
                <span class="material-symbols-rounded">shield</span>
                ML Risk Assessment
            </div>
            <div class="report-card-body">
                <strong>Risk Level:</strong> <span style="color:${getRiskColor(ra.risk_level)}">${ra.risk_level || 'N/A'}</span><br>
                <strong>Confidence:</strong> ${ra.confidence || 0}%<br>
                <strong>Model Accuracy:</strong> ${ra.model_accuracy || 0}%
            </div>
        </div>

        <!-- AI Analysis -->
        <div class="report-card">
            <div class="report-card-title">
                <span class="material-symbols-rounded">psychology</span>
                AI-Powered Credit Analysis
            </div>
            <div class="report-card-body">
                ${renderMarkdown(ai.financial_summary || '')}
                ${renderMarkdown(ai.risk_explanation || '')}
                ${renderMarkdown(ai.swot_analysis || '')}
            </div>
        </div>

        <!-- Final Recommendation -->
        <div class="report-card">
            <div class="report-card-title">
                <span class="material-symbols-rounded">gavel</span>
                Final Loan Recommendation
            </div>
            <div class="report-card-body">
                ${renderMarkdown(ai.loan_recommendation || '')}
                <br>
                <strong>Executive Summary:</strong><br>
                ${fr.summary || ''}
            </div>
        </div>
    `;
}

// ===================================================================
//  TAB SWITCHING
// ===================================================================
function switchTab(tabBtn) {
    // Deactivate all tabs
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    // Activate selected
    tabBtn.classList.add('active');
    const paneId = tabBtn.getAttribute('data-tab');
    document.getElementById(paneId).classList.add('active');
}

// ===================================================================
//  DOWNLOAD REPORT
// ===================================================================
function downloadReport() {
    const report = analysisData.report;
    if (!report || !report.report_metadata) {
        showToast('No report available to download.', 'error');
        return;
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `credit_report_${report.report_metadata.report_id || 'unknown'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Report downloaded successfully.', 'success');
}

// ===================================================================
//  RESET PIPELINE
// ===================================================================
function resetPipeline() {
    // Reset state
    selectedFile = null;
    analysisData = { companyInfo: {}, financialData: {}, riskResult: {}, reasoning: {}, report: {} };

    // Reset form
    document.getElementById('company-form').reset();
    removeFile();

    // Hide sections
    document.getElementById('results-section').classList.add('hidden');
    document.getElementById('report-section').classList.add('hidden');

    // Reset steps
    for (let i = 1; i <= 6; i++) {
        const step = document.getElementById(`step-${i}`);
        step.classList.remove('active', 'done');
    }
    document.getElementById('step-1').classList.add('active');

    // Reset connectors
    document.querySelectorAll('.step-connector').forEach(c => c.classList.remove('done'));

    // Reset nav
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    document.querySelector('.nav-link[data-section="onboarding"]').classList.add('active');

    updatePipelineStatus('Ready', '#22c55e');

    // Scroll to top
    document.getElementById('hero-section').scrollIntoView({ behavior: 'smooth' });

    showToast('Pipeline reset. Ready for new analysis.', 'info');
}

// ===================================================================
//  UTILITY FUNCTIONS
// ===================================================================

// ---- Loading overlay ----
function showLoading(title, subtitle) {
    document.getElementById('loading-title').textContent = title;
    document.getElementById('loading-subtitle').textContent = subtitle;
    document.getElementById('loading-progress-fill').style.width = '0%';
    document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loading-overlay').classList.add('hidden');
}

function updateLoadingText(title, subtitle) {
    document.getElementById('loading-title').textContent = title;
    document.getElementById('loading-subtitle').textContent = subtitle;
}

function updateProgress(percent) {
    document.getElementById('loading-progress-fill').style.width = `${percent}%`;
}

// ---- Stepper ----
function updateStep(stepNum, state) {
    const step = document.getElementById(`step-${stepNum}`);
    step.classList.remove('active', 'done');
    step.classList.add(state);

    // Update connectors (connector before step N is connector index N-2)
    if (state === 'done') {
        const connectors = document.querySelectorAll('.step-connector');
        if (stepNum - 1 < connectors.length) {
            connectors[stepNum - 1].classList.add('done');
        }
    }
}

// ---- Pipeline status ----
function updatePipelineStatus(text, color) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-text');
    statusDot.style.background = color;
    statusText.textContent = text;
}

// ---- Toast notifications ----
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const iconMap = {
        success: 'check_circle',
        error: 'error',
        info: 'info',
    };

    toast.innerHTML = `
        <span class="material-symbols-rounded">${iconMap[type] || 'info'}</span>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(80px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ---- Number formatting ----
function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return parseFloat(num).toLocaleString('en-IN', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    });
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// ---- Risk color ----
function getRiskColor(level) {
    switch (level) {
        case 'Low': return 'var(--risk-low)';
        case 'Medium': return 'var(--risk-medium)';
        case 'High': return 'var(--risk-high)';
        default: return 'var(--text-secondary)';
    }
}

// ---- Simple Markdown-to-HTML renderer ----
function renderMarkdown(text) {
    if (!text) return '';

    let html = text
        // Headers
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/^## (.+)$/gm, '<h3>$1</h3>')
        // Bold
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        // Italic
        .replace(/\*(.+?)\*/g, '<em>$1</em>')
        // Tables (simple pipe tables)
        .replace(/\|(.+)\|/g, (match) => {
            return match;
        })
        // Line breaks
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        // Bullet points
        .replace(/^- (.+)$/gm, '• $1');

    // Handle simple tables
    if (html.includes('|')) {
        const lines = html.split('<br>');
        let inTable = false;
        let tableHtml = '';
        const newLines = [];

        for (const line of lines) {
            if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
                if (!inTable) {
                    inTable = true;
                    tableHtml = '<table>';
                }
                const cells = line.split('|').filter(c => c.trim() !== '');
                if (cells.every(c => c.trim().match(/^[-:]+$/))) {
                    continue; // Skip separator row
                }
                const isHeader = !tableHtml.includes('<td>');
                const tag = isHeader ? 'th' : 'td';
                tableHtml += '<tr>' + cells.map(c => `<${tag}>${c.trim()}</${tag}>`).join('') + '</tr>';
            } else {
                if (inTable) {
                    tableHtml += '</table>';
                    newLines.push(tableHtml);
                    inTable = false;
                    tableHtml = '';
                }
                newLines.push(line);
            }
        }
        if (inTable) {
            tableHtml += '</table>';
            newLines.push(tableHtml);
        }
        html = newLines.join('<br>');
    }

    return html;
}
