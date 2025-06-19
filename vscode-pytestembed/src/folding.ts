/**
 * PyTestEmbed Folding Provider
 * 
 * Provides proper folding for test: and doc: blocks
 */

import * as vscode from 'vscode';
import { state, decorationTypes } from './state';

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

    // Register folding state tracker for test status icon movement
    registerFoldingStateTracker(context);
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

/**
 * Track folding state changes for test status icon movement
 */
function registerFoldingStateTracker(context: vscode.ExtensionContext) {
    // Track folding changes with a debounced approach
    let updateTimeout: NodeJS.Timeout | undefined;

    const disposable = vscode.window.onDidChangeTextEditorVisibleRanges((event) => {
        const editor = event.textEditor;
        if (!editor || !editor.document.fileName.endsWith('.py')) {
            return;
        }

        // Debounce updates to avoid excessive processing
        if (updateTimeout) {
            clearTimeout(updateTimeout);
        }

        updateTimeout = setTimeout(() => {
            updateTestStatusIconsForFolding(editor);
        }, 100);
    });

    context.subscriptions.push(disposable);
}

/**
 * Update test status icons based on current folding state
 */
async function updateTestStatusIconsForFolding(editor: vscode.TextEditor) {
    const document = editor.document;
    const foldedFunctions = new Set<number>();
    const foldedClasses = new Set<number>();

    // Detect which functions and classes are currently folded
    for (let i = 0; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const trimmed = line.text.trim();

        if (trimmed.startsWith('def ') || trimmed.startsWith('class ')) {
            // Check if this line is folded by seeing if the next line is visible
            const nextLineVisible = isLineVisible(editor, i + 1);
            if (!nextLineVisible) {
                if (trimmed.startsWith('def ')) {
                    foldedFunctions.add(i);
                } else {
                    foldedClasses.add(i);
                }
            }
        }
    }

    // Update decorations for folded functions
    for (const lineNumber of foldedFunctions) {
        await updateFunctionTestStatus(editor, lineNumber);
    }

    // Update decorations for folded classes
    for (const lineNumber of foldedClasses) {
        await updateClassTestStatus(editor, lineNumber);
    }
}

/**
 * Check if a line is currently visible (not folded)
 */
function isLineVisible(editor: vscode.TextEditor, lineNumber: number): boolean {
    if (lineNumber >= editor.document.lineCount) {
        return false;
    }

    // Check if the line is within any visible range
    const lineRange = new vscode.Range(lineNumber, 0, lineNumber, editor.document.lineAt(lineNumber).text.length);
    const isVisible = editor.visibleRanges.some(range => range.contains(lineRange));

    console.log(`👁️ Line ${lineNumber + 1} visibility: ${isVisible}`);
    return isVisible;
}

/**
 * Update test status for a folded function
 */
async function updateFunctionTestStatus(editor: vscode.TextEditor, functionLineNumber: number) {
    const document = editor.document;
    const functionLine = document.lineAt(functionLineNumber);
    const baseIndent = functionLine.firstNonWhitespaceCharacterIndex;

    // Find associated test: blocks and get their status
    let testStatus: 'pass' | 'fail' | 'running' | 'untested' = 'untested';

    for (let i = functionLineNumber + 1; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const trimmed = line.text.trim();

        // Skip empty lines
        if (trimmed === '') continue;

        // Stop if we hit another function/class at same level
        if (line.firstNonWhitespaceCharacterIndex <= baseIndent &&
            (trimmed.startsWith('def ') || trimmed.startsWith('class '))) {
            break;
        }

        // Check test: blocks
        if (trimmed === 'test:' && line.firstNonWhitespaceCharacterIndex === baseIndent) {
            const blockStatus = getTestBlockStatus(i);
            if (blockStatus === 'fail') {
                testStatus = 'fail';
                break; // Fail takes priority
            } else if (blockStatus === 'running') {
                testStatus = 'running';
            } else if (blockStatus === 'pass' && testStatus === 'untested') {
                testStatus = 'pass';
            }
        }
    }

    // Apply decoration to the function line
    applyTestStatusDecoration(editor, functionLineNumber, testStatus);
}

/**
 * Update test status for a folded class (aggregate all function tests + class tests)
 */
async function updateClassTestStatus(editor: vscode.TextEditor, classLineNumber: number) {
    const document = editor.document;
    const classLine = document.lineAt(classLineNumber);
    const baseIndent = classLine.firstNonWhitespaceCharacterIndex;

    let hasFailure = false;
    let hasRunning = false;
    let hasPass = false;

    // Check class-level test: blocks first
    for (let i = classLineNumber + 1; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        const trimmed = line.text.trim();

        // Skip empty lines
        if (trimmed === '') continue;

        // Stop if we hit another class at same level or less
        if (line.firstNonWhitespaceCharacterIndex <= baseIndent &&
            trimmed.startsWith('class ')) {
            break;
        }

        // Check class-level test: blocks
        if (trimmed === 'test:' && line.firstNonWhitespaceCharacterIndex === baseIndent) {
            const blockStatus = getTestBlockStatus(i);
            if (blockStatus === 'fail') hasFailure = true;
            else if (blockStatus === 'running') hasRunning = true;
            else if (blockStatus === 'pass') hasPass = true;
        }

        // Check function-level test: blocks within the class
        if (trimmed.startsWith('def ') && line.firstNonWhitespaceCharacterIndex > baseIndent) {
            const functionStatus = await getFunctionTestStatus(i);
            if (functionStatus === 'fail') hasFailure = true;
            else if (functionStatus === 'running') hasRunning = true;
            else if (functionStatus === 'pass') hasPass = true;
        }
    }

    // Determine aggregate status
    let aggregateStatus: 'pass' | 'fail' | 'running' | 'untested' = 'untested';
    if (hasFailure) {
        aggregateStatus = 'fail';
    } else if (hasRunning) {
        aggregateStatus = 'running';
    } else if (hasPass) {
        aggregateStatus = 'pass';
    }

    // Apply decoration to the class line
    applyTestStatusDecoration(editor, classLineNumber, aggregateStatus);
}

/**
 * Get test status for a specific test: block
 */
function getTestBlockStatus(testLineNumber: number): 'pass' | 'fail' | 'running' | 'untested' {
    // Check if we have test results for this line
    const editor = vscode.window.activeTextEditor;
    if (!editor) return 'untested';

    const filePath = editor.document.fileName;
    const testResults = state.testResults.get(filePath);

    if (testResults) {
        // Find test results for this specific line
        const lineResults = testResults.filter(result => result.line === testLineNumber);

        if (lineResults.length > 0) {
            // Check if any tests failed
            const hasFail = lineResults.some(result => result.status === 'fail' || result.status === 'error');
            const hasRunning = lineResults.some(result => result.status === 'running');
            const hasPass = lineResults.some(result => result.status === 'pass');

            if (hasFail) return 'fail';
            if (hasRunning) return 'running';
            if (hasPass) return 'pass';
        }
    }

    // Default to untested if no results
    return 'untested';
}

/**
 * Get aggregate test status for a function
 */
async function getFunctionTestStatus(functionLineNumber: number): Promise<'pass' | 'fail' | 'running' | 'untested'> {
    // This would use similar logic to updateFunctionTestStatus but just return the status
    // For now, return untested - this can be expanded
    return 'untested';
}

/**
 * Apply test status decoration to a specific line (function/class when folded)
 */
function applyTestStatusDecoration(editor: vscode.TextEditor, lineNumber: number, status: 'pass' | 'fail' | 'running' | 'untested') {
    console.log(`📍 Applying ${status} decoration to line ${lineNumber + 1}`);

    // Don't clear existing decorations - let the decoration system handle it
    // This prevents the icons from disappearing

    // Apply the appropriate decoration based on status
    const range = new vscode.Range(lineNumber, 0, lineNumber, 0);
    const decorationOptions: vscode.DecorationOptions = {
        range,
        hoverMessage: `Folded test status: ${status}`
    };

    // Create a new decoration array with just this line
    const decorations = [decorationOptions];

    switch (status) {
        case 'pass':
            editor.setDecorations(decorationTypes.blockPassIconDecorationType, decorations);
            break;
        case 'fail':
        case 'untested': // Show untested as fail (red)
            editor.setDecorations(decorationTypes.blockFailIconDecorationType, decorations);
            break;
        case 'running':
            editor.setDecorations(decorationTypes.blockRunningIconDecorationType, decorations);
            break;
    }
}

/**
 * Clear decorations for a specific line (more targeted approach)
 */
function clearLineDecorations(editor: vscode.TextEditor, lineNumber: number) {
    // Don't clear ALL decorations - this is too aggressive
    // Instead, we'll let the decoration system handle overlapping decorations
    // This function is kept for future use but currently does nothing
    console.log(`🧹 Would clear decorations for line ${lineNumber + 1} (currently disabled)`);
}
