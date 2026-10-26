#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, simpledialog
import json
import math
from datetime import datetime

class MikuPaint:
    def __init__(self, root):
        self.root = root
        self.root.title("MikuPaint - Hatsune Miku Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg='#0a0a0f')
        self.root.minsize(1000, 700)
        
        # Color scheme - Hatsune Miku full style
        self.colors = {
            'bg_dark': '#0a0a0f',
            'bg_panel': '#111118',
            'bg_toolbar': '#151520',
            'accent_cyan': '#39c5bb',
            'accent_pink': '#ff6b9d',
            'accent_purple': '#b84dff',
            'text': '#e0e0ff',
            'text_dim': '#8080a0',
            'border': '#39c5bb',
            'border_hover': '#ff6b9d',
            'active': '#ff6b9d'
        }
        
        # Canvas settings
        self.canvas_width = 800
        self.canvas_height = 600
        self.canvas_bg = '#ffffff'
        
        # Tool settings
        self.current_tool = 'pencil'
        self.current_color = '#000000'
        self.brush_size = 3
        self.eraser_size = 10
        
        # Drawing state
        self.old_x = None
        self.old_y = None
        self.start_x = None
        self.start_y = None
        self.temp_shape = None
        self.is_drawing = False
        
        # History for undo/redo
        self.history = []
        self.history_index = -1
        self.max_history = 50
        
        # Selection
        self.selection_rect = None
        self.selection_items = []
        
        # Ask for canvas size on startup
        self.ask_canvas_size()
        
        self.setup_ui()
        self.select_tool('pencil')
        self.setup_canvas()
        self.bind_shortcuts()
        
        # Save initial state
        self.save_to_history()
        
    def ask_canvas_size(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("New Canvas")
        dialog.geometry("320x220")
        dialog.configure(bg=self.colors['bg_panel'])
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 160
        y = (dialog.winfo_screenheight() // 2) - 110
        dialog.geometry(f"320x220+{x}+{y}")
        
        tk.Label(dialog, text="CREATE NEW CANVAS", 
                font=('Arial', 10, 'bold'), 
                bg=self.colors['bg_panel'], 
                fg=self.colors['accent_cyan']).pack(pady=(20,15))
        
        # Width
        frame_w = tk.Frame(dialog, bg=self.colors['bg_panel'])
        frame_w.pack(pady=5)
        tk.Label(frame_w, text="Width:", width=8, 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text']).pack(side=tk.LEFT)
        width_var = tk.StringVar(value="800")
        width_entry = tk.Entry(frame_w, textvariable=width_var, width=12,
                              bg=self.colors['bg_toolbar'], 
                              fg=self.colors['text'],
                              insertbackground=self.colors['accent_cyan'],
                              relief=tk.FLAT)
        width_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_w, text="px", 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_dim']).pack(side=tk.LEFT)
        
        # Height
        frame_h = tk.Frame(dialog, bg=self.colors['bg_panel'])
        frame_h.pack(pady=5)
        tk.Label(frame_h, text="Height:", width=8, 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text']).pack(side=tk.LEFT)
        height_var = tk.StringVar(value="600")
        height_entry = tk.Entry(frame_h, textvariable=height_var, width=12,
                               bg=self.colors['bg_toolbar'], 
                               fg=self.colors['text'],
                               insertbackground=self.colors['accent_cyan'],
                               relief=tk.FLAT)
        height_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(frame_h, text="px", 
                bg=self.colors['bg_panel'], 
                fg=self.colors['text_dim']).pack(side=tk.LEFT)
        
        def create():
            try:
                w = int(width_var.get())
                h = int(height_var.get())
                if w < 1 or h < 1 or w > 4096 or h > 4096:
                    raise ValueError
                self.canvas_width = w
                self.canvas_height = h
                dialog.destroy()
            except:
                messagebox.showerror("Error", "Invalid size! Use values between 1-4096")
        
        btn_frame = tk.Frame(dialog, bg=self.colors['bg_panel'])
        btn_frame.pack(pady=20)
        create_btn = tk.Button(btn_frame, text="CREATE", command=create,
                              bg=self.colors['accent_cyan'], 
                              fg='#000000',
                              font=('Arial', 8, 'bold'),
                              relief=tk.FLAT,
                              padx=20)
        create_btn.pack()
        
        dialog.bind('<Return>', lambda e: create())
        dialog.bind('<Escape>', lambda e: self.root.quit())
        width_entry.focus()
        
    def setup_ui(self):
        # Top bar with Miku decorations
        top_bar = tk.Frame(self.root, bg=self.colors['bg_panel'], height=40)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        tk.Label(top_bar, text="♪ MIKU PAINT ♪", 
                font=('Arial', 12, 'bold'),
                bg=self.colors['bg_panel'], 
                fg=self.colors['accent_cyan']).pack(side=tk.LEFT, padx=15)
        
        tk.Label(top_bar, text="HATSUNE MIKU EDITION", 
                font=('Arial', 7),
                bg=self.colors['bg_panel'], 
                fg=self.colors['accent_pink']).pack(side=tk.LEFT)
        
        # Menu buttons
        menu_frame = tk.Frame(top_bar, bg=self.colors['bg_panel'])
        menu_frame.pack(side=tk.RIGHT, padx=10)
        
        buttons = [
            ("NEW", self.new_canvas),
            ("OPEN", self.open_file),
            ("SAVE", self.save_file),
            ("UNDO", self.undo),
            ("REDO", self.redo)
        ]
        for text, cmd in buttons:
            btn = tk.Button(menu_frame, text=text, command=cmd,
                           bg=self.colors['bg_toolbar'], 
                           fg=self.colors['text'],
                           font=('Arial', 7, 'bold'),
                           relief=tk.FLAT,
                           padx=12, pady=2,
                           cursor='hand2')
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind('<Enter>', lambda e, b=btn: b.configure(bg=self.colors['accent_cyan'], fg='#000000'))
            btn.bind('<Leave>', lambda e, b=btn: b.configure(bg=self.colors['bg_toolbar'], fg=self.colors['text']))
        
        # Main container
        main_container = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left toolbar
        self.toolbar = tk.Frame(main_container, bg=self.colors['bg_toolbar'], width=80)
        self.toolbar.pack(side=tk.LEFT, fill=tk.Y)
        self.toolbar.pack_propagate(False)
        
        # Toolbar border
        tk.Frame(self.toolbar, bg=self.colors['accent_cyan'], height=2).pack(fill=tk.X)
        
        tk.Label(self.toolbar, text="TOOLS", 
                font=('Arial', 7, 'bold'),
                bg=self.colors['bg_toolbar'], 
                fg=self.colors['accent_pink']).pack(pady=(10,8))
        
        # Tools
        tools = [
            ('pencil', '✏'),
            ('brush', '🖌'),
            ('eraser', '⌫'),
            ('fill', '🪣'),
            ('line', '╱'),
            ('rect', '▭'),
            ('ellipse', '○'),
            ('picker', '💧'),
            ('text', 'T'),
            ('select', '⬚')
        ]
        
        self.tool_buttons = {}
        for tool_id, symbol in tools:
            btn = tk.Button(self.toolbar, text=symbol, 
                           font=('Arial', 16),
                           width=3, height=1,
                           bg=self.colors['bg_panel'], 
                           fg=self.colors['text'],
                           relief=tk.FLAT,
                           cursor='hand2',
                           command=lambda t=tool_id: self.select_tool(t))
            btn.pack(pady=2)
            self.tool_buttons[tool_id] = btn
            btn.bind('<Enter>', lambda e, b=btn, t=tool_id: 
                    b.configure(bg=self.colors['accent_purple']) if self.current_tool != t else None)
            btn.bind('<Leave>', lambda e, b=btn, t=tool_id: 
                    b.configure(bg=self.colors['active'] if self.current_tool == t else self.colors['bg_panel']))
        
        # Brush size
        tk.Label(self.toolbar, text="SIZE", 
                font=('Arial', 7, 'bold'),
                bg=self.colors['bg_toolbar'], 
                fg=self.colors['accent_pink']).pack(pady=(15,5))
        
        self.size_var = tk.IntVar(value=self.brush_size)
        size_scale = tk.Scale(self.toolbar, from_=1, to=50, 
                             orient=tk.VERTICAL,
                             variable=self.size_var,
                             command=self.update_size,
                             bg=self.colors['bg_toolbar'],
                             fg=self.colors['text'],
                             highlightthickness=0,
                             troughcolor=self.colors['bg_panel'],
                             activebackground=self.colors['accent_cyan'],
                             sliderrelief=tk.FLAT,
                             length=100)
        size_scale.pack()
        
        self.size_label = tk.Label(self.toolbar, text=str(self.brush_size),
                                 bg=self.colors['bg_toolbar'], 
                                 fg=self.colors['accent_cyan'],
                                 font=('Arial', 8))
        self.size_label.pack(pady=5)
        
        # Color picker
        tk.Label(self.toolbar, text="COLOR", 
                font=('Arial', 7, 'bold'),
                bg=self.colors['bg_toolbar'], 
                fg=self.colors['accent_pink']).pack(pady=(15,5))
        
        self.color_btn = tk.Button(self.toolbar, 
                                  bg=self.current_color,
                                  width=4, height=2,
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  command=self.choose_color)
        self.color_btn.pack()
        self.color_btn.bind('<Enter>', lambda e: self.color_btn.configure(relief=tk.RAISED))
        self.color_btn.bind('<Leave>', lambda e: self.color_btn.configure(relief=tk.FLAT))
        
        # Miku accent
        tk.Frame(self.toolbar, bg=self.colors['accent_cyan'], height=2).pack(fill=tk.X, side=tk.BOTTOM, pady=(0,5))
        tk.Label(self.toolbar, text="39", 
                font=('Arial', 6, 'bold'),
                bg=self.colors['bg_toolbar'], 
                fg=self.colors['accent_cyan']).pack(side=tk.BOTTOM)
        
        # Right panel - canvas area
        canvas_frame = tk.Frame(main_container, bg=self.colors['bg_dark'])
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas with scrollbars
        v_scroll = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL,
                               bg=self.colors['bg_panel'],
                               troughcolor=self.colors['bg_dark'],
                               activebackground=self.colors['accent_cyan'])
        h_scroll = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL,
                               bg=self.colors['bg_panel'],
                               troughcolor=self.colors['bg_dark'],
                               activebackground=self.colors['accent_cyan'])
        
        self.canvas = tk.Canvas(canvas_frame, 
                               width=self.canvas_width,
                               height=self.canvas_height,
                               bg=self.canvas_bg,
                               cursor='crosshair',
                               yscrollcommand=v_scroll.set,
                               xscrollcommand=h_scroll.set,
                               highlightthickness=2,
                               highlightbackground=self.colors['accent_cyan'],
                               highlightcolor=self.colors['accent_pink'])
        
        v_scroll.config(command=self.canvas.yview)
        h_scroll.config(command=self.canvas.xview)
        
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas.configure(scrollregion=(0,0,self.canvas_width,self.canvas_height))
        
        # Status bar
        status_bar = tk.Frame(self.root, bg=self.colors['bg_panel'], height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        tk.Frame(status_bar, bg=self.colors['accent_pink'], height=1).pack(fill=tk.X)
        
        self.status_label = tk.Label(status_bar, 
                                    text=f"Tool: Pencil | Size: {self.brush_size} | Canvas: {self.canvas_width}x{self.canvas_height}",
                                    bg=self.colors['bg_panel'], 
                                    fg=self.colors['text_dim'],
                                    font=('Arial', 7))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        tk.Label(status_bar, text="MikuPaint v1.0", 
                bg=self.colors['bg_panel'], 
                fg=self.colors['accent_cyan'],
                font=('Arial', 7, 'bold')).pack(side=tk.RIGHT, padx=10)
        
    def setup_canvas(self):
        self.canvas.bind('<Button-1>', self.on_button_press)
        self.canvas.bind('<B1-Motion>', self.on_button_motion)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_release)
        
    def bind_shortcuts(self):
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-n>', lambda e: self.new_canvas())
        self.root.bind('<KeyPress-p>', lambda e: self.select_tool('pencil'))
        self.root.bind('<KeyPress-b>', lambda e: self.select_tool('brush'))
        self.root.bind('<KeyPress-e>', lambda e: self.select_tool('eraser'))
        self.root.bind('<KeyPress-f>', lambda e: self.select_tool('fill'))
        self.root.bind('<KeyPress-l>', lambda e: self.select_tool('line'))
        self.root.bind('<KeyPress-r>', lambda e: self.select_tool('rect'))
        self.root.bind('<KeyPress-c>', lambda e: self.select_tool('ellipse'))
        self.root.bind('<KeyPress-i>', lambda e: self.select_tool('picker'))
        self.root.bind('<KeyPress-t>', lambda e: self.select_tool('text'))
        self.root.bind('<KeyPress-v>', lambda e: self.select_tool('select'))
        
    def select_tool(self, tool):
        self.current_tool = tool
        for tid, btn in self.tool_buttons.items():
            if tid == tool:
                btn.configure(bg=self.colors['active'])
            else:
                btn.configure(bg=self.colors['bg_panel'])
        if hasattr(self, 'update_status'):
            self.update_status()
        if hasattr(self, 'canvas'):
            if tool == 'text':
                self.canvas.config(cursor='xterm')
            elif tool == 'picker':
                self.canvas.config(cursor='crosshair')
            else:
                self.canvas.config(cursor='crosshair')
        
    def update_size(self, val):
        self.brush_size = int(val)
        self.eraser_size = int(val) + 7
        if hasattr(self, 'size_label'):
            self.size_label.configure(text=str(self.brush_size))
        if hasattr(self, 'update_status'):
            self.update_status()
        
    def choose_color(self):
        color = colorchooser.askcolor(title="Pick Color", color=self.current_color)[1]
        if color:
            self.current_color = color
            self.color_btn.configure(bg=self.current_color)
            
    def update_status(self):
        if not hasattr(self, 'status_label'):
            return
        tool_names = {
            'pencil': 'Pencil', 'brush': 'Brush', 'eraser': 'Eraser',
            'fill': 'Fill Bucket', 'line': 'Line', 'rect': 'Rectangle',
            'ellipse': 'Ellipse', 'picker': 'Color Picker', 
            'text': 'Text', 'select': 'Select'
        }
        self.status_label.configure(text=f"Tool: {tool_names.get(self.current_tool, self.current_tool)} | Size: {self.brush_size} | Canvas: {self.canvas_width}x{self.canvas_height}")
        
    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.old_x = self.start_x
        self.old_y = self.start_y
        self.is_drawing = True
        
        if self.current_tool == 'pencil':
            self.canvas.create_oval(self.start_x-self.brush_size, self.start_y-self.brush_size,
                                   self.start_x+self.brush_size, self.start_y+self.brush_size,
                                   fill=self.current_color, outline=self.current_color)
        elif self.current_tool == 'brush':
            self.canvas.create_oval(self.start_x-self.brush_size, self.start_y-self.brush_size,
                                   self.start_x+self.brush_size, self.start_y+self.brush_size,
                                   fill=self.current_color, outline='')
        elif self.current_tool == 'eraser':
            self.canvas.create_oval(self.start_x-self.eraser_size, self.start_y-self.eraser_size,
                                   self.start_x+self.eraser_size, self.start_y+self.eraser_size,
                                   fill=self.canvas_bg, outline='')
        elif self.current_tool == 'fill':
            self.fill_bucket(int(self.start_x), int(self.start_y))
            self.is_drawing = False
            self.save_to_history()
        elif self.current_tool == 'picker':
            self.pick_color(int(self.start_x), int(self.start_y))
            self.is_drawing = False
        elif self.current_tool == 'text':
            self.add_text(self.start_x, self.start_y)
            self.is_drawing = False
        elif self.current_tool in ['line', 'rect', 'ellipse']:
            pass
            
    def on_button_motion(self, event):
        if not self.is_drawing:
            return
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        if self.current_tool == 'pencil':
            self.canvas.create_line(self.old_x, self.old_y, cur_x, cur_y,
                                   fill=self.current_color, width=self.brush_size*2, capstyle=tk.ROUND)
            self.old_x = cur_x
            self.old_y = cur_y
        elif self.current_tool == 'brush':
            self.canvas.create_oval(cur_x-self.brush_size, cur_y-self.brush_size,
                                   cur_x+self.brush_size, cur_y+self.brush_size,
                                   fill=self.current_color, outline='')
        elif self.current_tool == 'eraser':
            self.canvas.create_oval(cur_x-self.eraser_size, cur_y-self.eraser_size,
                                   cur_x+self.eraser_size, cur_y+self.eraser_size,
                                   fill=self.canvas_bg, outline='')
        elif self.current_tool == 'line' and self.temp_shape:
            self.canvas.delete(self.temp_shape)
            self.temp_shape = self.canvas.create_line(self.start_x, self.start_y, cur_x, cur_y,
                                                     fill=self.current_color, width=max(1, self.brush_size))
        elif self.current_tool == 'rect' and self.temp_shape:
            self.canvas.delete(self.temp_shape)
            self.temp_shape = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y,
                                                          outline=self.current_color, width=max(1, self.brush_size))
        elif self.current_tool == 'ellipse' and self.temp_shape:
            self.canvas.delete(self.temp_shape)
            self.temp_shape = self.canvas.create_oval(self.start_x, self.start_y, cur_x, cur_y,
                                                     outline=self.current_color, width=max(1, self.brush_size))
        elif self.current_tool in ['line', 'rect', 'ellipse'] and not self.temp_shape:
            if self.current_tool == 'line':
                self.temp_shape = self.canvas.create_line(self.start_x, self.start_y, cur_x, cur_y,
                                                         fill=self.current_color, width=max(1, self.brush_size))
            elif self.current_tool == 'rect':
                self.temp_shape = self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y,
                                                              outline=self.current_color, width=max(1, self.brush_size))
            elif self.current_tool == 'ellipse':
                self.temp_shape = self.canvas.create_oval(self.start_x, self.start_y, cur_x, cur_y,
                                                         outline=self.current_color, width=max(1, self.brush_size))
        
    def on_button_release(self, event):
        if not self.is_drawing:
            return
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        
        if self.current_tool in ['line', 'rect', 'ellipse']:
            if self.temp_shape:
                self.canvas.delete(self.temp_shape)
            if self.current_tool == 'line':
                self.canvas.create_line(self.start_x, self.start_y, cur_x, cur_y,
                                       fill=self.current_color, width=max(1, self.brush_size))
            elif self.current_tool == 'rect':
                self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y,
                                            outline=self.current_color, width=max(1, self.brush_size))
            elif self.current_tool == 'ellipse':
                self.canvas.create_oval(self.start_x, self.start_y, cur_x, cur_y,
                                       outline=self.current_color, width=max(1, self.brush_size))
            self.temp_shape = None
            self.save_to_history()
        elif self.current_tool in ['pencil', 'brush', 'eraser']:
            self.save_to_history()
        
        self.is_drawing = False
        self.old_x = None
        self.old_y = None
        
    def fill_bucket(self, x, y):
        # Simple approximation - fill with rectangle if clicking on area
        # Note: True flood fill without PIL is complex, this is a simplified version
        self.canvas.create_rectangle(0, 0, self.canvas_width, self.canvas_height,
                                    fill=self.current_color, outline='')
        
    def pick_color(self, x, y):
        # Simplified color picker
        self.current_color = '#ff6b9d'
        self.color_btn.configure(bg=self.current_color)
        messagebox.showinfo("Color Picker", "Color picked! (Simplified in this version)")
        
    def add_text(self, x, y):
        text = simpledialog.askstring("Add Text", "Enter text:", parent=self.root)
        if text:
            self.canvas.create_text(x, y, text=text, 
                                   fill=self.current_color,
                                   font=('Arial', 12, 'bold'))
            self.save_to_history()
        
    def save_to_history(self):
        # Remove any history after current index
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        
        # Save canvas state
        items = []
        for item in self.canvas.find_all():
            coords = self.canvas.coords(item)
            item_type = self.canvas.type(item)
            config = {}
            if item_type == 'oval':
                config['type'] = 'oval'
                config['coords'] = coords
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['outline'] = self.canvas.itemcget(item, 'outline')
                config['width'] = self.canvas.itemcget(item, 'width')
            elif item_type == 'rectangle':
                config['type'] = 'rectangle'
                config['coords'] = coords
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['outline'] = self.canvas.itemcget(item, 'outline')
                config['width'] = self.canvas.itemcget(item, 'width')
            elif item_type == 'line':
                config['type'] = 'line'
                config['coords'] = coords
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['width'] = self.canvas.itemcget(item, 'width')
                config['capstyle'] = self.canvas.itemcget(item, 'capstyle')
                config['joinstyle'] = self.canvas.itemcget(item, 'joinstyle')
                config['smooth'] = self.canvas.itemcget(item, 'smooth')
            elif item_type == 'text':
                config['type'] = 'text'
                config['coords'] = coords
                config['text'] = self.canvas.itemcget(item, 'text')
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['font'] = self.canvas.itemcget(item, 'font')
            elif item_type == 'polygon':
                config['type'] = 'polygon'
                config['coords'] = coords
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['outline'] = self.canvas.itemcget(item, 'outline')
                config['width'] = self.canvas.itemcget(item, 'width')
                config['smooth'] = self.canvas.itemcget(item, 'smooth')
            items.append(config)
        
        state = {
            'canvas_width': self.canvas_width,
            'canvas_height': self.canvas_height,
            'items': items
        }
        
        self.history.append(state)
        self.history_index += 1
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.history_index -= 1
        
    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.restore_state(self.history[self.history_index])
            
    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.restore_state(self.history[self.history_index])
            
    def restore_state(self, state):
        self.canvas.delete('all')
        self.canvas_width = state['canvas_width']
        self.canvas_height = state['canvas_height']
        self.canvas.configure(scrollregion=(0,0,self.canvas_width,self.canvas_height))
        
        for item in state['items']:
            if item['type'] == 'oval':
                self.canvas.create_oval(item['coords'],
                                       fill=item.get('fill', ''),
                                       outline=item.get('outline', ''),
                                       width=item.get('width', 1))
            elif item['type'] == 'rectangle':
                self.canvas.create_rectangle(item['coords'],
                                            fill=item.get('fill', ''),
                                            outline=item.get('outline', ''),
                                            width=item.get('width', 1))
            elif item['type'] == 'line':
                self.canvas.create_line(item['coords'],
                                       fill=item.get('fill', 'black'),
                                       width=item.get('width', 1),
                                       capstyle=item.get('capstyle', 'butt'),
                                       joinstyle=item.get('joinstyle', 'round'),
                                       smooth=item.get('smooth', False))
            elif item['type'] == 'polygon':
                self.canvas.create_polygon(item['coords'],
                                          fill=item.get('fill', ''),
                                          outline=item.get('outline', ''),
                                          width=item.get('width', 1),
                                          smooth=item.get('smooth', False))
            elif item['type'] == 'text':
                self.canvas.create_text(item['coords'][0], item['coords'][1],
                                       text=item.get('text', ''),
                                       fill=item.get('fill', 'black'),
                                       font=item.get('font', 'Arial 12'))
        
    def new_canvas(self):
        self.ask_canvas_size()
        self.canvas.delete('all')
        self.canvas.configure(width=self.canvas_width, height=self.canvas_height,
                             scrollregion=(0,0,self.canvas_width,self.canvas_height))
        self.history = []
        self.history_index = -1
        self.save_to_history()
        self.update_status()
        
    def save_file(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".mipaint",
            filetypes=[("MikuPaint Files", "*.mipaint"), ("All Files", "*.*")],
            title="Save MikuPaint Project"
        )
        if not file_path:
            return
            
        items = []
        for item in self.canvas.find_all():
            coords = self.canvas.coords(item)
            item_type = self.canvas.type(item)
            config = {'type': item_type, 'coords': coords}
            
            if item_type == 'oval':
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['outline'] = self.canvas.itemcget(item, 'outline')
                config['width'] = self.canvas.itemcget(item, 'width')
            elif item_type == 'rectangle':
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['outline'] = self.canvas.itemcget(item, 'outline')
                config['width'] = self.canvas.itemcget(item, 'width')
            elif item_type == 'line':
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['width'] = self.canvas.itemcget(item, 'width')
                config['capstyle'] = self.canvas.itemcget(item, 'capstyle')
                config['joinstyle'] = self.canvas.itemcget(item, 'joinstyle')
                config['smooth'] = self.canvas.itemcget(item, 'smooth')
            elif item_type == 'polygon':
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['outline'] = self.canvas.itemcget(item, 'outline')
                config['width'] = self.canvas.itemcget(item, 'width')
                config['smooth'] = self.canvas.itemcget(item, 'smooth')
            elif item_type == 'text':
                config['text'] = self.canvas.itemcget(item, 'text')
                config['fill'] = self.canvas.itemcget(item, 'fill')
                config['font'] = self.canvas.itemcget(item, 'font')
                
            items.append(config)
        
        data = {
            'version': '1.0',
            'app': 'MikuPaint',
            'created': datetime.now().isoformat(),
            'canvas_width': self.canvas_width,
            'canvas_height': self.canvas_height,
            'items': items
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            messagebox.showinfo("Saved", "♪ Project saved successfully! ♪")
            self.root.title(f"MikuPaint - Hatsune Miku Edition - {file_path.split('/')[-1]}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {e}")
        
    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("MikuPaint Files", "*.mipaint"), ("All Files", "*.*")],
            title="Open MikuPaint Project"
        )
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.canvas.delete('all')
            self.canvas_width = data.get('canvas_width', 800)
            self.canvas_height = data.get('canvas_height', 600)
            self.canvas.configure(scrollregion=(0,0,self.canvas_width,self.canvas_height))
            
            for item in data.get('items', []):
                item_type = item['type']
                coords = item['coords']
                
                if item_type == 'oval':
                    self.canvas.create_oval(coords,
                                           fill=item.get('fill', ''),
                                           outline=item.get('outline', ''),
                                           width=item.get('width', 1))
                elif item_type == 'rectangle':
                    self.canvas.create_rectangle(coords,
                                                fill=item.get('fill', ''),
                                                outline=item.get('outline', ''),
                                                width=item.get('width', 1))
                elif item_type == 'line':
                    self.canvas.create_line(coords,
                                           fill=item.get('fill', 'black'),
                                           width=item.get('width', 1),
                                           capstyle=item.get('capstyle', 'butt'),
                                           joinstyle=item.get('joinstyle', 'round'),
                                           smooth=item.get('smooth', False))
                elif item_type == 'polygon':
                    self.canvas.create_polygon(coords,
                                               fill=item.get('fill', ''),
                                               outline=item.get('outline', ''),
                                               width=item.get('width', 1),
                                               smooth=item.get('smooth', False))
                elif item_type == 'text':
                    self.canvas.create_text(coords[0], coords[1],
                                           text=item.get('text', ''),
                                           fill=item.get('fill', 'black'),
                                           font=item.get('font', 'Arial 12'))
            
            self.history = []
            self.history_index = -1
            self.save_to_history()
            self.update_status()
            messagebox.showinfo("Opened", "♪ Project opened successfully! ♪")
            self.root.title(f"MikuPaint - Hatsune Miku Edition - {file_path.split('/')[-1]}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open: {e}")

def main():
    root = tk.Tk()
    app = MikuPaint(root)
    root.mainloop()

if __name__ == '__main__':
    main()
