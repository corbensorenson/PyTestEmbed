/**
 * PyTestEmbed Folding Provider
 * 
 * Provides proper folding for test: and doc: blocks
 */

import * as vscode from 'vscode';

/**
 * Folding range provider for PyTestEmbed syntax
 */
export class PyTestEmbedFoldingProvider implements vscode.FoldingRangeProvider {
    
    provideFoldingRanges(
        document: vscode.TextDocument, 
        context: vscode.FoldingContext, 
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.FoldingRange[]> {
        
        const foldingRanges: vscode.FoldingRange[] = [];
        
        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const trimmed = line.text.trim();
            
            // Check for test: or doc: blocks
            if (trimmed === 'test:' || trimmed === 'doc:') {
                const startLine = i;
                const baseIndent = line.firstNonWhitespaceCharacterIndex;
                let endLine = i;
                
                // Find the end of this block
                for (let j = i + 1; j < document.lineCount; j++) {
                    const nextLine = document.lineAt(j);
                    
                    // Skip empty lines
                    if (nextLine.text.trim() === '') {
                        continue;
                    }
                    
                    // If we hit a line with same or less indentation, we've found the end
                    if (nextLine.firstNonWhitespaceCharacterIndex <= baseIndent) {
                        break;
                    }
                    
                    endLine = j;
                }
                
                // Create folding range if the block has content
                if (endLine > startLine) {
                    foldingRanges.push(new vscode.FoldingRange(startLine, endLine));
                }
            }
        }
        
        return foldingRanges;
    }
}

/**
 * Register the folding provider
 */
export function registerFoldingProvider(context: vscode.ExtensionContext) {
    const provider = new PyTestEmbedFoldingProvider();
    
    const disposable = vscode.languages.registerFoldingRangeProvider(
        { scheme: 'file', language: 'python' },
        provider
    );
    
    context.subscriptions.push(disposable);
}

/**
 * Toggle folding for specific block types
 */
export async function toggleBlockFolding(blockType: 'test' | 'doc', fold: boolean) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }
    
    const document = editor.document;
    
    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        if (line.text.trim() === `${blockType}:`) {
            // Move cursor to this line and fold/unfold
            const position = new vscode.Position(i, 0);
            editor.selection = new vscode.Selection(position, position);
            
            if (fold) {
                await vscode.commands.executeCommand('editor.fold');
            } else {
                await vscode.commands.executeCommand('editor.unfold');
            }
        }
    }
}
