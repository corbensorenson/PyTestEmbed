/**
 * Command registration and handlers for PyTestEmbed VSCode Extension
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { state } from './state';
import { startLiveTesting, stopLiveTesting, runIndividualTest } from './liveTesting';
import { runTestAtCursor, showTestResultsPanel } from './testResults';
import { startMcpServer, stopMcpServer } from './mcpServer';
import { openPyTestEmbedPanel } from './panel';
import { BlockType } from './types';

/**
 * Register all PyTestEmbed commands
 */
export function registerCommands(context: vscode.ExtensionContext) {
    // Toggle commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleTestBlocks', () => {
            state.testBlocksVisible = !state.testBlocksVisible;
            toggleBlocksOfType('test', state.testBlocksVisible);
            updateStatusBar();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleDocBlocks', () => {
            state.docBlocksVisible = !state.docBlocksVisible;
            toggleBlocksOfType('doc', state.docBlocksVisible);
            updateStatusBar();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.showAllBlocks', () => {
            state.testBlocksVisible = true;
            state.docBlocksVisible = true;
            showAllBlocks();
            updateStatusBar();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.hideAllBlocks', () => {
            state.testBlocksVisible = false;
            state.docBlocksVisible = false;
            hideAllBlocks();
            updateStatusBar();
        })
    );

    // Execution commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.runTests', () => {
            runPyTestEmbedCommand('--test');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateDocs', () => {
            runPyTestEmbedCommand('--doc');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.runWithoutBlocks', () => {
            runPythonWithoutBlocks();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.runIgnoringTests', () => {
            runPythonFileIgnoringTests();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.openOutputPanel', () => {
            state.outputChannel.show();
        })
    );

    // Live testing commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.startLiveTesting', () => {
            startLiveTesting();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.stopLiveTesting', () => {
            stopLiveTesting();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleLiveTesting', () => {
            if (state.liveTestingEnabled) {
                stopLiveTesting();
            } else {
                startLiveTesting();
            }
        })
    );

    // Test execution commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.runTestAtCursor', () => {
            runTestAtCursor();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.runIndividualTest', (filePath: string, lineNumber: number) => {
            runIndividualTest(filePath, lineNumber);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.showTestResults', () => {
            showTestResultsPanel();
        })
    );

    // MCP server commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.startMcpServer', () => {
            startMcpServer();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.stopMcpServer', () => {
            stopMcpServer();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleMcpServer', () => {
            if (state.mcpServerEnabled) {
                stopMcpServer();
            } else {
                startMcpServer();
            }
        })
    );

    // Smart generation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateBlocks', () => {
            generateSmartBlocks('both');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateTestsOnly', () => {
            generateSmartBlocks('test');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateDocsOnly', () => {
            generateSmartBlocks('doc');
        })
    );

    // Quick Actions commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateBlocksAtLine', (uri: vscode.Uri, lineNumber: number, type: BlockType) => {
            generateBlocksAtLine(uri, lineNumber, type);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.quickFixFunction', (uri: vscode.Uri, lineNumber: number) => {
            quickFixFunction(uri, lineNumber);
        })
    );

    // Legacy commands for backward compatibility
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.foldTestBlocks', () => {
            foldBlocksOfType('test');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.foldDocBlocks', () => {
            foldBlocksOfType('doc');
        })
    );

    // PyTestEmbed panel commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.openPanel', () => {
            openPyTestEmbedPanel(context);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.clearPanelMessages', () => {
            import('./state').then(({ clearPanelMessages }) => {
                clearPanelMessages();
            });
        })
    );

    // PyTestEmbed-specific commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.configureLinter', () => {
            configurePyTestEmbedLinter();
        })
    );
}

/**
 * Run PyTestEmbed command with specified arguments
 */
function runPyTestEmbedCommand(args: string) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const terminal = vscode.window.createTerminal('PyTestEmbed');
    terminal.sendText(`pytestembed ${args} "${editor.document.fileName}"`);
    terminal.show();
}

/**
 * Run Python file ignoring test and doc blocks
 */
function runPythonFileIgnoringTests() {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        vscode.window.showErrorMessage('Please open a Python file');
        return;
    }

    const filePath = editor.document.fileName;
    const terminal = vscode.window.createTerminal('PyTestEmbed Run');
    terminal.sendText(`python "${filePath}"`);
    terminal.show();
    
    import('./state').then(({ addPanelMessage }) => {
        addPanelMessage(`Running Python file: ${path.basename(filePath)}`, 'info');
    });
}

/**
 * Run Python without PyTestEmbed blocks
 */
function runPythonWithoutBlocks() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const terminal = vscode.window.createTerminal('PyTestEmbed');
    terminal.sendText(`pytestembed --run "${editor.document.fileName}"`);
    terminal.show();
}

/**
 * Generate smart blocks
 */
function generateSmartBlocks(type: BlockType) {
    vscode.window.showInformationMessage(`Generating ${type} blocks...`);
    // Implementation would call AI generation service
}

/**
 * Generate blocks at a specific line
 */
function generateBlocksAtLine(uri: vscode.Uri, lineNumber: number, type: BlockType) {
    vscode.window.showTextDocument(uri).then(editor => {
        // Position cursor at the specified line
        const position = new vscode.Position(lineNumber - 1, 0);
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(new vscode.Range(position, position));

        // Generate blocks
        generateSmartBlocks(type);
    });
}

/**
 * Quick Fix function - analyze and fix function issues
 */
function quickFixFunction(uri: vscode.Uri, lineNumber: number) {
    vscode.window.showTextDocument(uri).then(editor => {
        // Position cursor at the specified line
        const position = new vscode.Position(lineNumber - 1, 0);
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(new vscode.Range(position, position));

        // For now, show a message - this could be enhanced to analyze the function
        vscode.window.showInformationMessage(
            'Quick Fix: Analyzing function for potential improvements...',
            'Analyze Code', 'Fix Syntax', 'Optimize Performance'
        ).then(choice => {
            if (choice === 'Analyze Code') {
                vscode.window.showInformationMessage('Code analysis feature coming soon!');
            } else if (choice === 'Fix Syntax') {
                vscode.window.showInformationMessage('Syntax fixing feature coming soon!');
            } else if (choice === 'Optimize Performance') {
                vscode.window.showInformationMessage('Performance optimization feature coming soon!');
            }
        });
    });
}

/**
 * Toggle blocks of a specific type
 */
function toggleBlocksOfType(blockType: 'test' | 'doc', visible: boolean) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }

    if (visible) {
        showBlocksOfType(editor, blockType);
    } else {
        hideBlocksOfType(editor, blockType);
    }

    vscode.window.showInformationMessage(`${visible ? 'Showing' : 'Hiding'} ${blockType} blocks`);
}

/**
 * Show all blocks
 */
function showAllBlocks() {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }

    showBlocksOfType(editor, 'test');
    showBlocksOfType(editor, 'doc');
    vscode.window.showInformationMessage('Showing all blocks');
}

/**
 * Hide all blocks
 */
function hideAllBlocks() {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }

    hideBlocksOfType(editor, 'test');
    hideBlocksOfType(editor, 'doc');
    vscode.window.showInformationMessage('Hiding all blocks');
}

/**
 * Collapse blocks of a specific type using VSCode's folding
 */
function hideBlocksOfType(editor: vscode.TextEditor, blockType: 'test' | 'doc') {
    const document = editor.document;
    const foldingRanges: vscode.FoldingRange[] = [];

    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        if (line.text.trim() === `${blockType}:`) {
            // Find the end of this block
            const baseIndent = line.firstNonWhitespaceCharacterIndex;
            let endLine = i;

            for (let j = i + 1; j < document.lineCount; j++) {
                const nextLine = document.lineAt(j);
                const trimmedText = nextLine.text.trim();

                if (trimmedText === '') {
                    continue; // Skip empty lines
                }

                const currentIndent = nextLine.firstNonWhitespaceCharacterIndex;
                if (currentIndent <= baseIndent) {
                    break; // End of block
                }

                endLine = j;
            }

            // Create folding range for this block
            if (endLine > i) {
                foldingRanges.push(new vscode.FoldingRange(i, endLine));
            }
        }
    }

    // Apply folding to these ranges
    if (foldingRanges.length > 0) {
        vscode.commands.executeCommand('editor.fold', {
            levels: 1,
            direction: 'down',
            selectionLines: foldingRanges.map(range => range.start)
        });
    }
}

/**
 * Expand blocks of a specific type using VSCode's folding
 */
function showBlocksOfType(editor: vscode.TextEditor, blockType: 'test' | 'doc') {
    const document = editor.document;
    const unfoldingRanges: number[] = [];

    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        if (line.text.trim() === `${blockType}:`) {
            unfoldingRanges.push(i);
        }
    }

    // Apply unfolding to these ranges
    if (unfoldingRanges.length > 0) {
        vscode.commands.executeCommand('editor.unfold', {
            levels: 1,
            direction: 'down',
            selectionLines: unfoldingRanges
        });
    }
}

/**
 * Fold blocks of a specific type
 */
function foldBlocksOfType(blockType: 'test' | 'doc') {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }

    // Use VSCode's built-in folding for this
    vscode.commands.executeCommand('editor.foldAll');
    vscode.window.showInformationMessage(`Folding ${blockType} blocks`);
}

/**
 * Configure PyTestEmbed linter
 */
function configurePyTestEmbedLinter() {
    vscode.window.showInformationMessage('Linter configuration feature coming soon!');
}

/**
 * Update status bar
 */
function updateStatusBar() {
    // Implementation for updating status bar based on current state
}
