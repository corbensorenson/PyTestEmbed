package com.pytestembed.plugin.folding

import com.intellij.lang.ASTNode
import com.intellij.lang.folding.FoldingBuilderEx
import com.intellij.lang.folding.FoldingDescriptor
import com.intellij.openapi.document.Document
import com.intellij.openapi.editor.Document
import com.intellij.openapi.util.TextRange
import com.intellij.psi.PsiElement
import com.intellij.psi.util.PsiTreeUtil
import com.jetbrains.python.psi.PyFile

/**
 * Folding builder for PyTestEmbed test: and doc: blocks.
 * Allows collapsing these blocks for cleaner code view.
 */
class PyTestEmbedFoldingBuilder : FoldingBuilderEx() {
    
    override fun buildFoldRegions(root: PsiElement, document: Document, quick: Boolean): Array<FoldingDescriptor> {
        val descriptors = mutableListOf<FoldingDescriptor>()
        
        if (root !is PyFile) return descriptors.toTypedArray()
        
        val text = document.text
        val lines = text.split('\n')
        
        for (i in lines.indices) {
            val line = lines[i]
            val trimmedLine = line.trim()
            
            // Check for test: or doc: blocks
            if (trimmedLine == "test:" || trimmedLine == "doc:") {
                val startOffset = text.indexOf(line, if (i == 0) 0 else text.indexOf('\n', 0).let { 
                    var pos = it
                    repeat(i - 1) { pos = text.indexOf('\n', pos + 1) }
                    pos + 1
                })
                
                if (startOffset >= 0) {
                    val blockEnd = findBlockEnd(lines, i)
                    if (blockEnd > i) {
                        val endOffset = getLineEndOffset(text, blockEnd)
                        if (endOffset > startOffset) {
                            val range = TextRange(startOffset, endOffset)
                            val placeholderText = if (trimmedLine == "test:") "test: ..." else "doc: ..."
                            descriptors.add(FoldingDescriptor(root.node, range, null, placeholderText))
                        }
                    }
                }
            }
        }
        
        return descriptors.toTypedArray()
    }
    
    override fun getPlaceholderText(node: ASTNode): String? {
        val text = node.text
        return when {
            text.trim().startsWith("test:") -> "test: ..."
            text.trim().startsWith("doc:") -> "doc: ..."
            else -> "..."
        }
    }
    
    override fun isCollapsedByDefault(node: ASTNode): Boolean {
        // Don't collapse by default, let users choose
        return false
    }
    
    /**
     * Find the end of a test: or doc: block by looking for the next line
     * with the same or less indentation.
     */
    private fun findBlockEnd(lines: List<String>, startLine: Int): Int {
        if (startLine >= lines.size - 1) return startLine
        
        val baseIndent = getIndentLevel(lines[startLine])
        
        for (i in (startLine + 1) until lines.size) {
            val line = lines[i]
            if (line.trim().isEmpty()) continue // Skip empty lines
            
            val indent = getIndentLevel(line)
            if (indent <= baseIndent) {
                return i - 1
            }
        }
        
        return lines.size - 1
    }
    
    /**
     * Get the indentation level of a line (number of leading spaces).
     */
    private fun getIndentLevel(line: String): Int {
        return line.takeWhile { it == ' ' || it == '\t' }.length
    }
    
    /**
     * Get the end offset of a specific line in the document.
     */
    private fun getLineEndOffset(text: String, lineNumber: Int): Int {
        val lines = text.split('\n')
        if (lineNumber >= lines.size) return text.length
        
        var offset = 0
        for (i in 0 until lineNumber) {
            offset += lines[i].length + 1 // +1 for newline
        }
        offset += lines[lineNumber].length
        
        return minOf(offset, text.length)
    }
}
