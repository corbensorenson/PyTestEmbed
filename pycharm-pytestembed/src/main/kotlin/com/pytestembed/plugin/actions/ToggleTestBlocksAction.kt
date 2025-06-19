package com.pytestembed.plugin.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.project.Project
import com.pytestembed.plugin.services.PyTestEmbedStateService

/**
 * Action to toggle visibility of test: blocks in the current file.
 * This action maintains state and provides visual feedback.
 */
class ToggleTestBlocksAction : AnAction() {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        
        val stateService = PyTestEmbedStateService.getInstance(project)
        val currentState = stateService.areTestBlocksVisible()
        
        if (currentState) {
            foldBlocksOfType(editor, "test")
            stateService.setTestBlocksVisible(false)
        } else {
            unfoldBlocksOfType(editor, "test")
            stateService.setTestBlocksVisible(true)
        }
        
        // Update the action presentation
        updatePresentation(e, !currentState)
    }
    
    override fun update(e: AnActionEvent) {
        val editor = e.getData(CommonDataKeys.EDITOR)
        val project = e.project
        
        e.presentation.isEnabledAndVisible = editor != null && project != null
        
        if (project != null) {
            val stateService = PyTestEmbedStateService.getInstance(project)
            updatePresentation(e, stateService.areTestBlocksVisible())
        }
    }
    
    private fun updatePresentation(e: AnActionEvent, visible: Boolean) {
        e.presentation.text = if (visible) "Hide Test Blocks" else "Show Test Blocks"
        e.presentation.description = if (visible) 
            "Hide all test: blocks in the current file" else 
            "Show all test: blocks in the current file"
    }
    
    /**
     * Fold all blocks of the specified type.
     */
    private fun foldBlocksOfType(editor: Editor, blockType: String) {
        val document = editor.document
        val text = document.text
        val lines = text.split('\n')
        
        val foldingModel = editor.foldingModel
        
        foldingModel.runBatchFoldingOperation {
            for (i in lines.indices) {
                val line = lines[i]
                val trimmedLine = line.trim()
                
                if (trimmedLine == "$blockType:") {
                    val startOffset = getLineStartOffset(text, i)
                    val endLine = findBlockEnd(lines, i)
                    
                    if (endLine > i) {
                        val endOffset = getLineEndOffset(text, endLine)
                        
                        val existingRegion = foldingModel.getCollapsedRegionAtOffset(startOffset)
                        if (existingRegion == null) {
                            val foldRegion = foldingModel.addFoldRegion(startOffset, endOffset, "$blockType: ...")
                            foldRegion?.isExpanded = false
                        } else {
                            existingRegion.isExpanded = false
                        }
                    }
                }
            }
        }
    }
    
    /**
     * Unfold all blocks of the specified type.
     */
    private fun unfoldBlocksOfType(editor: Editor, blockType: String) {
        val document = editor.document
        val text = document.text
        val lines = text.split('\n')
        
        val foldingModel = editor.foldingModel
        
        foldingModel.runBatchFoldingOperation {
            for (i in lines.indices) {
                val line = lines[i]
                val trimmedLine = line.trim()
                
                if (trimmedLine == "$blockType:") {
                    val startOffset = getLineStartOffset(text, i)
                    val existingRegion = foldingModel.getCollapsedRegionAtOffset(startOffset)
                    existingRegion?.isExpanded = true
                }
            }
        }
    }
    
    private fun findBlockEnd(lines: List<String>, startLine: Int): Int {
        if (startLine >= lines.size - 1) return startLine
        
        val baseIndent = getIndentLevel(lines[startLine])
        
        for (i in (startLine + 1) until lines.size) {
            val line = lines[i]
            if (line.trim().isEmpty()) continue
            
            val indent = getIndentLevel(line)
            if (indent <= baseIndent) {
                return i - 1
            }
        }
        
        return lines.size - 1
    }
    
    private fun getIndentLevel(line: String): Int {
        return line.takeWhile { it == ' ' || it == '\t' }.length
    }
    
    private fun getLineStartOffset(text: String, lineNumber: Int): Int {
        val lines = text.split('\n')
        if (lineNumber >= lines.size) return text.length
        
        var offset = 0
        for (i in 0 until lineNumber) {
            offset += lines[i].length + 1
        }
        
        return offset
    }
    
    private fun getLineEndOffset(text: String, lineNumber: Int): Int {
        val lines = text.split('\n')
        if (lineNumber >= lines.size) return text.length
        
        var offset = 0
        for (i in 0 until lineNumber) {
            offset += lines[i].length + 1
        }
        offset += lines[lineNumber].length
        
        return minOf(offset, text.length)
    }
}
