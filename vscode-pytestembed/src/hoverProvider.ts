import * as vscode from 'vscode';
import * as WebSocket from 'ws';

interface EnhancedDependency {
    id: string;
    name: string;
    file_path: string;
    line_number: number;
    documentation: string;
    element_type: string;
}

interface DependencyInfo {
    type: string;
    element_id: string;
    element_name: string;
    file_path: string;
    line_number: number;
    dependencies: string[];
    dependents: string[];
    enhanced_dependencies: EnhancedDependency[];
    enhanced_dependents: EnhancedDependency[];
    dependency_count: number;
    dependent_count: number;
}

export class PyTestEmbedHoverProvider implements vscode.HoverProvider {
    
    async provideHover(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | undefined> {

        // Get the word at the current position
        const wordRange = document.getWordRangeAtPosition(position);
        if (!wordRange) {
            return undefined;
        }

        const word = document.getText(wordRange);

        // Only provide hover for function/method names (simple heuristic)
        if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(word)) {
            return undefined;
        }

        // Skip common keywords and built-ins
        const skipWords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'finally',
                          'import', 'from', 'return', 'yield', 'pass', 'break', 'continue', 'self', 'cls',
                          'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'with', 'as'];
        if (skipWords.includes(word)) {
            return undefined;
        }

        // Get the current line to determine context
        const currentLine = document.lineAt(position.line);
        const lineText = currentLine.text;

        // Check if we're hovering over a function/class definition
        const isDefinition = lineText.trim().startsWith('def ') || lineText.trim().startsWith('class ');

        // Skip single-letter variables but allow class names (usually capitalized)
        if (!isDefinition && word.length === 1) {
            return undefined;
        }

        // Skip common variable patterns but allow class names
        if (!isDefinition && /^[a-z]+$/.test(word) && word.length > 1) {
            // Allow if it looks like a class name (starts with capital) or common function names
            if (!/^[A-Z]/.test(word) && !['foo', 'bar', 'baz', 'main'].includes(word)) {
                return undefined;
            }
        }

        // Get workspace folder
        const workspaceFolder = vscode.workspace.getWorkspaceFolder(document.uri);
        if (!workspaceFolder) {
            return undefined;
        }

        const relativePath = require('path').relative(workspaceFolder.uri.fsPath, document.uri.fsPath);
        const lineNumber = position.line + 1; // Convert to 1-based

        try {
            if (isDefinition) {
                // For function/class definitions, show dependencies
                const dependencyInfo = await this.getDependencyInfo(relativePath, word, lineNumber);
                if (dependencyInfo) {
                    return this.createDependencyHover(dependencyInfo);
                }
            } else {
                // For function calls, show documentation only
                const docInfo = await this.getDocumentationInfo(relativePath, word);
                if (docInfo) {
                    return await this.createDocumentationHover(word, docInfo, relativePath);
                }
            }
        } catch (error) {
            console.error('Error getting hover info:', error);
        }

        return undefined;
    }
    
    private async getDependencyInfo(filePath: string, elementName: string, lineNumber: number): Promise<DependencyInfo | null> {
        return new Promise((resolve, reject) => {
            // Connect to dedicated dependency service
            const ws = new WebSocket('ws://localhost:8770');

            const timeout = setTimeout(() => {
                ws.close();
                console.log(`⏰ Timeout getting dependency info for ${elementName}`);
                resolve(null);
            }, 5000); // Increased timeout

            ws.on('open', () => {
                const request = {
                    command: 'get_dependencies',
                    file_path: filePath,
                    element_name: elementName,
                    line_number: lineNumber
                };
                console.log(`🔍 Requesting dependency info for ${elementName} at ${filePath}:${lineNumber}`);
                ws.send(JSON.stringify(request));
            });

            ws.on('message', (data: WebSocket.Data) => {
                clearTimeout(timeout);
                try {
                    const response = JSON.parse(data.toString());
                    console.log(`📨 Received response type: ${response.type}`);

                    if (response.type === 'dependency_info') {
                        ws.close();
                        console.log(`✅ Got dependency info for ${elementName}: ${response.dependency_count} deps, ${response.dependent_count} dependents`);
                        resolve(response as DependencyInfo);
                    } else if (response.type === 'error') {
                        ws.close();
                        console.log(`❌ Error from dependency service: ${response.message}`);
                        resolve(null);
                    } else {
                        // Unexpected response type, keep waiting
                        console.log(`⚠️ Unexpected response type: ${response.type}`);
                    }
                } catch (error) {
                    ws.close();
                    console.log(`❌ Error parsing response: ${error}`);
                    reject(error);
                }
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                console.log(`❌ WebSocket error: ${error}`);
                reject(error);
            });

            ws.on('close', () => {
                clearTimeout(timeout);
            });
        });
    }
    
    private async getDocumentationInfo(filePath: string, elementName: string): Promise<string | null> {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://localhost:8770');

            const timeout = setTimeout(() => {
                ws.close();
                console.log(`⏰ Timeout getting documentation for ${elementName}`);
                resolve(null);
            }, 3000);

            ws.on('open', () => {
                const request = {
                    command: 'get_element_documentation',
                    file_path: filePath,
                    element_name: elementName
                };
                console.log(`📖 Requesting documentation for ${elementName}`);
                ws.send(JSON.stringify(request));
            });

            ws.on('message', (data: WebSocket.Data) => {
                clearTimeout(timeout);
                try {
                    const response = JSON.parse(data.toString());
                    console.log(`📨 Documentation response: ${response.type}`);

                    if (response.type === 'element_documentation') {
                        ws.close();
                        console.log(`✅ Got documentation for ${elementName}: ${response.documentation ? 'found' : 'not found'}`);
                        resolve(response.documentation || null);
                    } else if (response.type === 'error') {
                        ws.close();
                        console.log(`❌ Error getting documentation: ${response.message}`);
                        resolve(null);
                    }
                } catch (error) {
                    ws.close();
                    console.log(`❌ Error parsing documentation response: ${error}`);
                    reject(error);
                }
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                console.log(`❌ WebSocket error getting documentation: ${error}`);
                reject(error);
            });
        });
    }

    private async getElementLocation(filePath: string, elementName: string): Promise<{file_path: string, line_number: number} | null> {
        return new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://localhost:8770');

            const timeout = setTimeout(() => {
                ws.close();
                resolve(null);
            }, 3000);

            ws.on('open', () => {
                const request = {
                    command: 'get_dependencies',
                    file_path: filePath,
                    element_name: elementName,
                    line_number: 1
                };
                ws.send(JSON.stringify(request));
            });

            ws.on('message', (data: WebSocket.Data) => {
                clearTimeout(timeout);
                try {
                    const response = JSON.parse(data.toString());

                    if (response.type === 'dependency_info') {
                        ws.close();
                        // Return the element's own location
                        resolve({
                            file_path: response.file_path || filePath,
                            line_number: response.line_number || 1
                        });
                    } else {
                        ws.close();
                        resolve(null);
                    }
                } catch (error) {
                    ws.close();
                    resolve(null);
                }
            });

            ws.on('error', (error) => {
                clearTimeout(timeout);
                resolve(null);
            });
        });
    }

    private async createDocumentationHover(elementName: string, documentation: string, filePath: string): Promise<vscode.Hover> {
        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;

        // Try to get the element location for navigation
        const elementInfo = await this.getElementLocation(filePath, elementName);

        if (elementInfo) {
            // Use a simpler command URI format
            const navigateUri = vscode.Uri.parse(`command:pytestembed.navigateToElement?${encodeURIComponent(JSON.stringify(elementInfo))}`);
            markdown.appendMarkdown(`**📖 [${elementName}](${navigateUri}) 🔗**\n\n`);
        } else {
            markdown.appendMarkdown(`**📖 ${elementName}**\n\n`);
        }

        markdown.appendMarkdown(`${documentation}\n`);
        return new vscode.Hover(markdown);
    }

    private createDependencyHover(info: DependencyInfo): vscode.Hover {
        const markdown = new vscode.MarkdownString();
        markdown.isTrusted = true;

        // Header
        markdown.appendMarkdown(`**🔗 ${info.element_name}**\n\n`);
        
        // Dependencies section
        if (info.enhanced_dependencies.length > 0) {
            markdown.appendMarkdown(`**📥 Dependencies (${info.dependency_count}):**\n\n`);

            for (const dep of info.enhanced_dependencies) {
                // Use simpler command URI format
                const navigateUri = vscode.Uri.parse(`command:pytestembed.navigateToElement?${encodeURIComponent(JSON.stringify({file_path: dep.file_path, line_number: dep.line_number}))}`);
                markdown.appendMarkdown(`• [**${dep.name}**](${navigateUri}) (${dep.element_type}) 🔗`);

                if (dep.documentation) {
                    markdown.appendMarkdown(`  \n  📝 ${dep.documentation}`);
                }

                markdown.appendMarkdown(`\n\n`);
            }
        }
        
        // Dependents section
        if (info.enhanced_dependents.length > 0) {
            markdown.appendMarkdown(`**📤 Used by (${info.dependent_count}):**\n\n`);

            for (const dep of info.enhanced_dependents) {
                // Use simpler command URI format
                const navigateUri = vscode.Uri.parse(`command:pytestembed.navigateToElement?${encodeURIComponent(JSON.stringify({file_path: dep.file_path, line_number: dep.line_number}))}`);
                markdown.appendMarkdown(`• [**${dep.name}**](${navigateUri}) (${dep.element_type}) 🔗`);

                if (dep.documentation) {
                    markdown.appendMarkdown(`  \n  📝 ${dep.documentation}`);
                }

                markdown.appendMarkdown(`\n\n`);
            }
        }
        
        // If no dependencies or dependents
        if (info.enhanced_dependencies.length === 0 && info.enhanced_dependents.length === 0) {
            markdown.appendMarkdown(`*No dependencies or dependents found.*`);
        }
        
        return new vscode.Hover(markdown);
    }
}

export function registerHoverProvider(context: vscode.ExtensionContext) {
    const hoverProvider = new PyTestEmbedHoverProvider();
    
    const disposable = vscode.languages.registerHoverProvider(
        { scheme: 'file', language: 'python' },
        hoverProvider
    );
    
    context.subscriptions.push(disposable);
}
