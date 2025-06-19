import * as vscode from 'vscode';
import * as WebSocket from 'ws';
import { initializeState, state, cleanupState } from './state';
import { initializeTestResultDecorations, disposeTestResultDecorations, refreshTestResultDecorations } from './decorations';
import { registerCommands } from './commands';
import { markAllTestsAsFailing, markAllTestsAsUntested, markAllTestsAsRunning } from './testResults';
import { stopMcpServer } from './mcpServer';
import { registerHoverProvider } from './hoverProvider';
import { createServerStatusIndicators } from './statusBar';
import { registerProviders } from './providers';
import { registerFoldingProvider } from './folding';

/**
 * PyTestEmbed VSCode Extension
 *
 * Provides syntax highlighting, code folding, linting integration,
 * and comprehensive UI controls for PyTestEmbed embedded test and documentation blocks.
 */

/**
 * Register double-click handler for opening definitions in split editor
 */
function registerDoubleClickHandler(context: vscode.ExtensionContext) {
    let lastClickTime = 0;
    let lastClickPosition: vscode.Position | undefined;
    const doubleClickThreshold = 500; // milliseconds

    const clickHandler = vscode.window.onDidChangeTextEditorSelection(async (event) => {
        if (!event.textEditor || event.textEditor.document.languageId !== 'python') {
            return;
        }

        const currentTime = Date.now();
        const selection = event.selections[0];

        // Check if this is a potential double-click (same position, within time threshold)
        if (lastClickPosition &&
            selection.start.isEqual(lastClickPosition) &&
            currentTime - lastClickTime < doubleClickThreshold) {

            // This is a double-click, try to open definition in split editor
            await openDefinitionInSplitEditor(event.textEditor, selection.start);
        }

        lastClickTime = currentTime;
        lastClickPosition = selection.start;
    });

    context.subscriptions.push(clickHandler);
}

/**
 * Open the definition of the symbol at the given position in a split editor
 */
async function openDefinitionInSplitEditor(editor: vscode.TextEditor, position: vscode.Position) {
    try {
        // Get the word at the cursor position
        const wordRange = editor.document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return;
        }

        const word = editor.document.getText(wordRange);
        console.log(`🔍 Double-clicked on: ${word}`);

        // Use VSCode's built-in "Go to Definition" command to find the definition
        const definitions = await vscode.commands.executeCommand<vscode.Location[]>(
            'vscode.executeDefinitionProvider',
            editor.document.uri,
            position
        );

        if (definitions && definitions.length > 0) {
            const definition = definitions[0];
            console.log(`📍 Found definition at: ${definition.uri.fsPath}:${definition.range.start.line + 1}`);

            // Open the definition file in a split editor to the right
            const document = await vscode.workspace.openTextDocument(definition.uri);
            const splitEditor = await vscode.window.showTextDocument(document, {
                viewColumn: vscode.ViewColumn.Beside, // Open in split editor to the right
                selection: definition.range,
                preserveFocus: false
            });

            // Reveal the definition line
            splitEditor.revealRange(definition.range, vscode.TextEditorRevealType.InCenter);

            console.log(`✅ Opened ${word} definition in split editor`);
        } else {
            console.log(`❌ No definition found for: ${word}`);
        }
    } catch (error) {
        console.error(`❌ Error opening definition in split editor:`, error);
    }
}

export function activate(context: vscode.ExtensionContext) {
    console.log('PyTestEmbed extension is now active!');

    // Initialize extension state
    initializeState(context);

    // Initialize test result decorations
    initializeTestResultDecorations();

    // Create server status indicators
    createServerStatusIndicators(context);

    // Register providers (disabled - using new hover provider instead)
    // registerProviders(context);

    // Register hover provider for dependency tooltips
    registerHoverProvider(context);

    // Register folding provider for test: and doc: blocks
    registerFoldingProvider(context);

    // Register double-click handler for opening definitions in split editor
    registerDoubleClickHandler(context);

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
