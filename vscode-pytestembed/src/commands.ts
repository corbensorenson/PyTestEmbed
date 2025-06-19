/**
 * Command registration and handlers for PyTestEmbed VSCode Extension
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { state } from './state';
import { startLiveTesting, stopLiveTesting, runIndividualTest } from './liveTesting';
import { runTestAtCursor, showTestResultsPanel } from './testResults';
import { startMcpServer, stopMcpServer } from './mcpServer';
import { toggleBlockFolding } from './folding';
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

    // Navigation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.navigateToDefinition', (args: string) => {
            navigateToDefinition(args);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.navigateToElement', (...allArgs: any[]) => {
            console.log('🔗🔗🔗 NAVIGATION COMMAND CALLED! 🔗🔗🔗');
            console.log('🔗 RAW COMMAND ARGS - Length:', allArgs.length);
            console.log('🔗 RAW COMMAND ARGS - Full array:', allArgs);

            for (let i = 0; i < allArgs.length; i++) {
                console.log(`🔗 Arg[${i}]:`, allArgs[i], 'type:', typeof allArgs[i]);
                if (typeof allArgs[i] === 'string') {
                    console.log(`🔗 Arg[${i}] as string:`, JSON.stringify(allArgs[i]));
                }
            }

            // Try different approaches to extract the arguments
            let navigationArgs: any = null;

            if (allArgs.length === 0) {
                console.log('❌ No arguments passed');
                vscode.window.showErrorMessage('No navigation arguments provided');
                return;
            }

            const firstArg = allArgs[0];
            console.log('🔗 Processing first arg:', firstArg, 'type:', typeof firstArg);

            if (typeof firstArg === 'string') {
                console.log('🔗 Attempting to parse string argument...');
                try {
                    navigationArgs = JSON.parse(firstArg);
                    console.log('🔗 Successfully parsed string to object:', navigationArgs);
                } catch (error) {
                    console.log('❌ Failed to parse string as JSON:', error);
                    console.log('❌ Raw string was:', JSON.stringify(firstArg));
                    vscode.window.showErrorMessage(`Failed to parse navigation arguments: ${error}`);
                    return;
                }
            } else if (Array.isArray(firstArg)) {
                console.log('🔗 First arg is array, using first element...');
                navigationArgs = firstArg[0];
                console.log('🔗 Extracted from array:', navigationArgs);
            } else if (firstArg && typeof firstArg === 'object') {
                console.log('🔗 First arg is object, using directly...');
                navigationArgs = firstArg;
            } else {
                console.log('❌ Unrecognized argument format');
                vscode.window.showErrorMessage(`Unrecognized navigation argument format: ${typeof firstArg}`);
                return;
            }

            console.log('🔗 Final navigation args:', navigationArgs);
            console.log('🔗 file_path:', navigationArgs?.file_path);
            console.log('🔗 line_number:', navigationArgs?.line_number);

            if (!navigationArgs || !navigationArgs.file_path || !navigationArgs.line_number) {
                console.log('❌ Missing required properties in navigation args');
                vscode.window.showErrorMessage('Navigation arguments missing file_path or line_number');
                return;
            }

            navigateToElement(navigationArgs);
        })
    );

    // Test command for debugging navigation
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.testNavigation', () => {
            console.log('🧪 Testing navigation...');
            navigateToElement({file_path: 'test.py', line_number: 10});
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
async function toggleBlocksOfType(blockType: 'test' | 'doc', visible: boolean) {
    await toggleBlockFolding(blockType, !visible); // visible=true means unfold, visible=false means fold
    vscode.window.showInformationMessage(`${visible ? 'Showing' : 'Hiding'} ${blockType} blocks`);
}

/**
 * Show all blocks
 */
async function showAllBlocks() {
    // REMOVED - Will be implemented in separate folding.ts file
    vscode.window.showInformationMessage(`Folding logic temporarily disabled - being reimplemented`);
}

/**
 * Hide all blocks
 */
async function hideAllBlocks() {
    // REMOVED - Will be implemented in separate folding.ts file
    vscode.window.showInformationMessage(`Folding logic temporarily disabled - being reimplemented`);
}

/**
 * Collapse blocks of a specific type using VSCode's folding
 */
// REMOVED - All folding logic moved to folding.ts

/**
 * Expand blocks of a specific type using VSCode's folding
 */
// REMOVED - All folding logic moved to folding.ts

/**
 * Fold blocks of a specific type
 */
function foldBlocksOfType(blockType: 'test' | 'doc') {
    // REMOVED - Will be implemented in separate folding.ts file
    vscode.window.showInformationMessage(`Folding logic temporarily disabled - being reimplemented`);
}

/**
 * Configure PyTestEmbed linter
 */
function configurePyTestEmbedLinter() {
    vscode.window.showInformationMessage('Linter configuration feature coming soon!');
}

/**
 * Navigate to a definition based on dependency information
 */
async function navigateToDefinition(args: string) {
    try {
        const { file, name } = JSON.parse(args);

        // Find the workspace folder
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        // Construct the full file path
        const fullPath = path.join(workspaceFolder.uri.fsPath, file);
        const fileUri = vscode.Uri.file(fullPath);

        try {
            // Open the file and navigate to the definition
            const document = await vscode.workspace.openTextDocument(fileUri);
            const editor = await vscode.window.showTextDocument(document);

            // Search for the definition in the file
            const text = document.getText();
            const lines = text.split('\n');

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const trimmed = line.trim();

                // Look for function or class definitions
                if ((trimmed.startsWith(`def ${name}(`) ||
                     trimmed.startsWith(`class ${name}(`)) &&
                    trimmed.endsWith(':')) {

                    const position = new vscode.Position(i, line.indexOf(name));
                    editor.selection = new vscode.Selection(position, position);
                    editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);
                    return;
                }
            }

            // If not found, just show the file
            vscode.window.showInformationMessage(`Definition of '${name}' not found in ${file}`);
        } catch (error) {
            vscode.window.showErrorMessage(`Could not open file: ${file}`);
        }
    } catch (error) {
        vscode.window.showErrorMessage('Invalid navigation arguments');
    }
}

/**
 * Navigate to a specific element (for hover provider)
 */
async function navigateToElement(args: any) {
    try {
        console.log('🔗 navigateToElement called with args:', args, 'type:', typeof args);

        // Handle different argument formats
        let file_path: string, line_number: number;

        if (Array.isArray(args) && args.length > 0) {
            // Array format: [{file_path: "...", line_number: 123}]
            ({ file_path, line_number } = args[0]);
        } else if (args && typeof args === 'object' && args.file_path) {
            // Object format: {file_path: "...", line_number: 123}
            ({ file_path, line_number } = args);
        } else {
            console.log('❌ Invalid arguments format');
            vscode.window.showErrorMessage('Invalid navigation arguments format');
            return;
        }

        console.log(`🔗 Parsed: file_path=${file_path}, line_number=${line_number}`);

        // Find the workspace folder
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        // Construct the full file path
        const fullPath = path.join(workspaceFolder.uri.fsPath, file_path);
        const fileUri = vscode.Uri.file(fullPath);

        try {
            // Open the file and navigate to the line
            const document = await vscode.workspace.openTextDocument(fileUri);
            const editor = await vscode.window.showTextDocument(document);

            // Navigate to the specific line
            const position = new vscode.Position(line_number - 1, 0); // Convert to 0-based
            editor.selection = new vscode.Selection(position, position);
            editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);

        } catch (error) {
            vscode.window.showErrorMessage(`Could not open file: ${file_path}`);
        }

    } catch (error) {
        vscode.window.showErrorMessage('Invalid navigation arguments');
    }
}

/**
 * Update status bar
 */
function updateStatusBar() {
    // Implementation for updating status bar based on current state
}
