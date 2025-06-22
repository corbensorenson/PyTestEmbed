/**
 * Global state management for PyTestEmbed VSCode Extension
 */

import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as WebSocket from 'ws';
import { ExtensionState, TestResult, DecorationTypes } from './types';

// Global extension state
export let state: ExtensionState = {
    // Block visibility
    testBlocksVisible: true,
    docBlocksVisible: true,
    
    // Live testing state
    liveTestingEnabled: false,
    liveTestSocket: null,
    liveTestProcess: null,

    // Dependency service state
    dependencyServiceEnabled: false,
    dependencyServiceProcess: null,

    // AI generation service state
    aiGenerationServiceEnabled: false,
    aiGenerationServiceProcess: null,

    // MCP server state
    mcpServerEnabled: false,
    mcpServerProcess: null,
    
    // Test results
    testResults: new Map(),
    currentTestProgress: { current: 0, total: 0 },

    // Dependency information cache
    dependencyCache: new Map(),
    
    // UI components (will be initialized in activate)
    outputChannel: null as any,
    diagnosticCollection: null as any,
    testProgressStatusBar: null as any,
    liveTestServerStatusBar: null as any,
    dependencyServiceStatusBar: null as any,
    aiGenerationServiceStatusBar: null as any,
    mcpServerStatusBar: null as any,
    serverStatusCheckInterval: undefined,
    documentChangeTimeout: undefined,
    
    // Panel state
    pyTestEmbedPanel: undefined,
    panelMessages: [],
    
    // Decorations
    testResultDecorations: new Map(),
    coverageDecorations: new Map(),
    testResultIconDecorations: [],
    hiddenBlockDecorations: new Map()
};

// Decoration types (global)
export let decorationTypes: DecorationTypes = {
    passIconDecorationType: null as any,
    failIconDecorationType: null as any,
    runningIconDecorationType: null as any,
    errorIconDecorationType: null as any,
    blockPassIconDecorationType: null as any,
    blockFailIconDecorationType: null as any,
    blockRunningIconDecorationType: null as any,
    blockErrorIconDecorationType: null as any
};

/**
 * Initialize the extension state
 */
export function initializeState(context: vscode.ExtensionContext) {
    // Create output channel
    state.outputChannel = vscode.window.createOutputChannel('PyTestEmbed');
    context.subscriptions.push(state.outputChannel);

    // Create test progress status bar item
    state.testProgressStatusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    state.testProgressStatusBar.text = '$(loading~spin) Tests: 0/0';
    state.testProgressStatusBar.tooltip = 'PyTestEmbed Test Progress';
    context.subscriptions.push(state.testProgressStatusBar);

    // Create diagnostic collection for Problems integration
    state.diagnosticCollection = vscode.languages.createDiagnosticCollection('pytestembed');
    context.subscriptions.push(state.diagnosticCollection);
}

/**
 * Get current test results for a file
 */
export function getTestResults(filePath: string): TestResult[] {
    return state.testResults.get(filePath) || [];
}

/**
 * Set test results for a file
 */
export function setTestResults(filePath: string, results: TestResult[]) {
    state.testResults.set(filePath, results);
}

/**
 * Clear test results for a file
 */
export function clearTestResults(filePath: string) {
    state.testResults.delete(filePath);
}

/**
 * Update test progress
 */
export function updateTestProgress(current: number, total: number) {
    state.currentTestProgress = { current, total };
    
    if (total > 0) {
        const percentage = Math.round((current / total) * 100);
        state.testProgressStatusBar.text = `$(testing) Tests: ${current}/${total} (${percentage}%)`;
        state.testProgressStatusBar.show();
    } else {
        state.testProgressStatusBar.hide();
    }
}

/**
 * Add a message to the panel
 */
export function addPanelMessage(text: string, type: 'info' | 'success' | 'warning' | 'error') {
    const timestamp = new Date().toLocaleTimeString();
    const message = `[${timestamp}] ${text}`;
    state.panelMessages.push(message);
    
    // Keep only last 100 messages
    if (state.panelMessages.length > 100) {
        state.panelMessages = state.panelMessages.slice(-100);
    }
    
    // Update panel if it exists
    if (state.pyTestEmbedPanel) {
        state.pyTestEmbedPanel.webview.postMessage({
            type: 'addMessage',
            message: message,
            messageType: type
        });
    }
}

/**
 * Clear all panel messages
 */
export function clearPanelMessages() {
    state.panelMessages = [];
    if (state.pyTestEmbedPanel) {
        state.pyTestEmbedPanel.webview.postMessage({
            type: 'clearMessages'
        });
    }
}

/**
 * Clean up state on deactivation
 */
export function cleanupState() {
    // Clear intervals
    if (state.serverStatusCheckInterval) {
        clearInterval(state.serverStatusCheckInterval);
    }
    
    // Close connections
    if (state.liveTestSocket) {
        state.liveTestSocket.close();
    }
    
    if (state.liveTestProcess) {
        state.liveTestProcess.kill();
    }
    
    if (state.mcpServerProcess) {
        state.mcpServerProcess.kill();
    }
    
    // Clear decorations
    state.testResultDecorations.forEach(decoration => decoration.dispose());
    state.coverageDecorations.forEach(decoration => decoration.dispose());
    state.testResultIconDecorations.forEach(decoration => decoration.dispose());
}
