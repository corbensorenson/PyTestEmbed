package com.pytestembed.plugin.highlighting

import com.intellij.lexer.Lexer
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors
import com.intellij.openapi.editor.colors.TextAttributesKey
import com.intellij.openapi.fileTypes.SyntaxHighlighterBase
import com.intellij.psi.tree.IElementType
import com.jetbrains.python.highlighting.PyHighlighter
import com.jetbrains.python.lexer.PythonLexer
import com.jetbrains.python.psi.PyElementTypes

/**
 * Syntax highlighter for PyTestEmbed blocks within Python files.
 * Extends Python syntax highlighting to add special highlighting for test: and doc: blocks.
 */
class PyTestEmbedSyntaxHighlighter : SyntaxHighlighterBase() {
    
    companion object {
        // Define custom text attribute keys for PyTestEmbed syntax
        val TEST_KEYWORD = TextAttributesKey.createTextAttributesKey(
            "PYTESTEMBED_TEST_KEYWORD",
            DefaultLanguageHighlighterColors.KEYWORD
        )
        
        val DOC_KEYWORD = TextAttributesKey.createTextAttributesKey(
            "PYTESTEMBED_DOC_KEYWORD", 
            DefaultLanguageHighlighterColors.KEYWORD
        )
        
        val TEST_ASSERTION = TextAttributesKey.createTextAttributesKey(
            "PYTESTEMBED_TEST_ASSERTION",
            DefaultLanguageHighlighterColors.OPERATION_SIGN
        )
        
        val TEST_MESSAGE = TextAttributesKey.createTextAttributesKey(
            "PYTESTEMBED_TEST_MESSAGE",
            DefaultLanguageHighlighterColors.STRING
        )
        
        val DOC_CONTENT = TextAttributesKey.createTextAttributesKey(
            "PYTESTEMBED_DOC_CONTENT",
            DefaultLanguageHighlighterColors.DOC_COMMENT
        )
        
        private val PYTHON_HIGHLIGHTER = PyHighlighter()
    }
    
    override fun getHighlightingLexer(): Lexer {
        return PythonLexer()
    }
    
    override fun getTokenHighlights(tokenType: IElementType?): Array<TextAttributesKey> {
        // First, get the default Python highlighting
        val pythonHighlights = PYTHON_HIGHLIGHTER.getTokenHighlights(tokenType)
        
        // Add PyTestEmbed-specific highlighting
        return when (tokenType) {
            PyElementTypes.IDENTIFIER -> {
                // This would need more sophisticated logic to detect test: and doc: keywords
                // For now, we'll rely on the folding and inspection features
                pythonHighlights
            }
            else -> pythonHighlights
        }
    }
}
