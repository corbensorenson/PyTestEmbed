import * as vscode from 'vscode';
import { initializeState, state, cleanupState } from './state';
import { initializeTestResultDecorations, disposeTestResultDecorations, refreshTestResultDecorations } from './decorations';
import { registerCommands } from './commands';
import { registerProviders } from './providers';
import { registerFoldingProvider } from './folding';
import { PyTestEmbedHoverProvider } from './hoverProvider';
import { createStatusBarIndicators, disposeStatusBar } from './statusBar';
import { startLiveTesting, stopLiveTesting } from './liveClient';

/**
 * Minimal PyTestEmbed VSCode Extension - Pure Display Client
 */

export function activate(context: vscode.ExtensionContext) {
    console.log('🚀 PyTestEmbed extension activated - smart display client');

    // Show activation message to confirm extension is loading
    vscode.window.showInformationMessage('PyTestEmbed extension activated!');

    // Initialize state and UI
    initializeState(context);
    initializeTestResultDecorations();
    createStatusBarIndicators(context);

    // Register all functionality
    registerCommands(context);
    registerProviders(context);
    registerFoldingProvider(context);

    // Register hover provider for dependency information
    const hoverProvider = new PyTestEmbedHoverProvider();
    context.subscriptions.push(
        vscode.languages.registerHoverProvider(
            { scheme: 'file', language: 'python' },
            hoverProvider
        )
    );

    // Refresh decorations when files are opened
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor && state.liveTestingEnabled && editor.document.languageId === 'python') {
                refreshTestResultDecorations(editor.document.fileName);
            }
        })
    );
}

export function deactivate() {
    console.log('🛑 PyTestEmbed extension deactivated');

    // Stop live testing
    stopLiveTesting();

    // Clean up
    disposeTestResultDecorations();
    disposeStatusBar();
    cleanupState();
}
