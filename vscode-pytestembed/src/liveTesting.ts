/**
 * Live testing functionality - WebSocket communication and test execution
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as WebSocket from 'ws';
import { state, addPanelMessage, updateTestProgress, setTestResults } from './state';
import { refreshTestResultDecorations, updateCollapsedBlockStatusIndicators } from './decorations';
import { TestResult, LiveTestMessage } from './types';
import { updateTestStatus, markAllTestsAsFailing, markAllTestsAsUntested, markAllTestsAsRunning } from './testResults';

/**
 * Start live testing server and connect to it
 */
export function startLiveTesting() {
    if (state.liveTestingEnabled) {
        vscode.window.showInformationMessage('Live testing is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    state.outputChannel.appendLine('🚀 Starting PyTestEmbed Live Testing...');

    // Get Python interpreter from configuration
    const config = vscode.workspace.getConfiguration('pytestembed');
    const pythonInterpreter = config.get('pythonInterpreter', 'python');

    // Start the live test server
    state.liveTestProcess = cp.spawn(pythonInterpreter, ['-m', 'pytestembed.live_runner', workspaceFolder.uri.fsPath], {
        cwd: workspaceFolder.uri.fsPath,
        shell: true
    });

    state.liveTestProcess.stdout?.on('data', (data) => {
        state.outputChannel.append(data.toString());
    });

    state.liveTestProcess.stderr?.on('data', (data) => {
        state.outputChannel.append(data.toString());
    });

    state.liveTestProcess.on('close', (code) => {
        state.outputChannel.appendLine(`Live test server exited with code ${code}`);
        state.liveTestingEnabled = false;
        updateLiveTestingStatus();
    });

    // Wait a moment for server to start, then connect
    setTimeout(() => {
        connectToLiveTestServer();
    }, 2000);
}

/**
 * Stop live testing
 */
export function stopLiveTesting() {
    if (!state.liveTestingEnabled) {
        vscode.window.showInformationMessage('Live testing is not running');
        return;
    }

    state.outputChannel.appendLine('🛑 Stopping PyTestEmbed Live Testing...');

    // Close WebSocket connection
    if (state.liveTestSocket) {
        state.liveTestSocket.close();
        state.liveTestSocket = null;
    }

    // Kill the server process
    if (state.liveTestProcess) {
        state.liveTestProcess.kill();
        state.liveTestProcess = null;
    }

    // Clear decorations
    import('./decorations').then(({ clearAllDecorations }) => {
        clearAllDecorations();
    });

    state.liveTestingEnabled = false;
    updateLiveTestingStatus();
    addPanelMessage('Live testing stopped', 'info');
    vscode.window.showInformationMessage('Live testing stopped');
}

/**
 * Connect to the live test server via WebSocket
 */
function connectToLiveTestServer() {
    try {
        state.liveTestSocket = new WebSocket('ws://localhost:8765');

        state.liveTestSocket.on('open', () => {
            state.outputChannel.appendLine('✅ Connected to live test server');
            state.liveTestingEnabled = true;
            updateLiveTestingStatus();
            addPanelMessage('Connected to live test server', 'success');

            // Mark all tests in currently open Python files as failing initially
            vscode.window.visibleTextEditors.forEach(editor => {
                if (editor.document.languageId === 'python') {
                    markAllTestsAsFailing(editor.document.fileName);
                    refreshTestResultDecorations(editor.document.fileName);

                    // Then mark them as running and start actual tests
                    setTimeout(() => {
                        markAllTestsAsRunning(editor.document.fileName);
                        refreshTestResultDecorations(editor.document.fileName);

                        // Trigger test run for this file
                        const testRequest = {
                            command: 'run_tests',
                            file_path: editor.document.fileName
                        };
                        state.liveTestSocket?.send(JSON.stringify(testRequest));
                    }, 500);
                }
            });

            vscode.window.showInformationMessage('Live testing started');
        });

        state.liveTestSocket.on('message', (data: WebSocket.Data) => {
            handleLiveTestMessage(data.toString());
        });

        state.liveTestSocket.on('close', () => {
            state.outputChannel.appendLine('📡 Disconnected from live test server');
            state.liveTestingEnabled = false;
            updateLiveTestingStatus();
            addPanelMessage('Disconnected from live test server', 'warning');
        });

        state.liveTestSocket.on('error', (error: Error) => {
            state.outputChannel.appendLine(`❌ Live test connection error: ${error.message}`);
            vscode.window.showErrorMessage(`Failed to connect to live test server: ${error.message}`);
        });

    } catch (error) {
        state.outputChannel.appendLine(`❌ Failed to connect to live test server: ${error}`);
        vscode.window.showErrorMessage('Failed to start live testing');
    }
}

/**
 * Handle messages from the live test server
 */
function handleLiveTestMessage(message: string) {
    try {
        const data: LiveTestMessage = JSON.parse(message);

        // Send all messages to the panel
        addPanelMessage(`Received: ${data.type}`, 'info');

        switch (data.type) {
            case 'test_results':
                handleTestResults(data.data);
                addPanelMessage(`Test results for ${data.data.file_path}: ${data.data.tests.length} tests`, 'info');
                break;
            case 'individual_test_result':
                handleIndividualTestResult(data);
                const status = data.status === 'pass' ? 'success' : 'error';
                addPanelMessage(`Test ${data.status}: ${data.expression}`, status);
                break;
            case 'test_start':
                handleTestStart(data);
                addPanelMessage(`Starting tests for ${data.file_path || 'workspace'}`, 'info');
                break;
            case 'test_error':
                handleTestError(data);
                addPanelMessage(`Test error: ${data.error}`, 'error');
                break;
            case 'coverage':
                handleCoverage(data);
                addPanelMessage(`Coverage data received`, 'info');
                break;

            case 'dependency_analysis':
                addPanelMessage(`Dependency analysis: ${data.data.elements} elements, ${data.data.dependencies} dependencies`, 'info');
                break;
            case 'smart_test_selection':
                addPanelMessage(`Smart test selection: ${data.data.selected_count} tests selected`, 'info');
                break;
            case 'intelligent_test_selection':
                handleIntelligentTestSelection(data);
                const testCount = data.data.affected_tests ? data.data.affected_tests.length : 'unknown';
                addPanelMessage(`Intelligent test selection: ${testCount} tests affected in ${data.data.changed_file}`, 'info');
                break;
            case 'test_status_update':
                handleTestStatusUpdate(data);
                addPanelMessage(`Test status: ${data.data.test_name} - ${data.data.status}`,
                    data.data.status === 'pass' ? 'success' : 'warning');
                break;
            default:
                addPanelMessage(`Unknown message type: ${data.type}`, 'warning');
        }
    } catch (error) {
        state.outputChannel.appendLine(`❌ Error parsing live test message: ${error}`);
        addPanelMessage(`Error parsing message: ${error}`, 'error');
    }
}

/**
 * Handle test results from live server
 */
function handleTestResults(results: any) {
    let filePath = results.file_path;

    // Convert relative path to absolute path if needed
    if (!require('path').isAbsolute(filePath)) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            filePath = require('path').join(workspaceFolder.uri.fsPath, filePath);
        }
    }

    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);

    if (!editor) {
        console.log(`⚠️ No editor found for file: ${filePath}`);
        return;
    }

    console.log(`📊 Handling test results for: ${filePath} (${results.tests.length} tests)`);

    // Update test results tracking
    const fileResults: TestResult[] = [];

    results.tests.forEach((test: any) => {
        const testResult: TestResult = {
            line: test.line_number - 1, // Convert to 0-based
            expression: test.assertion,
            status: test.status,
            message: test.message
        };
        fileResults.push(testResult);

        // Update individual test status
        updateTestStatus(filePath, testResult.line, testResult.status, testResult.expression, testResult.message);
    });

    // Update progress
    const totalTests = results.tests.length;
    const passedTests = results.tests.filter((t: any) => t.status === 'pass').length;
    updateTestProgress(passedTests, totalTests);

    // Update collapsed block status indicators
    updateCollapsedBlockStatusIndicators(editor, fileResults);

    // Refresh decorations
    refreshTestResultDecorations(filePath);
}

/**
 * Handle individual test result
 */
function handleIndividualTestResult(data: LiveTestMessage) {
    let filePath = data.file_path!;
    const lineNumber = data.line_number! - 1; // Convert to 0-based
    const status = data.status!;
    const expression = data.expression!;
    const message = data.message;

    // Convert relative path to absolute path if needed
    if (!require('path').isAbsolute(filePath)) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            filePath = require('path').join(workspaceFolder.uri.fsPath, filePath);
        }
    }

    console.log(`🔄 Updating test status: ${filePath}:${lineNumber + 1} -> ${status}`);

    // Update test status
    updateTestStatus(filePath, lineNumber, status, expression, message);

    // Update progress
    state.currentTestProgress.current++;
    updateTestProgress(state.currentTestProgress.current, state.currentTestProgress.total);

    state.outputChannel.appendLine(`${status === 'pass' ? '✅' : '❌'} ${expression} - ${message || status}`);
}

/**
 * Handle test start notification
 */
function handleTestStart(data: LiveTestMessage) {
    vscode.window.setStatusBarMessage('PyTestEmbed: Running tests...', 2000);

    // Mark all tests as untested initially when live testing starts
    if (data.file_path) {
        markAllTestsAsUntested(data.file_path);
    }
}

/**
 * Handle test error
 */
function handleTestError(data: LiveTestMessage) {
    state.outputChannel.appendLine(`❌ Test error in ${data.file_path}: ${data.error}`);
    vscode.window.showErrorMessage(`Test error: ${data.error}`);
}

/**
 * Handle coverage information
 */
function handleCoverage(data: LiveTestMessage) {
    // Implementation for coverage visualization
    // This would show coverage information in the editor
}

/**
 * Handle intelligent test selection notification
 */
function handleIntelligentTestSelection(data: LiveTestMessage) {
    const changedFile = data.data.changed_file;
    const affectedTests = data.data.affected_tests || [];

    console.log(`🧠 Intelligent test selection for ${changedFile}: ${affectedTests.length} tests affected`);

    // Show status message
    vscode.window.setStatusBarMessage(
        `PyTestEmbed: Running ${affectedTests.length} affected tests...`,
        3000
    );

    state.outputChannel.appendLine(`🧠 Intelligent test selection: ${affectedTests.length} tests affected in ${changedFile}`);
}

/**
 * Handle test status update from server
 */
function handleTestStatusUpdate(data: LiveTestMessage) {
    const testData = data.data;
    const filePath = testData.file_path;
    const lineNumber = testData.line_number - 1; // Convert to 0-based
    const status = testData.status;
    const expression = testData.assertion;
    const message = testData.message;

    console.log(`📊 Test status update: ${filePath}:${lineNumber + 1} -> ${status}`);

    // Convert relative path to absolute path if needed
    let absolutePath = filePath;
    if (!require('path').isAbsolute(filePath)) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            absolutePath = require('path').join(workspaceFolder.uri.fsPath, filePath);
        }
    }

    // Update test status in VSCode
    updateTestStatus(absolutePath, lineNumber, status, expression, message);
}

/**
 * Update live testing status in UI
 */
function updateLiveTestingStatus() {
    vscode.commands.executeCommand('setContext', 'pytestembed.liveTestingEnabled', state.liveTestingEnabled);
}

/**
 * Run an individual test at a specific line
 */
export function runIndividualTest(filePath: string, lineNumber: number) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.fileName !== filePath) {
        vscode.window.showErrorMessage('File not currently open in editor');
        return;
    }

    const document = editor.document;
    const line = document.lineAt(lineNumber);
    const testExpression = extractTestExpression(line.text);

    if (!testExpression) {
        vscode.window.showErrorMessage('No valid test expression found on this line');
        return;
    }

    // Update test status to running
    updateTestStatus(filePath, lineNumber, 'running', testExpression);
    updateTestProgress(state.currentTestProgress.current, state.currentTestProgress.total + 1);

    // Extract context (variables defined before this test)
    const context = extractTestContext(document, lineNumber);

    // Send test execution request to live test server
    if (state.liveTestSocket && state.liveTestSocket.readyState === WebSocket.OPEN) {
        // Convert absolute path to relative path for the server
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        const relativePath = workspaceFolder ?
            require('path').relative(workspaceFolder.uri.fsPath, filePath) :
            filePath;

        const testRequest = {
            type: 'run_individual_test',
            file_path: relativePath,
            line_number: lineNumber + 1, // Convert back to 1-based for server
            expression: testExpression,
            context: context
        };

        state.liveTestSocket.send(JSON.stringify(testRequest));
        state.outputChannel.appendLine(`🧪 Running individual test: ${testExpression} (${relativePath}:${lineNumber + 1})`);
        console.log(`📤 Sent individual test request:`, testRequest);
    } else {
        vscode.window.showErrorMessage('Live testing is not active. Please start live testing first.');
        updateTestStatus(filePath, lineNumber, 'fail', testExpression, 'Live testing not active');
    }
}

/**
 * Extract test expression from a line of code
 */
function extractTestExpression(lineText: string): string | null {
    // Match PyTestEmbed test syntax: expression == expected: "description"
    // Handle both with and without trailing comma
    const match = lineText.match(/^\s*(.+?)\s*:\s*".*?"[,]?\s*$/);
    if (match) {
        return match[1].trim();
    }

    // Debug: log what we're trying to match
    console.log(`Failed to extract test expression from: "${lineText}"`);
    console.log(`Trimmed: "${lineText.trim()}"`);

    return null;
}

/**
 * Extract context code needed to run a test (variables defined before)
 */
function extractTestContext(document: vscode.TextDocument, testLineNumber: number): string {
    const contextLines: string[] = [];

    // Find the start of the test block
    let blockStartLine = testLineNumber;
    for (let i = testLineNumber; i >= 0; i--) {
        const line = document.lineAt(i);
        if (line.text.trim() === 'test:') {
            blockStartLine = i;
            break;
        }
    }

    // Collect all lines between test: and the current test line
    for (let i = blockStartLine + 1; i < testLineNumber; i++) {
        const line = document.lineAt(i);
        const trimmedText = line.text.trim();

        // Skip empty lines and test expressions
        if (trimmedText && !trimmedText.match(/^.+:\s*".*"[,]?$/)) {
            contextLines.push(line.text);
        }
    }

    return contextLines.join('\n');
}
