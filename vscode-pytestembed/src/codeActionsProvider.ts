/**
 * Code Actions Provider for PyTestEmbed test: and doc: blocks
 * Provides lightbulb quick fixes for enhancing test and documentation blocks
 */

import * as vscode from 'vscode';
import { state } from './state';

export class PyTestEmbedCodeActionsProvider implements vscode.CodeActionProvider {

    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix,
        vscode.CodeActionKind.Refactor
    ];

    provideCodeActions(
        document: vscode.TextDocument,
        range: vscode.Range | vscode.Selection,
        context: vscode.CodeActionContext,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<(vscode.CodeAction | vscode.Command)[]> {

        if (document.languageId !== 'python') {
            return [];
        }

        const actions: vscode.CodeAction[] = [];
        const line = document.lineAt(range.start.line);
        const trimmed = line.text.trim();

        // Check if we're in a test: or doc: block
        const blockInfo = this.getBlockInfo(document, range);
        if (blockInfo) {
            if (blockInfo.type === 'test') {
                actions.push(...this.createTestBlockActions(document, blockInfo));
            } else if (blockInfo.type === 'doc') {
                actions.push(...this.createDocBlockActions(document, blockInfo));
            }
        }

        // Quick actions for function definitions (from existing provider)
        if (trimmed.startsWith('def ') && trimmed.includes('(') && trimmed.endsWith(':')) {
            actions.push(...this.createFunctionActions(document, range));
        }

        // Individual test execution (if live testing is active)
        if (state.liveTestingEnabled && this.isTestExpression(trimmed)) {
            actions.push(...this.createTestExecutionActions(document, range));
        }

        return actions;
    }

    private getBlockInfo(document: vscode.TextDocument, range: vscode.Range): BlockInfo | null {
        const line = document.lineAt(range.start.line);
        const lineText = line.text.trim();

        // Check if we're on a test: or doc: line
        if (lineText.startsWith('test:')) {
            return {
                type: 'test',
                line: range.start.line,
                text: lineText,
                blockRange: this.getBlockRange(document, range.start.line, 'test:')
            };
        } else if (lineText.startsWith('doc:')) {
            return {
                type: 'doc',
                line: range.start.line,
                text: lineText,
                blockRange: this.getBlockRange(document, range.start.line, 'doc:')
            };
        }

        // Check if we're inside a test: or doc: block
        for (let i = range.start.line; i >= 0; i--) {
            const checkLine = document.lineAt(i).text.trim();
            if (checkLine.startsWith('test:')) {
                const blockRange = this.getBlockRange(document, i, 'test:');
                if (blockRange.contains(range)) {
                    return {
                        type: 'test',
                        line: i,
                        text: checkLine,
                        blockRange: blockRange
                    };
                }
                break;
            } else if (checkLine.startsWith('doc:')) {
                const blockRange = this.getBlockRange(document, i, 'doc:');
                if (blockRange.contains(range)) {
                    return {
                        type: 'doc',
                        line: i,
                        text: checkLine,
                        blockRange: blockRange
                    };
                }
                break;
            }
        }

        return null;
    }

    private getBlockRange(document: vscode.TextDocument, startLine: number, blockType: string): vscode.Range {
        const startLineObj = document.lineAt(startLine);
        const baseIndent = startLineObj.firstNonWhitespaceCharacterIndex;
        
        let endLine = startLine;
        
        // Find the end of the block (next line with same or less indentation)
        for (let i = startLine + 1; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const lineText = line.text.trim();
            
            // Skip empty lines
            if (lineText === '') {
                continue;
            }
            
            // If we hit a line with same or less indentation, we've found the end
            if (line.firstNonWhitespaceCharacterIndex <= baseIndent) {
                break;
            }
            
            endLine = i;
        }
        
        return new vscode.Range(startLine, 0, endLine, document.lineAt(endLine).text.length);
    }

    private createTestBlockActions(document: vscode.TextDocument, blockInfo: BlockInfo): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Rewrite test: block
        const rewriteAction = new vscode.CodeAction(
            '🔄 Rewrite test: block',
            vscode.CodeActionKind.Refactor
        );
        rewriteAction.command = {
            command: 'pytestembed.rewriteTestBlock',
            title: 'Rewrite test: block',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(rewriteAction);

        // Add another test
        const addTestAction = new vscode.CodeAction(
            '➕ Add another test',
            vscode.CodeActionKind.QuickFix
        );
        addTestAction.command = {
            command: 'pytestembed.addAnotherTest',
            title: 'Add another test',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(addTestAction);

        // Generate edge case tests
        const edgeCaseAction = new vscode.CodeAction(
            '🎯 Generate edge case tests',
            vscode.CodeActionKind.Refactor
        );
        edgeCaseAction.command = {
            command: 'pytestembed.generateEdgeCaseTests',
            title: 'Generate edge case tests',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(edgeCaseAction);

        // Improve test coverage
        const coverageAction = new vscode.CodeAction(
            '📊 Improve test coverage',
            vscode.CodeActionKind.Refactor
        );
        coverageAction.command = {
            command: 'pytestembed.improveTestCoverage',
            title: 'Improve test coverage',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(coverageAction);

        return actions;
    }

    private createDocBlockActions(document: vscode.TextDocument, blockInfo: BlockInfo): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];

        // Rewrite doc: block
        const rewriteAction = new vscode.CodeAction(
            '🔄 Rewrite doc: block',
            vscode.CodeActionKind.Refactor
        );
        rewriteAction.command = {
            command: 'pytestembed.rewriteDocBlock',
            title: 'Rewrite doc: block',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(rewriteAction);

        // Add more detail
        const detailAction = new vscode.CodeAction(
            '📝 Add more detail',
            vscode.CodeActionKind.QuickFix
        );
        detailAction.command = {
            command: 'pytestembed.addMoreDetail',
            title: 'Add more detail',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(detailAction);

        // Add examples
        const examplesAction = new vscode.CodeAction(
            '💡 Add examples',
            vscode.CodeActionKind.Refactor
        );
        examplesAction.command = {
            command: 'pytestembed.addExamples',
            title: 'Add examples',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(examplesAction);

        // Improve clarity
        const clarityAction = new vscode.CodeAction(
            '✨ Improve clarity',
            vscode.CodeActionKind.Refactor
        );
        clarityAction.command = {
            command: 'pytestembed.improveClarityDoc',
            title: 'Improve clarity',
            arguments: [document.uri.fsPath, blockInfo.line]
        };
        actions.push(clarityAction);

        return actions;
    }

    private createFunctionActions(document: vscode.TextDocument, range: vscode.Range): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];
        const lineNumber = range.start.line + 1;

        // Quick Fix - analyze and fix function issues
        const quickFixAction = new vscode.CodeAction('🔧 Quick Fix', vscode.CodeActionKind.QuickFix);
        quickFixAction.command = {
            command: 'pytestembed.quickFixFunction',
            title: 'Quick Fix',
            arguments: [document.uri, lineNumber]
        };
        actions.push(quickFixAction);

        // Generate Test Block
        const testAction = new vscode.CodeAction('🧪 Generate Test', vscode.CodeActionKind.QuickFix);
        testAction.command = {
            command: 'pytestembed.generateBlocksAtLine',
            title: 'Generate Test',
            arguments: [document.uri, lineNumber, 'test']
        };
        actions.push(testAction);

        // Generate Doc Block
        const docAction = new vscode.CodeAction('📝 Generate Doc', vscode.CodeActionKind.QuickFix);
        docAction.command = {
            command: 'pytestembed.generateBlocksAtLine',
            title: 'Generate Doc',
            arguments: [document.uri, lineNumber, 'doc']
        };
        actions.push(docAction);

        // Generate Both
        const bothAction = new vscode.CodeAction('🎯 Generate Both', vscode.CodeActionKind.QuickFix);
        bothAction.command = {
            command: 'pytestembed.generateBlocksAtLine',
            title: 'Generate Both',
            arguments: [document.uri, lineNumber, 'both']
        };
        actions.push(bothAction);

        return actions;
    }

    private createTestExecutionActions(document: vscode.TextDocument, range: vscode.Range): vscode.CodeAction[] {
        const actions: vscode.CodeAction[] = [];
        const lineNumber = range.start.line;

        const runTestAction = new vscode.CodeAction('▶️ Run This Test', vscode.CodeActionKind.QuickFix);
        runTestAction.command = {
            command: 'pytestembed.runIndividualTest',
            title: 'Run This Test',
            arguments: [document.fileName, lineNumber]
        };
        actions.push(runTestAction);

        return actions;
    }

    private isTestExpression(lineText: string): boolean {
        // Check if this line contains a PyTestEmbed test expression
        return /^\s*(.+?)\s*:\s*".*"[,]?$/.test(lineText);
    }
}

interface BlockInfo {
    type: 'test' | 'doc';
    line: number;
    text: string;
    blockRange: vscode.Range;
}

/**
 * Register the code actions provider
 */
export function registerCodeActionsProvider(context: vscode.ExtensionContext) {
    const provider = new PyTestEmbedCodeActionsProvider();
    
    const disposable = vscode.languages.registerCodeActionsProvider(
        { scheme: 'file', language: 'python' },
        provider,
        {
            providedCodeActionKinds: PyTestEmbedCodeActionsProvider.providedCodeActionKinds
        }
    );
    
    context.subscriptions.push(disposable);
}
