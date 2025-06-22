/**
 * Command registration and handlers for PyTestEmbed VSCode Extension
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { state } from './state';
import { startLiveTesting, stopLiveTesting, runIndividualTest } from './liveTesting';
import { runTestAtCursor, showTestResultsPanel } from './testResults';
import { startDependencyService, stopDependencyService } from './dependencyService';
import { startMcpServer, stopMcpServer } from './mcpServer';
import { toggleBlockFolding, foldFunctionWithBlocks } from './folding';
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

    // Dependency service commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.startDependencyService', () => {
            startDependencyService();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.stopDependencyService', () => {
            stopDependencyService();
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
        vscode.commands.registerCommand('pytestembed.toggleDependencyService', () => {
            if (state.dependencyServiceEnabled) {
                stopDependencyService();
            } else {
                startDependencyService();
            }
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

    // Navigate to element in split view
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.navigateToElementSplit', (...allArgs: any[]) => {
            console.log('🔗📱 SPLIT NAVIGATION COMMAND CALLED! 🔗📱');
            console.log('🔗 RAW COMMAND ARGS - Length:', allArgs.length);
            console.log('🔗 RAW COMMAND ARGS - Full array:', allArgs);

            // Use the same argument parsing logic as the regular navigation
            let navigationArgs: any = null;

            if (allArgs.length === 0) {
                console.log('❌ No arguments passed');
                vscode.window.showErrorMessage('No navigation arguments provided');
                return;
            }

            // Try different approaches to extract the arguments
            if (allArgs.length === 1) {
                const firstArg = allArgs[0];
                if (typeof firstArg === 'string') {
                    try {
                        navigationArgs = JSON.parse(firstArg);
                    } catch (e) {
                        console.log('❌ Failed to parse string argument as JSON');
                    }
                } else if (typeof firstArg === 'object') {
                    navigationArgs = firstArg;
                }
            }

            console.log('🔗 Final navigation args:', navigationArgs);

            if (!navigationArgs || !navigationArgs.file_path || !navigationArgs.line_number) {
                console.log('❌ Missing required properties in navigation args');
                vscode.window.showErrorMessage('Navigation arguments missing file_path or line_number');
                return;
            }

            navigateToElementSplit(navigationArgs);
        })
    );

    // Smart folding command
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.foldFunctionWithBlocks', () => {
            const editor = vscode.window.activeTextEditor;
            if (editor) {
                const lineNumber = editor.selection.active.line;
                foldFunctionWithBlocks(lineNumber);
            }
        })
    );

    // Toggle double-click navigation command
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleDoubleClickNavigation', () => {
            const config = vscode.workspace.getConfiguration('pytestembed');
            const currentValue = config.get<boolean>('doubleClickNavigation', true);
            config.update('doubleClickNavigation', !currentValue, vscode.ConfigurationTarget.Global);

            const status = !currentValue ? 'enabled' : 'disabled';
            vscode.window.showInformationMessage(`Double-click navigation ${status}`);
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
 * Generate smart blocks using Python AI service
 */
async function generateSmartBlocks(type: BlockType) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }

    const document = editor.document;
    const position = editor.selection.active;
    const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);

    if (!workspaceFolder) {
        vscode.window.showErrorMessage('File must be in a workspace');
        return;
    }

    const relativePath = require('path').relative(workspaceFolder.uri.fsPath, document.fileName);

    try {
        // Connect to AI service
        const WebSocket = require('ws');
        const ws = new WebSocket('ws://localhost:8771');

        ws.on('open', () => {
            const command = type === 'test' ? 'generate_test_block' :
                           type === 'doc' ? 'generate_doc_block' : 'generate_both_blocks';

            const request = {
                command: command,
                file_path: relativePath,
                line_number: position.line + 1  // Convert to 1-based
            };

            ws.send(JSON.stringify(request));
            vscode.window.showInformationMessage(`🤖 Generating ${type} blocks using AI...`);
        });

        ws.on('message', (data: string) => {
            const response = JSON.parse(data);

            if (response.success) {
                // Insert the generated content
                const insertPosition = new vscode.Position(position.line + 1, 0);
                editor.edit(editBuilder => {
                    editBuilder.insert(insertPosition, response.content + '\n');
                });

                const provider = response.provider_used || 'AI';
                const fallbackMsg = response.fallback_used ? ' (fallback)' : '';
                vscode.window.showInformationMessage(`✅ ${type} blocks generated using ${provider}${fallbackMsg}`);
            } else {
                vscode.window.showErrorMessage(`❌ Failed to generate ${type} blocks: ${response.error}`);
            }

            ws.close();
        });

        ws.on('error', (error: any) => {
            vscode.window.showErrorMessage(`❌ AI service connection failed: ${error.message}`);
        });

    } catch (error) {
        vscode.window.showErrorMessage(`❌ Error connecting to AI service: ${error}`);
    }
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
    await toggleBlockFolding('test', false); // false = unfold
    await toggleBlockFolding('doc', false);  // false = unfold
    vscode.window.showInformationMessage('Showing all blocks');
}

/**
 * Hide all blocks
 */
async function hideAllBlocks() {
    await toggleBlockFolding('test', true);  // true = fold
    await toggleBlockFolding('doc', true);   // true = fold
    vscode.window.showInformationMessage('Hiding all blocks');
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

        console.log(`🔗 Parsed: file_path=${file_path}, line_number=${line_number} (type: ${typeof line_number})`);

        // Ensure line_number is a number
        const lineNum = typeof line_number === 'string' ? parseInt(line_number, 10) : line_number;
        console.log(`🔗 Converted line number: ${lineNum}`);

        // Find the workspace folder
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        // Construct the full file path - handle both relative and absolute paths
        let fullPath: string;
        if (path.isAbsolute(file_path)) {
            fullPath = file_path;
        } else {
            // Try the file path as-is first
            fullPath = path.join(workspaceFolder.uri.fsPath, file_path);

            // If that doesn't exist, try looking in common directories
            if (!require('fs').existsSync(fullPath)) {
                const possiblePaths = [
                    path.join(workspaceFolder.uri.fsPath, 'testProject', file_path),
                    path.join(workspaceFolder.uri.fsPath, 'src', file_path),
                    path.join(workspaceFolder.uri.fsPath, file_path)
                ];

                for (const possiblePath of possiblePaths) {
                    if (require('fs').existsSync(possiblePath)) {
                        fullPath = possiblePath;
                        break;
                    }
                }
            }
        }

        const fileUri = vscode.Uri.file(fullPath);

        try {
            // Open the file and navigate to the line
            const document = await vscode.workspace.openTextDocument(fileUri);
            const editor = await vscode.window.showTextDocument(document);

            // Navigate to the specific line
            const position = new vscode.Position(lineNum - 1, 0); // Convert to 0-based
            console.log(`🔗 Navigating to position: line ${lineNum - 1} (0-based), column 0`);
            editor.selection = new vscode.Selection(position, position);
            editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);

        } catch (error) {
            console.error(`Navigation error for ${file_path}:`, error);
            vscode.window.showErrorMessage(`Could not open file: ${file_path} (tried: ${fullPath})`);
        }

    } catch (error) {
        vscode.window.showErrorMessage('Invalid navigation arguments');
    }
}

/**
 * Navigate to a specific element in split view (for hover provider)
 */
async function navigateToElementSplit(args: any) {
    try {
        console.log('🔗📱 navigateToElementSplit called with args:', args, 'type:', typeof args);

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

        console.log('🔗📱 Navigating to split view:', file_path, 'line:', line_number, '(type:', typeof line_number, ')');

        // Ensure line_number is a number
        const lineNum = typeof line_number === 'string' ? parseInt(line_number, 10) : line_number;
        console.log(`🔗📱 Converted line number: ${lineNum}`);

        // Find the workspace folder
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        // Construct the full file path - handle both relative and absolute paths
        let fullPath: string;
        if (path.isAbsolute(file_path)) {
            fullPath = file_path;
        } else {
            // Try the file path as-is first
            fullPath = path.join(workspaceFolder.uri.fsPath, file_path);

            // If that doesn't exist, try looking in common directories
            if (!require('fs').existsSync(fullPath)) {
                const possiblePaths = [
                    path.join(workspaceFolder.uri.fsPath, 'testProject', file_path),
                    path.join(workspaceFolder.uri.fsPath, 'src', file_path),
                    path.join(workspaceFolder.uri.fsPath, file_path)
                ];

                for (const possiblePath of possiblePaths) {
                    if (require('fs').existsSync(possiblePath)) {
                        fullPath = possiblePath;
                        break;
                    }
                }
            }
        }

        const fileUri = vscode.Uri.file(fullPath);

        try {
            // Open the file in split view and navigate to the line
            const document = await vscode.workspace.openTextDocument(fileUri);
            const editor = await vscode.window.showTextDocument(document, vscode.ViewColumn.Beside);

            // Navigate to the specific line
            const position = new vscode.Position(lineNum - 1, 0); // Convert to 0-based
            console.log(`🔗📱 Navigating to position: line ${lineNum - 1} (0-based), column 0`);
            editor.selection = new vscode.Selection(position, position);
            editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);

        } catch (error) {
            console.error(`Split view navigation error for ${file_path}:`, error);
            vscode.window.showErrorMessage(`Could not open file in split view: ${file_path} (tried: ${fullPath})`);
        }

    } catch (error) {
        vscode.window.showErrorMessage('Invalid navigation arguments for split view');
    }
}

/**
 * Update status bar
 */
function updateStatusBar() {
    // Implementation for updating status bar based on current state
}
