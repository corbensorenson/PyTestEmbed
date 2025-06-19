package com.pytestembed.plugin.inspections

import com.intellij.codeInspection.LocalInspectionTool
import com.intellij.codeInspection.ProblemsHolder
import com.intellij.psi.PsiElementVisitor
import com.jetbrains.python.inspections.PyInspectionVisitor
import com.jetbrains.python.psi.PyFile

/**
 * Custom inspection for PyTestEmbed blocks.
 * Suppresses standard Python inspections within test: and doc: blocks.
 */
class PyTestEmbedBlockInspection : LocalInspectionTool() {
    
    override fun buildVisitor(holder: ProblemsHolder, isOnTheFly: Boolean): PsiElementVisitor {
        return object : PyInspectionVisitor(holder, getContext(holder)) {
            
            override fun visitPyFile(node: PyFile) {
                // Check if this file contains PyTestEmbed syntax
                val text = node.text
                if (containsPyTestEmbedBlocks(text)) {
                    // For files with PyTestEmbed blocks, we could implement
                    // custom logic to suppress certain inspections within
                    // test: and doc: blocks
                    
                    // This is a placeholder - in a full implementation,
                    // we would analyze the AST to identify test: and doc: blocks
                    // and suppress inspections within those ranges
                }
                
                super.visitPyFile(node)
            }
        }
    }
    
    override fun getDisplayName(): String = "PyTestEmbed Block Inspection"
    
    override fun getShortName(): String = "PyTestEmbedBlock"
    
    override fun getGroupDisplayName(): String = "PyTestEmbed"
    
    override fun isEnabledByDefault(): Boolean = true
    
    /**
     * Check if the file contains PyTestEmbed test: or doc: blocks.
     */
    private fun containsPyTestEmbedBlocks(text: String): Boolean {
        return text.contains(Regex("^\\s*(test|doc):\\s*$", RegexOption.MULTILINE))
    }
}
