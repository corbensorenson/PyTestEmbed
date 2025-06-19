package com.pytestembed.plugin.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.editor.Editor
import com.pytestembed.plugin.services.PyTestEmbedStateService

/**
 * Action to show all test: and doc: blocks in the current file.
 */
class ShowAllBlocksAction : AnAction() {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        
        val stateService = PyTestEmbedStateService.getInstance(project)
        
        // Unfold all blocks
        unfoldAllBlocks(editor)
        
        // Update state
        stateService.showAllBlocks()
    }
    
    override fun update(e: AnActionEvent) {
        val editor = e.getData(CommonDataKeys.EDITOR)
        e.presentation.isEnabledAndVisible = editor != null
    }
    
    private fun unfoldAllBlocks(editor: Editor) {
        val foldingModel = editor.foldingModel
        
        foldingModel.runBatchFoldingOperation {
            val allRegions = foldingModel.allFoldRegions
            for (region in allRegions) {
                if (region.placeholderText?.contains("test:") == true || 
                    region.placeholderText?.contains("doc:") == true) {
                    region.isExpanded = true
                }
            }
        }
    }
}
