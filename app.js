// NL2SQL Studio - Main Application Logic

class NL2SQLApp {
    constructor() {
        this.db = null;
        this.databases = {};
        this.currentDbName = null;
        this.sqlEditor = null;
        this.settings = this.loadSettings();
        this.queryHistory = [];
        this.init();
    }

    async init() {
        // Initialize SQL.js
        this.SQL = await initSqlJs({
            locateFile: file => `https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/${file}`
        });

        // Initialize CodeMirror
        this.initCodeMirror();

        // Setup event listeners
        this.setupEventListeners();

        // Load saved databases from localStorage (if any)
        this.loadSavedDatabases();

        // Apply saved theme
        this.applyTheme();
    }

    initCodeMirror() {
        const textarea = document.getElementById('sqlEditor');
        this.sqlEditor = CodeMirror.fromTextArea(textarea, {
            mode: 'text/x-sql',
            theme: 'monokai',
            lineNumbers: true,
            lineWrapping: true,
            extraKeys: {
                "Ctrl-Space": "autocomplete",
                "Ctrl-Enter": () => this.runSQL()
            }
        });
    }

    setupEventListeners() {
        // Theme toggle
        document.getElementById('themeToggle').addEventListener('click', () => this.toggleTheme());

        // Settings
        document.getElementById('settingsBtn').addEventListener('click', () => this.openSettingsModal());
        document.getElementById('settingsProvider').addEventListener('change', (e) => this.toggleProviderSettings(e.target.value));

        // Database operations
        document.getElementById('uploadDbBtn').addEventListener('click', () => this.openUploadModal());
        document.getElementById('createDbBtn').addEventListener('click', () => this.createNewDatabase());
        document.getElementById('downloadDbBtn').addEventListener('click', () => this.downloadDatabase());
        document.getElementById('currentDb').addEventListener('change', (e) => this.switchDatabase(e.target.value));

        // File upload
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        dropZone.addEventListener('click', () => fileInput.click());
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            this.handleFiles(e.dataTransfer.files);
        });
        fileInput.addEventListener('change', (e) => this.handleFiles(e.target.files));

        // Tabs
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });

        // Natural Language Query
        document.getElementById('nlQueryBtn').addEventListener('click', () => this.executeNLQuery());
        document.getElementById('nlInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.executeNLQuery();
        });

        // SQL Editor
        document.getElementById('runSqlBtn').addEventListener('click', () => this.runSQL());
        document.getElementById('clearSqlBtn').addEventListener('click', () => this.sqlEditor.setValue(''));
        document.getElementById('formatSqlBtn').addEventListener('click', () => this.formatSQL());

        // Query Templates
        document.querySelectorAll('.template-item').forEach(template => {
            template.addEventListener('click', () => {
                const sql = template.dataset.template;
                this.sqlEditor.setValue(sql);
                this.switchTab('sql-editor');
            });
        });

        // LLM Provider selector
        document.getElementById('llmProvider').addEventListener('change', (e) => {
            this.settings.provider = e.target.value;
            this.saveSettings();
        });
    }

    // Theme Management
    toggleTheme() {
        const currentTheme = document.body.dataset.theme || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.body.dataset.theme = newTheme;

        // Update theme icon using Feather icons
        if (window.updateThemeIcon) {
            window.updateThemeIcon(newTheme);
        }

        localStorage.setItem('theme', newTheme);

        // Update CodeMirror theme
        this.sqlEditor.setOption('theme', newTheme === 'dark' ? 'monokai' : 'default');
    }

    applyTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.body.dataset.theme = savedTheme;

        // Update theme icon using Feather icons
        if (window.updateThemeIcon) {
            window.updateThemeIcon(savedTheme);
        }
    }

    // Tab Management
    switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === tabName);
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.toggle('active', content.id === tabName);
        });

        // Generate ER diagram when switching to that tab
        if (tabName === 'er-diagram' && this.db) {
            this.generateERDiagram();
        }
    }

    // Settings Management
    loadSettings() {
        const saved = localStorage.getItem('nl2sql_settings');
        return saved ? JSON.parse(saved) : {
            provider: 'openai',
            apiKey: '',
            model: {
                openai: 'gpt-3.5-turbo',
                gemini: 'gemini-pro',
                groq: 'mixtral-8x7b-32768'
            },
            customEndpoint: ''
        };
    }

    saveSettings() {
        this.settings.apiKey = document.getElementById('apiKey').value;
        this.settings.provider = document.getElementById('settingsProvider').value;
        this.settings.customEndpoint = document.getElementById('customEndpoint').value;

        // Save model selections
        this.settings.model.openai = document.getElementById('openaiModel').value;
        this.settings.model.gemini = document.getElementById('geminiModel').value;
        this.settings.model.groq = document.getElementById('groqModel').value;

        localStorage.setItem('nl2sql_settings', JSON.stringify(this.settings));

        // Update provider dropdown
        document.getElementById('llmProvider').value = this.settings.provider;

        this.closeSettingsModal();
        this.showAlert('Settings saved successfully', 'success');
    }

    openSettingsModal() {
        document.getElementById('settingsModal').classList.add('active');
        document.getElementById('apiKey').value = this.settings.apiKey;
        document.getElementById('settingsProvider').value = this.settings.provider;
        document.getElementById('customEndpoint').value = this.settings.customEndpoint || '';

        // Load model selections
        document.getElementById('openaiModel').value = this.settings.model.openai;
        document.getElementById('geminiModel').value = this.settings.model.gemini;
        document.getElementById('groqModel').value = this.settings.model.groq;

        this.toggleProviderSettings(this.settings.provider);
    }

    closeSettingsModal() {
        document.getElementById('settingsModal').classList.remove('active');
    }

    toggleProviderSettings(provider) {
        document.querySelectorAll('.provider-settings').forEach(el => {
            el.style.display = 'none';
        });
        const providerSettings = document.getElementById(`${provider}Settings`);
        if (providerSettings) {
            providerSettings.style.display = 'block';
        }
    }

    // Database Management
    async handleFiles(files) {
        for (const file of files) {
            const ext = file.name.split('.').pop().toLowerCase();

            if (['db', 'sqlite', 'sqlite3'].includes(ext)) {
                await this.loadDatabaseFile(file);
            } else if (ext === 'sql') {
                await this.loadSQLFile(file);
            } else {
                this.showAlert('Unsupported file type: ' + ext, 'error');
            }
        }
        this.closeUploadModal();
    }

    async loadDatabaseFile(file) {
        try {
            const buffer = await file.arrayBuffer();
            const uint8Array = new Uint8Array(buffer);
            this.db = new this.SQL.Database(uint8Array);

            const dbName = file.name;
            this.databases[dbName] = this.db;
            this.currentDbName = dbName;

            this.updateDatabaseList();
            this.updateSchemaExplorer();
            this.showAlert(`Database "${dbName}" loaded successfully`, 'success');

            // Save to localStorage (with size limit check)
            this.saveDatabaseToStorage(dbName);
        } catch (error) {
            this.showAlert('Error loading database: ' + error.message, 'error');
        }
    }

    async loadSQLFile(file) {
        try {
            const text = await file.text();

            if (!this.db) {
                this.db = new this.SQL.Database();
                const dbName = file.name.replace('.sql', '.db');
                this.databases[dbName] = this.db;
                this.currentDbName = dbName;
            }

            this.db.run(text);
            this.updateDatabaseList();
            this.updateSchemaExplorer();
            this.showAlert('SQL file executed successfully', 'success');
        } catch (error) {
            this.showAlert('Error executing SQL file: ' + error.message, 'error');
        }
    }

    createNewDatabase() {
        const name = prompt('Enter database name:');
        if (!name) return;

        const dbName = name.endsWith('.db') ? name : name + '.db';
        this.db = new this.SQL.Database();
        this.databases[dbName] = this.db;
        this.currentDbName = dbName;

        this.updateDatabaseList();
        this.updateSchemaExplorer();
        this.showAlert(`Database "${dbName}" created successfully`, 'success');
    }

    switchDatabase(dbName) {
        if (!dbName || !this.databases[dbName]) return;

        this.db = this.databases[dbName];
        this.currentDbName = dbName;
        this.updateSchemaExplorer();
    }

    downloadDatabase() {
        if (!this.db || !this.currentDbName) {
            this.showAlert('No database to download', 'warning');
            return;
        }

        const data = this.db.export();
        const blob = new Blob([data], { type: 'application/octet-stream' });
        const url = URL.createObjectURL(blob);

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
        const filename = `${this.currentDbName.replace('.db', '')}_${timestamp}.db`;

        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();

        URL.revokeObjectURL(url);
        this.showAlert('Database downloaded successfully', 'success');
    }

    updateDatabaseList() {
        const select = document.getElementById('currentDb');
        select.innerHTML = '<option value="">Select database...</option>';

        Object.keys(this.databases).forEach(dbName => {
            const option = document.createElement('option');
            option.value = dbName;
            option.textContent = dbName;
            if (dbName === this.currentDbName) {
                option.selected = true;
            }
            select.appendChild(option);
        });
    }

    updateSchemaExplorer() {
        if (!this.db) {
            document.getElementById('schemaExplorer').innerHTML =
                '<p style="color: var(--text-secondary); font-size: 14px;">No database loaded</p>';
            return;
        }

        try {
            const tables = this.db.exec("SELECT name FROM sqlite_master WHERE type='table'")[0];
            if (!tables) {
                document.getElementById('schemaExplorer').innerHTML =
                    '<p style="color: var(--text-secondary); font-size: 14px;">No tables found</p>';
                return;
            }

            let html = '';
            tables.values.forEach(([tableName]) => {
                const columns = this.db.exec(`PRAGMA table_info(${tableName})`)[0];
                const count = this.db.exec(`SELECT COUNT(*) FROM ${tableName}`)[0].values[0][0];

                html += `
                    <div class="schema-table" onclick="app.toggleSchemaTable('${tableName}')">
                        <div class="schema-table-name">
                            <span>📊 ${tableName}</span>
                            <span style="font-size: 12px; color: var(--text-secondary);">${count} rows</span>
                        </div>
                        <div class="schema-columns" id="schema-${tableName}">
                `;

                if (columns) {
                    columns.values.forEach(col => {
                        const [cid, name, type, notnull, dflt_value, pk] = col;
                        const isPK = pk === 1 ? '🔑' : '';
                        const isRequired = notnull === 1 ? '*' : '';
                        html += `
                            <div class="schema-column">
                                ${isPK} ${name} <span style="color: var(--primary);">${type}</span>${isRequired}
                            </div>
                        `;
                    });
                }

                html += '</div></div>';
            });

            document.getElementById('schemaExplorer').innerHTML = html;
        } catch (error) {
            this.showAlert('Error loading schema: ' + error.message, 'error');
        }
    }

    toggleSchemaTable(tableName) {
        const element = document.getElementById(`schema-${tableName}`);
        element.classList.toggle('active');
    }

    // Natural Language Query Processing
    async executeNLQuery() {
        const query = document.getElementById('nlInput').value.trim();
        if (!query) {
            this.showAlert('Please enter a question', 'warning');
            return;
        }

        if (!this.db) {
            this.showAlert('Please load a database first', 'warning');
            return;
        }

        if (!this.settings.apiKey) {
            this.showAlert('Please configure your API key in settings', 'warning');
            this.openSettingsModal();
            return;
        }

        const resultsDiv = document.getElementById('nlResults');
        resultsDiv.innerHTML = '<div class="spinner"></div>';

        try {
            // Get schema information
            const schema = this.getSchemaForLLM();

            // Generate SQL using LLM
            const sqlQuery = await this.generateSQL(query, schema);

            // Display generated SQL
            let html = `
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">Generated SQL</span>
                        <button class="btn btn-secondary" onclick="app.copySQLToEditor('${this.escapeHtml(sqlQuery)}')">
                            📋 Copy to Editor
                        </button>
                    </div>
                    <div class="code-block">
                        <pre>${this.escapeHtml(sqlQuery)}</pre>
                    </div>
                </div>
            `;

            // Execute SQL
            try {
                const results = this.db.exec(sqlQuery);

                if (results.length > 0) {
                    const result = results[0];
                    html += this.renderQueryResults(result, query);

                    // Get explanation from LLM
                    const explanation = await this.getExplanation(query, sqlQuery, result);
                    html += `
                        <div class="card">
                            <div class="card-header">
                                <span class="card-title">Answer</span>
                            </div>
                            <div style="padding: 10px;">
                                ${explanation}
                            </div>
                        </div>
                    `;
                } else {
                    html += '<div class="alert alert-warning">Query returned no results</div>';
                }
            } catch (sqlError) {
                // Try to fix the SQL with LLM
                html += `<div class="alert alert-error">SQL Error: ${sqlError.message}</div>`;
                html += '<div class="alert alert-warning">Attempting to fix SQL...</div>';

                const fixedSQL = await this.fixSQL(sqlQuery, sqlError.message, schema);
                if (fixedSQL && fixedSQL !== sqlQuery) {
                    html += `
                        <div class="card">
                            <div class="card-header">
                                <span class="card-title">Fixed SQL</span>
                            </div>
                            <div class="code-block">
                                <pre>${this.escapeHtml(fixedSQL)}</pre>
                            </div>
                        </div>
                    `;

                    try {
                        const fixedResults = this.db.exec(fixedSQL);
                        if (fixedResults.length > 0) {
                            html += this.renderQueryResults(fixedResults[0], query);
                        }
                    } catch (fixError) {
                        html += `<div class="alert alert-error">Fixed SQL also failed: ${fixError.message}</div>`;
                    }
                }
            }

            resultsDiv.innerHTML = html;

            // Add to history
            this.addToHistory(query);

        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-error">Error: ${error.message}</div>`;
        }
    }

    async generateSQL(naturalQuery, schema) {
        const prompt = `Given the following database schema:

${schema}

Generate a SQL query for this request: "${naturalQuery}"

Return ONLY the SQL query, no explanations or markdown.`;

        return await this.callLLM(prompt);
    }

    async fixSQL(sqlQuery, errorMessage, schema) {
        const prompt = `The following SQL query failed with an error:

SQL Query:
${sqlQuery}

Error:
${errorMessage}

Database Schema:
${schema}

Please fix the SQL query. Return ONLY the corrected SQL, no explanations.`;

        return await this.callLLM(prompt);
    }

    async getExplanation(question, sqlQuery, results) {
        const resultsPreview = results.values.slice(0, 5).map(row => row.join(', ')).join('\n');
        const prompt = `Given this question: "${question}"

And this SQL query: ${sqlQuery}

Which returned these results (first 5 rows):
${results.columns.join(', ')}
${resultsPreview}

Provide a brief, natural language answer to the original question based on the results. Be concise and direct.`;

        return await this.callLLM(prompt);
    }

    // Helper function to clean markdown codeblocks from LLM responses
    cleanLLMResponse(response) {
        if (!response) return response;

        // Remove markdown codeblocks (```sql ... ``` or ``` ... ```)
        const codeblockRegex = /```(?:sql|SQL)?\s*\n?([\s\S]*?)\n?```/g;
        const match = codeblockRegex.exec(response);

        if (match) {
            // Return the content inside the codeblock
            return match[1].trim();
        }

        // If no codeblock found, return the original response trimmed
        return response.trim();
    }

    async callLLM(prompt) {
        const provider = this.settings.provider;
        const apiKey = this.settings.apiKey;

        if (provider === 'openai') {
            const endpoint = this.settings.customEndpoint || 'https://api.openai.com/v1/chat/completions';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: this.settings.model.openai,
                    messages: [
                        { role: 'system', content: 'You are a SQL expert. Respond only with SQL queries or brief explanations as requested.' },
                        { role: 'user', content: prompt }
                    ],
                    temperature: 0.1,
                    max_tokens: 500
                })
            });

            if (!response.ok) {
                throw new Error(`OpenAI API error: ${response.statusText}`);
            }

            const data = await response.json();
            return this.cleanLLMResponse(data.choices[0].message.content);

        } else if (provider === 'gemini') {
            const endpoint = this.settings.customEndpoint ||
                `https://generativelanguage.googleapis.com/v1beta/models/${this.settings.model.gemini}:generateContent?key=${apiKey}`;

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contents: [{
                        parts: [{
                            text: prompt
                        }]
                    }],
                    generationConfig: {
                        temperature: 0.1,
                        maxOutputTokens: 500
                    }
                })
            });

            if (!response.ok) {
                throw new Error(`Gemini API error: ${response.statusText}`);
            }

            const data = await response.json();
            return this.cleanLLMResponse(data.candidates[0].content.parts[0].text);

        } else if (provider === 'groq') {
            const endpoint = this.settings.customEndpoint || 'https://api.groq.com/openai/v1/chat/completions';

            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: this.settings.model.groq,
                    messages: [
                        { role: 'system', content: 'You are a SQL expert. Respond only with SQL queries or brief explanations as requested.' },
                        { role: 'user', content: prompt }
                    ],
                    temperature: 0.1,
                    max_tokens: 500
                })
            });

            if (!response.ok) {
                throw new Error(`Groq API error: ${response.statusText}`);
            }

            const data = await response.json();
            return this.cleanLLMResponse(data.choices[0].message.content);
        }

        throw new Error('Unknown LLM provider');
    }

    getSchemaForLLM() {
        if (!this.db) return '';

        let schema = '';
        const tables = this.db.exec("SELECT name FROM sqlite_master WHERE type='table'")[0];

        if (tables) {
            tables.values.forEach(([tableName]) => {
                schema += `Table: ${tableName}\n`;
                const columns = this.db.exec(`PRAGMA table_info(${tableName})`)[0];

                if (columns) {
                    schema += 'Columns:\n';
                    columns.values.forEach(col => {
                        const [cid, name, type, notnull, dflt_value, pk] = col;
                        schema += `  - ${name} (${type})${pk ? ' PRIMARY KEY' : ''}${notnull ? ' NOT NULL' : ''}\n`;
                    });
                }

                // Add foreign keys if any
                const fks = this.db.exec(`PRAGMA foreign_key_list(${tableName})`)[0];
                if (fks && fks.values.length > 0) {
                    schema += 'Foreign Keys:\n';
                    fks.values.forEach(fk => {
                        schema += `  - ${fk[3]} -> ${fk[2]}.${fk[4]}\n`;
                    });
                }

                schema += '\n';
            });
        }

        return schema;
    }

    // SQL Editor Functions
    runSQL() {
        const sql = this.sqlEditor.getValue().trim();
        if (!sql) {
            this.showAlert('Please enter a SQL query', 'warning');
            return;
        }

        if (!this.db) {
            this.showAlert('Please load a database first', 'warning');
            return;
        }

        const resultsDiv = document.getElementById('sqlResults');
        resultsDiv.innerHTML = '';

        try {
            // Split by semicolon for multi-statement execution
            const statements = sql.split(';').filter(s => s.trim());
            let allResults = [];

            statements.forEach((statement, index) => {
                if (!statement.trim()) return;

                const results = this.db.exec(statement);
                if (results.length > 0) {
                    allResults.push({
                        statement: statement,
                        result: results[0],
                        index: index + 1
                    });
                }
            });

            if (allResults.length === 0) {
                resultsDiv.innerHTML = '<div class="alert alert-success">Query executed successfully (no results to display)</div>';
            } else {
                let html = '';
                allResults.forEach(({ statement, result, index }) => {
                    if (allResults.length > 1) {
                        html += `<h4>Statement ${index}</h4>`;
                    }
                    html += this.renderQueryResults(result);
                });
                resultsDiv.innerHTML = html;
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-error">SQL Error: ${error.message}</div>`;
        }
    }

    formatSQL() {
        const sql = this.sqlEditor.getValue();
        // Basic SQL formatting
        const formatted = sql
            .replace(/\s+/g, ' ')
            .replace(/\s*,\s*/g, ',\n  ')
            .replace(/\s+(FROM|WHERE|GROUP BY|ORDER BY|HAVING|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN)/gi, '\n$1')
            .replace(/\s+(AND|OR)\s+/gi, '\n  $1 ')
            .trim();

        this.sqlEditor.setValue(formatted);
    }

    copySQLToEditor(sql) {
        // Unescape the SQL
        const unescaped = sql.replace(/&#39;/g, "'").replace(/&quot;/g, '"').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
        this.sqlEditor.setValue(unescaped);
        this.switchTab('sql-editor');
    }

    // Result Rendering
    renderQueryResults(result, originalQuery = null) {
        const totalRows = result.values.length;
        const displayRows = Math.min(totalRows, 100);

        let html = `
            <div class="results-header">
                <span class="results-info">
                    Showing ${displayRows} of ${totalRows} rows
                </span>
                <button class="btn btn-secondary" onclick="app.exportCSV(${JSON.stringify(result).replace(/"/g, '&quot;')})">
                    📥 Export CSV
                </button>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
        `;

        result.columns.forEach(col => {
            html += `<th>${this.escapeHtml(col)}</th>`;
        });

        html += '</tr></thead><tbody>';

        result.values.slice(0, displayRows).forEach(row => {
            html += '<tr>';
            row.forEach(cell => {
                const value = cell === null ? '<i>NULL</i>' : this.escapeHtml(String(cell));
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });

        html += '</tbody></table></div>';

        if (totalRows > displayRows) {
            html += `<div class="alert alert-warning">Showing first ${displayRows} rows. Full results contain ${totalRows} rows.</div>`;
        }

        return html;
    }

    exportCSV(result) {
        let csv = result.columns.map(col => `"${col}"`).join(',') + '\n';

        result.values.forEach(row => {
            csv += row.map(cell => {
                if (cell === null) return '';
                const str = String(cell);
                return str.includes(',') || str.includes('"') || str.includes('\n')
                    ? `"${str.replace(/"/g, '""')}"`
                    : str;
            }).join(',') + '\n';
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `query_results_${new Date().getTime()}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // ER Diagram Generation
    generateERDiagram() {
        if (!this.db) {
            document.getElementById('erDiagramContainer').innerHTML =
                '<p style="color: var(--text-secondary);">No database loaded</p>';
            return;
        }

        try {
            const tables = this.db.exec("SELECT name FROM sqlite_master WHERE type='table'")[0];
            if (!tables) {
                document.getElementById('erDiagramContainer').innerHTML =
                    '<p style="color: var(--text-secondary);">No tables found</p>';
                return;
            }

            // Create SVG
            const svg = this.createERDiagramSVG(tables.values.map(t => t[0]));
            document.getElementById('erDiagramContainer').innerHTML = svg;
        } catch (error) {
            document.getElementById('erDiagramContainer').innerHTML =
                `<div class="alert alert-error">Error generating diagram: ${error.message}</div>`;
        }
    }

    createERDiagramSVG(tableNames) {
        const tables = [];
        const relationships = [];

        // Gather table information
        tableNames.forEach((tableName, index) => {
            const columns = this.db.exec(`PRAGMA table_info(${tableName})`)[0];
            const foreignKeys = this.db.exec(`PRAGMA foreign_key_list(${tableName})`)[0];

            const tableInfo = {
                name: tableName,
                columns: columns ? columns.values.map(col => ({
                    name: col[1],
                    type: col[2],
                    pk: col[5] === 1
                })) : [],
                x: (index % 3) * 250 + 50,
                y: Math.floor(index / 3) * 200 + 50
            };

            tables.push(tableInfo);

            // Add relationships
            if (foreignKeys) {
                foreignKeys.values.forEach(fk => {
                    relationships.push({
                        from: tableName,
                        to: fk[2],
                        fromColumn: fk[3],
                        toColumn: fk[4]
                    });
                });
            }
        });

        // Calculate SVG dimensions
        const width = Math.max(800, tables.length * 150);
        const height = Math.max(600, Math.ceil(tables.length / 3) * 250);

        let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
        svg += '<defs>';
        svg += '<marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">';
        svg += '<polygon points="0 0, 10 3.5, 0 7" fill="#666" />';
        svg += '</marker>';
        svg += '</defs>';

        // Draw relationships first (so they appear behind tables)
        relationships.forEach(rel => {
            const fromTable = tables.find(t => t.name === rel.from);
            const toTable = tables.find(t => t.name === rel.to);

            if (fromTable && toTable) {
                const x1 = fromTable.x + 100;
                const y1 = fromTable.y + 50;
                const x2 = toTable.x + 100;
                const y2 = toTable.y + 50;

                svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" 
                        stroke="#666" stroke-width="2" marker-end="url(#arrowhead)" opacity="0.5"/>`;
            }
        });

        // Draw tables
        tables.forEach(table => {
            const tableHeight = 30 + table.columns.length * 25;

            // Table rectangle
            svg += `<g transform="translate(${table.x}, ${table.y})">`;
            svg += `<rect width="200" height="${tableHeight}" fill="var(--bg-primary)" 
                    stroke="var(--border)" stroke-width="2" rx="5"/>`;

            // Table name
            svg += `<rect width="200" height="30" fill="var(--primary)" rx="5"/>`;
            svg += `<text x="100" y="20" text-anchor="middle" fill="white" font-weight="bold">
                    ${table.name}</text>`;

            // Columns
            table.columns.forEach((col, i) => {
                const y = 30 + i * 25 + 17;
                const pkIcon = col.pk ? '🔑 ' : '';
                svg += `<text x="10" y="${y}" fill="var(--text-primary)" font-size="12">
                        ${pkIcon}${col.name}</text>`;
                svg += `<text x="190" y="${y}" text-anchor="end" fill="var(--text-secondary)" font-size="11">
                        ${col.type}</text>`;
            });

            svg += '</g>';
        });

        svg += '</svg>';
        return svg;
    }

    // Utility Functions
    showAlert(message, type = 'info') {
        const alertClass = type === 'success' ? 'alert-success' :
            type === 'error' ? 'alert-error' :
                type === 'warning' ? 'alert-warning' : 'alert-info';

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert ${alertClass}`;
        alertDiv.textContent = message;
        alertDiv.style.position = 'fixed';
        alertDiv.style.top = '20px';
        alertDiv.style.right = '20px';
        alertDiv.style.zIndex = '9999';
        alertDiv.style.maxWidth = '400px';

        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    addToHistory(query) {
        this.queryHistory.unshift(query);
        this.queryHistory = this.queryHistory.slice(0, 10); // Keep last 10

        const historyDiv = document.getElementById('nlHistory');
        const historyList = document.getElementById('historyList');

        historyDiv.style.display = 'block';
        historyList.innerHTML = this.queryHistory.map(q =>
            `<div style="padding: 5px; cursor: pointer; color: var(--text-secondary); font-size: 14px;" 
                  onclick="document.getElementById('nlInput').value = '${this.escapeHtml(q)}'">
                ${this.escapeHtml(q)}
            </div>`
        ).join('');
    }

    openUploadModal() {
        document.getElementById('uploadModal').classList.add('active');
    }

    closeUploadModal() {
        document.getElementById('uploadModal').classList.remove('active');
    }

    // Local Storage Management
    saveDatabaseToStorage(dbName) {
        try {
            const data = this.db.export();
            const base64 = btoa(String.fromCharCode.apply(null, data));

            // Check size (localStorage typically has 5-10MB limit)
            if (base64.length > 4 * 1024 * 1024) { // 4MB limit to be safe
                console.warn('Database too large for localStorage');
                return;
            }

            const savedDbs = JSON.parse(localStorage.getItem('nl2sql_databases') || '{}');
            savedDbs[dbName] = base64;
            localStorage.setItem('nl2sql_databases', JSON.stringify(savedDbs));
        } catch (error) {
            console.error('Error saving to localStorage:', error);
        }
    }

    loadSavedDatabases() {
        try {
            const savedDbs = JSON.parse(localStorage.getItem('nl2sql_databases') || '{}');

            Object.entries(savedDbs).forEach(([name, base64]) => {
                const binaryString = atob(base64);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                const db = new this.SQL.Database(bytes);
                this.databases[name] = db;

                if (!this.currentDbName) {
                    this.currentDbName = name;
                    this.db = db;
                }
            });

            if (Object.keys(this.databases).length > 0) {
                this.updateDatabaseList();
                this.updateSchemaExplorer();
            }
        } catch (error) {
            console.error('Error loading saved databases:', error);
        }
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new NL2SQLApp();
});

// Global functions for onclick handlers
function closeSettingsModal() {
    document.getElementById('settingsModal').classList.remove('active');
}

function closeUploadModal() {
    document.getElementById('uploadModal').classList.remove('active');
}

function saveSettings() {
    app.saveSettings();
}