/**
 * ETL SQL Generator - Frontend Application
 * 자연어 → SQL 변환 웹 애플리케이션
 */

// DOM Elements
const elements = {
    // Real DB connection
    quickConnectSelect: document.getElementById('quickConnectSelect'),
    dbTypeSelect: document.getElementById('dbTypeSelect'),
    dbHost: document.getElementById('dbHost'),
    dbPort: document.getElementById('dbPort'),
    dbName: document.getElementById('dbName'),
    dbUser: document.getElementById('dbUser'),
    dbPassword: document.getElementById('dbPassword'),
    connectionStatus: document.getElementById('connectionStatus'),
    connectBtn: document.getElementById('connectBtn'),
    disconnectBtn: document.getElementById('disconnectBtn'),
    extractMetadataGroup: document.getElementById('extractMetadataGroup'),
    extractMetadataBtn: document.getElementById('extractMetadataBtn'),
    
    // Query
    includeEtlCheckbox: document.getElementById('includeEtl'),
    queryInput: document.getElementById('queryInput'),
    generateBtn: document.getElementById('generateBtn'),
    llmSelect: document.getElementById('llmSelect'),
    executeBtn: document.getElementById('executeBtn'),
    copyBtn: document.getElementById('copyBtn'),
    loading: document.getElementById('loading'),
    resultContainer: document.getElementById('resultContainer'),
    emptyState: document.getElementById('emptyState'),
    examplesSection: document.getElementById('examplesSection'),
    exampleList: document.getElementById('exampleList'),
    refreshSamplesBtn: document.getElementById('refreshSamplesBtn'),
    
    // Result sections
    intentSection: document.getElementById('intentSection'),
    intentSummary: document.getElementById('intentSummary'),
    sqlSection: document.getElementById('sqlSection'),
    sqlCodeEditor: document.getElementById('sqlCodeEditor'), // Changed from sqlCode
    blockedSection: document.getElementById('blockedSection'),
    blockReason: document.getElementById('blockReason'),
    assumptionsSection: document.getElementById('assumptionsSection'),
    assumptionsList: document.getElementById('assumptionsList'),
    safetySection: document.getElementById('safetySection'),
    safetyList: document.getElementById('safetyList'),
    tablesSection: document.getElementById('tablesSection'),
    tablesList: document.getElementById('tablesList'),
    etlSection: document.getElementById('etlSection'),
    etlPipeline: document.getElementById('etlPipeline'),
    
    // New Execution Panel
    executionPanel: document.getElementById('executionPanel'),
    queryResultContainer: document.getElementById('queryResultContainer'),
    runQueryBtn: document.getElementById('runQueryBtn'),
    closeExecutionPanel: document.getElementById('closeExecutionPanel'),
    
    // Metadata Modal
    viewMetadataBtn: document.getElementById('viewMetadataBtn'),
    metadataModal: document.getElementById('metadataModal'),
    closeMetadataModal: document.getElementById('closeMetadataModal'),
    metadataJsonViewer: document.getElementById('metadataJsonViewer')
};

// State
let currentDbType = 'postgresql';

let currentSource = 'realdb';
let isConnected = false;
let extractedMetadata = null;
let currentResult = null;

// Saved Connections Configuration
const savedConnections = {
    'alliza_dev': {
        name: 'Alliza 개발 DB',
        type: 'postgresql',
        host: '3.37.160.231',
        port: 8642,
        database: 'alliza_dev',
        user: 'alliza',
        password: 'zeppelin'
    },
    'lawpilot_dev': {
        name: 'Lawpilot 개발 DB',
        type: 'postgresql', // Assuming Postgres based on context, 7677 can be anything but usually users stick to one DB type in these demos
        host: '3.37.160.231',
        port: 7677,
        database: 'lawplatform',
        user: 'lawplatform',
        password: 'core001*'
    }
};

// Example queries per DB type
// No static examples needed
const exampleQueries = {};

// Initialize
function init() {
    setupEventListeners();
    updatePortDefault();
    populateSavedConnections();
}

// Populate Saved Connections
function populateSavedConnections() {
    if (!elements.quickConnectSelect) return;
    
    Object.keys(savedConnections).forEach(key => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = savedConnections[key].name;
        elements.quickConnectSelect.appendChild(option);
    });
}

// Event Listeners
function setupEventListeners() {
    // Quick Connect Selection
    if (elements.quickConnectSelect) {
        elements.quickConnectSelect.addEventListener('change', (e) => {
            const key = e.target.value;
            if (key && savedConnections[key]) {
                const config = savedConnections[key];
                elements.dbTypeSelect.value = config.type;
                elements.dbHost.value = config.host;
                elements.dbPort.value = config.port;
                elements.dbName.value = config.database;
                elements.dbUser.value = config.user;
                elements.dbPassword.value = config.password;
                
                // Trigger change to update port defaults if needed (though we just set it)
                // elements.dbTypeSelect.dispatchEvent(new Event('change')); 
            }
        });
    }

    // DB Type Selection (real DB)
    elements.dbTypeSelect.addEventListener('change', () => {
        updatePortDefault();
    });
    
    // Database Connection
    elements.connectBtn.addEventListener('click', connectDatabase);
    elements.disconnectBtn.addEventListener('click', disconnectDatabase);
    elements.extractMetadataBtn.addEventListener('click', extractMetadata);
    
    // Refresh Samples Button
    if (elements.refreshSamplesBtn) {
        elements.refreshSamplesBtn.addEventListener('click', () => {
            if (extractedMetadata) {
                const icon = elements.refreshSamplesBtn.querySelector('svg');
                icon.classList.add('rotating-icon');
                elements.refreshSamplesBtn.disabled = true;
                
                generateSamples(extractedMetadata).finally(() => {
                    icon.classList.remove('rotating-icon');
                    elements.refreshSamplesBtn.disabled = false;
                });
            }
        });
    }
    
    // Generate Button
    elements.generateBtn.addEventListener('click', generateSQL);
    
    // Execute Button (Sidebar)
    elements.executeBtn.addEventListener('click', executeQuery);
    
    // Run Query Button (SQL Card)
    if (elements.runQueryBtn) {
        elements.runQueryBtn.addEventListener('click', executeQuery);
    }

    // Close Execution Panel
    if (elements.closeExecutionPanel) {
        elements.closeExecutionPanel.addEventListener('click', () => {
            elements.executionPanel.classList.add('hidden');
        });
    }
    
    // Copy Button
    elements.copyBtn.addEventListener('click', copySQL);

    // Metadata Modal Events
    if (elements.viewMetadataBtn) {
        elements.viewMetadataBtn.addEventListener('click', () => {
            if (extractedMetadata) {
                elements.metadataJsonViewer.textContent = JSON.stringify(extractedMetadata, null, 2);
                elements.metadataModal.classList.remove('hidden');
            } else {
                alert('추출된 메타데이터가 없습니다. 먼저 Extract Schema를 실행해주세요.');
            }
        });
    }

    if (elements.closeMetadataModal) {
        elements.closeMetadataModal.addEventListener('click', () => {
            elements.metadataModal.classList.add('hidden');
        });
    }

    // Close modal on outside click
    window.addEventListener('click', (e) => {
        if (e.target === elements.metadataModal) {
            elements.metadataModal.classList.add('hidden');
        }
    });
    
    // Enter key to generate
    elements.queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            generateSQL();
        }
    });

    // Execute with Cmd+Enter in Editor
    if (elements.sqlCodeEditor) {
        elements.sqlCodeEditor.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                executeQuery();
            }
        });
    }

    // Collapsible sections
    document.querySelectorAll('.section-header').forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.sidebar-section');
            section.classList.toggle('collapsed');
        });
    });
}

// Update default port based on DB type
function updatePortDefault() {
    const dbType = elements.dbTypeSelect.value;
    elements.dbPort.value = dbType === 'postgresql' ? '5432' : '3306';
}

// Render example queries
function renderExamples() {
    const examples = exampleQueries[currentDbType] || [];
    elements.exampleList.innerHTML = examples.map(q => 
        `<div class="example-item" onclick="setQuery('${q}')">${q}</div>`
    ).join('');
}

// Set query from example
window.setQuery = function(query) {
    elements.queryInput.value = query;
    elements.queryInput.focus();
};

// Load sample metadata into editor
async function loadSampleMetadata() {
    try {
        const response = await fetch(`/api/sample-metadata/${currentDbType}`);
        if (response.ok) {
            const metadata = await response.json();
            elements.metadataEditor.value = JSON.stringify(metadata, null, 2);
        }
    } catch (error) {
        console.error('Failed to load sample metadata:', error);
    }
}

// ===== Database Connection =====

async function connectDatabase() {
    const dbType = elements.dbTypeSelect.value;
    const host = elements.dbHost.value.trim();
    const port = parseInt(elements.dbPort.value) || (dbType === 'postgresql' ? 5432 : 3306);
    const database = elements.dbName.value.trim();
    const user = elements.dbUser.value.trim();
    const password = elements.dbPassword.value;
    
    if (!host || !database || !user) {
        alert('호스트, 데이터베이스, 사용자 정보를 입력해주세요.');
        return;
    }
    
    updateConnectionStatus('connecting', '연결 중...');
    
    try {
        const response = await fetch('/api/db/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_type: dbType, host, port, database, user, password })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '연결 실패');
        }
        
        const result = await response.json();
        isConnected = true;
        updateConnectionStatus('connected', `✓ ${database}에 연결됨`);
        
        elements.connectBtn.classList.add('hidden');
        elements.disconnectBtn.classList.remove('hidden');
        elements.extractMetadataGroup.classList.remove('hidden');
        elements.executeBtn.classList.remove('hidden');
        
        // Auto-collapse after connection to save space
        const dbSection = document.getElementById('dbSection');
        if (dbSection) dbSection.classList.add('collapsed');
        
    } catch (error) {
        console.error('Connection error:', error);
        updateConnectionStatus('disconnected', `연결 실패: ${error.message}`);
        isConnected = false;
    }
}

async function disconnectDatabase() {
    try {
        await fetch('/api/db/disconnect', { method: 'POST' });
    } catch (error) {
        console.error('Disconnect error:', error);
    }
    
    isConnected = false;
    extractedMetadata = null;
    updateConnectionStatus('disconnected', '연결 안됨');
    
    elements.connectBtn.classList.remove('hidden');
    elements.disconnectBtn.classList.add('hidden');
    elements.extractMetadataGroup.classList.add('hidden');
    elements.executeBtn.classList.add('hidden');
}

async function extractMetadata() {
    if (!isConnected) {
        alert('먼저 데이터베이스에 연결해주세요.');
        return;
    }
    
    elements.extractMetadataBtn.textContent = '📥 추출 중...';
    elements.extractMetadataBtn.disabled = true;
    
    try {
        const response = await fetch('/api/db/metadata');
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '메타데이터 추출 실패');
        }
        
        const result = await response.json();
        extractedMetadata = result.metadata;
        
        alert(`✓ ${result.table_count}개의 테이블 메타데이터를 추출했습니다.\n메타데이터를 기반으로 추천 쿼리를 자동 생성합니다.`);
        
        // Generate Samples automatically after metadata extraction
        await generateSamples(extractedMetadata);
        
    } catch (error) {
        console.error('Metadata extraction error:', error);
        alert(`메타데이터 추출 실패: ${error.message}`);
    } finally {
        elements.extractMetadataBtn.textContent = '📥 Extract Schema';
        elements.extractMetadataBtn.disabled = false;
    }
}

async function generateSamples(metadata) {
    try {
        const selectedModel = elements.llmSelect ? elements.llmSelect.value : 'gpt-5-mini-2025-08-07';
        const provider = selectedModel.startsWith('gpt') ? 'openai' : 'google';

        const response = await fetch('/api/generate-samples', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                metadata,
                provider: provider,
                model_name: selectedModel
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            renderSampleQueries(data.samples);
        }
    } catch (e) {
        console.error("Failed to generate samples", e);
    }
}

function renderSampleQueries(samples) {
    if (!samples || samples.length === 0) return;
    
    elements.examplesSection.classList.remove('hidden');
    elements.exampleList.innerHTML = samples.map(q => 
        `<div class="example-item" onclick="setQuery('${escapeHtml(q)}')">${escapeHtml(q)}</div>`
    ).join('');
}

function updateConnectionStatus(status, text) {
    const dot = elements.connectionStatus.querySelector('.status-dot');
    const textEl = elements.connectionStatus.querySelector('.status-text');
    
    dot.className = `status-dot ${status}`;
    textEl.textContent = text;
}

// ===== SQL Generation =====

async function generateSQL() {
    const query = elements.queryInput.value.trim();
    if (!query) {
        alert('자연어 요청을 입력해주세요.');
        return;
    }
    
    showLoading();
    
    try {
        const selectedModel = elements.llmSelect ? elements.llmSelect.value : 'gpt-5-mini-2025-08-07';
        const provider = selectedModel.startsWith('gpt') ? 'openai' : 'google';

        const requestBody = {
            request: query,
            db_type: currentDbType,
            include_etl: elements.includeEtlCheckbox.checked,
            provider: provider,
            model_name: selectedModel
        };
        
        // Use appropriate metadata source
        if (currentSource === 'realdb' && extractedMetadata) {
            requestBody.database_info = extractedMetadata;
        } else if (elements.customMetadataCheckbox.checked && elements.metadataEditor.value.trim()) {
            try {
                requestBody.database_info = JSON.parse(elements.metadataEditor.value);
            } catch (e) {
                alert('메타데이터 JSON 형식이 올바르지 않습니다.');
                hideLoading();
                return;
            }
        }
        
        const response = await fetch('/api/generate-sql', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'SQL 생성 실패');
        }
        
        const result = await response.json();
        currentResult = result;
        renderResult(result);
        
    } catch (error) {
        console.error('Error generating SQL:', error);
        renderError(error.message);
    } finally {
        hideLoading();
    }
}

// ===== Query Execution =====

async function executeQuery() {
    if (!isConnected) {
        alert('먼저 데이터베이스에 연결해주세요.');
        return;
    }
    
    // Get SQL from editor
    const sqlToExecute = elements.sqlCodeEditor.value.trim();
    if (!sqlToExecute) {
        alert('실행할 SQL이 없습니다.');
        return;
    }
    
    // Show panel if hidden
    elements.executionPanel.classList.remove('hidden');
    elements.queryResultContainer.innerHTML = '<div class="spinner" style="margin: 2rem auto;"></div><p style="text-align:center">Executing...</p>';

    // showLoading(); // Don't hide the main view, just show loading in the right panel/result area
    
    try {
        const response = await fetch('/api/db/execute', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql: sqlToExecute, limit: 50 })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '쿼리 실행 실패');
        }
        
        const result = await response.json();
        renderQueryResult(result);
        
    } catch (error) {
        console.error('Query execution error:', error);
        // alert(`쿼리 실행 실패: ${error.message}`);
        renderQueryError(error.message);
    } finally {
        // hideLoading();
    }
}

function renderQueryError(message) {
    let html = `
        <div class="result-card warning-card">
            <div class="card-header">
                <h3>⚠️ Execution Error</h3>
            </div>
            <div class="card-body">
                <p>${escapeHtml(message)}</p>
            </div>
        </div>
    `;
    elements.queryResultContainer.innerHTML = html;
}

function renderQueryResult(result) {
    let html = '';
    
    if (result.columns && result.data) {
        html += `<div style="margin-bottom: 1rem; font-weight: 600;">${result.row_count} rows returned</div>`;
        html += '<div class="result-table-container"><table class="result-table">';
        html += '<thead><tr>';
        result.columns.forEach(col => {
            html += `<th>${escapeHtml(col)}</th>`;
        });
        html += '</tr></thead><tbody>';
        
        result.data.forEach(row => {
            html += '<tr>';
            result.columns.forEach(col => {
                const val = row[col];
                html += `<td>${val !== null ? escapeHtml(String(val)) : '<span style="opacity:0.5">NULL</span>'}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
    } else {
        html += '<p>No data returned.</p>';
    }
    
    elements.queryResultContainer.innerHTML = html;
}

// ===== Result Rendering =====

function renderResult(result) {
    elements.emptyState.classList.add('hidden');
    elements.resultContainer.classList.remove('hidden');
    
    // Hide query result if exists
    const queryResultSection = document.getElementById('queryResultSection');
    if (queryResultSection) {
        queryResultSection.classList.add('hidden');
    }
    
    // Intent Summary
    elements.intentSummary.textContent = result.intent_summary || '-';
    
    // SQL or Blocked
    if (result.is_blocked) {
        elements.sqlSection.classList.add('hidden');
        elements.blockedSection.classList.remove('hidden');
        elements.blockReason.textContent = result.block_reason || '이 요청은 처리할 수 없습니다.';
        elements.copyBtn.disabled = true;
        elements.executeBtn.disabled = true;
    } else {
        elements.blockedSection.classList.add('hidden');
        elements.sqlSection.classList.remove('hidden');
        elements.sqlCodeEditor.value = result.sql || ''; // Use value for textarea
        elements.copyBtn.disabled = !result.sql;
        elements.executeBtn.disabled = !result.sql;
        if (elements.runQueryBtn) elements.runQueryBtn.disabled = !result.sql;
    }
    
    // Assumptions
    if (result.assumptions && result.assumptions.length > 0) {
        elements.assumptionsSection.classList.remove('hidden');
        elements.assumptionsList.innerHTML = result.assumptions
            .map(a => `<li>${escapeHtml(a)}</li>`)
            .join('');
    } else {
        elements.assumptionsSection.classList.add('hidden');
    }
    
    // Safety Notes
    if (result.safety_notes && result.safety_notes.length > 0) {
        elements.safetySection.classList.remove('hidden');
        elements.safetyList.innerHTML = result.safety_notes
            .map(n => `<li>${escapeHtml(n)}</li>`)
            .join('');
    } else {
        elements.safetySection.classList.add('hidden');
    }
    
    // Tables Used
    if (result.tables_used && result.tables_used.length > 0) {
        elements.tablesSection.classList.remove('hidden');
        elements.tablesList.innerHTML = result.tables_used
            .map(t => `<span class="table-tag">${escapeHtml(t)}</span>`)
            .join('');
    } else {
        elements.tablesSection.classList.add('hidden');
    }
    
    // ETL Pipeline
    if (result.etl_pipeline) {
        elements.etlSection.classList.remove('hidden');
        renderETLPipeline(result.etl_pipeline);
    } else {
        elements.etlSection.classList.add('hidden');
    }
}

// Render ETL Pipeline
function renderETLPipeline(pipeline) {
    let html = '';
    
    // Extract
    if (pipeline.extract) {
        html += `
            <div class="etl-stage">
                <h4>📥 Extract</h4>
                <p><strong>소스 테이블:</strong> ${(pipeline.extract.source_tables || []).join(', ') || '-'}</p>
                <p><strong>조건:</strong> ${escapeHtml(pipeline.extract.conditions) || '-'}</p>
            </div>
        `;
    }
    
    // Transform
    if (pipeline.transform && pipeline.transform.length > 0) {
        html += `
            <div class="etl-stage">
                <h4>⚙️ Transform</h4>
                <ul>
                    ${pipeline.transform.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
                </ul>
            </div>
        `;
    }
    
    // Load
    if (pipeline.load) {
        html += `
            <div class="etl-stage">
                <h4>📤 Load</h4>
                <p><strong>대상 테이블:</strong> ${escapeHtml(pipeline.load.target_table) || '-'}</p>
                <p><strong>쓰기 모드:</strong> ${escapeHtml(pipeline.load.write_mode) || '-'}</p>
            </div>
        `;
    }
    
    elements.etlPipeline.innerHTML = html;
}

// Render error
function renderError(message) {
    elements.emptyState.classList.add('hidden');
    elements.resultContainer.classList.remove('hidden');
    
    elements.sqlSection.classList.add('hidden');
    elements.blockedSection.classList.remove('hidden');
    elements.blockReason.textContent = message;
    elements.copyBtn.disabled = true;
    
    elements.assumptionsSection.classList.add('hidden');
    elements.safetySection.classList.add('hidden');
    elements.tablesSection.classList.add('hidden');
    elements.etlSection.classList.add('hidden');
}

// Copy SQL to clipboard
async function copySQL() {
    const sqlToCopy = elements.sqlCodeEditor ? elements.sqlCodeEditor.value : (currentResult ? currentResult.sql : '');
    if (!sqlToCopy) return;
    
    try {
        await navigator.clipboard.writeText(sqlToCopy);
        
        const originalText = elements.copyBtn.innerHTML;
        elements.copyBtn.innerHTML = '✓ 복사됨';
        elements.copyBtn.style.background = 'var(--accent-green)';
        elements.copyBtn.style.borderColor = 'var(--accent-green)';
        elements.copyBtn.style.color = 'white';
        
        setTimeout(() => {
            elements.copyBtn.innerHTML = originalText;
            elements.copyBtn.style.background = '';
            elements.copyBtn.style.borderColor = '';
            elements.copyBtn.style.color = '';
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
    }
}

// UI State helpers
function showLoading() {
    elements.loading.classList.remove('hidden');
    elements.resultContainer.classList.add('hidden');
    elements.emptyState.classList.add('hidden');
    elements.generateBtn.disabled = true;
}

function hideLoading() {
    elements.loading.classList.add('hidden');
    elements.generateBtn.disabled = false;
}

function showEmptyState() {
    elements.emptyState.classList.remove('hidden');
    elements.resultContainer.classList.add('hidden');
}

// Escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
