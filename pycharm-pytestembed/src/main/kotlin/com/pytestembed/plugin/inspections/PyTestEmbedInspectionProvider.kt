package com.pytestembed.plugin.inspections

import com.intellij.codeInspection.InspectionToolProvider

/**
 * Provides custom inspections for PyTestEmbed files.
 * Mainly used to suppress standard Python inspections within test: and doc: blocks.
 */
class PyTestEmbedInspectionProvider : InspectionToolProvider {
    
    override fun getInspectionClasses(): Array<Class<*>> {
        return arrayOf(
            PyTestEmbedBlockInspection::class.java
        )
    }
}
