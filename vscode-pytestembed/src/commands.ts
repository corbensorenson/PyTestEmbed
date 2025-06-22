/**
 * Commands for PyTestEmbed VSCode Extension
 */

import * as vscode from 'vscode';
import { startLiveTesting, stopLiveTesting, requestAIGeneration, requestAIEnhancement, startDependencyService } from './liveClient';
import { updateLiveTestStatus, updateDependencyStatus, updateMcpStatus } from './statusBar';
import { state } from './state';

/**
 * Register all commands
 */
export function registerCommands(context: vscode.ExtensionContext) {
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
                updateLiveTestStatus(false);
            } else {
                startLiveTesting();
                updateLiveTestStatus(true);
            }
        })
    );

    // Service management commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleDependencyService', () => {
            startDependencyService();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.toggleMcpService', () => {
            // Send command to Python server to toggle MCP service
            vscode.window.showInformationMessage('MCP service toggle - handled by Python server');
        })
    );

    // AI Generation commands (inline CodeLens)
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateTestsInline', (uri: vscode.Uri, lineNumber: number) => {
            requestAIGeneration(uri, lineNumber, 'test');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateDocsInline', (uri: vscode.Uri, lineNumber: number) => {
            requestAIGeneration(uri, lineNumber, 'doc');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateBothInline', (uri: vscode.Uri, lineNumber: number) => {
            requestAIGeneration(uri, lineNumber, 'both');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.showDependenciesInline', (uri: vscode.Uri, lineNumber: number, elementName: string) => {
            // Show dependency information for the element
            vscode.window.showInformationMessage(`Dependencies for ${elementName} - feature coming soon`);
        })
    );

    // Enhanced AI generation commands for existing blocks
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.generateAdditionalTests', (uri: vscode.Uri, lineNumber: number) => {
            requestAIEnhancement(uri, lineNumber, 'generate_additional_tests');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.regenerateTests', (uri: vscode.Uri, lineNumber: number) => {
            requestAIEnhancement(uri, lineNumber, 'regenerate_tests');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.improveTestCoverage', (uri: vscode.Uri, lineNumber: number) => {
            requestAIEnhancement(uri, lineNumber, 'improve_test_coverage');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.regenerateDocs', (uri: vscode.Uri, lineNumber: number) => {
            requestAIEnhancement(uri, lineNumber, 'regenerate_docs');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.addMoreDocDetail', (uri: vscode.Uri, lineNumber: number) => {
            requestAIEnhancement(uri, lineNumber, 'add_more_doc_detail');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.addDocExamples', (uri: vscode.Uri, lineNumber: number) => {
            requestAIEnhancement(uri, lineNumber, 'add_doc_examples');
        })
    );

    // Navigation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.navigateToDefinition', (args: any) => {
            navigateToElement(args, false);
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('pytestembed.navigateToDefinitionSplit', (args: any) => {
            navigateToElement(args, true);
        })
    );

    // Add missing commands that are declared in package.json
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
            runPyTestEmbedCommand('--run');
        })
    );

    // Placeholder commands for package.json compatibility
    const placeholderCommands = [
        'pytestembed.toggleTestBlocks',
        'pytestembed.toggleDocBlocks',
        'pytestembed.showAllBlocks',
        'pytestembed.hideAllBlocks',
        'pytestembed.configureLinter',
        'pytestembed.openOutputPanel',
        'pytestembed.generateBlocks',
        'pytestembed.generateTestsOnly',
        'pytestembed.generateDocsOnly',
        'pytestembed.startMcpServer',
        'pytestembed.stopMcpServer',
        'pytestembed.openPanel',
        'pytestembed.runIgnoringTests',
        'pytestembed.toggleDoubleClickNavigation',
        'pytestembed.toggleDependencyServer'
    ];

    placeholderCommands.forEach(commandId => {
        context.subscriptions.push(
            vscode.commands.registerCommand(commandId, () => {
                vscode.window.showInformationMessage(`${commandId} - feature coming soon`);
            })
        );
    });
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
 * Navigate to element definition
 */
async function navigateToElement(args: any, splitView: boolean = false) {
    try {
        const { file_path, line_number } = args;

        const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
        if (!workspaceFolder) {
            vscode.window.showErrorMessage('No workspace folder found');
            return;
        }

        const fullPath = require('path').resolve(workspaceFolder.uri.fsPath, file_path);
        const fileUri = vscode.Uri.file(fullPath);

        const document = await vscode.workspace.openTextDocument(fileUri);

        const viewColumn = splitView ? vscode.ViewColumn.Beside : vscode.ViewColumn.Active;
        const editor = await vscode.window.showTextDocument(document, viewColumn);

        const position = new vscode.Position(line_number - 1, 0);
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(new vscode.Range(position, position), vscode.TextEditorRevealType.InCenter);

    } catch (error) {
        vscode.window.showErrorMessage(`Failed to navigate: ${error}`);
    }
}
