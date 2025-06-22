/**
 * Minimal PyTestEmbed Folding Provider
 */

import * as vscode from 'vscode';

/**
 * Simple folding provider for test: and doc: blocks
 */
export class PyTestEmbedFoldingProvider implements vscode.FoldingRangeProvider {
    
    provideFoldingRanges(document: vscode.TextDocument): vscode.FoldingRange[] {
        const ranges: vscode.FoldingRange[] = [];
        
        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const trimmed = line.text.trim();
            
            if (trimmed === 'test:' || trimmed === 'doc:') {
                const baseIndent = line.firstNonWhitespaceCharacterIndex;
                let endLine = i;
                
                // Find end of block
                for (let j = i + 1; j < document.lineCount; j++) {
                    const nextLine = document.lineAt(j);
                    if (nextLine.text.trim() === '') continue;
                    if (nextLine.firstNonWhitespaceCharacterIndex <= baseIndent) break;
                    endLine = j;
                }
                
                if (endLine > i) {
                    ranges.push(new vscode.FoldingRange(i, endLine));
                }
            }
        }
        
        return ranges;
    }
}

/**
 * Register minimal folding provider
 */
export function registerFoldingProvider(context: vscode.ExtensionContext) {
    const provider = new PyTestEmbedFoldingProvider();
    const disposable = vscode.languages.registerFoldingRangeProvider(
        { scheme: 'file', language: 'python' },
        provider
    );
    context.subscriptions.push(disposable);
}
