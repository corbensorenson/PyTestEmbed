/**
 * Minimal live testing client - pure display client for PyTestEmbed Python server
 */

import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import { state } from './state';
import { refreshTestResultDecorations } from './decorations';
import { TestResult } from './types';

let liveSocket: WebSocket | null = null;

/**
 * Start live testing - connect to Python server
 */
export function startLiveTesting() {
    if (liveSocket) {
        vscode.window.showWarningMessage('Live testing is already active');
        return;
    }

    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    console.log('🔗 Connecting to PyTestEmbed Python server...');
    
    liveSocket = new WebSocket('ws://localhost:8768');
    
    liveSocket.on('open', () => {
        console.log('✅ Connected to PyTestEmbed Python server');
        state.liveTestingEnabled = true;
        
        // Request all existing test results
        sendCommand('get_all_test_results');
        
        vscode.window.showInformationMessage('Live testing started');
        vscode.commands.executeCommand('setContext', 'pytestembed.liveTestingEnabled', true);
    });

    liveSocket.on('message', (data: WebSocket.Data) => {
        try {
            const message = JSON.parse(data.toString());
            handleMessage(message);
        } catch (error) {
            console.error('Error parsing message:', error);
        }
    });

    liveSocket.on('close', () => {
        console.log('❌ Disconnected from PyTestEmbed Python server');
        liveSocket = null;
        state.liveTestingEnabled = false;
        vscode.commands.executeCommand('setContext', 'pytestembed.liveTestingEnabled', false);
    });

    liveSocket.on('error', (error) => {
        console.error('WebSocket error:', error);
        vscode.window.showErrorMessage('Failed to connect to PyTestEmbed server. Make sure it\'s running.');
    });
}

/**
 * Stop live testing
 */
export function stopLiveTesting() {
    if (liveSocket) {
        liveSocket.close();
        liveSocket = null;
        state.liveTestingEnabled = false;
        vscode.commands.executeCommand('setContext', 'pytestembed.liveTestingEnabled', false);
        vscode.window.showInformationMessage('Live testing stopped');
    }
}

/**
 * Send command to Python server
 */
function sendCommand(command: string, data?: any) {
    if (liveSocket && liveSocket.readyState === WebSocket.OPEN) {
        const message = { command, ...data };
        liveSocket.send(JSON.stringify(message));
        console.log(`📤 Sent command: ${command}`);
    }
}

/**
 * Handle messages from Python server
 */
function handleMessage(message: any) {
    switch (message.type) {
        case 'test_results':
            handleTestResults(message.data);
            break;
        case 'test_status_update':
            handleTestStatusUpdate(message.data);
            break;
        case 'dependency_info':
            handleDependencyInfo(message);
            break;
        case 'dependency_graph_updated':
            console.log(`🔗 Python server updated dependency graph for: ${message.data?.changed_file}`);
            break;
        case 'clear_dependency_cache':
            console.log(`🗑️ Python server cleared dependency cache for: ${message.data?.file_path}`);
            break;
        case 'debug_message':
            console.log(`🐛 ${message.message}`);
            break;
        default:
            console.log(`📨 Unknown message type: ${message.type}`);
    }
}

/**
 * Handle test results from Python server
 */
function handleTestResults(results: any) {
    let filePath = results.file_path;
    
    // Convert relative to absolute path
    if (!require('path').isAbsolute(filePath)) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            filePath = require('path').join(workspaceFolder.uri.fsPath, filePath);
        }
    }

    console.log(`📊 Handling test results for: ${filePath} (${results.tests?.length || 0} tests)`);
    
    // Store results
    const testResults: TestResult[] = (results.tests || []).map((test: any) => ({
        line: test.line_number - 1, // Convert to 0-based
        expression: test.assertion || test.test_name,
        status: test.status,
        message: test.message
    }));
    
    state.testResults.set(filePath, testResults);
    console.log(`💾 Saved ${testResults.length} test results for file`);
    
    // Update decorations if file is open
    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);
    if (editor) {
        refreshTestResultDecorations(filePath);
        console.log(`🎨 Refreshed decorations for open file`);
    }
}

/**
 * Handle individual test status updates
 */
function handleTestStatusUpdate(data: any) {
    let filePath = data.file_path;
    
    // Convert relative to absolute path
    if (!require('path').isAbsolute(filePath)) {
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (workspaceFolder) {
            filePath = require('path').join(workspaceFolder.uri.fsPath, filePath);
        }
    }

    console.log(`📊 Test status update: ${require('path').basename(filePath)}:${data.line_number} -> ${data.status}`);
    
    // Update individual test result
    const fileResults = state.testResults.get(filePath) || [];
    const testResult: TestResult = {
        line: data.line_number - 1, // Convert to 0-based
        expression: data.assertion || data.test_name,
        status: data.status,
        message: data.message
    };
    
    const existingIndex = fileResults.findIndex(r => r.line === testResult.line);
    if (existingIndex >= 0) {
        fileResults[existingIndex] = testResult;
    } else {
        fileResults.push(testResult);
    }
    
    state.testResults.set(filePath, fileResults);
    
    // Update decorations if file is open
    const editor = vscode.window.visibleTextEditors.find(e => e.document.fileName === filePath);
    if (editor) {
        refreshTestResultDecorations(filePath);
    }
}

/**
 * Handle dependency information (for hover tooltips)
 */
function handleDependencyInfo(data: any) {
    // Cache dependency info for hover tooltips
    if (data.element_id) {
        state.dependencyCache.set(data.element_id, data);
        console.log(`🔗 Cached dependency info for ${data.element_name}`);
    }
}

/**
 * Request dependency info for hover
 */
export function requestDependencyInfo(filePath: string, elementName: string, lineNumber: number) {
    sendCommand('get_dependencies', {
        file_path: filePath,
        element_name: elementName,
        line_number: lineNumber
    });
}

/**
 * Get cached dependency info
 */
export function getCachedDependencyInfo(elementId: string) {
    return state.dependencyCache.get(elementId);
}

/**
 * Request AI generation for test/doc blocks
 */
export function requestAIGeneration(uri: vscode.Uri, lineNumber: number, type: 'test' | 'doc' | 'both') {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const relativePath = vscode.workspace.asRelativePath(uri);

    sendCommand('generate_ai_blocks', {
        file_path: relativePath,
        line_number: lineNumber,
        block_type: type
    });

    vscode.window.showInformationMessage(`Generating ${type} blocks...`);
}

/**
 * Request AI enhancement for existing test/doc blocks
 */
export function requestAIEnhancement(uri: vscode.Uri, lineNumber: number, enhancementType: string) {
    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
    if (!workspaceFolder) {
        vscode.window.showErrorMessage('No workspace folder found');
        return;
    }

    const relativePath = vscode.workspace.asRelativePath(uri);

    sendCommand('enhance_ai_blocks', {
        file_path: relativePath,
        line_number: lineNumber,
        enhancement_type: enhancementType
    });

    const actionName = enhancementType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    vscode.window.showInformationMessage(`${actionName}...`);
}

/**
 * Start dependency service and connect to it
 */
export function startDependencyService() {
    // Start the dependency service via Python server
    sendCommand('start_dependency_service', {});

    // Try to connect to dependency service WebSocket
    connectToDependencyService();

    vscode.window.showInformationMessage('Starting dependency service...');
}

/**
 * Connect to dependency service WebSocket
 */
function connectToDependencyService() {
    try {
        const dependencyWs = new WebSocket('ws://localhost:8770');

        dependencyWs.on('open', () => {
            console.log('🔗 Connected to dependency service');
            vscode.window.showInformationMessage('Dependency service connected');

            // Update status bar
            vscode.commands.executeCommand('setContext', 'pytestembed.dependencyServiceEnabled', true);
        });

        dependencyWs.on('message', (data: WebSocket.Data) => {
            try {
                const message = JSON.parse(data.toString());
                handleDependencyMessage(message);
            } catch (error) {
                console.error('Error parsing dependency message:', error);
            }
        });

        dependencyWs.on('error', (error) => {
            console.error('Dependency service connection error:', error);
            vscode.window.showErrorMessage('Failed to connect to dependency service');
        });

        dependencyWs.on('close', () => {
            console.log('🔌 Dependency service disconnected');
            vscode.commands.executeCommand('setContext', 'pytestembed.dependencyServiceEnabled', false);
        });

    } catch (error) {
        console.error('Error connecting to dependency service:', error);
        vscode.window.showErrorMessage('Failed to start dependency service connection');
    }
}

/**
 * Handle messages from dependency service
 */
function handleDependencyMessage(message: any) {
    if (message.type === 'dependency_info') {
        // Cache dependency information
        const elementId = `${message.file_path}:${message.element_name}:${message.line_number}`;
        state.dependencyCache.set(elementId, message);
        console.log(`📦 Cached dependency info for ${elementId}`);
    }
}

/**
 * Request dependency info from dependency service (via live client)
 */
export function requestDependencyInfoViaLive(filePath: string, elementName: string, lineNumber: number) {
    // This will be used by the hover provider
    sendCommand('request_dependency_info', {
        file_path: filePath,
        element_name: elementName,
        line_number: lineNumber
    });
}
