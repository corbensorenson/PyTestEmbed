/**
 * VSCode providers for PyTestEmbed extension
 */

import * as vscode from 'vscode';
import { state } from './state';
import { runIndividualTest } from './liveTesting';
import { BlockType } from './types';

/**
 * Register all providers
 */
export function registerProviders(context: vscode.ExtensionContext) {
    // Register folding range provider for Python files
    const foldingProvider = new PyTestEmbedFoldingProvider();
    context.subscriptions.push(
        vscode.languages.registerFoldingRangeProvider(
            { scheme: 'file', language: 'python' },
            foldingProvider
        )
    );

    // Register status bar items
    const statusBarManager = new StatusBarManager();
    context.subscriptions.push(statusBarManager);

    // Register tree data provider for the explorer view
    const treeDataProvider = new PyTestEmbedTreeDataProvider();
    vscode.window.createTreeView('pytestembedView', {
        treeDataProvider: treeDataProvider
    });

    // Register tree data provider for the panel view
    const panelTreeDataProvider = new PyTestEmbedPanelTreeDataProvider();
    vscode.window.createTreeView('pytestembedLiveServer', {
        treeDataProvider: panelTreeDataProvider
    });

    // Register Quick Fix provider
    const quickFixProvider = new PyTestEmbedQuickFixProvider();
    context.subscriptions.push(
        vscode.languages.registerCodeActionsProvider(
            { scheme: 'file', language: 'python' },
            quickFixProvider,
            {
                providedCodeActionKinds: PyTestEmbedQuickFixProvider.providedCodeActionKinds
            }
        )
    );

    // Register Hover provider for dependency information
    const hoverProvider = new PyTestEmbedHoverProvider();
    context.subscriptions.push(
        vscode.languages.registerHoverProvider(
            { scheme: 'file', language: 'python' },
            hoverProvider
        )
    );

    // Register Definition provider for navigation
    const definitionProvider = new PyTestEmbedDefinitionProvider();
    context.subscriptions.push(
        vscode.languages.registerDefinitionProvider(
            { scheme: 'file', language: 'python' },
            definitionProvider
        )
    );
}

/**
 * Folding range provider for PyTestEmbed test: and doc: blocks
 */
class PyTestEmbedFoldingProvider implements vscode.FoldingRangeProvider {
    provideFoldingRanges(
        document: vscode.TextDocument,
        context: vscode.FoldingContext,
        token: vscode.CancellationToken
    ): vscode.ProviderResult<vscode.FoldingRange[]> {
        const ranges: vscode.FoldingRange[] = [];
        
        for (let i = 0; i < document.lineCount; i++) {
            const line = document.lineAt(i);
            const trimmedText = line.text.trim();
            
            // Check if this line starts a test: or doc: block
            if (trimmedText === 'test:' || trimmedText === 'doc:') {
                const startLine = i;
                const baseIndent = line.firstNonWhitespaceCharacterIndex;
                
                // Find the end of the block by looking for lines with greater indentation
                let endLine = startLine;
                for (let j = i + 1; j < document.lineCount; j++) {
                    const nextLine = document.lineAt(j);
                    const nextTrimmed = nextLine.text.trim();
                    
                    // Skip empty lines
                    if (nextTrimmed === '') {
                        continue;
                    }
                    
                    const nextIndent = nextLine.firstNonWhitespaceCharacterIndex;
                    
                    // If the next non-empty line has the same or less indentation, we've reached the end
                    if (nextIndent <= baseIndent) {
                        break;
                    }
                    
                    endLine = j;
                }
                
                // Only create a folding range if there's content to fold
                if (endLine > startLine) {
                    const kind = trimmedText === 'test:' 
                        ? vscode.FoldingRangeKind.Region 
                        : vscode.FoldingRangeKind.Comment;
                    
                    ranges.push(new vscode.FoldingRange(startLine, endLine, kind));
                }
                
                // Skip ahead to avoid processing the same block again
                i = endLine;
            }
        }
        
        return ranges;
    }
}

/**
 * Status bar manager for PyTestEmbed controls
 */
class StatusBarManager {
    private testToggleItem: vscode.StatusBarItem;
    private docToggleItem: vscode.StatusBarItem;

    constructor() {
        // Create status bar items (removed runTestsItem and generateDocsItem to save space)
        this.testToggleItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
        this.docToggleItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 99);

        // Configure items
        this.testToggleItem.command = 'pytestembed.toggleTestBlocks';
        this.testToggleItem.tooltip = 'Toggle Test Blocks Visibility';

        this.docToggleItem.command = 'pytestembed.toggleDocBlocks';
        this.docToggleItem.tooltip = 'Toggle Doc Blocks Visibility';

        this.updateItems();
        this.showItems();
    }

    updateItems() {
        this.testToggleItem.text = state.testBlocksVisible ? '$(beaker) Tests' : '$(beaker-stop) Tests';
        this.docToggleItem.text = state.docBlocksVisible ? '$(book) Docs' : '$(book) Docs';
    }

    showItems() {
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'python' && isPyTestEmbedFile(editor.document)) {
            this.testToggleItem.show();
            this.docToggleItem.show();
        } else {
            this.hideItems();
        }
    }

    hideItems() {
        this.testToggleItem.hide();
        this.docToggleItem.hide();
    }

    dispose() {
        this.testToggleItem.dispose();
        this.docToggleItem.dispose();
    }
}

/**
 * Tree data provider for PyTestEmbed view
 */
class PyTestEmbedTreeDataProvider implements vscode.TreeDataProvider<PyTestEmbedItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<PyTestEmbedItem | undefined | null | void> = new vscode.EventEmitter<PyTestEmbedItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<PyTestEmbedItem | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: PyTestEmbedItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: PyTestEmbedItem): Thenable<PyTestEmbedItem[]> {
        if (!element) {
            // Root items
            return Promise.resolve([
                new PyTestEmbedItem('Toggle Test Blocks', vscode.TreeItemCollapsibleState.None, 'pytestembed.toggleTestBlocks', '$(beaker)'),
                new PyTestEmbedItem('Toggle Doc Blocks', vscode.TreeItemCollapsibleState.None, 'pytestembed.toggleDocBlocks', '$(book)'),
                new PyTestEmbedItem('Show All Blocks', vscode.TreeItemCollapsibleState.None, 'pytestembed.showAllBlocks', '$(eye)'),
                new PyTestEmbedItem('Hide All Blocks', vscode.TreeItemCollapsibleState.None, 'pytestembed.hideAllBlocks', '$(eye-closed)'),
                new PyTestEmbedItem('Configure Linter', vscode.TreeItemCollapsibleState.None, 'pytestembed.configureLinter', '$(settings-gear)'),
                new PyTestEmbedItem('Run Tests', vscode.TreeItemCollapsibleState.None, 'pytestembed.runTests', '$(play)'),
                new PyTestEmbedItem('Generate Docs', vscode.TreeItemCollapsibleState.None, 'pytestembed.generateDocs', '$(file-text)'),
                new PyTestEmbedItem('Run Without Blocks', vscode.TreeItemCollapsibleState.None, 'pytestembed.runWithoutBlocks', '$(run)')
            ]);
        }
        return Promise.resolve([]);
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
}

/**
 * Tree data provider for PyTestEmbed panel view (Live Server)
 */
class PyTestEmbedPanelTreeDataProvider implements vscode.TreeDataProvider<PyTestEmbedPanelItem> {
    private _onDidChangeTreeData: vscode.EventEmitter<PyTestEmbedPanelItem | undefined | null | void> = new vscode.EventEmitter<PyTestEmbedPanelItem | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<PyTestEmbedPanelItem | undefined | null | void> = this._onDidChangeTreeData.event;

    getTreeItem(element: PyTestEmbedPanelItem): vscode.TreeItem {
        return element;
    }

    getChildren(element?: PyTestEmbedPanelItem): Thenable<PyTestEmbedPanelItem[]> {
        if (!element) {
            // Root items for the panel
            return Promise.resolve([
                new PyTestEmbedPanelItem('Live Test Server', vscode.TreeItemCollapsibleState.Expanded, undefined, '$(debug-alt)'),
                new PyTestEmbedPanelItem('MCP Server', vscode.TreeItemCollapsibleState.Expanded, undefined, '$(debug-alt)'),
                new PyTestEmbedPanelItem('Messages', vscode.TreeItemCollapsibleState.Expanded, undefined, '$(output)')
            ]);
        } else if (element.label === 'Live Test Server') {
            return Promise.resolve([
                new PyTestEmbedPanelItem('Start Live Testing', vscode.TreeItemCollapsibleState.None, 'pytestembed.startLiveTesting', '$(play)'),
                new PyTestEmbedPanelItem('Stop Live Testing', vscode.TreeItemCollapsibleState.None, 'pytestembed.stopLiveTesting', '$(stop)')
            ]);
        } else if (element.label === 'MCP Server') {
            return Promise.resolve([
                new PyTestEmbedPanelItem('Start MCP Server', vscode.TreeItemCollapsibleState.None, 'pytestembed.startMcpServer', '$(play)'),
                new PyTestEmbedPanelItem('Stop MCP Server', vscode.TreeItemCollapsibleState.None, 'pytestembed.stopMcpServer', '$(stop)')
            ]);
        } else if (element.label === 'Messages') {
            return Promise.resolve([
                new PyTestEmbedPanelItem('Clear Messages', vscode.TreeItemCollapsibleState.None, 'pytestembed.clearPanelMessages', '$(clear-all)'),
                new PyTestEmbedPanelItem('Open Panel', vscode.TreeItemCollapsibleState.None, 'pytestembed.openPanel', '$(window)')
            ]);
        }
        return Promise.resolve([]);
    }

    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
}

class PyTestEmbedPanelItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly commandName?: string,
        iconName?: string
    ) {
        super(label, collapsibleState);
        if (commandName) {
            this.command = {
                command: commandName,
                title: label
            };
        }
        if (iconName) {
            this.iconPath = new vscode.ThemeIcon(iconName.replace('$(', '').replace(')', ''));
        }
    }
}

class PyTestEmbedItem extends vscode.TreeItem {
    constructor(
        public readonly label: string,
        public readonly collapsibleState: vscode.TreeItemCollapsibleState,
        public readonly commandName?: string,
        iconName?: string
    ) {
        super(label, collapsibleState);
        if (commandName) {
            this.command = {
                command: commandName,
                title: label
            };
        }
        if (iconName) {
            this.iconPath = new vscode.ThemeIcon(iconName.replace('$(', '').replace(')', ''));
        }
    }
}

/**
 * Quick Actions provider for PyTestEmbed functions
 */
class PyTestEmbedQuickFixProvider implements vscode.CodeActionProvider {
    public static readonly providedCodeActionKinds = [
        vscode.CodeActionKind.QuickFix
    ];

    public provideCodeActions(document: vscode.TextDocument, range: vscode.Range | vscode.Selection, context: vscode.CodeActionContext, token: vscode.CancellationToken): vscode.CodeAction[] | undefined {
        if (document.languageId !== 'python') {
            return;
        }

        const actions: vscode.CodeAction[] = [];
        const line = document.lineAt(range.start.line);
        const trimmed = line.text.trim();

        // Quick actions for function definitions
        if (trimmed.startsWith('def ') && trimmed.includes('(') && trimmed.endsWith(':')) {
            const lineNumber = range.start.line + 1;

            // Quick Fix - analyze and fix function issues
            const quickFixAction = new vscode.CodeAction('Quick Fix', vscode.CodeActionKind.QuickFix);
            quickFixAction.command = {
                command: 'pytestembed.quickFixFunction',
                title: 'Quick Fix',
                arguments: [document.uri, lineNumber]
            };
            actions.push(quickFixAction);

            // Generate Test Block
            const testAction = new vscode.CodeAction('Generate Test', vscode.CodeActionKind.QuickFix);
            testAction.command = {
                command: 'pytestembed.generateBlocksAtLine',
                title: 'Generate Test',
                arguments: [document.uri, lineNumber, 'test']
            };
            actions.push(testAction);

            // Generate Doc Block
            const docAction = new vscode.CodeAction('Generate Doc', vscode.CodeActionKind.QuickFix);
            docAction.command = {
                command: 'pytestembed.generateBlocksAtLine',
                title: 'Generate Doc',
                arguments: [document.uri, lineNumber, 'doc']
            };
            actions.push(docAction);

            // Generate Both
            const bothAction = new vscode.CodeAction('Generate Both', vscode.CodeActionKind.QuickFix);
            bothAction.command = {
                command: 'pytestembed.generateBlocksAtLine',
                title: 'Generate Both',
                arguments: [document.uri, lineNumber, 'both']
            };
            actions.push(bothAction);
        }

        // Individual test execution (if live testing is active)
        if (state.liveTestingEnabled && this.isTestExpression(trimmed)) {
            const lineNumber = range.start.line;

            const runTestAction = new vscode.CodeAction('Run This Test', vscode.CodeActionKind.QuickFix);
            runTestAction.command = {
                command: 'pytestembed.runIndividualTest',
                title: 'Run This Test',
                arguments: [document.fileName, lineNumber]
            };
            actions.push(runTestAction);
        }

        return actions;
    }

    private isTestExpression(lineText: string): boolean {
        // Check if this line contains a PyTestEmbed test expression
        return /^\s*(.+?)\s*:\s*".*"[,]?$/.test(lineText);
    }
}

/**
 * Hover provider for dependency information
 */
class PyTestEmbedHoverProvider implements vscode.HoverProvider {
    public provideHover(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken): vscode.ProviderResult<vscode.Hover> {
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return;
        }

        const word = document.getText(wordRange);
        const line = document.lineAt(position.line);

        // Check if this is a function or class definition
        if (this.isFunctionOrClassDefinition(line.text, word)) {
            return this.getDependencyHover(document, word, position);
        }

        return;
    }

    private isFunctionOrClassDefinition(lineText: string, word: string): boolean {
        const trimmed = lineText.trim();
        return (trimmed.startsWith('def ') || trimmed.startsWith('class ')) &&
               trimmed.includes(word) &&
               trimmed.includes('(') &&
               trimmed.endsWith(':');
    }

    private async getDependencyHover(document: vscode.TextDocument, elementName: string, position: vscode.Position): Promise<vscode.Hover | undefined> {
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!workspaceFolder) {
            return;
        }

        const relativePath = require('path').relative(workspaceFolder.uri.fsPath, document.fileName);
        const elementId = `${relativePath}:${elementName}:${position.line + 1}`;

        // Check if we have cached dependency information
        const cachedInfo = state.dependencyCache.get(elementId);

        if (cachedInfo) {
            // Use cached information to create rich hover content
            const hoverContent = new vscode.MarkdownString();
            hoverContent.isTrusted = true;
            hoverContent.supportHtml = true;

            // Header with element name and dead code indicator
            if (cachedInfo.is_dead_code) {
                hoverContent.appendMarkdown(`**⚠️ ${elementName}** *(Dead Code)*\n\n`);
                hoverContent.appendMarkdown(`🚨 **This code appears to be unused**\n\n`);
            } else {
                hoverContent.appendMarkdown(`**🔗 ${elementName}**\n\n`);
            }

            // Dependencies section
            if (cachedInfo.enhanced_dependencies && cachedInfo.enhanced_dependencies.length > 0) {
                hoverContent.appendMarkdown(`**Dependencies (${cachedInfo.dependency_count}):**\n`);
                cachedInfo.enhanced_dependencies.slice(0, 5).forEach(dep => {
                    const tooltip = dep.documentation ? dep.documentation.replace(/\n/g, ' ').substring(0, 100) : `${dep.element_type} in ${dep.file_path}`;
                    hoverContent.appendMarkdown(`• [${dep.name}](command:pytestembed.navigateToDefinition?${encodeURIComponent(JSON.stringify({file: dep.file_path, name: dep.name}))} "${tooltip}")\n`);
                });
                if (cachedInfo.enhanced_dependencies.length > 5) {
                    hoverContent.appendMarkdown(`• ... and ${cachedInfo.enhanced_dependencies.length - 5} more\n`);
                }
                hoverContent.appendMarkdown(`\n`);
            } else if (cachedInfo.dependencies && cachedInfo.dependencies.length > 0) {
                // Fallback to original format if enhanced not available
                hoverContent.appendMarkdown(`**Dependencies (${cachedInfo.dependency_count}):**\n`);
                cachedInfo.dependencies.slice(0, 5).forEach(dep => {
                    const [depFile, depName] = dep.split(':');
                    hoverContent.appendMarkdown(`• [${depName}](command:pytestembed.navigateToDefinition?${encodeURIComponent(JSON.stringify({file: depFile, name: depName}))})\n`);
                });
                if (cachedInfo.dependencies.length > 5) {
                    hoverContent.appendMarkdown(`• ... and ${cachedInfo.dependencies.length - 5} more\n`);
                }
                hoverContent.appendMarkdown(`\n`);
            } else {
                hoverContent.appendMarkdown(`**Dependencies:** None\n\n`);
            }

            // Dependents section
            if (cachedInfo.enhanced_dependents && cachedInfo.enhanced_dependents.length > 0) {
                hoverContent.appendMarkdown(`**Used by (${cachedInfo.dependent_count}):**\n`);
                cachedInfo.enhanced_dependents.slice(0, 5).forEach(dep => {
                    const tooltip = dep.documentation ? dep.documentation.replace(/\n/g, ' ').substring(0, 100) : `${dep.element_type} in ${dep.file_path}`;
                    hoverContent.appendMarkdown(`• [${dep.name}](command:pytestembed.navigateToDefinition?${encodeURIComponent(JSON.stringify({file: dep.file_path, name: dep.name}))} "${tooltip}")\n`);
                });
                if (cachedInfo.enhanced_dependents.length > 5) {
                    hoverContent.appendMarkdown(`• ... and ${cachedInfo.enhanced_dependents.length - 5} more\n`);
                }
            } else if (cachedInfo.dependents && cachedInfo.dependents.length > 0) {
                // Fallback to original format if enhanced not available
                hoverContent.appendMarkdown(`**Used by (${cachedInfo.dependent_count}):**\n`);
                cachedInfo.dependents.slice(0, 5).forEach(dep => {
                    const [depFile, depName] = dep.split(':');
                    hoverContent.appendMarkdown(`• [${depName}](command:pytestembed.navigateToDefinition?${encodeURIComponent(JSON.stringify({file: depFile, name: depName}))})\n`);
                });
                if (cachedInfo.dependents.length > 5) {
                    hoverContent.appendMarkdown(`• ... and ${cachedInfo.dependents.length - 5} more\n`);
                }
            } else {
                hoverContent.appendMarkdown(`**Used by:** None (potential dead code)\n`);
            }

            return new vscode.Hover(hoverContent);
        }

        // Request dependency information from the live server if not cached
        if (state.liveTestSocket && state.liveTestSocket.readyState === 1) {
            try {
                const request = {
                    command: 'get_dependencies',
                    element_id: elementId,
                    file_path: relativePath,
                    element_name: elementName,
                    line_number: position.line + 1
                };

                state.liveTestSocket.send(JSON.stringify(request));

                // Return a loading hover
                const hoverContent = new vscode.MarkdownString();
                hoverContent.appendMarkdown(`**${elementName}** - Dependency Information\n\n`);
                hoverContent.appendMarkdown(`🔍 Loading dependency information...\n\n`);
                hoverContent.appendMarkdown(`*Hover again in a moment for updated information*`);

                return new vscode.Hover(hoverContent);
            } catch (error) {
                console.error('Error requesting dependency information:', error);
            }
        }

        // Fallback hover when live server is not available
        const hoverContent = new vscode.MarkdownString();
        hoverContent.appendMarkdown(`**${elementName}**\n\n`);
        hoverContent.appendMarkdown(`🔗 Dependency information available when Live Test Server is connected\n\n`);
        hoverContent.appendMarkdown(`Start the Live Test Server to see:\n`);
        hoverContent.appendMarkdown(`• What this depends on\n`);
        hoverContent.appendMarkdown(`• What depends on this\n`);
        hoverContent.appendMarkdown(`• Dead code detection\n`);
        hoverContent.appendMarkdown(`• Navigation links`);

        return new vscode.Hover(hoverContent);
    }
}

/**
 * Definition provider for navigation to dependencies
 */
class PyTestEmbedDefinitionProvider implements vscode.DefinitionProvider {
    public provideDefinition(document: vscode.TextDocument, position: vscode.Position, token: vscode.CancellationToken): vscode.ProviderResult<vscode.Definition> {
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return;
        }

        const word = document.getText(wordRange);

        // Check if this is a function call that we can navigate to
        if (this.isFunctionCall(document, position, word)) {
            return this.findDefinition(document, word);
        }

        return;
    }

    private isFunctionCall(document: vscode.TextDocument, position: vscode.Position, word: string): boolean {
        const line = document.lineAt(position.line);
        const lineText = line.text;
        const wordStart = line.text.indexOf(word, position.character - word.length);

        // Check if there's a '(' after the word (indicating a function call)
        if (wordStart >= 0 && wordStart + word.length < lineText.length) {
            const nextChar = lineText[wordStart + word.length];
            return nextChar === '(';
        }

        return false;
    }

    private async findDefinition(document: vscode.TextDocument, functionName: string): Promise<vscode.Location[]> {
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!workspaceFolder) {
            return [];
        }

        // Search for the function definition in the workspace
        const files = await vscode.workspace.findFiles('**/*.py', '**/node_modules/**');
        const locations: vscode.Location[] = [];

        for (const file of files) {
            try {
                const fileDocument = await vscode.workspace.openTextDocument(file);
                const text = fileDocument.getText();
                const lines = text.split('\n');

                for (let i = 0; i < lines.length; i++) {
                    const line = lines[i];
                    const trimmed = line.trim();

                    // Look for function or class definitions
                    if ((trimmed.startsWith(`def ${functionName}(`) ||
                         trimmed.startsWith(`class ${functionName}(`)) &&
                        trimmed.endsWith(':')) {

                        const position = new vscode.Position(i, line.indexOf(functionName));
                        locations.push(new vscode.Location(file, position));
                    }
                }
            } catch (error) {
                // Skip files that can't be read
                continue;
            }
        }

        return locations;
    }
}

/**
 * Check if a document contains PyTestEmbed syntax
 */
function isPyTestEmbedFile(document: vscode.TextDocument): boolean {
    const text = document.getText();
    return text.includes('test:') || text.includes('doc:');
}
