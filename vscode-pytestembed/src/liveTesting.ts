/**
 * Live testing functionality - WebSocket communication and test execution
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as WebSocket from 'ws';
import { state, addPanelMessage, updateTestProgress, setTestResults } from './state';
import { refreshTestResultDecorations, updateCollapsedBlockStatusIndicators } from './decorations';
import { TestResult, LiveTestMessage, DependencyInfo } from './types';
import { updateTestStatus, markAllTestsAsFailing, markAllTestsAsUntested, markAllTestsAsRunning } from './testResults';

/**
 * Start live testing server and connect to it
 */
export async function startLiveTesting() {
    if (state.liveTestingEnabled) {
        vscode.window.showInformationMessage('Live testing is already running');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    try {
        // Start live test server process - Python will handle dependency service startup
        const process = cp.spawn('python', [
            '-m', 'pytestembed.live_runner',
            workspaceFolder.uri.fsPath,
            '8765'
        ], {
            cwd: workspaceFolder.uri.fsPath,
            stdio: ['pipe', 'pipe', 'pipe']
        });

        process.stdout?.on('data', (data) => {
            const output = data.toString();
            console.log('Live Test Server:', output);
            state.outputChannel.appendLine(`[Live Test] ${output}`);
        });

        process.stderr?.on('data', (data) => {
            const output = data.toString();
            console.error('Live Test Server Error:', output);
            state.outputChannel.appendLine(`[Live Test Error] ${output}`);
        });

        process.on('close', (code) => {
            console.log(`Live test server exited with code ${code}`);
            state.outputChannel.appendLine(`[Live Test] Process exited with code ${code}`);
            state.liveTestingEnabled = false;
            state.liveTestProcess = null;
        });

        process.on('error', (error) => {
            console.error('Failed to start live test server:', error);
            vscode.window.showErrorMessage(`Failed to start live test server: ${error.message}`);
            state.liveTestingEnabled = false;
            state.liveTestProcess = null;
        });

        state.liveTestProcess = process;
        state.liveTestingEnabled = true;

        vscode.window.showInformationMessage('Live test server started successfully');
        state.outputChannel.appendLine('[Live Test] Started successfully');

        // Wait a bit then connect
        setTimeout(() => {
            connectToLiveTestServer();
        }, 3000);

    } catch (error) {
        console.error('Error starting live test server:', error);
        vscode.window.showErrorMessage(`Error starting live test server: ${error}`);
    }
}

// Removed server checking and startup functions - Python handles service dependencies

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
            addPanelMessage('✅ Live Test Server: Connected', 'success');
            vscode.window.showInformationMessage('✅ Live testing connected successfully');

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
            addPanelMessage('❌ Live Test Server: Disconnected', 'warning');
        });

        state.liveTestSocket.on('error', (error: Error) => {
            state.outputChannel.appendLine(`❌ Live test connection error: ${error.message}`);
            state.liveTestingEnabled = false;
            updateLiveTestingStatus();
            addPanelMessage(`❌ Live Test Server: Connection failed - ${error.message}`, 'error');
            vscode.window.showErrorMessage(`❌ Failed to connect to live test server: ${error.message}`);
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
            case 'dependency_info':
                handleDependencyInfo(data);
                addPanelMessage(`Dependency info: ${(data as any).element_name} - ${(data as any).dependency_count} deps, ${(data as any).dependent_count} dependents`, 'info');
                break;
            case 'dependency_error':
                addPanelMessage(`Dependency error: ${(data as any).error}`, 'error');
                break;
            case 'dependency_graph_updated':
                handleDependencyGraphUpdate(data);
                addPanelMessage(`Dependency graph updated for: ${(data as any).data?.changed_file}`, 'info');
                break;
            case 'clear_dependency_cache':
                handleClearDependencyCache(data);
                addPanelMessage(`Dependency cache cleared for: ${(data as any).data?.file_path}`, 'info');
                break;

            // New message types from Python-centric architecture
            case 'test_discovery':
                handleTestDiscoveryResponse(data);
                addPanelMessage(`Test discovery for ${data.file_path}: ${data.tests?.length || 0} tests found`, 'info');
                break;

            case 'test_at_line':
                handleTestAtLineResponse(data);
                addPanelMessage(`Test at line ${(data.line_number || 0) + 1}: ${data.test ? 'found' : 'not found'}`, 'info');
                break;

            case 'test_context':
                handleTestContextResponse(data);
                addPanelMessage(`Test context extracted for line ${(data.line_number || 0) + 1}`, 'info');
                break;

            case 'individual_test_start':
                handleIndividualTestStart(data);
                addPanelMessage(`Individual test started: ${data.test?.expression || 'unknown'}`, 'info');
                break;

            case 'individual_test_result':
                handleIndividualTestResult(data);
                addPanelMessage(`Individual test completed: ${data.result?.status || 'unknown'}`, 'info');
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
    // Handle both old and new message formats
    const file_path = data.file_path;
    const line_number = data.line_number;
    const test = data.test;
    const result = data.result;

    if (!file_path || line_number === undefined) {
        console.warn('Invalid test result data:', data);
        return;
    }

    // Convert relative path back to absolute
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    const absolutePath = workspaceFolder ?
        require('path').join(workspaceFolder.uri.fsPath, file_path) :
        file_path;

    // Update test status based on result
    const status = result?.status || data.status || 'fail';
    const message = result?.error || result?.message || test?.message || data.message || '';
    const expression = test?.expression || data.expression || 'Test';
    const lineNumber = line_number - 1; // Convert to 0-based

    console.log(`🔄 Updating test status: ${absolutePath}:${lineNumber + 1} -> ${status}`);

    // Update test status
    updateTestStatus(absolutePath, lineNumber, status, expression, message);

    // Update progress
    state.currentTestProgress.current++;
    updateTestProgress(state.currentTestProgress.current, state.currentTestProgress.total);

    state.outputChannel.appendLine(`${status === 'pass' ? '✅' : '❌'} ${expression} - ${message || status}`);
    if (result?.error) {
        state.outputChannel.appendLine(`   Error: ${result.error}`);
    }
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
 * Handle dependency information from server
 */
function handleDependencyInfo(data: any) {
    const dependencyInfo: DependencyInfo = {
        element_id: data.element_id,
        element_name: data.element_name,
        file_path: data.file_path,
        line_number: data.line_number,
        dependencies: data.dependencies || [],
        dependents: data.dependents || [],
        is_dead_code: data.is_dead_code || false,
        dependency_count: data.dependency_count || 0,
        dependent_count: data.dependent_count || 0
    };

    // Cache the dependency information
    state.dependencyCache.set(data.element_id, dependencyInfo);

    console.log(`🔗 Cached dependency info for ${data.element_name}: ${data.dependency_count} deps, ${data.dependent_count} dependents`);
}

/**
 * Handle dependency graph update notification
 */
function handleDependencyGraphUpdate(data: any) {
    const updateData = data.data;
    console.log(`🔄 Dependency graph updated for file: ${updateData.changed_file}`);

    // The dependency graph has been updated on the server side
    // Any new hover requests will get fresh data
}

/**
 * Handle dependency cache clearing for a file
 */
function handleClearDependencyCache(data: any) {
    const clearData = data.data;
    const filePath = clearData.file_path;

    console.log(`🗑️ Clearing dependency cache for file: ${filePath}`);

    // Remove all cached dependency info for elements in this file
    const keysToRemove: string[] = [];
    for (const [elementId, _] of state.dependencyCache) {
        if (elementId.startsWith(filePath + ':')) {
            keysToRemove.push(elementId);
        }
    }

    for (const key of keysToRemove) {
        state.dependencyCache.delete(key);
    }

    console.log(`🗑️ Removed ${keysToRemove.length} cached dependency entries for ${filePath}`);
}

/**
 * Update live testing status in UI
 */
function updateLiveTestingStatus() {
    vscode.commands.executeCommand('setContext', 'pytestembed.liveTestingEnabled', state.liveTestingEnabled);
}

/**
 * Run an individual test at a specific line
 * Simplified version - all logic moved to Python core
 */
export function runIndividualTest(filePath: string, lineNumber: number) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document.fileName !== filePath) {
        vscode.window.showErrorMessage('File not currently open in editor');
        return;
    }

    // Update test status to running (visual feedback only)
    updateTestStatus(filePath, lineNumber, 'running', 'Running test...');
    updateTestProgress(state.currentTestProgress.current, state.currentTestProgress.total + 1);

    // Send test execution request to live test server
    // All test logic (expression extraction, context extraction, execution) handled by Python core
    if (state.liveTestSocket && state.liveTestSocket.readyState === WebSocket.OPEN) {
        // Convert absolute path to relative path for the server
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(editor.document.uri);
        const relativePath = workspaceFolder ?
            require('path').relative(workspaceFolder.uri.fsPath, filePath) :
            filePath;

        const testRequest = {
            command: 'run_test_at_line',
            file_path: relativePath,
            line_number: lineNumber  // 0-based for Python core
        };

        state.liveTestSocket.send(JSON.stringify(testRequest));
        state.outputChannel.appendLine(`🧪 Running individual test at line ${lineNumber + 1} (${relativePath})`);
        console.log(`📤 Sent individual test request:`, testRequest);
    } else {
        vscode.window.showErrorMessage('Live testing is not active. Please start live testing first.');
        updateTestStatus(filePath, lineNumber, 'fail', 'Test failed', 'Live testing not active');
    }
}

// Test expression extraction and context extraction logic moved to Python core
// VSCode extension now only handles UI and communication

/**
 * Handle test discovery response from Python core
 */
function handleTestDiscoveryResponse(data: any) {
    // Import here to avoid circular dependency
    const { handleTestDiscoveryResponse } = require('./testResults');
    handleTestDiscoveryResponse(data);
}

/**
 * Handle test at line response from Python core
 */
function handleTestAtLineResponse(data: any) {
    console.log(`Test at line ${data.line_number + 1}:`, data.test);
    // Could be used for hover information or other IDE features
}

/**
 * Handle test context response from Python core
 */
function handleTestContextResponse(data: any) {
    console.log(`Test context for line ${data.line_number + 1}:`, data.context);
    // Could be used for debugging or test execution features
}

/**
 * Handle individual test start notification
 */
function handleIndividualTestStart(data: any) {
    const { file_path, line_number, test } = data;

    // Convert relative path back to absolute
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    const absolutePath = workspaceFolder ?
        require('path').join(workspaceFolder.uri.fsPath, file_path) :
        file_path;

    // Update test status to running
    updateTestStatus(absolutePath, line_number, 'running', test?.expression || 'Running test...');

    state.outputChannel.appendLine(`🧪 Individual test started: ${test?.expression || 'unknown'} (${file_path}:${line_number + 1})`);
}

// Duplicate function removed - using the first implementation above
