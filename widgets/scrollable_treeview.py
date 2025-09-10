# widgets/scrollable_treeview.py
import tkinter as tk
from tkinter import ttk

class ScrollableTreeview(ttk.Frame):
    """
    Small wrapper Frame that contains a Treeview plus vertical & horizontal scrollbars.
    Also adds mouse-wheel support (vertical scrolling) and Shift+wheel for horizontal.
    Use .get_tree() to access the actual ttk.Treeview instance.
    """

    def __init__(self, master, columns=(), show="headings", height=15, **tree_kwargs):
        super().__init__(master)
        self.tree = ttk.Treeview(self, columns=columns, show=show, height=height, **tree_kwargs)

        # Scrollbars
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        # Layout: tree left/top, hsb bottom, vsb right
        self.vsb.pack(side="right", fill="y")
        self.hsb.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

        # Better wheel scroll (faster) and horizontal with Shift
        self._bind_mousewheel(self.tree)

    def get_tree(self):
        return self.tree

    # -------- mouse wheel handling --------
    def _on_mousewheel(self, event):
        """
        Normalize wheel events across platforms.
        Scroll vertically. Multiply by 3 to make scrolling snappier.
        """
        # Linux (Button-4/Button-5) handled elsewhere; here for Windows/macOS
        try:
            delta = int(-1 * (event.delta / 120))
        except Exception:
            delta = 0
        if delta == 0:
            # fallback for small delta values
            if hasattr(event, "num"):
                if event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
        # scroll faster: 3 units per wheel "click"
        self.tree.yview_scroll(delta * 3, "units")

    def _on_shift_mousewheel(self, event):
        """Shift + wheel -> horizontal scroll"""
        try:
            delta = int(-1 * (event.delta / 120))
        except Exception:
            delta = 0
        if delta == 0:
            if hasattr(event, "num"):
                if event.num == 4:
                    delta = -1
                elif event.num == 5:
                    delta = 1
        self.tree.xview_scroll(delta * 3, "units")

    def _bind_mousewheel(self, widget):
        # Bind when pointer enters the tree so other widgets keep their scrolling behaviour
        def _enter(e):
            # Windows + macOS
            widget.bind_all("<MouseWheel>", self._on_mousewheel)
            # Linux
            widget.bind_all("<Button-4>", self._on_mousewheel)
            widget.bind_all("<Button-5>", self._on_mousewheel)
            # Shift (horizontal)
            widget.bind_all("<Shift-MouseWheel>", self._on_shift_mousewheel)
            widget.bind_all("<Shift-Button-4>", self._on_shift_mousewheel)
            widget.bind_all("<Shift-Button-5>", self._on_shift_mousewheel)

        def _leave(e):
            widget.unbind_all("<MouseWheel>")
            widget.unbind_all("<Button-4>")
            widget.unbind_all("<Button-5>")
            widget.unbind_all("<Shift-MouseWheel>")
            widget.unbind_all("<Shift-Button-4>")
            widget.unbind_all("<Shift-Button-5>")

        widget.bind("<Enter>", _enter)
        widget.bind("<Leave>", _leave)
