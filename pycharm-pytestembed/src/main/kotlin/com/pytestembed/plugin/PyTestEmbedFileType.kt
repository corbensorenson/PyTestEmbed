package com.pytestembed.plugin

import com.intellij.openapi.fileTypes.FileType
import com.intellij.openapi.vfs.VirtualFile
import com.jetbrains.python.PythonFileType
import javax.swing.Icon

/**
 * File type for Python files with PyTestEmbed syntax.
 * Extends the standard Python file type to add PyTestEmbed-specific features.
 */
class PyTestEmbedFileType : FileType {
    
    companion object {
        @JvmStatic
        val INSTANCE = PyTestEmbedFileType()
    }
    
    override fun getName(): String = "Python with PyTestEmbed"
    
    override fun getDescription(): String = "Python file with embedded test and documentation blocks"
    
    override fun getDefaultExtension(): String = "py"
    
    override fun getIcon(): Icon? = PythonFileType.INSTANCE.icon
    
    override fun isBinary(): Boolean = false
    
    override fun isReadOnly(): Boolean = false
    
    override fun getCharset(file: VirtualFile, content: ByteArray): String? = null
    
    /**
     * Determines if a file contains PyTestEmbed syntax by checking for test: or doc: blocks.
     */
    fun isPyTestEmbedFile(content: String): Boolean {
        return content.contains(Regex("^\\s*(test|doc):\\s*$", RegexOption.MULTILINE))
    }
}
