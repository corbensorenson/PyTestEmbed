/**
 * Test result management and status tracking
 */

import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import { state, getTestResults, setTestResults, updateTestProgress } from './state';
import { refreshTestResultDecorations } from './decorations';
import { TestResult, TestStatus } from './types';

/**
 * Mark all tests in a file as failing initially (when live testing is enabled)
 */
export function markAllTestsAsFailing(filePath: string) {
    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);
    if (!editor) return;

    const document = editor.document;
    const fileResults: TestResult[] = [];

    // Find all test expressions in the file
    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const testExpression = extractTestExpression(line.text);
        
        if (testExpression) {
            fileResults.push({
                line: i,
                expression: testExpression,
                status: 'fail',
                message: 'Test not run yet'
            });
        }
    }

    if (fileResults.length > 0) {
        setTestResults(filePath, fileResults);
        updateProblemsPanel(filePath, fileResults);
    }
}

/**
 * Mark all test expressions in a file as untested (fail status) initially
 */
export function markAllTestsAsUntested(filePath: string) {
    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);
    if (!editor) return;

    const document = editor.document;
    const untestedTests: TestResult[] = [];

    // Find all test expressions in the file
    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const expression = extractTestExpression(line.text);

        if (expression) {
            const testResult: TestResult = {
                line: i,
                expression,
                status: 'fail', // Mark as fail initially (untested)
                message: 'Not tested yet'
            };
            untestedTests.push(testResult);
            updateTestStatus(filePath, i, 'fail', expression, 'Not tested yet');
        }
    }

    // Update progress to show total tests found
    state.currentTestProgress = { current: 0, total: untestedTests.length };
    updateTestProgress(0, untestedTests.length);

    // Refresh decorations
    refreshTestResultDecorations(filePath);
}

/**
 * Mark all test expressions in a file as running (but preserve existing results)
 */
export function markAllTestsAsRunning(filePath: string) {
    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);
    if (!editor) return;

    const document = editor.document;
    const fileResults = getTestResults(filePath);

    // Find all test expressions in the file and mark as running if not already tested
    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const expression = extractTestExpression(line.text);

        if (expression) {
            const existingResult = fileResults.find(result => result.line === i);

            // Only mark as running if it's currently untested or failed
            if (!existingResult || (existingResult.status === 'fail' && existingResult.message === 'Not tested yet')) {
                updateTestStatus(filePath, i, 'running', expression, 'Running test...');
            }
        }
    }

    // Refresh decorations
    refreshTestResultDecorations(filePath);
}

/**
 * Update test status and refresh decorations
 */
export function updateTestStatus(filePath: string, lineNumber: number, status: TestStatus, expression: string, message?: string) {
    console.log(`🔄 updateTestStatus called: ${filePath}:${lineNumber + 1} -> ${status} (${expression})`);

    const fileResults = getTestResults(filePath);
    const existingIndex = fileResults.findIndex(result => result.line === lineNumber);

    const testResult: TestResult = {
        line: lineNumber,
        expression,
        status,
        message
    };

    if (existingIndex >= 0) {
        console.log(`   📝 Updating existing test at index ${existingIndex}`);
        fileResults[existingIndex] = testResult;
    } else {
        console.log(`   ➕ Adding new test result`);
        fileResults.push(testResult);
    }

    setTestResults(filePath, fileResults);
    console.log(`   💾 Saved ${fileResults.length} test results for file`);

    // Refresh decorations for this file
    refreshTestResultDecorations(filePath);
    console.log(`   🎨 Refreshed decorations`);

    // Update Problems panel
    updateProblemsPanel(filePath, fileResults);
    console.log(`   📋 Updated problems panel`);
}

/**
 * Update VSCode Problems panel with test results
 */
export function updateProblemsPanel(filePath: string, fileResults: TestResult[]) {
    const uri = vscode.Uri.file(filePath);
    const diagnostics: vscode.Diagnostic[] = [];

    fileResults.forEach(result => {
        if (result.status === 'fail' || result.status === 'error') {
            const range = new vscode.Range(result.line, 0, result.line, 1000);
            const severity = result.status === 'error' ? vscode.DiagnosticSeverity.Error : vscode.DiagnosticSeverity.Warning;

            const diagnostic = new vscode.Diagnostic(
                range,
                result.message || `Test failed: ${result.expression}`,
                severity
            );

            diagnostic.source = 'PyTestEmbed';
            diagnostic.code = result.status === 'error' ? 'test-error' : 'test-failure';

            diagnostics.push(diagnostic);
        }
    });

    // Update the diagnostic collection
    state.diagnosticCollection.set(uri, diagnostics);
}

/**
 * Clear problems for a specific file
 */
export function clearProblemsForFile(filePath: string) {
    const uri = vscode.Uri.file(filePath);
    state.diagnosticCollection.delete(uri);
}

/**
 * Clear all problems
 */
export function clearAllProblems() {
    state.diagnosticCollection.clear();
}

/**
 * Extract test expression from a line of code
 * DEPRECATED: This logic has been moved to Python core.
 * This function is kept for backward compatibility but should not be used for new features.
 */
export function extractTestExpression(lineText: string): string | null {
    // This is a simplified fallback - the Python core now handles all test parsing
    const match = lineText.match(/^\s*(.+?)\s*:\s*".*"[,]?$/);
    if (match) {
        return match[1].trim();
    }
    return null;
}

/**
 * Request test discovery from Python core for a file
 * This replaces local test parsing with server-side discovery
 */
export function requestTestDiscovery(filePath: string, callback: (tests: any[]) => void) {
    const { state } = require('./extension');

    if (state.liveTestSocket && state.liveTestSocket.readyState === WebSocket.OPEN) {
        // Convert absolute path to relative path for the server
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(vscode.Uri.file(filePath));
        const relativePath = workspaceFolder ?
            require('path').relative(workspaceFolder.uri.fsPath, filePath) :
            filePath;

        const request = {
            command: 'discover_tests',
            file_path: relativePath
        };

        // Store callback for when response comes back
        if (!state.testDiscoveryCallbacks) {
            state.testDiscoveryCallbacks = new Map();
        }
        state.testDiscoveryCallbacks.set(relativePath, callback);

        state.liveTestSocket.send(JSON.stringify(request));
        console.log(`📤 Requested test discovery for: ${relativePath}`);
    } else {
        console.warn('Live test socket not available for test discovery');
        callback([]);
    }
}

/**
 * Handle test discovery response from Python core
 */
export function handleTestDiscoveryResponse(data: any) {
    const { state } = require('./extension');

    if (data.type === 'test_discovery' && state.testDiscoveryCallbacks) {
        const callback = state.testDiscoveryCallbacks.get(data.file_path);
        if (callback) {
            callback(data.tests || []);
            state.testDiscoveryCallbacks.delete(data.file_path);
        }
    }
}

/**
 * Run test at cursor position
 */
export function runTestAtCursor() {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !state.liveTestingEnabled) {
        return;
    }

    const position = editor.selection.active;
    const filePath = editor.document.fileName;
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);

    if (!workspaceFolder) {
        return;
    }

    const relativePath = require('path').relative(workspaceFolder.uri.fsPath, filePath);

    if (state.liveTestSocket && state.liveTestSocket.readyState === WebSocket.OPEN) {
        state.liveTestSocket.send(JSON.stringify({
            command: 'run_test',
            file_path: relativePath,
            line_number: position.line + 1
        }));
    }
}

/**
 * Show test results panel
 */
export function showTestResultsPanel() {
    // Create and show a webview panel with test results
    const panel = vscode.window.createWebviewPanel(
        'pytestembedResults',
        'PyTestEmbed Test Results',
        vscode.ViewColumn.Beside,
        {
            enableScripts: true
        }
    );

    panel.webview.html = getTestResultsWebviewContent();
}

/**
 * Get HTML content for test results webview
 */
function getTestResultsWebviewContent(): string {
    return `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PyTestEmbed Test Results</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .test-result { margin: 10px 0; padding: 10px; border-radius: 5px; }
            .pass { background-color: rgba(0, 255, 0, 0.1); border-left: 4px solid green; }
            .fail { background-color: rgba(255, 0, 0, 0.1); border-left: 4px solid red; }
            .error { background-color: rgba(255, 165, 0, 0.1); border-left: 4px solid orange; }
        </style>
    </head>
    <body>
        <h1>PyTestEmbed Live Test Results</h1>
        <div id="results">
            <p>Live test results will appear here...</p>
        </div>
        <script>
            // WebSocket connection to receive live updates
            // This would connect to the live test server for real-time updates
        </script>
    </body>
    </html>
    `;
}

/**
 * Get all test results for display
 */
export function getAllTestResults(): Map<string, TestResult[]> {
    return state.testResults;
}

/**
 * Get test results summary
 */
export function getTestResultsSummary(): { total: number; passed: number; failed: number; errors: number } {
    let total = 0;
    let passed = 0;
    let failed = 0;
    let errors = 0;

    state.testResults.forEach(fileResults => {
        fileResults.forEach(result => {
            total++;
            switch (result.status) {
                case 'pass':
                    passed++;
                    break;
                case 'fail':
                    failed++;
                    break;
                case 'error':
                    errors++;
                    break;
            }
        });
    });

    return { total, passed, failed, errors };
}
