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
 * Register the enhanced folding provider (functions, classes, test:, doc: blocks)
 */
export function registerFoldingProvider(context: vscode.ExtensionContext) {
    // Use the enhanced provider that creates compound folding ranges
    const provider = new CompoundFoldingProvider();

    const disposable = vscode.languages.registerFoldingRangeProvider(
        { scheme: 'file', language: 'python' },
        provider
    );

    context.subscriptions.push(disposable);

    // NO EVENT LISTENER - causes too many problems
}

/**
 * Toggle folding for specific block types (ONLY test: and doc: blocks)
 */
export async function toggleBlockFolding(blockType: 'test' | 'doc', fold: boolean) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }

    const document = editor.document;

    // Only fold/unfold test: and doc: blocks, not functions/classes
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

/**
 * Smart folding: fold function/class and its associated test/doc blocks
 */
export async function foldFunctionWithBlocks(lineNumber: number) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || !editor.document.fileName.endsWith('.py')) {
        return;
    }

    const document = editor.document;
    const line = document.lineAt(lineNumber);
    const trimmed = line.text.trim();

    // Check if this is a function or class definition
    if (trimmed.startsWith('def ') || trimmed.startsWith('class ')) {
        // First fold the function/class itself
        const position = new vscode.Position(lineNumber, 0);
        editor.selection = new vscode.Selection(position, position);
        await vscode.commands.executeCommand('editor.fold');

        // Then find and fold associated test: and doc: blocks
        await foldAssociatedBlocks(lineNumber);
    }
}

/**
 * Find and fold test: and doc: blocks associated with a function/class
 */
async function foldAssociatedBlocks(functionLineNumber: number) {
    const editor = vscode.window.activeTextEditor;
    if (!editor) return;

    const document = editor.document;
    const functionLine = document.lineAt(functionLineNumber);
    const baseIndent = functionLine.firstNonWhitespaceCharacterIndex;

    console.log(`🔍 Looking for test/doc blocks after function at line ${functionLineNumber + 1}`);
    console.log(`📏 Function indent: ${baseIndent}`);

    // Look for test: and doc: blocks immediately after the function
    let foundBlocks = 0;
    for (let i = functionLineNumber + 1; i < document.lineCount && foundBlocks < 10; i++) {
        const line = document.lineAt(i);
        const trimmed = line.text.trim();

        // Skip empty lines
        if (trimmed === '') continue;

        console.log(`📝 Line ${i + 1}: "${trimmed}", indent: ${line.firstNonWhitespaceCharacterIndex}`);

        // If we find test: or doc: blocks at same indentation level, fold them
        if ((trimmed === 'test:' || trimmed === 'doc:') &&
            line.firstNonWhitespaceCharacterIndex === baseIndent) {
            console.log(`🔽 Folding ${trimmed} block at line ${i + 1}`);
            const position = new vscode.Position(i, 0);
            editor.selection = new vscode.Selection(position, position);
            await vscode.commands.executeCommand('editor.fold');
            foundBlocks++;

            // Small delay to ensure folding completes
            await new Promise(resolve => setTimeout(resolve, 150));
            continue;
        }

        // If we hit another function/class at same level or less, stop looking
        if (line.firstNonWhitespaceCharacterIndex <= baseIndent &&
            (trimmed.startsWith('def ') || trimmed.startsWith('class '))) {
            console.log(`🛑 Hit another function/class at line ${i + 1}, stopping search`);
            break;
        }

        // If we've gone too far past the function without finding blocks, stop
        if (line.firstNonWhitespaceCharacterIndex < baseIndent) {
            console.log(`🛑 Reached lower indentation at line ${i + 1}, stopping search`);
            break;
        }
    }

    console.log(`✅ Found and folded ${foundBlocks} blocks`);
}

/**
 * Enhanced folding provider that includes function/class folding
 */
export class EnhancedPyTestEmbedFoldingProvider implements vscode.FoldingRangeProvider {

    provideFoldingRanges(
        document: vscode.TextDocument,
        context: vscode.FoldingContext,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.FoldingRange[]> {

        const foldingRanges: vscode.FoldingRange[] = [];

        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const trimmed = line.text.trim();

            // Handle test: and doc: blocks
            if (trimmed === 'test:' || trimmed === 'doc:') {
                const range = this.getBlockRange(document, i);
                if (range) {
                    foldingRanges.push(range);
                }
            }

            // Handle function and class definitions
            if (trimmed.startsWith('def ') || trimmed.startsWith('class ')) {
                const range = this.getFunctionClassRange(document, i);
                if (range) {
                    foldingRanges.push(range);
                }
            }
        }

        return foldingRanges;
    }

    private getBlockRange(document: vscode.TextDocument, startLine: number): vscode.FoldingRange | null {
        const line = document.lineAt(startLine);
        const baseIndent = line.firstNonWhitespaceCharacterIndex;
        let endLine = startLine;

        // Find the end of this block
        for (let j = startLine + 1; j < document.lineCount; j++) {
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
            return new vscode.FoldingRange(startLine, endLine);
        }

        return null;
    }

    private getFunctionClassRange(document: vscode.TextDocument, startLine: number): vscode.FoldingRange | null {
        const line = document.lineAt(startLine);
        const baseIndent = line.firstNonWhitespaceCharacterIndex;
        let endLine = startLine;

        // Find the end of this function/class
        for (let j = startLine + 1; j < document.lineCount; j++) {
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

        // Create folding range if the function/class has content
        if (endLine > startLine) {
            return new vscode.FoldingRange(startLine, endLine);
        }

        return null;
    }
}

/**
 * Compound folding provider that creates single folding ranges for function+blocks
 */
class CompoundFoldingProvider implements vscode.FoldingRangeProvider {

    provideFoldingRanges(
        document: vscode.TextDocument,
        context: vscode.FoldingContext,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.FoldingRange[]> {

        const foldingRanges: vscode.FoldingRange[] = [];

        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const trimmed = line.text.trim();

            // Handle function and class definitions with their blocks
            if (trimmed.startsWith('def ') || trimmed.startsWith('class ')) {
                const range = this.getCompoundRange(document, i);
                if (range) {
                    foldingRanges.push(range);
                }
            }

            // Handle standalone test: and doc: blocks
            else if (trimmed === 'test:' || trimmed === 'doc:') {
                const range = this.getStandaloneBlockRange(document, i);
                if (range) {
                    foldingRanges.push(range);
                }
            }
        }

        return foldingRanges;
    }

    /**
     * Get compound range that includes function/class AND its test/doc blocks
     */
    private getCompoundRange(document: vscode.TextDocument, startLine: number): vscode.FoldingRange | null {
        const line = document.lineAt(startLine);
        const baseIndent = line.firstNonWhitespaceCharacterIndex;
        let endLine = startLine;

        // Find the end of the function/class body
        for (let j = startLine + 1; j < document.lineCount; j++) {
            const nextLine = document.lineAt(j);

            // Skip empty lines
            if (nextLine.text.trim() === '') {
                continue;
            }

            // If we hit a line with same or less indentation, we've found the end of the body
            if (nextLine.firstNonWhitespaceCharacterIndex <= baseIndent) {
                break;
            }

            endLine = j;
        }

        // Now look for associated test: and doc: blocks immediately after
        for (let j = endLine + 1; j < document.lineCount; j++) {
            const nextLine = document.lineAt(j);
            const trimmed = nextLine.text.trim();

            // Skip empty lines
            if (trimmed === '') {
                continue;
            }

            // If we find test: or doc: blocks at same indentation, include them
            if ((trimmed === 'test:' || trimmed === 'doc:') &&
                nextLine.firstNonWhitespaceCharacterIndex === baseIndent) {

                // Find the end of this block
                let blockEnd = j;
                for (let k = j + 1; k < document.lineCount; k++) {
                    const blockLine = document.lineAt(k);

                    if (blockLine.text.trim() === '') {
                        continue;
                    }

                    if (blockLine.firstNonWhitespaceCharacterIndex <= baseIndent) {
                        break;
                    }

                    blockEnd = k;
                }

                endLine = blockEnd;
                continue;
            }

            // If we hit anything else at same level, stop
            if (nextLine.firstNonWhitespaceCharacterIndex <= baseIndent) {
                break;
            }
        }

        // Create folding range if there's content to fold
        if (endLine > startLine) {
            return new vscode.FoldingRange(startLine, endLine);
        }

        return null;
    }

    /**
     * Get range for standalone test: or doc: blocks (not associated with functions)
     */
    private getStandaloneBlockRange(document: vscode.TextDocument, startLine: number): vscode.FoldingRange | null {
        const line = document.lineAt(startLine);
        const baseIndent = line.firstNonWhitespaceCharacterIndex;
        let endLine = startLine;

        // Check if this block is immediately after a function/class (if so, skip it - it's handled by compound range)
        if (startLine > 0) {
            for (let i = startLine - 1; i >= 0; i--) {
                const prevLine = document.lineAt(i);

                if (prevLine.text.trim() === '') {
                    continue;
                }

                // If we find a function/class at same indent level, this block belongs to it
                if (prevLine.firstNonWhitespaceCharacterIndex === baseIndent &&
                    (prevLine.text.trim().startsWith('def ') || prevLine.text.trim().startsWith('class '))) {
                    return null; // Skip - handled by compound range
                }

                break;
            }
        }

        // Find the end of this standalone block
        for (let j = startLine + 1; j < document.lineCount; j++) {
            const nextLine = document.lineAt(j);

            if (nextLine.text.trim() === '') {
                continue;
            }

            if (nextLine.firstNonWhitespaceCharacterIndex <= baseIndent) {
                break;
            }

            endLine = j;
        }

        if (endLine > startLine) {
            return new vscode.FoldingRange(startLine, endLine);
        }

        return null;
    }
}
