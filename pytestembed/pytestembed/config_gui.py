"""
PyTestEmbed Configuration GUI

Tkinter-based GUI for configuring PyTestEmbed settings including AI providers,
models, custom prompts, and general preferences.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from typing import Dict, Any
from .config_manager import get_config_manager, ConfigManager


class ConfigGUI:
    """Main configuration GUI for PyTestEmbed."""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.root = tk.Tk()
        self.root.title("PyTestEmbed Configuration")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables for form fields
        self.vars = {}
        self.setup_variables()
        
        # Create GUI
        self.create_widgets()
        self.load_current_config()
    
    def setup_variables(self):
        """Setup tkinter variables for form fields."""
        # AI Provider settings
        self.vars['ai_provider'] = tk.StringVar()
        self.vars['ollama_url'] = tk.StringVar()
        self.vars['ollama_model'] = tk.StringVar()
        self.vars['lmstudio_url'] = tk.StringVar()
        self.vars['lmstudio_model'] = tk.StringVar()
        self.vars['temperature'] = tk.DoubleVar()
        self.vars['max_tokens'] = tk.IntVar()
        self.vars['no_think'] = tk.BooleanVar()
        self.vars['python_interpreter'] = tk.StringVar()
        
        # General settings
        self.vars['cache_enabled'] = tk.BooleanVar()
        self.vars['cache_dir'] = tk.StringVar()
        self.vars['temp_dir'] = tk.StringVar()
        self.vars['verbose'] = tk.BooleanVar()
        self.vars['test_timeout'] = tk.IntVar()
        self.vars['auto_generate_tests'] = tk.BooleanVar()
        self.vars['auto_generate_docs'] = tk.BooleanVar()
        self.vars['live_testing'] = tk.BooleanVar()
        
        # IDE settings
        self.vars['vscode_integration'] = tk.BooleanVar()
        self.vars['pycharm_integration'] = tk.BooleanVar()
        self.vars['live_server_port'] = tk.IntVar()

        # MCP Server settings
        self.vars['mcp_server_enabled'] = tk.BooleanVar()
        self.vars['mcp_server_port'] = tk.IntVar()
        self.vars['auto_start_mcp_server'] = tk.BooleanVar()
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_ai_tab()
        self.create_general_tab()
        self.create_prompts_tab()
        self.create_advanced_tab()
        
        # Create bottom buttons
        self.create_bottom_buttons()
    
    def create_ai_tab(self):
        """Create AI provider configuration tab."""
        ai_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_frame, text="AI Provider")
        
        # Provider selection
        provider_frame = ttk.LabelFrame(ai_frame, text="AI Provider", padding=10)
        provider_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(provider_frame, text="Provider:").grid(row=0, column=0, sticky=tk.W, pady=2)
        provider_combo = ttk.Combobox(provider_frame, textvariable=self.vars['ai_provider'],
                                     values=["ollama", "lmstudio"], state="readonly")
        provider_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        provider_combo.bind('<<ComboboxSelected>>', self.on_provider_changed)
        
        # Test connection button
        test_btn = ttk.Button(provider_frame, text="Test Connection", command=self.test_connection)
        test_btn.grid(row=0, column=2, padx=(20, 0), pady=2)
        
        # Ollama settings
        ollama_frame = ttk.LabelFrame(ai_frame, text="Ollama Settings", padding=10)
        ollama_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(ollama_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(ollama_frame, textvariable=self.vars['ollama_url'], width=30).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(ollama_frame, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ollama_model_combo = ttk.Combobox(ollama_frame, textvariable=self.vars['ollama_model'], width=27)
        self.ollama_model_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        refresh_ollama_btn = ttk.Button(ollama_frame, text="Refresh Models", 
                                       command=lambda: self.refresh_models("ollama"))
        refresh_ollama_btn.grid(row=1, column=2, padx=(10, 0), pady=2)
        
        # LMStudio settings
        lmstudio_frame = ttk.LabelFrame(ai_frame, text="LMStudio Settings", padding=10)
        lmstudio_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(lmstudio_frame, text="URL:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(lmstudio_frame, textvariable=self.vars['lmstudio_url'], width=30).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(lmstudio_frame, text="Model:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lmstudio_model_combo = ttk.Combobox(lmstudio_frame, textvariable=self.vars['lmstudio_model'], width=27)
        self.lmstudio_model_combo.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        refresh_lmstudio_btn = ttk.Button(lmstudio_frame, text="Refresh Models",
                                         command=lambda: self.refresh_models("lmstudio"))
        refresh_lmstudio_btn.grid(row=1, column=2, padx=(10, 0), pady=2)
        
        # Generation settings
        gen_frame = ttk.LabelFrame(ai_frame, text="Generation Settings", padding=10)
        gen_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(gen_frame, text="Temperature:").grid(row=0, column=0, sticky=tk.W, pady=2)
        temp_scale = ttk.Scale(gen_frame, from_=0.0, to=1.0, variable=self.vars['temperature'], 
                              orient=tk.HORIZONTAL, length=200)
        temp_scale.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        temp_label = ttk.Label(gen_frame, text="0.3")
        temp_label.grid(row=0, column=2, padx=(10, 0), pady=2)
        
        def update_temp_label(val):
            temp_label.config(text=f"{float(val):.2f}")
        temp_scale.config(command=update_temp_label)
        
        ttk.Label(gen_frame, text="Max Tokens:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(gen_frame, from_=100, to=4000, textvariable=self.vars['max_tokens'],
                   width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        # No Think option
        ttk.Checkbutton(gen_frame, text="Disable AI reasoning (/no_think)",
                       variable=self.vars['no_think']).grid(row=2, column=0, columnspan=2,
                                                           sticky=tk.W, pady=5)
        ttk.Label(gen_frame, text="Adds /no_think to prompts for models that support it",
                 font=('TkDefaultFont', 8)).grid(row=3, column=0, columnspan=3,
                                                sticky=tk.W, pady=(0, 5))
    
    def create_general_tab(self):
        """Create general settings tab."""
        general_frame = ttk.Frame(self.notebook)
        self.notebook.add(general_frame, text="General")
        
        # Cache settings
        cache_frame = ttk.LabelFrame(general_frame, text="Cache Settings", padding=10)
        cache_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(cache_frame, text="Enable caching", 
                       variable=self.vars['cache_enabled']).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(cache_frame, text="Cache Directory:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(cache_frame, textvariable=self.vars['cache_dir'], width=40).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        ttk.Label(cache_frame, text="Temp Directory:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(cache_frame, textvariable=self.vars['temp_dir'], width=40).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Testing settings
        test_frame = ttk.LabelFrame(general_frame, text="Testing Settings", padding=10)
        test_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(test_frame, text="Verbose output", 
                       variable=self.vars['verbose']).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(test_frame, text="Auto-generate tests", 
                       variable=self.vars['auto_generate_tests']).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(test_frame, text="Auto-generate docs", 
                       variable=self.vars['auto_generate_docs']).grid(row=2, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(test_frame, text="Enable live testing", 
                       variable=self.vars['live_testing']).grid(row=3, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(test_frame, text="Test Timeout (seconds):").grid(row=4, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(test_frame, from_=5, to=300, textvariable=self.vars['test_timeout'], 
                   width=10).grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=2)
        
        # IDE settings
        ide_frame = ttk.LabelFrame(general_frame, text="IDE Integration", padding=10)
        ide_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Checkbutton(ide_frame, text="VSCode integration", 
                       variable=self.vars['vscode_integration']).grid(row=0, column=0, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(ide_frame, text="PyCharm integration", 
                       variable=self.vars['pycharm_integration']).grid(row=1, column=0, sticky=tk.W, pady=2)
        
        ttk.Label(ide_frame, text="Live Server Port:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(ide_frame, from_=8000, to=9999, textvariable=self.vars['live_server_port'],
                   width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        ttk.Label(ide_frame, text="Python Interpreter:").grid(row=3, column=0, sticky=tk.W, pady=2)
        interpreter_frame = ttk.Frame(ide_frame)
        interpreter_frame.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        ttk.Entry(interpreter_frame, textvariable=self.vars['python_interpreter'], width=30).pack(side=tk.LEFT)
        ttk.Button(interpreter_frame, text="Browse", command=self.browse_python_interpreter).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(ide_frame, text="Path to Python interpreter for live testing",
                 font=('TkDefaultFont', 8)).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # MCP Server settings
        mcp_frame = ttk.LabelFrame(general_frame, text="MCP Server (Agentic Coding)", padding=10)
        mcp_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Checkbutton(mcp_frame, text="Enable MCP Server",
                       variable=self.vars['mcp_server_enabled']).grid(row=0, column=0, sticky=tk.W, pady=2)

        ttk.Checkbutton(mcp_frame, text="Auto-start MCP Server",
                       variable=self.vars['auto_start_mcp_server']).grid(row=1, column=0, sticky=tk.W, pady=2)

        ttk.Label(mcp_frame, text="MCP Server Port:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Spinbox(mcp_frame, from_=3000, to=9999, textvariable=self.vars['mcp_server_port'],
                   width=10).grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=2)

        ttk.Label(mcp_frame, text="Enables AI agents (Augment, Cline) to use PyTestEmbed",
                 font=('TkDefaultFont', 8)).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
    
    def create_prompts_tab(self):
        """Create custom prompts tab."""
        prompts_frame = ttk.Frame(self.notebook)
        self.notebook.add(prompts_frame, text="Custom Prompts")
        
        # Prompt selection
        prompt_select_frame = ttk.Frame(prompts_frame)
        prompt_select_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(prompt_select_frame, text="Prompt Type:").pack(side=tk.LEFT)
        self.prompt_type_var = tk.StringVar(value="test_generation")
        prompt_combo = ttk.Combobox(prompt_select_frame, textvariable=self.prompt_type_var,
                                   values=["test_generation", "doc_generation", "conversion", "unified_docs"],
                                   state="readonly")
        prompt_combo.pack(side=tk.LEFT, padx=(10, 0))
        prompt_combo.bind('<<ComboboxSelected>>', self.on_prompt_type_changed)
        
        # Reset button
        reset_prompt_btn = ttk.Button(prompt_select_frame, text="Reset to Default", 
                                     command=self.reset_current_prompt)
        reset_prompt_btn.pack(side=tk.RIGHT)
        
        # Prompt editor
        editor_frame = ttk.LabelFrame(prompts_frame, text="Prompt Editor", padding=10)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.prompt_text = scrolledtext.ScrolledText(editor_frame, wrap=tk.WORD, height=20)
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        
        # Help text
        help_frame = ttk.Frame(prompts_frame)
        help_frame.pack(fill=tk.X, padx=10, pady=5)
        
        help_text = ("Available placeholders: {function_name}, {parameters}, {return_type}, "
                    "{source_code}, {test_count}, {module_name}, {function_list}")
        ttk.Label(help_frame, text=help_text, foreground="gray").pack()
    
    def create_advanced_tab(self):
        """Create advanced settings tab."""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="Advanced")
        
        # Import/Export
        io_frame = ttk.LabelFrame(advanced_frame, text="Import/Export", padding=10)
        io_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(io_frame, text="Export Config", command=self.export_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="Import Config", command=self.import_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(io_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side=tk.LEFT, padx=5)
        
        # Status and info
        status_frame = ttk.LabelFrame(advanced_frame, text="Status", padding=10)
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=15, state=tk.DISABLED)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Add initial status
        self.add_status("PyTestEmbed Configuration GUI loaded")
        self.add_status(f"Config file: {self.config_manager.config_file}")
    
    def create_bottom_buttons(self):
        """Create bottom action buttons."""
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Apply", command=self.apply_config).pack(side=tk.RIGHT, padx=5)
    
    def load_current_config(self):
        """Load current configuration into GUI."""
        config = self.config_manager.config
        
        # AI Provider settings
        self.vars['ai_provider'].set(config.ai_provider.provider)
        self.vars['ollama_url'].set(config.ai_provider.ollama_url)
        self.vars['ollama_model'].set(config.ai_provider.ollama_model)
        self.vars['lmstudio_url'].set(config.ai_provider.lmstudio_url)
        self.vars['lmstudio_model'].set(config.ai_provider.lmstudio_model)
        self.vars['temperature'].set(config.ai_provider.temperature)
        self.vars['max_tokens'].set(config.ai_provider.max_tokens)
        self.vars['no_think'].set(config.ai_provider.no_think)
        
        # General settings
        self.vars['cache_enabled'].set(config.cache_enabled)
        self.vars['cache_dir'].set(config.cache_dir)
        self.vars['temp_dir'].set(config.temp_dir)
        self.vars['verbose'].set(config.verbose)
        self.vars['test_timeout'].set(config.test_timeout)
        self.vars['auto_generate_tests'].set(config.auto_generate_tests)
        self.vars['auto_generate_docs'].set(config.auto_generate_docs)
        self.vars['live_testing'].set(config.live_testing)
        
        # IDE settings
        self.vars['vscode_integration'].set(config.vscode_integration)
        self.vars['pycharm_integration'].set(config.pycharm_integration)
        self.vars['live_server_port'].set(config.live_server_port)
        self.vars['python_interpreter'].set(config.python_interpreter)

        # MCP Server settings
        self.vars['mcp_server_enabled'].set(config.mcp_server_enabled)
        self.vars['mcp_server_port'].set(config.mcp_server_port)
        self.vars['auto_start_mcp_server'].set(config.auto_start_mcp_server)
        
        # Load current prompt
        self.load_current_prompt()
        
        # Refresh model lists
        self.refresh_models("ollama")
        self.refresh_models("lmstudio")
    
    def load_current_prompt(self):
        """Load the current prompt into the editor."""
        prompt_type = self.prompt_type_var.get()
        prompt = self.config_manager.get_custom_prompt(prompt_type)
        
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, prompt)
    
    def on_provider_changed(self, event=None):
        """Handle AI provider selection change."""
        provider = self.vars['ai_provider'].get()
        self.add_status(f"Selected AI provider: {provider}")
    
    def on_prompt_type_changed(self, event=None):
        """Handle prompt type selection change."""
        self.save_current_prompt()
        self.load_current_prompt()
    
    def save_current_prompt(self):
        """Save the current prompt from the editor."""
        prompt_type = self.prompt_type_var.get()
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        self.config_manager.set_custom_prompt(prompt_type, prompt)
    
    def reset_current_prompt(self):
        """Reset current prompt to default."""
        prompt_type = self.prompt_type_var.get()
        
        # Get default prompt
        if prompt_type == "test_generation":
            default_prompt = self.config_manager._get_default_test_prompt()
        elif prompt_type == "doc_generation":
            default_prompt = self.config_manager._get_default_doc_prompt()
        elif prompt_type == "conversion":
            default_prompt = self.config_manager._get_default_conversion_prompt()
        elif prompt_type == "unified_docs":
            default_prompt = self.config_manager._get_default_unified_docs_prompt()
        else:
            return
        
        self.prompt_text.delete(1.0, tk.END)
        self.prompt_text.insert(1.0, default_prompt)
        self.add_status(f"Reset {prompt_type} prompt to default")
    
    def refresh_models(self, provider: str):
        """Refresh available models for a provider."""
        def _refresh():
            try:
                models = self.config_manager.get_available_models(provider)
                
                if provider == "ollama":
                    self.ollama_model_combo['values'] = models
                elif provider == "lmstudio":
                    self.lmstudio_model_combo['values'] = models
                
                self.add_status(f"Refreshed {provider} models: {len(models)} found")
            except Exception as e:
                self.add_status(f"Error refreshing {provider} models: {e}")
        
        # Run in thread to avoid blocking GUI
        threading.Thread(target=_refresh, daemon=True).start()
    
    def test_connection(self):
        """Test connection to the selected AI provider."""
        def _test():
            provider = self.vars['ai_provider'].get()
            success, message = self.config_manager.test_ai_connection(provider)
            
            if success:
                self.add_status(f"✅ {message}")
                messagebox.showinfo("Connection Test", message)
            else:
                self.add_status(f"❌ {message}")
                messagebox.showerror("Connection Test", message)
        
        threading.Thread(target=_test, daemon=True).start()

    def browse_python_interpreter(self):
        """Browse for Python interpreter."""
        file_path = filedialog.askopenfilename(
            title="Select Python Interpreter",
            filetypes=[("Python executable", "python*"), ("All files", "*.*")]
        )

        if file_path:
            self.vars['python_interpreter'].set(file_path)
            self.add_status(f"Selected Python interpreter: {file_path}")

    def apply_config(self):
        """Apply configuration without saving."""
        self.save_current_prompt()
        
        # Update config object
        config = self.config_manager.config
        
        # AI Provider settings
        config.ai_provider.provider = self.vars['ai_provider'].get()
        config.ai_provider.ollama_url = self.vars['ollama_url'].get()
        config.ai_provider.ollama_model = self.vars['ollama_model'].get()
        config.ai_provider.lmstudio_url = self.vars['lmstudio_url'].get()
        config.ai_provider.lmstudio_model = self.vars['lmstudio_model'].get()
        config.ai_provider.temperature = self.vars['temperature'].get()
        config.ai_provider.max_tokens = self.vars['max_tokens'].get()
        config.ai_provider.no_think = self.vars['no_think'].get()
        
        # General settings
        config.cache_enabled = self.vars['cache_enabled'].get()
        config.cache_dir = self.vars['cache_dir'].get()
        config.temp_dir = self.vars['temp_dir'].get()
        config.verbose = self.vars['verbose'].get()
        config.test_timeout = self.vars['test_timeout'].get()
        config.auto_generate_tests = self.vars['auto_generate_tests'].get()
        config.auto_generate_docs = self.vars['auto_generate_docs'].get()
        config.live_testing = self.vars['live_testing'].get()
        
        # IDE settings
        config.vscode_integration = self.vars['vscode_integration'].get()
        config.pycharm_integration = self.vars['pycharm_integration'].get()
        config.live_server_port = self.vars['live_server_port'].get()
        config.python_interpreter = self.vars['python_interpreter'].get()

        # MCP Server settings
        config.mcp_server_enabled = self.vars['mcp_server_enabled'].get()
        config.mcp_server_port = self.vars['mcp_server_port'].get()
        config.auto_start_mcp_server = self.vars['auto_start_mcp_server'].get()
        
        self.add_status("Configuration applied")
    
    def save_config(self):
        """Save configuration and close."""
        self.apply_config()
        
        if self.config_manager.save_config():
            self.add_status("Configuration saved successfully")
            messagebox.showinfo("Save", "Configuration saved successfully!")
            self.root.quit()
        else:
            messagebox.showerror("Save Error", "Failed to save configuration")
    
    def export_config(self):
        """Export configuration to file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.config_manager.export_config(file_path):
                self.add_status(f"Configuration exported to {file_path}")
                messagebox.showinfo("Export", "Configuration exported successfully!")
            else:
                messagebox.showerror("Export Error", "Failed to export configuration")
    
    def import_config(self):
        """Import configuration from file."""
        file_path = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.config_manager.import_config(file_path):
                self.load_current_config()
                self.add_status(f"Configuration imported from {file_path}")
                messagebox.showinfo("Import", "Configuration imported successfully!")
            else:
                messagebox.showerror("Import Error", "Failed to import configuration")
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Reset", "Reset all settings to defaults?"):
            self.config_manager.reset_to_defaults()
            self.load_current_config()
            self.add_status("Configuration reset to defaults")
    
    def add_status(self, message: str):
        """Add a status message."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)
    
    def run(self):
        """Run the GUI."""
        self.root.mainloop()


def launch_config_gui():
    """Launch the configuration GUI."""
    try:
        gui = ConfigGUI()
        gui.run()
    except Exception as e:
        print(f"Error launching config GUI: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    launch_config_gui()
