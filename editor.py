import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import queue
import time
import re
from pathlib import Path
import sys
import webbrowser
import os
import json
import keyword
import tkinter.ttk as ttk
import urllib.request
import urllib.parse
import tkinter.simpledialog as simpledialog
from datetime import datetime
import tkinter.font as tkfont
class BuildLogWindow:
    def __init__(self, parent, title='Build Log'):
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.geometry('700x400')
        self.text = ScrolledText(self.top, state='disabled', wrap='word')
        self.text.pack(fill='both', expand=True)
        btn_frame = tk.Frame(self.top)
        btn_frame.pack(fill='x')
        tk.Button(btn_frame, text='Clear', command=self._clear).pack(side='left')
        tk.Button(btn_frame, text='Close', command=self.top.destroy).pack(side='right')
    def _clear(self):
        self.text.config(state='normal')
        self.text.delete('1.0', 'end')
        self.text.config(state='disabled')
    def append(self, line: str):
        self.text.config(state='normal')
        self.text.insert('end', line)
        self.text.see('end')
        self.text.config(state='disabled')
class FindReplaceDialog:
    def __init__(self, parent, text_widget):
        self.parent = parent
        self.text = text_widget
        self.top = tk.Toplevel(parent)
        self.top.title('Find/Replace')
        self.top.transient(parent)
        self.top.resizable(False, False)
        tk.Label(self.top, text='Find:').grid(row=0, column=0, sticky='e')
        self.find_entry = tk.Entry(self.top, width=30)
        self.find_entry.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(self.top, text='Replace:').grid(row=1, column=0, sticky='e')
        self.replace_entry = tk.Entry(self.top, width=30)
        self.replace_entry.grid(row=1, column=1, padx=4, pady=4)
        self.match_case = tk.BooleanVar(value=False)
        self.use_regex = tk.BooleanVar(value=False)
        opt_frame = tk.Frame(self.top)
        opt_frame.grid(row=2, column=0, columnspan=2, sticky='w', padx=4)
        tk.Checkbutton(opt_frame, text='Match case', variable=self.match_case).pack(side='left')
        tk.Checkbutton(opt_frame, text='Regex', variable=self.use_regex).pack(side='left')
        btn_frame = tk.Frame(self.top)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=6)
        tk.Button(btn_frame, text='Find Next', command=self.find_next).pack(side='left', padx=2)
        tk.Button(btn_frame, text='Replace', command=self.replace_one).pack(side='left', padx=2)
        tk.Button(btn_frame, text='Replace All', command=self.replace_all).pack(side='left', padx=2)
        tk.Button(btn_frame, text='Close', command=self.top.destroy).pack(side='left', padx=2)
    def _clear_find_tags(self):
        self.text.tag_remove('find_match', '1.0', 'end')
    def find_next(self):
        target = self.find_entry.get()
        if not target:
            return
        if self.use_regex.get():
            start_index = self.text.index('insert')
            content = self.text.get(start_index, 'end-1c')
            flags = 0 if self.match_case.get() else re.IGNORECASE
            m = re.search(target, content, flags)
            if not m:
                content = self.text.get('1.0', 'end-1c')
                m = re.search(target, content, flags)
                if not m:
                    messagebox.showinfo('Find', 'Text not found')
                    return
                abs_start = m.start()
                start = f'1.0+{abs_start}c'
            else:
                start = f'insert+{m.start()}c'
            end = f'{start}+{len(m.group(0))}c'
        else:
            nocase = not self.match_case.get()
            idx = self.text.search(target, 'insert', nocase=nocase, stopindex='end')
            if not idx:
                idx = self.text.search(target, '1.0', nocase=nocase, stopindex='insert')
                if not idx:
                    messagebox.showinfo('Find', 'Text not found')
                    return
            start = idx
            end = f"{idx}+{len(target)}c"
        self._clear_find_tags()
        self.text.tag_add('find_match', start, end)
        self.text.tag_config('find_match', background='yellow')
        self.text.mark_set('insert', end)
        self.text.see(start)
    def replace_one(self):
        sel = self.text.tag_ranges('sel')
        if sel:
            start = sel[0]
            end = sel[1]
            self.text.delete(start, end)
            self.text.insert(start, self.replace_entry.get())
        else:
            self.find_next()
            ranges = self.text.tag_ranges('find_match')
            if ranges:
                self.text.delete(ranges[0], ranges[1])
                self.text.insert(ranges[0], self.replace_entry.get())
    def replace_all(self):
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        if not find_text:
            return
        count = 0
        if self.use_regex.get():
            content = self.text.get('1.0', 'end-1c')
            flags = 0 if self.match_case.get() else re.IGNORECASE
            new_content, n = re.subn(find_text, replace_text, content, flags=flags)
            if n:
                self.text.delete('1.0', 'end')
                self.text.insert('1.0', new_content)
            count = n
        else:
            nocase = not self.match_case.get()
            idx = '1.0'
            while True:
                idx = self.text.search(find_text, idx, nocase=nocase, stopindex='end')
                if not idx:
                    break
                end = f"{idx}+{len(find_text)}c"
                self.text.delete(idx, end)
                self.text.insert(idx, replace_text)
                idx = f"{idx}+{len(replace_text)}c"
                count += 1
        messagebox.showinfo('Replace All', f'Replaced {count} occurrences')
class SettingsDialog:
    def __init__(self, parent, autosave_seconds, on_save):
        self.top = tk.Toplevel(parent)
        self.top.title('Settings')
        self.top.resizable(False, False)
        tk.Label(self.top, text='Autosave interval (seconds):').grid(row=0, column=0, padx=6, pady=6)
        self.spin = tk.Spinbox(self.top, from_=5, to=3600, width=8)
        self.spin.grid(row=0, column=1, padx=6, pady=6)
        self.spin.delete(0, 'end')
        self.spin.insert(0, str(autosave_seconds))
        btn_frame = tk.Frame(self.top)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=6)
        tk.Button(btn_frame, text='Save', command=lambda: self._save(on_save)).pack(side='left', padx=4)
        tk.Button(btn_frame, text='Cancel', command=self.top.destroy).pack(side='right', padx=4)
    def _save(self, on_save):
        try:
            val = int(self.spin.get())
            on_save(val)
            self.top.destroy()
        except ValueError:
            messagebox.showerror('Invalid', 'Please enter a valid integer')
class FontDialog:
    def __init__(self, parent, font_obj: tkfont.Font, on_save):
        self.top = tk.Toplevel(parent)
        self.top.title('Font')
        self.top.resizable(False, False)
        self.font_obj = font_obj
        families = sorted(set(tkfont.families()))
        tk.Label(self.top, text='Family:').grid(row=0, column=0, sticky='e', padx=4, pady=4)
        self.family_var = tk.StringVar(value=font_obj.actual().get('family', families[0] if families else 'Arial'))
        self.family_menu = tk.OptionMenu(self.top, self.family_var, *families)
        self.family_menu.grid(row=0, column=1, padx=4, pady=4)
        tk.Label(self.top, text='Size:').grid(row=1, column=0, sticky='e', padx=4, pady=4)
        self.size_spin = tk.Spinbox(self.top, from_=6, to=72, width=6)
        self.size_spin.grid(row=1, column=1, padx=4, pady=4)
        self.size_spin.delete(0, 'end')
        self.size_spin.insert(0, str(font_obj.actual().get('size', 12)))
        self.bold_var = tk.BooleanVar(value=(font_obj.actual().get('weight') == 'bold'))
        self.italic_var = tk.BooleanVar(value=(font_obj.actual().get('slant') == 'italic'))
        self.underline_var = tk.BooleanVar(value=bool(font_obj.actual().get('underline')))
        self.over_var = tk.BooleanVar(value=bool(font_obj.actual().get('overstrike')))
        chk_frame = tk.Frame(self.top)
        chk_frame.grid(row=2, column=0, columnspan=2, pady=4)
        tk.Checkbutton(chk_frame, text='Bold', variable=self.bold_var).pack(side='left', padx=4)
        tk.Checkbutton(chk_frame, text='Italic', variable=self.italic_var).pack(side='left', padx=4)
        tk.Checkbutton(chk_frame, text='Underline', variable=self.underline_var).pack(side='left', padx=4)
        tk.Checkbutton(chk_frame, text='Strikethrough', variable=self.over_var).pack(side='left', padx=4)
        btn_frame = tk.Frame(self.top)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=6)
        tk.Button(btn_frame, text='Apply', command=lambda: self._apply(on_save)).pack(side='left', padx=4)
        tk.Button(btn_frame, text='Cancel', command=self.top.destroy).pack(side='right', padx=4)
    def _apply(self, on_save):
        try:
            family = self.family_var.get()
            size = int(self.size_spin.get())
            weight = 'bold' if self.bold_var.get() else 'normal'
            slant = 'italic' if self.italic_var.get() else 'roman'
            underline = 1 if self.underline_var.get() else 0
            over = 1 if self.over_var.get() else 0
            self.font_obj.configure(family=family, size=size, weight=weight, slant=slant, underline=underline, overstrike=over)
            on_save()
            self.top.destroy()
        except Exception as e:
            messagebox.showerror('Error', str(e))
class VersionHistoryDialog:
    def __init__(self, parent, filepath: str, versions: list, on_restore):
        self.top = tk.Toplevel(parent)
        self.top.title('Version History - ' + Path(filepath).name)
        self.top.geometry('700x400')
        self.versions = versions
        self.on_restore = on_restore
        left = tk.Frame(self.top)
        left.pack(side='left', fill='y')
        right = tk.Frame(self.top)
        right.pack(side='left', fill='both', expand=True)
        self.listbox = tk.Listbox(left, width=40)
        self.listbox.pack(fill='y', expand=True)
        for p in versions:
            try:
                ts = p.stem
                dt = datetime.strptime(ts, '%Y%m%d%H%M%S')
                label = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                label = p.name
            self.listbox.insert('end', label)
        btn_frame = tk.Frame(left)
        btn_frame.pack(fill='x')
        tk.Button(btn_frame, text='Preview', command=self._preview).pack(side='left', padx=4, pady=4)
        tk.Button(btn_frame, text='Restore', command=self._restore).pack(side='left', padx=4, pady=4)
        tk.Button(btn_frame, text='Close', command=self.top.destroy).pack(side='right', padx=4, pady=4)
        self.preview = ScrolledText(right, state='disabled', wrap='word')
        self.preview.pack(fill='both', expand=True)
    def _preview(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        p = self.versions[idx]
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = f.read()
            self.preview.config(state='normal')
            self.preview.delete('1.0', 'end')
            self.preview.insert('1.0', data)
            self.preview.config(state='disabled')
        except Exception as e:
            messagebox.showerror('Error', str(e))
    def _restore(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        p = self.versions[idx]
        if messagebox.askyesno('Restore', 'Restore selected version? This will overwrite the current file.'):
            self.on_restore(p)
            self.top.destroy()
class SimpleTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title('Simple Text Editor')
        self.filepath = None
        self.autosave_seconds = 30
        self.autosave_path = Path.cwd() / '.autosave.txt'
        self._autosave_after_id = None
        self.autosave_enabled = tk.BooleanVar(value=True)
        self._line_numbers_after_id = None
        self.wrap_enabled = tk.BooleanVar(value=True)
        self.theme = tk.StringVar(value='dark')
        self.recent_files = []
        self._recent_path = Path.cwd() / '.recent.json'
        self._load_recent()
        self._build_ui()
        self._schedule_autosave()
        self.personal_dict_path = Path.cwd() / '.personal_dict.json'
        self.personal_dictionary = self._load_personal_dictionary()
        self.picky_mode = False
        self.char_limit_min = 2000
        self.char_limit_max = 150000
    def _build_ui(self):
        content_frame = tk.Frame(self.root)
        toolbar = ttk.Frame(self.root, padding=(4,4))
        toolbar.pack(fill='x', side='top')
        btn_opts = {'padx':4, 'pady':2}
        ttk.Button(toolbar, text='New', command=self.new_file).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Open', command=self.open_file).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Save', command=self.save_file).pack(side='left', **btn_opts)
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=6)
        ttk.Button(toolbar, text='Bold', command=self.toggle_bold).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Italic', command=self.toggle_italic).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Strike', command=self.toggle_strikethrough).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Bullets', command=self.toggle_bullets).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Numbered', command=self.toggle_numbered_list).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Chars', command=self.insert_special_character_dialog).pack(side='left', **btn_opts)
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=6)
        ttk.Button(toolbar, text='Undo', command=lambda: self.text.edit_undo()).pack(side='left', **btn_opts)
        ttk.Button(toolbar, text='Redo', command=lambda: self.text.edit_redo()).pack(side='left', **btn_opts)
        content_frame.pack(fill='both', expand=True)
        self.linenumbers = tk.Text(content_frame, width=5, padx=4, takefocus=0, border=0, background='#f0f0f0', state='disabled')
        self.linenumbers.pack(side='left', fill='y')
        text_frame = tk.Frame(content_frame)
        text_frame.pack(side='left', fill='both', expand=True)
        self.text = tk.Text(text_frame, wrap='word', undo=True)
        self.text_font = tkfont.Font(font=self.text['font'])
        families = set(tkfont.families())
        preferred = None
        for f in ('Segoe UI', 'Inter', 'Roboto', 'Helvetica', 'Arial'):
            if f in families:
                preferred = f
                break
        if preferred:
            try:
                self.text_font.configure(family=preferred, size=12)
            except Exception:
                pass
        self.text.config(font=self.text_font)
        self.v_scroll = tk.Scrollbar(text_frame, orient='vertical', command=self._on_vscroll)
        self.text.config(yscrollcommand=self._on_yscroll)
        self.v_scroll.pack(side='right', fill='y')
        self.text.pack(side='left', fill='both', expand=True)
        self.status = tk.Label(self.root, text='Ready', anchor='w')
        self.status.pack(fill='x', side='bottom')
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label='New', accelerator='Ctrl+N', command=self.new_file)
        file_menu.add_command(label='Open...', accelerator='Ctrl+O', command=self.open_file)
        file_menu.add_command(label='Save', accelerator='Ctrl+S', command=self.save_file)
        file_menu.add_command(label='Save As...', command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.root.quit)
        menubar.add_cascade(label='File', menu=file_menu)
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label='Undo', accelerator='Ctrl+Z', command=self.text.edit_undo)
        edit_menu.add_command(label='Redo', accelerator='Ctrl+Y', command=self.text.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label='Cut', accelerator='Ctrl+X', command=lambda: self.root.focus_get().event_generate('<<Cut>>'))
        edit_menu.add_command(label='Copy', accelerator='Ctrl+C', command=lambda: self.root.focus_get().event_generate('<<Copy>>'))
        edit_menu.add_command(label='Paste', accelerator='Ctrl+V', command=lambda: self.root.focus_get().event_generate('<<Paste>>'))
        edit_menu.add_separator()
        edit_menu.add_command(label='Select All', accelerator='Ctrl+A', command=lambda: self.select_all())
        menubar.add_cascade(label='Edit', menu=edit_menu)
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label='Find/Replace', accelerator='Ctrl+F', command=self.open_find_dialog)
        tools_menu.add_command(label='Settings...', command=self.open_settings)
        tools_menu.add_checkbutton(label='Autosave', variable=self.autosave_enabled, onvalue=True, offvalue=False, command=self._toggle_autosave)
        tools_menu.add_command(label='Toggle Theme', command=self._toggle_theme)
        tools_menu.add_command(label='Create Installer...', command=self.create_installer)
        menubar.add_cascade(label='Tools', menu=tools_menu)
        format_menu = tk.Menu(menubar, tearoff=0)
        format_menu.add_command(label='Font...', command=self.open_font_dialog)
        format_menu.add_separator()
        format_menu.add_command(label='Bold', accelerator='Ctrl+B', command=self.toggle_bold)
        format_menu.add_command(label='Italic', accelerator='Ctrl+I', command=self.toggle_italic)
        format_menu.add_command(label='Strikethrough', command=self.toggle_strikethrough)
        format_menu.add_command(label='Highlight', command=self.toggle_highlight)
        format_menu.add_separator()
        format_menu.add_command(label='Subscript', command=self.apply_subscript)
        format_menu.add_command(label='Superscript', command=self.apply_superscript)
        format_menu.add_command(label='Font Size...', command=self.change_font_size_dialog)
        format_menu.add_separator()
        format_menu.add_command(label='Bulleted List', command=self.toggle_bullets)
        format_menu.add_command(label='Numbered List', command=self.toggle_numbered_list)
        format_menu.add_command(label='Checklist', command=self.toggle_checklist)
        format_menu.add_separator()
        format_menu.add_command(label='Special Characters...', command=self.insert_special_character_dialog)
        format_menu.add_separator()
        format_menu.add_command(label='Basic Check...', command=self.grammar_check)
        format_menu.add_command(label='Advanced Check (LanguageTool)...', command=self.advanced_grammar_check)
        menubar.add_cascade(label='Format', menu=format_menu)
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_checkbutton(label='Word Wrap', variable=self.wrap_enabled, command=self._toggle_wrap)
        menubar.add_cascade(label='View', menu=view_menu)
        recent_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Recent', menu=recent_menu)
        self._recent_menu = recent_menu
        self._rebuild_recent_menu()
        tools_menu.add_command(label='Version History...', command=self.open_version_history)
        self.root.config(menu=menubar)
        quick_menu = tk.Menu(menubar, tearoff=0)
        quick_menu.add_command(label='New', command=self.new_file)
        quick_menu.add_command(label='Open', command=self.open_file)
        quick_menu.add_command(label='Save', command=self.save_file)
        quick_menu.add_command(label='Find', command=self.open_find_dialog)
        quick_menu.add_command(label='Font...', command=self.open_font_dialog)
        quick_menu.add_command(label='Toggle Theme', command=self._toggle_theme)
        menubar.add_cascade(label='Quick', menu=quick_menu)
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-a>', lambda e: self.select_all())
        self.root.bind('<Control-y>', lambda e: self.text.edit_redo())
        self.root.bind('<Control-z>', lambda e: self.text.edit_undo())
        self.text.bind('<KeyRelease>', lambda e: (self._update_status_bar(), self._highlight_syntax()))
        self.text.bind('<ButtonRelease-1>', lambda e: self._update_status_bar())
        self._update_line_numbers()
        self._update_status_bar()
        self._apply_theme()
        self._apply_wrap()
    def new_file(self):
        if not self._confirm_discard_changes():
            return
        dlg = tk.Toplevel(self.root)
        dlg.title('New Document')
        dlg.transient(self.root)
        dlg.grab_set()
        lbl = ttk.Label(dlg, text='Choose mode for new document:')
        lbl.pack(padx=12, pady=(12, 6))
        def choose_normal():
            self._create_blank()
            dlg.destroy()
        def choose_docu():
            dlg.destroy()
            topic = simpledialog.askstring('DocuTyper Topic', 'Enter topic for DocuTyper:')
            if topic:
                self.start_docutyper(topic)
        def choose_hack():
            dlg.destroy()
            self.start_hackertyper()
        btn_frame = ttk.Frame(dlg)
        btn_frame.pack(padx=12, pady=8)
        ttk.Button(btn_frame, text='Normal', command=choose_normal).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text='DocuTyper', command=choose_docu).grid(row=0, column=1, padx=6)
        ttk.Button(btn_frame, text='Hackertyper', command=choose_hack).grid(row=0, column=2, padx=6)
        ttk.Button(dlg, text='Cancel', command=dlg.destroy).pack(pady=(0,12))
        dlg.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width()//2) - (dlg.winfo_width()//2)
        y = self.root.winfo_rooty() + (self.root.winfo_height()//2) - (dlg.winfo_height()//2)
        try:
            dlg.geometry(f'+{x}+{y}')
        except Exception:
            pass
        self.text.delete('1.0', 'end')
        self.filepath = None
        self.root.title('Untitled - Simple Text Editor')
        self.text.edit_modified(False)
    def _create_blank(self):
        self.text.delete('1.0', 'end')
        self.filepath = None
        self.root.title('Untitled - Simple Text Editor')
        self.text.edit_modified(False)
    def start_hackertyper(self):
        try:
            src_path = Path(__file__).resolve()
            with open(src_path, 'r', encoding='utf-8') as f:
                data = f.read()
        except Exception:
            messagebox.showerror('Hackertyper', 'Could not load source for Hackertyper.')
            return
        self.text.delete('1.0', 'end')
        self.hackertyper_enabled = True
        self.hackertyper_text = data
        self.hackertyper_pos = 0
        self.hackertyper_stack = []
        self._update_status('Hackertyper active — press keys to type the editor source; Backspace works normally')
        self.text.bind('<KeyPress>', self._hackertyper_keypress)
    def _hackertyper_keypress(self, event):
        if event.keysym == 'BackSpace':
            try:
                if not getattr(self, 'hackertyper_enabled', False):
                    return None
                if self.hackertyper_pos <= 0:
                    return 'break'
                pos_index = f'insert-1c'
                ch = self.text.get(pos_index, 'insert')
                if ch:
                    self.text.delete(pos_index, 'insert')
                    self.hackertyper_stack.append(ch)
                    self.hackertyper_pos -= 1
                    self.text.edit_modified(True)
            except Exception:
                pass
            return 'break'
        if len(event.keysym) > 1 and event.keysym.startswith('Control'):
            return None
        try:
            if not getattr(self, 'hackertyper_enabled', False):
                return None
            if getattr(self, 'hackertyper_stack', None):
                ch = self.hackertyper_stack.pop()
                self.text.insert('insert', ch)
                self.hackertyper_pos += 1
            else:
                if self.hackertyper_pos >= len(self.hackertyper_text):
                    self._update_status('Hackertyper: End of source')
                    self.hackertyper_enabled = False
                    try:
                        self.text.unbind('<KeyPress>')
                    except Exception:
                        pass
                    return 'break'
                ch = self.hackertyper_text[self.hackertyper_pos]
                self.hackertyper_pos += 1
                self.text.insert('insert', ch)
            self.text.edit_modified(True)
            if self.hackertyper_pos % 50 == 0:
                self._update_status(f'Hackertyper: {self.hackertyper_pos}/{len(self.hackertyper_text)} chars')
        except Exception:
            pass
        return 'break'
    def open_file(self):
        if not self._confirm_discard_changes():
            return
        path = filedialog.askopenfilename(filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = f.read()
                self.text.delete('1.0', 'end')
                self.text.insert('1.0', data)
                self.filepath = path
                self.root.title(f"{path} - Simple Text Editor")
                self.text.edit_modified(False)
                self._update_status('File opened')
            except Exception as e:
                messagebox.showerror('Error', f'Could not open file: {e}')
    def save_file(self):
        if self.filepath:
            try:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    f.write(self.text.get('1.0', 'end-1c'))
                self._update_status('File saved')
                try:
                    self._save_version(self.filepath)
                except Exception:
                    pass
                self.text.edit_modified(False)
            except Exception as e:
                messagebox.showerror('Error', f'Could not save file: {e}')
        else:
            self.save_file_as()
    def save_file_as(self):
        path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text Files', '*.txt'), ('All Files', '*.*')])
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.text.get('1.0', 'end-1c'))
            self.filepath = path
            self.root.title(f"{path} - Simple Text Editor")
            self._update_status('File saved')
            try:
                self._save_version(self.filepath)
            except Exception:
                pass
            self.text.edit_modified(False)
        except Exception as e:
            messagebox.showerror('Error', f'Could not save file: {e}')
    def select_all(self):
        self.text.tag_add('sel', '1.0', 'end')
        return 'break'
    def _confirm_discard_changes(self):
        if self.text.edit_modified():
            resp = messagebox.askyesnocancel('Unsaved Changes', 'You have unsaved changes. Save before continuing?')
            if resp is None:
                return False
            if resp:
                self.save_file()
        return True
    def _schedule_autosave(self):
        try:
            if self._autosave_after_id:
                self.root.after_cancel(self._autosave_after_id)
        except Exception:
            pass
        if self.autosave_enabled.get():
            self._autosave_after_id = self.root.after(self.autosave_seconds * 1000, self._autosave)
    def _autosave(self):
        try:
            if self.text.edit_modified():
                data = self.text.get('1.0', 'end-1c')
                with open(self.autosave_path, 'w', encoding='utf-8') as f:
                    f.write(data)
                self._update_status(f'Autosaved to {self.autosave_path.name} at {time.strftime("%H:%M:%S")}')
            else:
                self._update_status('No changes to autosave')
        except Exception as e:
            self._update_status(f'Autosave failed: {e}')
        finally:
            self._schedule_autosave()
    def _update_status(self, text):
        try:
            self.status.config(text=text)
        except Exception:
            pass
    def _flash_status(self, color='#4caf50', duration=400):
        try:
            orig = self.status.cget('background')
            self.status.config(background=color)
            self.root.after(duration, lambda: self.status.config(background=orig))
        except Exception:
            pass
    def _versions_dir_for(self, filepath: str) -> Path:
        p = Path(filepath)
        return p.parent / '.versions' / p.name
    def _save_version(self, filepath: str):
        try:
            vdir = self._versions_dir_for(filepath)
            vdir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d%H%M%S')
            fname = f'{ts}.txt'
            with open(vdir / fname, 'w', encoding='utf-8') as f:
                f.write(self.text.get('1.0', 'end-1c'))
        except Exception:
            pass
    def _list_versions(self, filepath: str):
        try:
            vdir = self._versions_dir_for(filepath)
            if not vdir.exists():
                return []
            items = sorted(vdir.iterdir(), reverse=True)
            return items
        except Exception:
            return []
    def open_version_history(self):
        if not self.filepath:
            messagebox.showinfo('Version History', 'Save the file first to start version history.')
            return
        versions = self._list_versions(self.filepath)
        VersionHistoryDialog(self.root, self.filepath, versions, self._restore_version)
    def _restore_version(self, version_path: Path):
        try:
            with open(version_path, 'r', encoding='utf-8') as f:
                data = f.read()
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(data)
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', data)
            self.text.edit_modified(False)
            self._save_version(self.filepath)
            self._update_status('Restored version')
        except Exception as e:
            messagebox.showerror('Error', f'Could not restore version: {e}')
    def _load_recent(self):
        try:
            if self._recent_path.exists():
                with open(self._recent_path, 'r', encoding='utf-8') as f:
                    self.recent_files = json.load(f)
        except Exception:
            self.recent_files = []
    def _save_recent(self):
        try:
            with open(self._recent_path, 'w', encoding='utf-8') as f:
                json.dump(self.recent_files[:10], f)
        except Exception:
            pass
    def _add_recent(self, path: str):
        try:
            path = str(path)
            if path in self.recent_files:
                self.recent_files.remove(path)
            self.recent_files.insert(0, path)
            self.recent_files = self.recent_files[:10]
            self._save_recent()
            self._rebuild_recent_menu()
        except Exception:
            pass
    def _rebuild_recent_menu(self):
        try:
            self._recent_menu.delete(0, 'end')
            if not self.recent_files:
                self._recent_menu.add_command(label='(no recent files)', state='disabled')
                return
            for p in self.recent_files:
                self._recent_menu.add_command(label=p, command=lambda p=p: self._open_recent(p))
            self._recent_menu.add_separator()
            self._recent_menu.add_command(label='Clear Recent', command=self._clear_recent)
        except Exception:
            pass
    def _open_recent(self, path):
        if not Path(path).exists():
            messagebox.showerror('Open Recent', f'File not found: {path}')
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = f.read()
            self.text.delete('1.0', 'end')
            self.text.insert('1.0', data)
            self.filepath = path
            self.root.title(f"{path} - Simple Text Editor")
            self.text.edit_modified(False)
            self._add_recent(path)
        except Exception as e:
            messagebox.showerror('Error', str(e))
    def _clear_recent(self):
        self.recent_files = []
        self._save_recent()
        self._rebuild_recent_menu()
    def _apply_wrap(self):
        try:
            wrap_mode = 'word' if self.wrap_enabled.get() else 'none'
            self.text.config(wrap=wrap_mode)
        except Exception:
            pass
    def _toggle_wrap(self):
        self._apply_wrap()
        self._update_status('Word wrap ' + ('enabled' if self.wrap_enabled.get() else 'disabled'))
    def _apply_theme(self):
        try:
            if self.theme.get() == 'dark':
                bg = '#1e1e1e'; fg = '#dcdcdc'; lbg = '#2b2b2b'
            else:
                bg = 'white'; fg = 'black'; lbg = '#f0f0f0'
            self.text.config(background=bg, foreground=fg, insertbackground=fg)
            self.linenumbers.config(background=lbg, foreground=fg)
            self.status.config(background=lbg)
        except Exception:
            pass
    def _toggle_theme(self):
        self.theme.set('dark' if self.theme.get() == 'light' else 'light')
        self._apply_theme()
        self._update_status('Theme: ' + self.theme.get())
    def _highlight_syntax(self):
        try:
            content = self.text.get('1.0', 'end-1c')
            self.text.tag_remove('py_keyword', '1.0', 'end')
            kw = keyword.kwlist
            if not kw:
                return
            pattern = r"\\b(" + "|".join(re.escape(w) for w in kw) + r")\\b"
            for m in re.finditer(pattern, content):
                start = f'1.0+{m.start()}c'
                end = f'1.0+{m.end()}c'
                self.text.tag_add('py_keyword', start, end)
            self.text.tag_config('py_keyword', foreground='#0000ff')
        except Exception:
            pass
    def _on_yscroll(self, first, last):
        try:
            self.v_scroll.set(first, last)
        except Exception:
            pass
        try:
            self.linenumbers.yview_moveto(first)
        except Exception:
            pass
    def _on_vscroll(self, *args):
        try:
            self.text.yview(*args)
            self.linenumbers.yview(*args)
        except Exception:
            pass
    def _update_line_numbers(self):
        try:
            last_line = int(self.text.index('end-1c').split('.')[0])
            lines = '\n'.join(str(i) for i in range(1, last_line + 1)) + '\n'
            self.linenumbers.config(state='normal')
            self.linenumbers.delete('1.0', 'end')
            self.linenumbers.insert('1.0', lines)
            self.linenumbers.config(state='disabled')
        except Exception:
            pass
        try:
            if self._line_numbers_after_id:
                self.root.after_cancel(self._line_numbers_after_id)
        except Exception:
            pass
        self._line_numbers_after_id = self.root.after(200, self._update_line_numbers)
    def _update_status_bar(self):
        try:
            index = self.text.index('insert')
            line, col = index.split('.')
            content = self.text.get('1.0', 'end-1c')
            words = len(re.findall(r"\w+", content))
            chars = len(content)
            chars_no_spaces = len(content.replace(' ', ''))
            spaces = content.count(' ')
            lines = content.count('\n') + (1 if content else 0)
            periods = content.count('.')
            self._update_status(
                f'Ln {line}, Col {int(col)+1}    Words: {words}    Chars: {chars} ({chars_no_spaces} w/o spaces)    Spaces: {spaces}    Lines: {lines}    Periods: {periods}'
            )
        except Exception:
            pass
    def _toggle_autosave(self):
        if self.autosave_enabled.get():
            self._schedule_autosave()
            self._update_status('Autosave enabled')
        else:
            try:
                if self._autosave_after_id:
                    self.root.after_cancel(self._autosave_after_id)
            except Exception:
                pass
            self._update_status('Autosave disabled')
    def toggle_sidebar(self):
        try:
            if self.sidebar_visible:
                try:
                    self.paned.forget(self.sidebar)
                except Exception:
                    pass
                self.sidebar_visible = False
                self._update_status('Sidebar hidden')
            else:
                try:
                    self.paned.insert(0, self.sidebar)
                except Exception:
                    self.paned.add(self.sidebar)
                self.sidebar_visible = True
                self._update_status('Sidebar shown')
        except Exception:
            pass
    def _open_google_search(self, query: str):
        try:
            q = urllib.parse.quote_plus(query)
            url = f'https://www.google.com/search?q={q}' if q else 'https://www.google.com'
            webbrowser.open(url)
            self._update_status('Opened Google search')
        except Exception as e:
            messagebox.showerror('Error', f'Could not open browser: {e}')
    def _clear_google_results(self):
        try:
            self.google_results.delete(0, 'end')
            self.google_preview.config(state='normal')
            self.google_preview.delete('1.0', 'end')
            self.google_preview.config(state='disabled')
        except Exception:
            pass
    def _search_google_in_app(self, query: str):
        if not query:
            return
        self._update_status('Searching Google...')
        def worker():
            try:
                sr = urllib.parse.quote_plus(query)
                search_url = f'https://www.google.com/search?q={sr}&hl=en'
                headers = {'User-Agent': 'SimpleTextEditor/1.0 (https://example.local)'}
                req = urllib.request.Request(search_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                pattern = re.compile(r'<a[^>]+href="/url\?q=(?P<url>https?://[^&\"]+)"[^>]*>\s*(?:<div[^>]*>)?\s*(?:<h3[^>]*>)?(?P<title>[^<]{1,300})', re.IGNORECASE)
                items = []
                for m in pattern.finditer(html):
                    u = urllib.parse.unquote(m.group('url'))
                    t = re.sub('<[^<]+?>', '', m.group('title')).strip()
                    if t and u:
                        items.append((t, u))
                    if len(items) >= 20:
                        break
                def ui_update():
                    try:
                        self.google_results.delete(0, 'end')
                        self._google_items = items
                        for i, (t, u) in enumerate(items):
                            self.google_results.insert('end', f'{i+1}. {t}')
                        self._update_status(f'Found {len(items)} results')
                    except Exception:
                        pass
                self.root.after(0, ui_update)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror('Search Error', str(e)))
        threading.Thread(target=worker, daemon=True).start()
    def _on_google_result_select(self):
        try:
            sel = self.google_results.curselection()
            if not sel:
                return
            idx = sel[0]
            item = getattr(self, '_google_items', [])[idx]
            if not item:
                return
            title, url = item
            self._update_status('Fetching page...')
            def worker_fetch():
                try:
                    headers = {'User-Agent': 'SimpleTextEditor/1.0 (https://example.local)'}
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        html = resp.read().decode('utf-8', errors='ignore')
                    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.S|re.I)
                    text = re.sub('<[^<]+?>', '', html)
                    snippet = text.strip()[:20000]

                    self.root.after(0, lambda: self._show_google_preview(title, url, snippet))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror('Fetch Error', str(e)))
            threading.Thread(target=worker_fetch, daemon=True).start()
        except Exception:
            pass
    def _show_google_preview(self, title, url, snippet):
        try:
            self.google_preview.config(state='normal')
            self.google_preview.delete('1.0', 'end')
            self.google_preview.insert('1.0', f'{title}\n{url}\n\n')
            self.google_preview.insert('end', snippet)
            self.google_preview.config(state='disabled')
            self._update_status('Preview updated')
        except Exception:
            pass
    def fetch_wikipedia(self, topic: str) -> str | None:
        try:
            term = topic.strip()
            if not term:
                return None
            sr = urllib.parse.quote_plus(f'intitle:{term}')
            search_url = f'https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={sr}&format=json'
            headers = {'User-Agent': 'SimpleTextEditor/1.0 (https://example.local)'}
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                sdata = resp.read()
            sobj = json.loads(sdata.decode('utf-8'))
            results = sobj.get('query', {}).get('search', [])
            chosen_title = None
            lowered = term.lower()
            for r in results:
                title = r.get('title', '')
                if lowered in title.lower():
                    chosen_title = title
                    break
            if not chosen_title and results:
                chosen_title = results[0].get('title')
            if not chosen_title:
                q = urllib.parse.quote(topic)
            else:
                q = urllib.parse.quote(chosen_title)
            url = f'https://en.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext&format=json&titles={q}&redirects=1'
            req2 = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req2, timeout=10) as resp:
                data = resp.read()
            obj = json.loads(data.decode('utf-8'))
            pages = obj.get('query', {}).get('pages', {})
            if not pages:
                return None
            page = next(iter(pages.values()))
            extract = page.get('extract', '')
            if not extract:
                return None
            return extract.replace('\r\n', '\n')
        except Exception:
            return None
    def start_docutyper(self, topic: str):
        self._update_status(f'Fetching Wikipedia article for "{topic}"...')
        article = self.fetch_wikipedia(topic)
        if not article:
            messagebox.showerror('DocuTyper', f'Could not fetch article for: {topic}')
            return
        self.text.delete('1.0', 'end')
        self.docutyper_enabled = True
        self.docutyper_text = article
        self.docutyper_pos = 0
        self.docutyper_stack = []
        self._update_status('DocuTyper active — press keys to type the article; Backspace works normally')
        self.text.bind('<KeyPress>', self._docutyper_keypress)
    def _docutyper_keypress(self, event):
        if event.keysym == 'BackSpace':
            try:
                if not getattr(self, 'docutyper_enabled', False):
                    return None
                if self.docutyper_pos <= 0:
                    return 'break'
                pos_index = f'insert-1c'
                ch = self.text.get(pos_index, 'insert')
                if ch:
                    self.text.delete(pos_index, 'insert')
                    self.docutyper_stack.append(ch)
                    self.docutyper_pos -= 1
                    self.text.edit_modified(True)
            except Exception:
                pass
            return 'break'
        if len(event.keysym) > 1 and event.keysym.startswith('Control'):
            return None
        try:
            if not getattr(self, 'docutyper_enabled', False):
                return None
            if getattr(self, 'docutyper_stack', None):
                ch = self.docutyper_stack.pop()
                self.text.insert('insert', ch)
                self.docutyper_pos += 1
            else:
                if self.docutyper_pos >= len(self.docutyper_text):
                    self._update_status('DocuTyper: End of article')
                    self.docutyper_enabled = False
                    try:
                        self.text.unbind('<KeyPress>')
                    except Exception:
                        pass
                    return 'break'
                ch = self.docutyper_text[self.docutyper_pos]
                self.docutyper_pos += 1
                self.text.insert('insert', ch)
            self.text.edit_modified(True)
            if self.docutyper_pos % 50 == 0:
                self._update_status(f'DocuTyper: {self.docutyper_pos}/{len(self.docutyper_text)} chars')
        except Exception:
            pass
        return 'break'
    def open_find_dialog(self):
        FindReplaceDialog(self.root, self.text)
    def open_settings(self):
        def on_save(val):
            try:
                self.autosave_seconds = int(val)
                self._schedule_autosave()
                self._update_status(f'Autosave interval set to {self.autosave_seconds}s')
            except Exception as e:
                messagebox.showerror('Error', str(e))
        SettingsDialog(self.root, self.autosave_seconds, on_save)
    def open_font_dialog(self):
        def on_save():
            try:
                fam = self.text_font.actual().get('family')
                size = self.text_font.actual().get('size')
                self.linenumbers.config(font=(fam, size))
            except Exception:
                pass
            self._update_status('Font updated')
        FontDialog(self.root, self.text_font, on_save)
    def _get_selection_range(self):
        try:
            start = self.text.index('sel.first')
            end = self.text.index('sel.last')
        except Exception:
            start = self.text.index('insert wordstart')
            end = self.text.index('insert wordend')
        return start, end
    def _ensure_tag_font(self, tag, **font_opts):
        try:
            if not hasattr(self, '_tag_fonts'):
                self._tag_fonts = {}
            if tag in self._tag_fonts:
                f = self._tag_fonts[tag]
            else:
                base = tkfont.Font(**self.text_font.actual())
                for k, v in font_opts.items():
                    if k == 'weight':
                        base.configure(weight=v)
                    elif k == 'slant':
                        base.configure(slant=v)
                    elif k == 'underline':
                        base.configure(underline=1 if v else 0)
                    elif k == 'overstrike':
                        base.configure(overstrike=1 if v else 0)
                    elif k == 'size':
                        base.configure(size=v)
                self._tag_fonts[tag] = base
                f = base
            self.text.tag_configure(tag, font=f)
        except Exception:
            pass
    def _load_personal_dictionary(self):
        try:
            if self.personal_dict_path.exists():
                with open(self.personal_dict_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data if isinstance(data, list) else [])
        except Exception:
            pass
        return set()

    def _save_personal_dictionary(self):
        try:
            with open(self.personal_dict_path, 'w', encoding='utf-8') as f:
                json.dump(sorted(list(self.personal_dictionary)), f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    def add_to_personal_dictionary(self, word: str):
        try:
            w = word.strip()
            if w:
                self.personal_dictionary.add(w)
                self._save_personal_dictionary()
                self._update_status(f'Added "{w}" to personal dictionary')
        except Exception:
            pass
    def get_text_statistics(self, text: str) -> dict:
        words = re.findall(r"\w+", text)
        freqs = {}
        for w in words:
            lw = w.lower()
            freqs[lw] = freqs.get(lw, 0) + 1
        stats = {
            'chars': len(text),
            'words': len(words),
            'unique_words': len(freqs),
            'top_words': sorted(freqs.items(), key=lambda x: x[1], reverse=True)[:10]
        }
        return stats
    def toggle_bold(self):
        start, end = self._get_selection_range()
        try:
            if 'bold' in self.text.tag_names(start):
                self.text.tag_remove('bold', start, end)
            else:
                self._ensure_tag_font('bold', weight='bold')
                self.text.tag_add('bold', start, end)
        except Exception:
            pass
    def toggle_italic(self):
        start, end = self._get_selection_range()
        try:
            if 'italic' in self.text.tag_names(start):
                self.text.tag_remove('italic', start, end)
            else:
                self._ensure_tag_font('italic', slant='italic')
                self.text.tag_add('italic', start, end)
        except Exception:
            pass
    def toggle_strikethrough(self):
        start, end = self._get_selection_range()
        try:
            if 'strike' in self.text.tag_names(start):
                self.text.tag_remove('strike', start, end)
            else:
                self._ensure_tag_font('strike', overstrike=True)
                self.text.tag_add('strike', start, end)
        except Exception:
            pass
    def toggle_highlight(self):
        start, end = self._get_selection_range()
        try:
            if 'highlight' in self.text.tag_names(start):
                self.text.tag_remove('highlight', start, end)
            else:
                self.text.tag_configure('highlight', background='#fff59d')
                self.text.tag_add('highlight', start, end)
        except Exception:
            pass
    def change_font_size_dialog(self):
        start, end = self._get_selection_range()
        def apply_size():
            try:
                val = int(size_var.get())
            except Exception:
                return
            try:
                self._ensure_tag_font(f'fs_{val}', size=val)
                self.text.tag_add(f'fs_{val}', start, end)
            except Exception:
                pass
            d.destroy()
        d = tk.Toplevel(self.root)
        d.transient(self.root)
        d.grab_set()
        ttk.Label(d, text='Font size:').pack(padx=8, pady=(8,0))
        size_var = tk.StringVar(value=str(self.text_font.actual().get('size', 12)))
        ttk.Entry(d, textvariable=size_var).pack(padx=8, pady=6)
        ttk.Button(d, text='Apply', command=apply_size).pack(pady=(0,8))
    def insert_special_character_dialog(self):
        chars = ['—', '–', '•', '…', '©', '®', '€', '£', '±', '×', '÷', '✓']
        d = tk.Toplevel(self.root)
        d.title('Special Characters')
        d.transient(self.root)
        d.grab_set()
        frm = ttk.Frame(d)
        frm.pack(padx=8, pady=8)
        for i, ch in enumerate(chars):
            b = ttk.Button(frm, text=ch, width=4, command=lambda c=ch: (self.text.insert('insert', c), d.destroy()))
            b.grid(row=i//6, column=i%6, padx=4, pady=4)
    def _lines_from_range(self, start, end):
        sline = int(start.split('.')[0])
        eline = int(end.split('.')[0])
        return sline, eline
    def toggle_bullets(self):
        try:
            start, end = self._get_selection_range()
            sline, eline = self._lines_from_range(start, end)
            for ln in range(sline, eline+1):
                idx = f'{ln}.0'
                line = self.text.get(idx, f'{ln}.end')
                if line.lstrip().startswith('•'):
                    new = line.replace('• ', '', 1)
                    self.text.delete(idx, f'{ln}.end')
                    self.text.insert(idx, new)
                else:
                    self.text.insert(idx, '• ')
        except Exception:
            pass
    def toggle_numbered_list(self):
        try:
            start, end = self._get_selection_range()
            sline, eline = self._lines_from_range(start, end)
            first = self.text.get(f'{sline}.0', f'{sline}.end')
            if re.match(r'\s*\d+\.\s+', first):
                for ln in range(sline, eline+1):
                    idx = f'{ln}.0'
                    line = self.text.get(idx, f'{ln}.end')
                    new = re.sub(r'^\s*\d+\.\s+', '', line)
                    self.text.delete(idx, f'{ln}.end')
                    self.text.insert(idx, new)
            else:
                for i, ln in enumerate(range(sline, eline+1), start=1):
                    idx = f'{ln}.0'
                    self.text.insert(idx, f'{i}. ')
        except Exception:
            pass
    def toggle_checklist(self):
        try:
            start, end = self._get_selection_range()
            sline, eline = self._lines_from_range(start, end)
            for ln in range(sline, eline+1):
                idx = f'{ln}.0'
                line = self.text.get(idx, f'{ln}.end')
                if line.lstrip().startswith('[ ]') or line.lstrip().startswith('[x]'):
                    new = re.sub(r'^\s*\[.\]\s*', '', line)
                    self.text.delete(idx, f'{ln}.end')
                    self.text.insert(idx, new)
                else:
                    self.text.insert(idx, '[ ] ')
        except Exception:
            pass
    def apply_subscript(self):
        start, end = self._get_selection_range()
        try:
            sz = max(6, int(self.text_font.actual().get('size', 12)) - 2)
            self._ensure_tag_font('sub', size=sz)
            self.text.tag_add('sub', start, end)
        except Exception:
            pass
    def apply_superscript(self):
        start, end = self._get_selection_range()
        try:
            sz = max(6, int(self.text_font.actual().get('size', 12)) - 2)
            self._ensure_tag_font('sup', size=sz)
            self.text.tag_add('sup', start, end)
        except Exception:
            pass
    def grammar_check(self):
        try:
            text = self.text.get('1.0', 'end-1c')
            findings = []
            for m in re.finditer(r' {2,}', text):
                findings.append(('double_space', m.start(), m.end(), 'Double space', 'Replace with single space'))
            for m in re.finditer(r"\b(\w+)\s+\1\b", text, re.IGNORECASE):
                findings.append(('repeated_word', m.start(), m.end(), 'Repeated word', f'Remove duplicate "{m.group(1)}"'))
            common = {'teh':'the', 'adn':'and', 'recieve':'receive', 'alot':'a lot', 'seperate':'separate', 'occured':'occurred'}
            for k, v in common.items():
                for m in re.finditer(rf'\b{k}\b', text, re.IGNORECASE):
                    findings.append(('misspelling', m.start(), m.end(), f'Misspelling "{k}"', f'Replace with "{v}"'))
            for m in re.finditer(r'([.!?])([A-Za-z0-9"\'"(])', text):
                findings.append(('missing_space', m.start(2), m.start(2)+1, 'Missing space after punctuation', 'Insert space'))
            for m in re.finditer(r'(?<=[.!?]\s)([a-z])', text):
                findings.append(('capitalize', m.start(1), m.start(1)+1, 'Sentence not capitalized', 'Capitalize first letter'))
            for m in re.finditer(r'[ \t]+$', text, re.M):
                findings.append(('trailing_space', m.start(), m.end(), 'Trailing whitespace', 'Remove extra spaces'))
            for m in re.finditer(r'([^.!?]{200,})', text):
                findings.append(('long_sentence', m.start(), m.end(), 'Long sentence (>200 chars)', 'Consider shortening'))
            for m in re.finditer(r'\b(was|were|is|are|been|being)\s+\w+ed\b', text, re.IGNORECASE):
                findings.append(('passive', m.start(), m.end(), 'Possible passive voice', 'Consider active voice'))
            if not findings:
                messagebox.showinfo('Grammar Check', 'No issues found (expanded checks).')
                return
            d = tk.Toplevel(self.root)
            d.title('Grammar Check — Findings')
            d.transient(self.root)
            frm = ttk.Frame(d)
            frm.pack(fill='both', expand=True, padx=8, pady=8)
            lb = tk.Listbox(frm, width=100, height=14)
            for i, item in enumerate(findings):
                rule, s, e, desc, fix = item
                snippet = text[max(0, s-30):min(len(text), e+30)].replace('\n', ' ')
                lb.insert('end', f'{i+1}. {desc}: "{snippet}" -> {fix}')
            lb.pack(fill='both', expand=True)
            stats = self.get_text_statistics(text)
            stats_frame = ttk.Frame(d)
            stats_frame.pack(fill='x', padx=8)
            stats_lbl = ttk.Label(stats_frame, text=f"Chars: {stats['chars']}  Words: {stats['words']}  Unique: {stats['unique_words']}")
            stats_lbl.pack(side='left')
            def show_stats():
                top = '\n'.join(f'{w}: {c}' for w, c in stats['top_words'])
                messagebox.showinfo('Text Statistics', f"Chars: {stats['chars']}\nWords: {stats['words']}\nUnique words: {stats['unique_words']}\nTop: {top}")
            def add_selected_to_dict():
                sel = lb.curselection()
                if not sel:
                    return
                idx = sel[0]
                rule, s, e, desc, fix = findings[idx]
                word = self.text.get(f'1.0+{s}c', f'1.0+{e}c')
                if word:
                    self.add_to_personal_dictionary(word)
                    messagebox.showinfo('Personal Dictionary', f'Added "{word}" to personal dictionary')
            def toggle_picky():
                self.picky_mode = not self.picky_mode
                messagebox.showinfo('Picky Mode', f'Picky mode set to {self.picky_mode}')
            def fix_all():
                new = text
                for k, v in common.items():
                    if k not in self.personal_dictionary:
                        new = re.sub(rf"\b{re.escape(k)}\b", v, new, flags=re.IGNORECASE)
                new = re.sub(r' {2,}', ' ', new)
                new = re.sub(r"\b(\w+)\s+\1\b", r'\1', new, flags=re.IGNORECASE)
                new = re.sub(r'([.!?])([A-Za-z0-9"\'"(])', r'\1 \2', new)
                new = re.sub(r'(?<=[.!?]\s)([a-z])', lambda m: m.group(1).upper(), new)
                new = re.sub(r'[ \t]+$', '', new, flags=re.M)
                if self.picky_mode:
                    overused = ['very', 'really', 'just', 'basically', 'actually']
                    for ow in overused:
                        new = re.sub(rf"\b{ow}\b", '', new, flags=re.IGNORECASE)
                    informal = ['gonna', 'wanna', "ain't", 'lol', 'u']
                    for t in informal:
                        new = re.sub(rf"\b{t}\b", '', new, flags=re.IGNORECASE)
                self.text.delete('1.0', 'end')
                self.text.insert('1.0', new)
                d.destroy()
            btns = ttk.Frame(d)
            btns.pack(fill='x', pady=6)
            ttk.Button(btns, text='Fix All (safe fixes)', command=fix_all).pack(side='left', padx=6)
            ttk.Button(btns, text='Add Selected to Dictionary', command=add_selected_to_dict).pack(side='left', padx=6)
            ttk.Button(btns, text='Stats', command=show_stats).pack(side='left', padx=6)
            ttk.Button(btns, text='Toggle Picky Mode', command=toggle_picky).pack(side='left', padx=6)
            ttk.Button(btns, text='Close', command=d.destroy).pack(side='right', padx=6)
        except Exception as e:
            messagebox.showerror('Grammar Check', f'Error: {e}')
    def advanced_grammar_check(self):
        """Use LanguageTool (if available) for an advanced grammar check and show findings.
        If the package isn't installed, offer to install it via pip.
        """
        try:
            try:
                import language_tool_python
            except Exception:
                if messagebox.askyesno('Advanced Grammar', 'LanguageTool (language-tool-python) is not installed. Install now?'):
                    try:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'language-tool-python'])
                        import importlib
                        language_tool_python = importlib.import_module('language_tool_python')
                    except Exception as ie:
                        messagebox.showerror('Install Failed', f'Could not install LanguageTool: {ie}')
                        return
                else:
                    return
            text = self.text.get('1.0', 'end-1c')
            if not text.strip():
                messagebox.showinfo('Advanced Grammar', 'Document is empty.')
                return
            def java_available():
                try:
                    proc = subprocess.run(['java', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    return proc.returncode == 0
                except FileNotFoundError:
                    return False
                except Exception:
                    return False
            if not java_available():
                jd = tk.Toplevel(self.root)
                jd.title('Java Not Found')
                jd.transient(self.root)
                jd.grab_set()
                ttk.Label(jd, text='LanguageTool requires a Java runtime to run. Install Java to use Advanced Check.').pack(padx=12, pady=(12,6))
                def open_java_page():
                    url = 'https://adoptium.net/'
                    try:
                        opened = webbrowser.open_new_tab(url)
                        if not opened:
                            if os.name == 'nt':
                                subprocess.run(['cmd', '/c', 'start', url], check=False)
                            else:
                                subprocess.run(['xdg-open', url], check=False)
                    except Exception as ex:
                        try:
                            if os.name == 'nt':
                                subprocess.run(['cmd', '/c', 'start', url], check=False)
                            else:
                                subprocess.run(['xdg-open', url], check=False)
                        except Exception:
                            messagebox.showerror('Open Browser', f'Could not open browser: {ex}')
                    finally:
                        try:
                            jd.destroy()
                        except Exception:
                            pass
                def locate_java():
                    f = filedialog.askopenfilename(title='Locate java executable', filetypes=[('Executable','*.exe' if os.name=='nt' else '*')])
                    if not f:
                        return
                    jdir = os.path.dirname(f)
                    try:
                        os.environ['PATH'] = jdir + os.pathsep + os.environ.get('PATH', '')
                        parent = os.path.dirname(jdir)
                        os.environ.setdefault('JAVA_HOME', parent)
                        messagebox.showinfo('Locate Java', 'Java location added to PATH for this session.')
                        try:
                            jd.destroy()
                        except Exception:
                            pass
                    except Exception as e:
                        messagebox.showerror('Locate Java', f'Could not set PATH: {e}')
                btnf = ttk.Frame(jd)
                btnf.pack(pady=(0,12), padx=12, fill='x')
                ttk.Button(btnf, text='Open Java download page', command=open_java_page).pack(side='left')
                ttk.Button(btnf, text='Locate Java...', command=locate_java).pack(side='left', padx=6)
                ttk.Button(btnf, text='Cancel', command=jd.destroy).pack(side='right')
                jd.update_idletasks()
                try:
                    x = self.root.winfo_rootx() + (self.root.winfo_width()//2) - (jd.winfo_width()//2)
                    y = self.root.winfo_rooty() + (self.root.winfo_height()//2) - (jd.winfo_height()//2)
                    jd.geometry(f'+{x}+{y}')
                except Exception:
                    pass
                try:
                    self.root.wait_window(jd)
                except Exception:
                    pass
                if not java_available():
                    return
            self._update_status('Running advanced grammar check...')
            tool = language_tool_python.LanguageTool('en-US')
            matches = tool.check(text)
            if not matches:
                messagebox.showinfo('Advanced Grammar', 'No issues found by LanguageTool.')
                return
            d = tk.Toplevel(self.root)
            d.title('Advanced Grammar — LanguageTool Findings')
            d.transient(self.root)
            frm = ttk.Frame(d)
            frm.pack(fill='both', expand=True, padx=8, pady=8)
            lb = tk.Listbox(frm, width=100, height=14)
            for i, m in enumerate(matches):
                err_len = getattr(m, 'errorLength', None)
                if err_len is None:
                    err_len = getattr(m, 'length', 0)
                start = max(0, int(m.offset) - 30)
                end = min(len(text), int(m.offset) + int(err_len or 0) + 30)
                snippet = text[start:end].replace('\n', ' ')
                sugg = ', '.join(getattr(m, 'replacements', [])[:5])
                rule_id = getattr(m, 'ruleId', '') or getattr(m, 'ruleId', '')
                lb.insert('end', f'{i+1}. {rule_id}: "{snippet}" -> {sugg}')
            lb.pack(fill='both', expand=True)
            def apply_suggestion():
                sel = lb.curselection()
                if not sel:
                    messagebox.showinfo('Apply Suggestion', 'No selection')
                    return
                idx = sel[0]
                m = matches[idx]
                repls = getattr(m, 'replacements', None) or []
                if not repls:
                    messagebox.showinfo('Apply Suggestion', 'No suggestions available for this item')
                    return
                replacement = repls[0]
                try:
                    start_off = int(m.offset)
                    err_len = getattr(m, 'errorLength', None)
                    if err_len is None:
                        err_len = getattr(m, 'length', 0)
                    start_idx = f'1.0+{start_off}c'
                    end_idx = f'1.0+{start_off + int(err_len or 0)}c'
                    self.text.delete(start_idx, end_idx)
                    self.text.insert(start_idx, replacement)
                    self.text.edit_modified(True)
                    self._update_status('Applied LanguageTool suggestion')
                except Exception as e:
                    messagebox.showerror('Apply Suggestion', f'Failed to apply suggestion: {e}')
                finally:
                    try:
                        d.destroy()
                    except Exception:
                        pass
            btns = ttk.Frame(d)
            btns.pack(fill='x', pady=6)
            ttk.Button(btns, text='Apply Suggestion', command=apply_suggestion).pack(side='left', padx=6)
            ttk.Button(btns, text='Close', command=d.destroy).pack(side='right', padx=6)
        except Exception as e:
            messagebox.showerror('Advanced Grammar', f'Error: {e}')
    def create_installer(self):
        script = Path(__file__).parent / 'make_installer.ps1'
        if not script.exists():
            messagebox.showerror('Installer', 'Installer script not found.')
            return
        log_win = BuildLogWindow(self.root, title='Installer Build Log')
        q = queue.Queue()
        def reader_thread():
            try:
                cmd = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script)]
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in proc.stdout:
                    q.put(line)
                proc.wait()
                q.put(f'--PROCESS EXIT CODE: {proc.returncode}\n')
            except Exception as e:
                q.put(f'ERROR: {e}\n')
        def poll_queue():
            try:
                while True:
                    line = q.get_nowait()
                    log_win.append(line)
            except queue.Empty:
                pass
            if threading.active_count() > 1 or not q.empty():
                self.root.after(200, poll_queue)
        threading.Thread(target=reader_thread, daemon=True).start()
        poll_queue()
def main():
    root = tk.Tk()
    app = SimpleTextEditor(root)
    root.geometry('900x650')
    root.mainloop()
if __name__ == '__main__':
    main()
