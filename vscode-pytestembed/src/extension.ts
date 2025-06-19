import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import { initializeState, state, cleanupState } from './state';
import { initializeTestResultDecorations, disposeTestResultDecorations, refreshTestResultDecorations } from './decorations';
import { registerCommands } from './commands';
import { markAllTestsAsFailing, markAllTestsAsUntested, markAllTestsAsRunning } from './testResults';
import { stopMcpServer } from './mcpServer';
import { createServerStatusIndicators } from './statusBar';
import { registerProviders } from './providers';

/**
 * PyTestEmbed VSCode Extension
 *
 * Provides syntax highlighting, code folding, linting integration,
 * and comprehensive UI controls for PyTestEmbed embedded test and documentation blocks.
 */

export function activate(context: vscode.ExtensionContext) {
    console.log('PyTestEmbed extension is now active!');

    // Initialize extension state
    initializeState(context);

    // Initialize test result decorations
    initializeTestResultDecorations();

    // Create server status indicators
    createServerStatusIndicators(context);

    // Register providers
    registerProviders(context);

    // Register all commands
    registerCommands(context);

    // Register event listeners for test result decorations
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor && state.liveTestingEnabled) {
                // Mark all tests as failing initially if no results exist
                if (!state.testResults.has(editor.document.fileName)) {
                    markAllTestsAsFailing(editor.document.fileName);
                }
                refreshTestResultDecorations(editor.document.fileName);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument(document => {
            if (document.languageId === 'python' && state.liveTestingEnabled) {
                const filePath = document.fileName;
                const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);

                if (workspaceFolder) {
                    const relativePath = require('path').relative(workspaceFolder.uri.fsPath, filePath);

                    // Trigger intelligent test selection based on what changed
                    if (state.liveTestSocket && state.liveTestSocket.readyState === WebSocket.OPEN) {
                        const testRequest = {
                            command: 'run_intelligent_tests',
                            file_path: relativePath
                        };
                        state.liveTestSocket.send(JSON.stringify(testRequest));
                        console.log(`🧠 Triggered intelligent test selection for: ${relativePath}`);
                    }
                }
            }
        })
    );
}

export function deactivate() {
    console.log('PyTestEmbed extension is now deactivated.');

    // Clean up decorations
    disposeTestResultDecorations();

    // Stop MCP server if running
    if (state.mcpServerEnabled) {
        stopMcpServer();
    }

    // Clean up all state
    cleanupState();
}
