import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk, messagebox
from pathlib import Path

# -------------------- STRUCTURE GENERATORS --------------------
def get_folder_structure(path, indent="", hide_hidden=False):
    structure = ""
    try:
        for item in sorted(os.listdir(path)):
            if hide_hidden and item.startswith('.'):
                continue
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                structure += f"{indent}📁 {item}/\n"
                structure += get_folder_structure(item_path, indent + "    ", hide_hidden)
            else:
                structure += f"{indent}📄 {item}\n"
    except PermissionError:
        structure += f"{indent}⛔ [Permission Denied]\n"
    return structure

def get_preceding_structure(target_path, hide_hidden=False):
    path = Path(target_path).resolve()
    structure = ""
    current_path = Path(path.anchor)
    
    try:
        parts = path.relative_to(current_path).parts
    except ValueError:
        parts = path.parts[1:]
    
    indent = ""
    structure += f"📁 {current_path.name}/\n"
    
    for part in parts:
        indent += "    "
        current_path = current_path / part
        if current_path.exists():
            structure += f"{indent}📁 {part}/\n"
            if current_path == path:
                structure += get_folder_structure(str(current_path), indent + "    ", hide_hidden)
        else:
            structure += f"{indent}❌ {part} (Not Found)\n"
            break
    return structure

def get_succeeding_structure(target_path, hide_hidden=False):
    parent = Path(target_path).parent
    target_name = Path(target_path).name
    structure = ""
    
    try:
        dirs = sorted([d.name for d in parent.iterdir() if d.is_dir()])
        if target_name not in dirs:
            return "Target folder not found in parent directory"
        
        idx = dirs.index(target_name)
        for dir_name in dirs[idx:]:
            dir_path = parent / dir_name
            structure += f"📁 {dir_name}/\n"
            structure += get_folder_structure(str(dir_path), "    ", hide_hidden)
            
    except PermissionError:
        return "⛔ [Permission Denied]"
    
    return structure

# -------------------- TREEVIEW MANAGEMENT --------------------
def populate_tree(tree, parent, path, hide_hidden=False):
    try:
        for item in sorted(os.listdir(path)):
            if hide_hidden and item.startswith('.'):
                continue
            item_path = os.path.join(path, item)
            node = tree.insert(parent, 'end', text=item, open=False)
            if os.path.isdir(item_path):
                populate_tree(tree, node, item_path, hide_hidden)
    except PermissionError:
        pass

def populate_preceding_tree(tree, target_path, hide_hidden=False):
    path = Path(target_path).resolve()
    current_path = Path(path.anchor)
    root_node = tree.insert('', 'end', text=current_path.name, open=True)
    
    for part in path.relative_to(current_path).parts:
        current_path = current_path / part
        node = tree.insert(root_node, 'end', text=part, open=True)
        if current_path.is_dir():
            populate_tree(tree, node, str(current_path), hide_hidden)
        root_node = node

def populate_succeeding_tree(tree, target_path, hide_hidden=False):
    parent = Path(target_path).parent
    target_name = Path(target_path).name
    
    try:
        dirs = sorted([d.name for d in parent.iterdir() if d.is_dir()])
        idx = dirs.index(target_name)
        
        parent_node = tree.insert('', 'end', text=parent.name, open=True)
        for dir_name in dirs[idx:]:
            node = tree.insert(parent_node, 'end', text=dir_name, open=True)
            populate_tree(tree, node, str(parent / dir_name), hide_hidden)
            
    except (PermissionError, ValueError):
        pass

# -------------------- CORE APPLICATION --------------------
class FolderMap(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FolderMap - Enhanced Viewer")
        self.geometry("1000x700")
        self.configure(bg="#1e1e1e")
        self.current_path = tk.StringVar()
        self.hide_hidden_var = tk.BooleanVar(value=False)
        
        self.style = ttk.Style()
        self.style.configure("Treeview", background="#2b2b2b", foreground="white")
        self.style.map("Treeview", background=[('selected', '#444')])
        
        self.create_widgets()
        self.mode_var.trace_add('write', self.refresh_display)
        self.hide_hidden_var.trace_add('write', self.update_mode_options)
    
    def create_widgets(self):
        control_frame = tk.Frame(self, bg="#1e1e1e")
        control_frame.pack(pady=10, fill=tk.X)
        
        ttk.Button(control_frame, text="📂 Select Folder", 
                 command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="💾 Export TXT", 
                 command=self.export_txt).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(control_frame, text="Hide Hidden Files", 
                      variable=self.hide_hidden_var).pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="Target Only")
        self.mode_menu = ttk.Combobox(control_frame, textvariable=self.mode_var,
                                    state="readonly", width=15)
        self.mode_menu.pack(side=tk.RIGHT, padx=5)
        self.update_mode_options()
        
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#1e1e1e")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.tree = ttk.Treeview(main_pane)
        main_pane.add(self.tree)
        
        self.text_area = scrolledtext.ScrolledText(main_pane, wrap=tk.WORD,
                                                bg="#2b2b2b", fg="white")
        main_pane.add(self.text_area)
    
    def update_mode_options(self, *args):
        if self.hide_hidden_var.get():
            modes = ["Target Only", "With Succeeding"]
            if self.mode_var.get() == "With Preceding":
                self.mode_var.set("Target Only")
        else:
            modes = ["Target Only", "With Preceding", "With Succeeding"]
        
        self.mode_menu['values'] = modes
    
    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.current_path.set(path)
            self.refresh_display()
    
    def refresh_display(self, *args):
        path = self.current_path.get()
        if not path or not os.path.exists(path):
            return
        
        self.tree.delete(*self.tree.get_children())
        self.text_area.delete(1.0, tk.END)
        
        mode = self.mode_var.get()
        hide_hidden = self.hide_hidden_var.get()
        
        # Update Treeview
        if mode == "Target Only":
            root_node = self.tree.insert('', 'end', text=os.path.basename(path), open=True)
            populate_tree(self.tree, root_node, path, hide_hidden)
        elif mode == "With Preceding":
            populate_preceding_tree(self.tree, path, hide_hidden)
        elif mode == "With Succeeding":
            populate_succeeding_tree(self.tree, path, hide_hidden)
        
        # Update Text Area
        text_generators = {
            "Target Only": lambda p: get_folder_structure(p, hide_hidden=hide_hidden),
            "With Preceding": lambda p: get_preceding_structure(p, hide_hidden=hide_hidden),
            "With Succeeding": lambda p: get_succeeding_structure(p, hide_hidden=hide_hidden)
        }
        structure = text_generators[mode](path)
        self.text_area.insert(tk.END, f"Folder Structure ({mode}):\n\n{structure}")
    
    def export_txt(self):
        if not self.current_path.get():
            messagebox.showerror("Error", "No folder selected")
            return
        
        export_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if export_path:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(self.text_area.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Exported to {export_path}")

if __name__ == "__main__":
    app = FolderMap()
    app.mainloop()