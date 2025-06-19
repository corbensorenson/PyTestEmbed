package com.pytestembed.plugin.actions

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.editor.Editor
import com.intellij.openapi.project.Project
import com.pytestembed.plugin.services.SmartGenerationService

class GenerateSmartBlocksAction : AnAction(
    "Generate Test & Doc Blocks (AI)",
    "Generate both test and documentation blocks using AI",
    null
) {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        
        val caretModel = editor.caretModel
        val lineNumber = caretModel.logicalPosition.line + 1 // Convert to 1-based
        
        val smartGenerationService = SmartGenerationService.getInstance(project)
        smartGenerationService.generateBothBlocks(editor, lineNumber)
    }
    
    override fun update(e: AnActionEvent) {
        val project = e.project
        val editor = e.getData(CommonDataKeys.EDITOR)
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        
        e.presentation.isEnabledAndVisible = project != null && 
                                           editor != null && 
                                           virtualFile != null && 
                                           virtualFile.extension == "py"
    }
}

class GenerateTestBlockAction : AnAction(
    "Generate Test Block (AI)",
    "Generate test block using AI",
    null
) {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        
        val caretModel = editor.caretModel
        val lineNumber = caretModel.logicalPosition.line + 1 // Convert to 1-based
        
        val smartGenerationService = SmartGenerationService.getInstance(project)
        smartGenerationService.generateTestBlocks(editor, lineNumber)
    }
    
    override fun update(e: AnActionEvent) {
        val project = e.project
        val editor = e.getData(CommonDataKeys.EDITOR)
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        
        e.presentation.isEnabledAndVisible = project != null && 
                                           editor != null && 
                                           virtualFile != null && 
                                           virtualFile.extension == "py"
    }
}

class GenerateDocBlockAction : AnAction(
    "Generate Doc Block (AI)",
    "Generate documentation block using AI",
    null
) {
    
    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        
        val caretModel = editor.caretModel
        val lineNumber = caretModel.logicalPosition.line + 1 // Convert to 1-based
        
        val smartGenerationService = SmartGenerationService.getInstance(project)
        smartGenerationService.generateDocBlocks(editor, lineNumber)
    }
    
    override fun update(e: AnActionEvent) {
        val project = e.project
        val editor = e.getData(CommonDataKeys.EDITOR)
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        
        e.presentation.isEnabledAndVisible = project != null && 
                                           editor != null && 
                                           virtualFile != null && 
                                           virtualFile.extension == "py"
    }
}
