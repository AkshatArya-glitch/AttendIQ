"""
AttendIQ — Student Attendance System  v6  (Redesigned)
Python · Tkinter · CSV

HOW TO RUN:  python AttendIQ_redesigned.py

Files created automatically alongside this script:
  students.csv    — student records (imported or added manually)
  attendance.csv  — daily attendance log

CSV import format:  id, name, roll, class, section, gender
"""

import tkinter as tk
import tkinter.font
from tkinter import ttk, messagebox, filedialog
import csv, os
from datetime import datetime, date, timedelta

# ══ DESIGN SYSTEM ════════════════════════════════════════════════
# Clean white + dark navy blue + vibrant accents — crisp & professional

# Backgrounds
BG          = "#f1f4f9"   # very light blue-grey page bg
SURFACE     = "#ffffff"   # pure white card surface
SURFACE2    = "#edf1f7"   # light input/field surface
SURFACE3    = "#e2e8f3"   # subtle hover surface
BORDER      = "#c4cfe3"   # clean slate border

# Text
TEXT        = "#0f172a"   # near-black primary text
TEXT2       = "#475569"   # secondary text (slate)
MUTED       = "#94a3b8"   # muted placeholder text

# Accent palette  (NAVY replaces teal as primary)
NAVY        = "#1e3a5f"   # ★ primary — dark navy blue
NAVY2       = "#162d4a"   # navy hover / darker shade
NAVY_LIGHT  = "#e8eef7"   # very light navy tint (backgrounds)
TEAL        = NAVY        # keep TEAL alias so existing refs still work
TEAL2       = NAVY2       # keep TEAL2 alias

AMBER       = "#b45309"   # warning / add-class  (darker amber)
AMBER2      = "#92400e"   # amber hover
EMERALD     = "#047857"   # success / present     (darker green)
CORAL       = "#be123c"   # danger / absent       (darker rose)
VIOLET      = "#5b21b6"   # register panel        (deeper violet)
VIOLET2     = "#4c1d95"   # violet hover
GOLD        = "#d97706"   # at-risk gold

# Semantic tag colours — light pastel, dark text  (crisp on white)
TAG_P_BG    = "#dcfce7";  TAG_P_FG = "#14532d"   # present
TAG_A_BG    = "#ffe4e6";  TAG_A_FG = "#881337"   # absent

# Section header colours (kept for legacy)
SEC_TEAL    = NAVY
SEC_VIOLET  = VIOLET
SEC_AMBER   = AMBER

AVATAR_COLORS = [NAVY, VIOLET, EMERALD, CORAL, AMBER,
                 "#1d4ed8", "#fb7185", "#7c3aed", "#059669", "#db2777"]

_DIR            = os.path.dirname(os.path.abspath(__file__))
STUDENTS_FILE   = os.path.join(_DIR, "students.csv")
ATTENDANCE_FILE = os.path.join(_DIR, "attendance.csv")

# FONT_MAIN is resolved once after the Tk root window is created (see AttendIQ.__init__)
FONT_MAIN  = "Inter"   # placeholder; overwritten at runtime

# ══ FILE HELPERS ═════════════════════════════════════════════════
def load_students():
    if not os.path.exists(STUDENTS_FILE): return []
    rows = []
    with open(STUDENTS_FILE, newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if not r or r[0].strip().lower() == "id": continue
            if len(r) == 5: r = [r[0], r[1], r[2], "10", r[3], r[4]]
            if len(r) >= 6: rows.append(tuple(r[:6]))
    return rows

def save_students(students):
    with open(STUDENTS_FILE, "w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(students)

def load_attendance():
    if not os.path.exists(ATTENDANCE_FILE): return {}
    records = {}
    with open(ATTENDANCE_FILE, newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) == 3:
                sid, d, st = row
                records.setdefault(sid, {})[d] = st
    return records

def flush_att(att):
    with open(ATTENDANCE_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for sid, dates in att.items():
            for d, st in dates.items():
                w.writerow([sid, d, st])

# ══ UTILITIES ════════════════════════════════════════════════════
def workdays_back(n):
    return [(date.today() - timedelta(days=i)).isoformat() for i in range(n)]

def all_att_dates(att):
    dates = set()
    for d_map in att.values(): dates.update(d_map.keys())
    return sorted(dates, reverse=True)

def get_initials(name):
    return "".join(p[0] for p in name.split()[:2]).upper()

def att_pct(sid, att, days=None):
    rec = att.get(sid, {})
    relevant = {d: rec[d] for d in days if d in rec} if days is not None else rec
    if not relevant: return 0
    return round(sum(1 for v in relevant.values() if v == "P") / len(relevant) * 100)

def pct_color(pct):
    return EMERALD if pct >= 85 else AMBER if pct >= 75 else CORAL

def av_color(sid):
    try:    return AVATAR_COLORS[int(sid) % len(AVATAR_COLORS)]
    except: return TEAL

def next_id(students):
    ids = [int(s[0]) for s in students if s[0].isdigit()]
    return str(max(ids, default=0) + 1)

def get_classes(students, extra_classes=None):
    classes = set(s[3] for s in students)
    if extra_classes: classes.update(extra_classes.keys())
    return sorted(classes, key=lambda x: (len(x), x))

def get_sections_for_class(students, cls, extra_classes=None):
    secs = set(s[4] for s in students if s[3] == cls)
    if extra_classes and cls in extra_classes: secs.update(extra_classes[cls])
    return sorted(secs)

# ── Widget helpers ────────────────────────────────────────────────
def make_btn(parent, text, cmd, bg=SURFACE2, fg=TEXT2,
             font_size=10, bold=True, padx=12, pady=5):
    _bg = bg  # capture for closures
    b = tk.Button(parent, text=text, command=cmd, bg=_bg, fg=fg,
                  relief="flat", font=(FONT_MAIN, font_size, "bold" if bold else "normal"),
                  padx=padx, pady=pady, cursor="hand2",
                  activebackground=_darken(_bg), activeforeground=fg, bd=0,
                  highlightthickness=0)
    def _enter(e): b.config(bg=_darken(_bg))
    def _leave(e): b.config(bg=_bg)
    b.bind("<Enter>", _enter); b.bind("<Leave>", _leave)
    return b

def _darken(hex_color):
    """Return a slightly darker shade of a hex color."""
    try:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        r, g, b = max(0,r-20), max(0,g-20), max(0,b-20)
        return f"#{r:02x}{g:02x}{b:02x}"
    except: return hex_color

def _lbl(parent, text, font_size=9, bold=False, fg=TEXT, bg=SURFACE, **kw):
    return tk.Label(parent, text=text, bg=bg, fg=fg,
                    font=(FONT_MAIN, font_size, "bold" if bold else "normal"), **kw)

def _divider(parent, bg=BORDER, height=1, **kw):
    return tk.Frame(parent, bg=bg, height=height, **kw)

def _pill(parent, text, bg, fg, font_size=8):
    """Rounded-looking label pill."""
    f = tk.Frame(parent, bg=bg)
    tk.Label(f, text=text, bg=bg, fg=fg,
             font=(FONT_MAIN, font_size, "bold"), padx=8, pady=3).pack()
    return f

# ══ STUDENT PROFILE POPUP ════════════════════════════════════════
class StudentProfileWindow(tk.Toplevel):
    def __init__(self, parent_app, sid):
        super().__init__(parent_app)
        student = next((s for s in parent_app.students if s[0] == sid), None)
        if not student: self.destroy(); return

        sid, name, roll, cls, section, gender = student
        pct     = att_pct(sid, parent_app.att)
        att_rec = parent_app.att.get(sid, {})
        present = sum(1 for v in att_rec.values() if v == "P")
        absent  = sum(1 for v in att_rec.values() if v == "A")

        self.title(f"Profile — {name}")
        self.geometry("560x640")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.transient(parent_app); self.grab_set()

        color = av_color(sid)

        # ── Navy header bar ───────────────────────────────────────
        hdr_frame = tk.Frame(self, bg=NAVY)
        hdr_frame.pack(fill="x")

        inner = tk.Frame(hdr_frame, bg=NAVY)
        inner.pack(fill="x", padx=22, pady=18)

        # Avatar circle (colour stays distinct per student)
        av = tk.Frame(inner, bg=color, width=56, height=56)
        av.pack(side="left", padx=(0, 16)); av.pack_propagate(False)
        tk.Label(av, text=get_initials(name), font=(FONT_MAIN, 16, "bold"),
                 bg=color, fg="#ffffff").place(relx=0.5, rely=0.5, anchor="center")

        # Name / meta — white on navy
        meta = tk.Frame(inner, bg=NAVY)
        meta.pack(side="left", fill="x", expand=True)
        tk.Label(meta, text=name, font=(FONT_MAIN, 16, "bold"),
                 bg=NAVY, fg="#ffffff", anchor="w").pack(fill="x")
        info = f"Roll {roll}  ·  Class {cls}  ·  Section {section}  ·  {'Male' if gender=='M' else 'Female'}"
        tk.Label(meta, text=info, font=(FONT_MAIN, 9),
                 bg=NAVY, fg="#93b4d4", anchor="w").pack(fill="x", pady=(4, 0))

        # Attendance % badge — sky blue on navy
        tk.Label(inner, text=f"{pct}%", font=(FONT_MAIN, 28, "bold"),
                 bg=NAVY, fg="#60a5fa").pack(side="right", padx=(0, 4))

        # Thin bottom border under header
        tk.Frame(self, bg="#0f2847", height=3).pack(fill="x")

        # Stat cards row
        sr = tk.Frame(self, bg=BG)
        sr.pack(fill="x", padx=16, pady=14)
        status_text  = "On Track ✓" if pct >= 85 else "Warning ⚠" if pct >= 75 else "At Risk ✗"
        status_color = pct_color(pct)

        for label, val, color_fg, card_bg, border_c in [
            ("Total Days", str(len(att_rec)), TEXT,      SURFACE,  BORDER),
            ("Present",    str(present),      EMERALD,   TAG_P_BG, EMERALD),
            ("Absent",     str(absent),       CORAL,     TAG_A_BG, CORAL),
            ("Status",     status_text,       status_color, SURFACE, status_color),
        ]:
            box = tk.Frame(sr, bg=card_bg, highlightbackground=border_c, highlightthickness=1)
            box.pack(side="left", expand=True, fill="both", padx=(0, 8))
            tk.Label(box, text=val,   font=(FONT_MAIN, 16, "bold"), bg=card_bg, fg=color_fg).pack(pady=(12, 2))
            tk.Label(box, text=label, font=(FONT_MAIN, 8, "bold"),  bg=card_bg, fg=TEXT2).pack(pady=(0, 12))

        _divider(self, bg=BORDER).pack(fill="x", padx=16)
        tk.Label(self, text="Attendance History", font=(FONT_MAIN, 10, "bold"),
                 bg=BG, fg=NAVY).pack(anchor="w", padx=20, pady=(12, 6))

        # Treeview
        tf = tk.Frame(self, bg=SURFACE)
        tf.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        cols = ("Date", "Day", "Status")
        tree = ttk.Treeview(tf, columns=cols, show="headings", height=12, selectmode="none")
        vsb  = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        for c, w in zip(cols, (170, 120, 110)):
            tree.heading(c, text=c)
            tree.column(c, width=w, anchor="center")
        tree.tag_configure("P", background=TAG_P_BG, foreground=TAG_P_FG)
        tree.tag_configure("A", background=TAG_A_BG, foreground=TAG_A_FG)
        for d in sorted(att_rec, reverse=True):
            st = att_rec[d]
            dt = datetime.fromisoformat(d)
            tree.insert("", "end", values=(dt.strftime("%d %B %Y"), dt.strftime("%A"),
                                           "Present" if st == "P" else "Absent"), tags=(st,))
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)

        make_btn(self, "Close", self.destroy, bg=NAVY, fg="#ffffff", bold=True, padx=24, pady=8
                 ).pack(pady=(0, 18))


# ══ AT-RISK POPUP ════════════════════════════════════════════════
class AtRiskWindow(tk.Toplevel):
    def __init__(self, parent_app):
        super().__init__(parent_app)
        self.title("⚠  Students At Risk")
        self.geometry("580x520")
        self.configure(bg=BG)
        self.transient(parent_app); self.grab_set()

        # ── Navy header bar ───────────────────────────────────────
        hdr = tk.Frame(self, bg=NAVY)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=NAVY)
        hdr_inner.pack(fill="x", padx=20, pady=16)
        tk.Label(hdr_inner, text="⚠", font=("Segoe UI Emoji", 18),
                 bg=NAVY, fg=GOLD).pack(side="left", padx=(0, 10))
        title_f = tk.Frame(hdr_inner, bg=NAVY)
        title_f.pack(side="left")
        tk.Label(title_f, text="Students At Risk", font=(FONT_MAIN, 14, "bold"),
                 bg=NAVY, fg="#ffffff").pack(anchor="w")
        tk.Label(title_f, text="Attendance below 75%", font=(FONT_MAIN, 9),
                 bg=NAVY, fg="#93b4d4").pack(anchor="w")
        tk.Frame(self, bg="#0f2847", height=3).pack(fill="x")

        at_risk = sorted(
            [(s, att_pct(s[0], parent_app.att)) for s in parent_app.students
             if att_pct(s[0], parent_app.att) < 75],
            key=lambda x: x[1])

        tk.Label(self, text=f"  {len(at_risk)} student(s) below 75% attendance",
                 font=(FONT_MAIN, 9, "bold"), bg=BG, fg=TEXT2).pack(anchor="w", padx=18, pady=(10, 6))

        tf = tk.Frame(self, bg=SURFACE)
        tf.pack(fill="both", expand=True, padx=16, pady=(0, 14))
        cols = ("Name", "Class", "Sec", "Roll", "Att %")
        tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="none")
        vsb  = ttk.Scrollbar(tf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        widths = {"Name": 200, "Class": 70, "Sec": 50, "Roll": 60, "Att %": 70}
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=widths[c], anchor="center" if c != "Name" else "w")
        tree.tag_configure("bad",  background=TAG_A_BG, foreground=CORAL)
        tree.tag_configure("warn", background="#fef3c7", foreground="#92400e")
        for s, pct in at_risk:
            sid, name, roll, cls, sec, gender = s
            tree.insert("", "end", values=(name, cls, sec, roll, f"{pct}%"),
                        tags=("bad" if pct < 60 else "warn",))
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        if not at_risk:
            tk.Label(tf, text="🎉  No students at risk!", font=(FONT_MAIN, 11, "bold"),
                     bg=SURFACE, fg=EMERALD).pack(pady=40)

        make_btn(self, "Close", self.destroy, padx=18, pady=6).pack(pady=(0, 14))


# ══ ADD / EDIT STUDENT DIALOG ═════════════════════════════════════
class StudentDialog(tk.Toplevel):
    def __init__(self, parent, on_save, existing=None):
        super().__init__(parent)
        self.on_save    = on_save
        self.parent_app = parent
        is_edit = existing is not None
        self.title("Edit Student" if is_edit else "Add Student")
        self.geometry("430x430")
        self.resizable(False, False)
        self.configure(bg=SURFACE)
        self.grab_set(); self.transient(parent); self.focus_set()

        accent = VIOLET if is_edit else NAVY
        # ── Navy header bar (same style as main topbar) ───────────
        hdr = tk.Frame(self, bg=NAVY)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=NAVY)
        hdr_inner.pack(fill="x", padx=20, pady=14)
        icon = "✏" if is_edit else "➕"
        tk.Label(hdr_inner, text=icon, font=(FONT_MAIN, 16, "bold"),
                 bg=NAVY, fg="#60a5fa").pack(side="left", padx=(0, 10))
        title_f = tk.Frame(hdr_inner, bg=NAVY)
        title_f.pack(side="left")
        tk.Label(title_f, text="Edit Student" if is_edit else "Add New Student",
                 font=(FONT_MAIN, 13, "bold"), bg=NAVY, fg="#ffffff").pack(anchor="w")
        tk.Label(title_f, text="Update existing record" if is_edit else "Fill in student details below",
                 font=(FONT_MAIN, 9), bg=NAVY, fg="#93b4d4").pack(anchor="w")
        tk.Frame(self, bg="#0f2847", height=3).pack(fill="x")

        form = tk.Frame(self, bg=SURFACE)
        form.pack(fill="x", padx=22, pady=14)
        form.columnconfigure(1, weight=1)

        all_classes  = get_classes(parent.students, getattr(parent, "extra_classes", None))
        all_sections = sorted(
            set(s[4] for s in parent.students) |
            {sec for secs in getattr(parent, "extra_classes", {}).values() for sec in secs})

        self.vars = {}; self.cls_var = tk.StringVar()
        self.sec_var = tk.StringVar(); self.gen_var = tk.StringVar(value="Male")

        entry_style = dict(bg=SURFACE2, fg=TEXT, insertbackground=NAVY, relief="flat",
                           font=(FONT_MAIN, 10, "bold"), highlightbackground=BORDER, highlightthickness=1)

        for row_i, (label, key) in enumerate([("Full Name", "name"), ("Roll No.", "roll")]):
            tk.Label(form, text=label, font=(FONT_MAIN, 9, "bold"), bg=SURFACE, fg=TEXT2).grid(
                row=row_i, column=0, sticky="w", padx=(0, 14), pady=(10, 2))
            v = tk.StringVar()
            e = tk.Entry(form, textvariable=v, **entry_style)
            e.grid(row=row_i, column=1, sticky="ew", ipady=7)
            e.bind("<FocusIn>",  lambda ev, x=e: x.config(highlightbackground=NAVY))
            e.bind("<FocusOut>", lambda ev, x=e: x.config(highlightbackground=BORDER))
            self.vars[key] = v

        for row_i, (label, var, values, hint, extra_kw) in enumerate([
            ("Class",   self.cls_var, all_classes,        "e.g. BCA, BBA, 10, 11", {}),
            ("Section", self.sec_var, all_sections,       "",                       {}),
            ("Gender",  self.gen_var, ["Male", "Female"], "",                       {"state": "readonly"}),
        ], start=2):
            tk.Label(form, text=label, font=(FONT_MAIN, 9, "bold"), bg=SURFACE, fg=TEXT2).grid(
                row=row_i * 2, column=0, sticky="w", padx=(0, 14), pady=(10, 2))
            cb = ttk.Combobox(form, textvariable=var, values=values,
                              font=(FONT_MAIN, 10), **extra_kw)
            cb.grid(row=row_i * 2, column=1, sticky="ew", ipady=5)
            if hint:
                tk.Label(form, text=hint, font=(FONT_MAIN, 8), bg=SURFACE, fg=MUTED).grid(
                    row=row_i * 2 + 1, column=1, sticky="w")
            if values: var.set(values[0])
            if label == "Class":   self.cls_cb = cb
            if label == "Section": self.sec_cb = cb

        self.existing_sid = None
        if existing:
            sid, name, roll, cls, section, gender = existing
            self.existing_sid = sid
            self.vars["name"].set(name); self.vars["roll"].set(roll)
            self.cls_var.set(cls); self.sec_var.set(section)
            self.gen_var.set("Male" if gender == "M" else "Female")

        _divider(self, bg=BORDER).pack(fill="x", pady=(10, 0))
        br = tk.Frame(self, bg=SURFACE)
        br.pack(fill="x", padx=22, pady=14)
        make_btn(br, "Cancel", self.destroy, padx=14, pady=7).pack(side="right", padx=(6, 0))
        make_btn(br, "Save" if is_edit else "Add Student", self._submit,
                 bg=accent, fg="#ffffff", bold=True, padx=14, pady=7).pack(side="right")
        self.bind("<Return>", lambda _: self._submit())
        self.bind("<Escape>", lambda _: self.destroy())

    def _submit(self):
        name = self.vars["name"].get().strip(); roll = self.vars["roll"].get().strip()
        cls  = self.cls_var.get().strip();      section = self.sec_var.get().strip()
        gender = "M" if self.gen_var.get() in ("M", "Male") else "F"
        for field, val in [("Full Name", name), ("Roll Number", roll),
                           ("Class", cls), ("Section", section)]:
            if not val:
                messagebox.showwarning("Required", f"{field} is required.", parent=self); return
        self.on_save(self.existing_sid, name, roll, cls, section, gender)
        self.destroy()


# ══ ADD CLASS / SECTION DIALOG ════════════════════════════════════
class AddClassSectionDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Add Class / Section")
        self.geometry("380x270")
        self.resizable(False, False)
        self.configure(bg=SURFACE)
        self.grab_set(); self.transient(parent); self.focus_set()

        # ── Navy header bar ───────────────────────────────────────
        hdr = tk.Frame(self, bg=NAVY)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=NAVY)
        hdr_inner.pack(fill="x", padx=20, pady=14)
        tk.Label(hdr_inner, text="🏫", font=("Segoe UI Emoji", 16),
                 bg=NAVY, fg="#fbbf24").pack(side="left", padx=(0, 10))
        title_f = tk.Frame(hdr_inner, bg=NAVY)
        title_f.pack(side="left")
        tk.Label(title_f, text="Add Class / Section", font=(FONT_MAIN, 13, "bold"),
                 bg=NAVY, fg="#ffffff").pack(anchor="w")
        tk.Label(title_f, text="Creates a slot — add students to populate it.",
                 font=(FONT_MAIN, 9), bg=NAVY, fg="#93b4d4").pack(anchor="w")
        tk.Frame(self, bg="#0f2847", height=3).pack(fill="x")

        form = tk.Frame(self, bg=SURFACE)
        form.pack(fill="x", padx=22, pady=14)
        form.columnconfigure(1, weight=1)

        self.cls_var = tk.StringVar(); self.sec_var = tk.StringVar()
        entry_style = dict(bg=SURFACE2, fg=TEXT, insertbackground=NAVY, relief="flat",
                           font=(FONT_MAIN, 10, "bold"), highlightbackground=BORDER, highlightthickness=1)

        for row_i, (label, var, hint) in enumerate([
            ("Class",   self.cls_var, "e.g. BCA, BBA, 10, Grade 5"),
            ("Section", self.sec_var, "e.g. A, B, Science"),
        ]):
            tk.Label(form, text=label, font=(FONT_MAIN, 9, "bold"), bg=SURFACE, fg=TEXT2).grid(
                row=row_i * 2, column=0, sticky="w", padx=(0, 14), pady=(8, 2))
            e = tk.Entry(form, textvariable=var, **entry_style)
            e.grid(row=row_i * 2, column=1, sticky="ew", ipady=7)
            e.bind("<FocusIn>",  lambda ev, x=e: x.config(highlightbackground=NAVY))
            e.bind("<FocusOut>", lambda ev, x=e: x.config(highlightbackground=BORDER))
            tk.Label(form, text=hint, font=(FONT_MAIN, 8), bg=SURFACE, fg=MUTED).grid(
                row=row_i * 2 + 1, column=1, sticky="w")

        _divider(self, bg=BORDER).pack(fill="x")
        br = tk.Frame(self, bg=SURFACE)
        br.pack(fill="x", padx=22, pady=12)
        make_btn(br, "Cancel", self.destroy, padx=14, pady=7).pack(side="right", padx=(6, 0))
        make_btn(br, "Create", self._submit, bg=AMBER, fg="#ffffff", bold=True, padx=14, pady=7).pack(side="right")

    def _submit(self):
        cls = self.cls_var.get().strip(); sec = self.sec_var.get().strip()
        if not cls or not sec:
            messagebox.showwarning("Required", "Both Class and Section are required.", parent=self); return
        existing = [(s[3], s[4]) for s in self.parent_app.students]
        extra    = [(c, s) for c, secs in self.parent_app.extra_classes.items() for s in secs]
        if (cls, sec) in existing or (cls, sec) in extra:
            messagebox.showwarning("Duplicate", f"Class {cls} · Section {sec} already exists.", parent=self); return
        self.parent_app._on_class_section_created(cls, sec)
        self.destroy()


# ══ IMPORT CSV DIALOG ═════════════════════════════════════════════
class ImportCSVDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent_app = parent
        self.title("Import Data from CSV")
        self.geometry("490x310")
        self.resizable(False, False)
        self.configure(bg=SURFACE)
        self.grab_set(); self.transient(parent); self.focus_set()

        # ── Navy header bar ───────────────────────────────────────
        hdr = tk.Frame(self, bg=NAVY)
        hdr.pack(fill="x")
        hdr_inner = tk.Frame(hdr, bg=NAVY)
        hdr_inner.pack(fill="x", padx=20, pady=14)
        tk.Label(hdr_inner, text="📂", font=("Segoe UI Emoji", 16),
                 bg=NAVY, fg="#60a5fa").pack(side="left", padx=(0, 10))
        title_f = tk.Frame(hdr_inner, bg=NAVY)
        title_f.pack(side="left")
        tk.Label(title_f, text="Import Students + Attendance", font=(FONT_MAIN, 13, "bold"),
                 bg=NAVY, fg="#ffffff").pack(anchor="w")
        tk.Label(title_f, text="CSV: id, name, roll, class, section, gender",
                 font=(FONT_MAIN, 9), bg=NAVY, fg="#93b4d4").pack(anchor="w")
        tk.Frame(self, bg="#0f2847", height=3).pack(fill="x")

        fr = tk.Frame(self, bg=SURFACE)
        fr.pack(fill="x", padx=22, pady=14)
        self.path_var = tk.StringVar(value="No file selected")
        tk.Label(fr, textvariable=self.path_var, bg=SURFACE2, fg=TEXT2,
                 font=(FONT_MAIN, 9), padx=10, pady=8, anchor="w",
                 highlightbackground=BORDER, highlightthickness=1).pack(side="left", fill="x", expand=True)
        make_btn(fr, "Browse…", self._browse, bg=NAVY, fg="#ffffff", padx=12, pady=4).pack(side="right", padx=(8, 0))

        self.result_lbl = tk.Label(self, text="", font=(FONT_MAIN, 9, "bold"),
                                   bg=SURFACE, fg=NAVY, wraplength=450, justify="left")
        self.result_lbl.pack(padx=22, pady=6, anchor="w")

        _divider(self, bg=BORDER).pack(fill="x")
        br = tk.Frame(self, bg=SURFACE)
        br.pack(fill="x", padx=22, pady=12)
        make_btn(br, "Close", self.destroy, padx=14, pady=7).pack(side="right")
        self.import_btn = make_btn(br, "Import", self._import, bg=EMERALD, fg="#ffffff", bold=True, padx=14, pady=7)
        self.import_btn.config(state="disabled")
        self.import_btn.pack(side="right", padx=(0, 6))
        self._filepath = None

    def _browse(self):
        path = filedialog.askopenfilename(title="Select CSV",
                                          filetypes=[("CSV files", "*.csv"), ("All", "*.*")])
        if path:
            self._filepath = path
            self.path_var.set(os.path.basename(path))
            self.import_btn.config(state="normal")
            self.result_lbl.config(text="")

    def _import(self):
        if not self._filepath: return
        try:
            with open(self._filepath, newline="", encoding="utf-8") as f:
                rows = list(csv.reader(f))
        except Exception as e:
            messagebox.showerror("Read Error", str(e), parent=self); return
        if not rows:
            messagebox.showwarning("Empty File", "The selected file has no data.", parent=self); return

        header     = [c.strip() for c in rows[0]]
        has_header = header[0].strip().lower() == "id"
        date_cols  = []
        if has_header:
            for i, col in enumerate(header[6:], start=6):
                col = col.strip()
                if len(col) == 10 and col[4] == "-" and col[7] == "-":
                    try: datetime.fromisoformat(col); date_cols.append((i, col))
                    except ValueError: pass
            data_rows = rows[1:]
        else:
            data_rows = rows

        added = updated = skipped = att_records = 0
        idx_map = {s[0]: i for i, s in enumerate(self.parent_app.students)}

        for r in data_rows:
            if not r or r[0].strip() in ("", "id"): continue
            if len(r) == 5: r = [r[0], r[1], r[2], "10", r[3], r[4]]
            if len(r) < 6: skipped += 1; continue
            sid = r[0].strip()
            t   = tuple(x.strip() for x in r[:6])
            if sid in idx_map:
                self.parent_app.students[idx_map[sid]] = t; updated += 1
            else:
                self.parent_app.students.append(t)
                idx_map[sid] = len(self.parent_app.students) - 1; added += 1
            for col_i, date_str in date_cols:
                if col_i < len(r):
                    val = r[col_i].strip().upper()
                    if val in ("P", "A"):
                        self.parent_app.att.setdefault(sid, {})[date_str] = val
                        att_records += 1

        save_students(self.parent_app.students)
        flush_att(self.parent_app.att)
        self.parent_app.reg_class_var.set("")
        self.parent_app.reg_section_var.set("")
        self.parent_app.refresh_all()
        att_msg = f"  ·  {att_records} attendance records" if att_records else ""
        self.result_lbl.config(fg=EMERALD,
            text=f"✅  Added {added}  ·  Updated {updated}  ·  Skipped {skipped}{att_msg}")


# ══ MAIN APPLICATION ══════════════════════════════════════════════
class AttendIQ(tk.Tk):
    def __init__(self):
        super().__init__()
        # Resolve best available font family after Tk root exists
        global FONT_MAIN
        _avail = tkinter.font.families(self)
        for _f in ("Inter", "Roboto", "Segoe UI", "Helvetica Neue", "Arial"):
            if _f in _avail:
                FONT_MAIN = _f
                break
        self.title("AttendIQ — Student Attendance Management")
        self.geometry("1360x860")
        self.minsize(980, 680)
        self.configure(bg=BG)

        self.students      = load_students()
        self.att           = load_attendance()
        self.extra_classes = {}
        self.selected      = set()
        self.today_str     = date.today().isoformat()

        self.reg_view_mode = tk.StringVar(value="30days")
        self._update_reg_days()

        self.search_var  = tk.StringVar()
        self.filter_cls  = tk.StringVar(value="All")
        self.filter_sec  = tk.StringVar(value="All")
        self.filter_stat = tk.StringVar(value="All")
        self.reg_class_var   = tk.StringVar(value="")
        self.reg_section_var = tk.StringVar(value="")

        self._refresh_pending    = False
        self._search_placeholder = "Search by name, roll or class…"

        self._build_ui()
        self._set_default_register()
        self.refresh_all()

    # ── Days helper ───────────────────────────────────────────────
    def _update_reg_days(self):
        if self.reg_view_mode.get() == "all":
            self.full_days = all_att_dates(self.att) or workdays_back(30)
        else:
            self.full_days = workdays_back(30)

    def _set_default_register(self):
        classes = get_classes(self.students, self.extra_classes)
        if not classes: return
        cls = self.reg_class_var.get()
        if not cls or cls not in classes:
            cls = classes[0]; self.reg_class_var.set(cls)
        secs = get_sections_for_class(self.students, cls, self.extra_classes)
        sec  = self.reg_section_var.get()
        if not sec or sec not in secs:
            sec = "A" if "A" in secs else (secs[0] if secs else "")
            self.reg_section_var.set(sec)
        if hasattr(self, "reg_section_cb"):
            self.reg_section_cb.configure(values=secs, state="readonly" if secs else "disabled")

    # ── UI Build ──────────────────────────────────────────────────
    def _build_ui(self):
        self._apply_styles()
        self._build_topbar()
        self._build_main()

    def _apply_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        # Treeview
        s.configure("Treeview",
                    background=SURFACE, fieldbackground=SURFACE,
                    foreground=TEXT, rowheight=38, borderwidth=0,
                    font=(FONT_MAIN, 11, "bold"))
        s.configure("Treeview.Heading",
                    background="#dde6f3", foreground=NAVY,
                    font=(FONT_MAIN, 10, "bold"), borderwidth=0, relief="flat")
        s.map("Treeview",
              background=[("selected", "#e0e7ff")],
              foreground=[("selected", TEXT)])
        # Scrollbars
        for orient in ("Vertical", "Horizontal"):
            s.configure(f"{orient}.TScrollbar",
                        background=SURFACE3, troughcolor=SURFACE,
                        borderwidth=0, arrowsize=12, arrowcolor=NAVY)
        # Combobox
        s.configure("TCombobox",
                    fieldbackground=SURFACE2, background=SURFACE2,
                    foreground=TEXT, selectbackground=NAVY2, borderwidth=1,
                    arrowsize=14, font=(FONT_MAIN, 10, "bold"))
        s.map("TCombobox",
              fieldbackground=[("readonly", SURFACE2)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", TEAL2)])
        # Radiobutton
        s.configure("TRadiobutton",
                    background=SURFACE, foreground=TEXT2,
                    font=(FONT_MAIN, 9, "bold"))

    def _build_topbar(self):
        bar = tk.Frame(self, bg=NAVY, height=76)
        bar.pack(fill="x"); bar.pack_propagate(False)
        # Bottom accent line
        tk.Frame(self, bg="#0f2847", height=3).pack(fill="x")

        # ── Wordmark ─────────────────────────────────────────────────
        logo_frame = tk.Frame(bar, bg=NAVY)
        logo_frame.pack(side="left", padx=(24, 0))

        name_row = tk.Frame(logo_frame, bg=NAVY)
        name_row.pack(anchor="w")
        tk.Label(name_row, text="Attend", font=(FONT_MAIN, 28, "bold"),
                 bg=NAVY, fg="#ffffff").pack(side="left")
        tk.Label(name_row, text="IQ", font=(FONT_MAIN, 28, "bold"),
                 bg=NAVY, fg="#60a5fa").pack(side="left")   # sky-blue accent on navy

        tk.Label(logo_frame, text="ATTENDANCE MANAGEMENT SYSTEM",
                 font=(FONT_MAIN, 8, "bold"),
                 bg=NAVY, fg="#93b4d4").pack(anchor="w")

        # Separator
        tk.Frame(bar, bg="#2d5080", width=1).pack(side="left", fill="y", padx=(20, 0), pady=12)

        # Date pill
        date_pill = tk.Frame(bar, bg="#162d4a")
        date_pill.pack(side="left", padx=18)
        tk.Label(date_pill, text=date.today().strftime("%A, %d %B %Y"),
                 font=(FONT_MAIN, 10, "bold"), bg="#162d4a", fg="#bfdbfe",
                 padx=14, pady=7).pack()

        # Action buttons (right-to-left) — each a DISTINCT colour family
        #  Add Student  → bright sky blue  (primary CTA, stands out on navy)
        #  Add Class    → amber/gold
        #  Import CSV   → slate-teal
        #  Export       → indigo
        #  Save         → emerald green
        #  Clear Data   → crimson red
        for text, cmd, bg_, fg_ in [
            ("🗑  Clear Data",        self._clear_all_data,          "#be123c", "#ffffff"),
            ("💾  Save",              self._save_all,                "#065f46", "#ffffff"),
            ("📦  Export by Class",   self._export_by_class_section, "#4338ca", "#ffffff"),
            ("📂  Import CSV",        self._import_csv,              "#0e6251", "#ffffff"),
            ("🏫  Add Class",         self._add_class_section,       "#92400e", "#ffffff"),
            ("➕  Add Student",       self._add_student,             "#2563eb", "#ffffff"),
        ]:
            b = tk.Button(bar, text=text, command=cmd, bg=bg_, fg=fg_, relief="flat",
                          font=(FONT_MAIN, 10, "bold"), padx=12, pady=0, cursor="hand2",
                          activebackground=_darken(bg_), activeforeground="#ffffff", bd=0,
                          highlightthickness=0)
            b.pack(side="right", padx=(0, 8), pady=14, ipady=5)

    def _build_main(self):
        p = tk.Frame(self, bg=BG)
        p.pack(fill="both", expand=True)

        self.stats_frame = tk.Frame(p, bg=BG)
        self.stats_frame.pack(fill="x", padx=18, pady=(14, 10))

        body = tk.Frame(p, bg=BG)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        body.columnconfigure(0, weight=0, minsize=440)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        self._build_student_panel(body)
        self._build_register_panel(body)

    # ── Stat cards ────────────────────────────────────────────────
    def _build_stat_cards(self):
        cls = self.reg_class_var.get(); sec = self.reg_section_var.get()
        if cls and sec:   subset = [s for s in self.students if s[3] == cls and s[4] == sec]
        elif cls:         subset = [s for s in self.students if s[3] == cls]
        else:             subset = list(self.students)

        total  = len(subset)
        pres   = sum(1 for s in subset if self.att.get(s[0], {}).get(self.today_str) == "P")
        abs_   = sum(1 for s in subset if self.att.get(s[0], {}).get(self.today_str) == "A")
        atrisk = sum(1 for s in self.students if att_pct(s[0], self.att) < 75)
        new_vals = [str(total), str(pres), str(abs_), str(total - pres - abs_), str(atrisk)]

        CARDS = [
            ("🎓", "Total Students",  NAVY,    NAVY_LIGHT, NAVY,  False),
            ("✅", "Present Today",   EMERALD, TAG_P_BG, EMERALD, False),
            ("❌", "Absent Today",    CORAL,   TAG_A_BG, CORAL,   False),
            ("❓", "Unmarked Today",  TEXT2,   SURFACE2, BORDER,  False),
            ("⚠️", "At Risk (<75%)", AMBER,   "#fffbeb", AMBER,  True),
        ]

        if not hasattr(self, "_stat_val_labels"):
            self._stat_val_labels = []
            for i, (icon, label, color, card_bg, border_c, clickable) in enumerate(CARDS):
                c = tk.Frame(self.stats_frame, bg=card_bg,
                             highlightbackground=border_c, highlightthickness=1)
                c.pack(side="left", expand=True, fill="both", padx=(0, 8))
                tk.Frame(c, bg=color, height=4).pack(fill="x")
                tk.Label(c, text=icon, font=("Segoe UI Emoji", 18),
                         bg=card_bg, fg=color).pack(pady=(10, 2))
                val_lbl = tk.Label(c, text=new_vals[i],
                                   font=(FONT_MAIN, 26, "bold"), bg=card_bg, fg=color)
                val_lbl.pack()
                self._stat_val_labels.append(val_lbl)
                tk.Label(c, text=label.upper(),
                         font=(FONT_MAIN, 8, "bold"),
                         bg=card_bg, fg=color).pack(pady=(2, 10))
                if clickable:
                    c.configure(cursor="hand2")
                    for w in c.winfo_children():
                        w.configure(cursor="hand2")
                        w.bind("<Button-1>", lambda e: AtRiskWindow(self))
                    c.bind("<Button-1>", lambda e: AtRiskWindow(self))

            self._ctx_lbl = tk.Label(self.stats_frame, font=(FONT_MAIN, 8),
                                     bg=BG, fg=MUTED)
            self._ctx_lbl.place(relx=1.0, rely=1.0, anchor="se")
        else:
            for lbl, val in zip(self._stat_val_labels, new_vals):
                lbl.config(text=val)

        ctx = (f"Class {cls} · Sec {sec}" if (cls and sec) else f"Class {cls}" if cls else "All students")
        self._ctx_lbl.config(text=f"Register: {ctx}")

    # ── Student panel ─────────────────────────────────────────────
    def _build_student_panel(self, parent):
        frame = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # Section header
        sec_hdr = tk.Frame(frame, bg=NAVY, height=46)
        sec_hdr.pack(fill="x"); sec_hdr.pack_propagate(False)
        tk.Label(sec_hdr, text="  👥  Student List", font=(FONT_MAIN, 12, "bold"),
                 bg=NAVY, fg="#ffffff", padx=10).pack(side="left", fill="y")
        self.stu_count_lbl = tk.Label(sec_hdr, text="", font=(FONT_MAIN, 8, "bold"),
                                      bg="#162d4a", fg="#bfdbfe", padx=10, pady=4)
        self.stu_count_lbl.pack(side="left", padx=8, pady=9)

        # Search bar
        sf1 = tk.Frame(frame, bg=SURFACE)
        sf1.pack(fill="x", padx=12, pady=(10, 6))
        sw = tk.Frame(sf1, bg=SURFACE2, highlightbackground=BORDER, highlightthickness=1)
        sw.pack(fill="x")
        tk.Label(sw, text="🔍", bg=SURFACE2, fg=MUTED, font=(FONT_MAIN, 9)).pack(side="left", padx=(8, 2))
        self._se = tk.Entry(sw, textvariable=self.search_var, bg=SURFACE2, fg=MUTED,
                            insertbackground=NAVY, relief="flat",
                            font=(FONT_MAIN, 10, "bold"))
        self._se.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 4))
        tk.Button(sw, text="✕", command=self._clear_search, bg=SURFACE2, fg=MUTED,
                  relief="flat", font=(FONT_MAIN, 9), cursor="hand2",
                  padx=4, bd=0, highlightthickness=0).pack(side="right", padx=4)
        self._se.insert(0, self._search_placeholder)
        self._se.bind("<FocusIn>",  self._sfocus_in)
        self._se.bind("<FocusOut>", self._sfocus_out)
        self._se.bind("<FocusIn>",  lambda e: sw.config(highlightbackground=NAVY), add="+")
        self._se.bind("<FocusOut>", lambda e: sw.config(highlightbackground=BORDER), add="+")
        self.search_var.trace_add("write", lambda *_: self._schedule_refresh_list())

        # Filters row
        sf2 = tk.Frame(frame, bg=SURFACE)
        sf2.pack(fill="x", padx=12, pady=(0, 6))
        all_classes = get_classes(self.students, self.extra_classes)
        all_sections = sorted(
            set(s[4] for s in self.students) |
            {sec for secs in self.extra_classes.values() for sec in secs})

        for label, var, values, width, bind_cmd in [
            ("Class:",  self.filter_cls,  ["All"] + all_classes,                   8, lambda _: self._on_list_cls_change()),
            ("Sec:",    self.filter_sec,  ["All"] + all_sections,                  6, lambda _: self._refresh_list()),
            ("Status:", self.filter_stat, ["All", "Present", "Absent", "Unmarked"],9, lambda _: self._refresh_list()),
        ]:
            tk.Label(sf2, text=label, font=(FONT_MAIN, 10, "bold"),
                     bg=SURFACE, fg=TEXT2).pack(side="left", padx=(0, 4))
            cb = ttk.Combobox(sf2, textvariable=var, values=values,
                              state="readonly", width=width)
            cb.pack(side="left", padx=(0, 10))
            cb.bind("<<ComboboxSelected>>", bind_cmd)
            if label == "Class:": self.list_cls_cb = cb
            if label == "Sec:":   self.list_sec_cb = cb

        # Action bar
        action_bar = tk.Frame(frame, bg=SURFACE3)
        action_bar.pack(fill="x")
        btn_kw = dict(font=(FONT_MAIN, 9, "bold"), relief="flat",
                      padx=8, pady=4, cursor="hand2", bd=0, highlightthickness=0)
        self._sel_all_btn = tk.Button(action_bar, text="☐ Select All",
                                      command=self._toggle_select_all,
                                      bg=SURFACE3, fg=TEXT2, **btn_kw)
        self._sel_all_btn.pack(side="left", padx=(6, 2), pady=4)
        self.sel_lbl = tk.Label(action_bar, text="", font=(FONT_MAIN, 8, "bold"),
                                bg=SURFACE3, fg=NAVY)
        self.sel_lbl.pack(side="left", padx=4)
        make_btn(action_bar, "✅ Mark Present", lambda: self._bulk_mark("P"),
                 bg="#047857", fg="#ffffff", font_size=9, padx=8, pady=4
                 ).pack(side="right", padx=4, pady=4)
        make_btn(action_bar, "❌ Mark Absent", lambda: self._bulk_mark("A"),
                 bg="#be123c", fg="#ffffff", font_size=9, padx=8, pady=4
                 ).pack(side="right", padx=(0, 4), pady=4)
        make_btn(action_bar, "🗑 Remove", self._bulk_remove,
                 bg="#374151", fg="#ffffff", font_size=9, padx=8, pady=4
                 ).pack(side="right", padx=(0, 4), pady=4)

        # Treeview
        lc = tk.Frame(frame, bg=SURFACE)
        lc.pack(fill="both", expand=True)
        stu_cols = ("chk", "name", "roll", "cls", "sec", "today", "pct")
        self.stu_tree = ttk.Treeview(lc, columns=stu_cols, show="headings",
                                     selectmode="extended")
        vsb = ttk.Scrollbar(lc, orient="vertical", command=self.stu_tree.yview)
        self.stu_tree.configure(yscrollcommand=vsb.set)
        for col, text, width, anchor, stretch in [
            ("chk",   "✓",     32,  "center", False),
            ("name",  "Name",  155, "w",      True),
            ("roll",  "Roll",  44,  "center", False),
            ("cls",   "Class", 58,  "center", False),
            ("sec",   "Sec",   36,  "center", False),
            ("today", "Today", 54,  "center", False),
            ("pct",   "Att%",  50,  "center", False),
        ]:
            self.stu_tree.heading(col, text=text)
            self.stu_tree.column(col, width=width, anchor=anchor, stretch=stretch)
        for tag, cfg in [
            ("sel",     {"background": "#dbeafe", "foreground": TEXT}),
            ("present", {"background": TAG_P_BG,  "foreground": EMERALD}),
            ("absent",  {"background": TAG_A_BG,  "foreground": CORAL}),
            ("atrisk",  {"foreground": AMBER}),
        ]:
            self.stu_tree.tag_configure(tag, **cfg)
        vsb.pack(side="right", fill="y")
        self.stu_tree.pack(fill="both", expand=True)
        self.stu_tree.bind("<ButtonRelease-1>", self._on_stu_click)
        self.stu_tree.bind("<Double-Button-1>", self._on_stu_dbl)
        self.stu_tree.bind("<Button-3>", self._on_stu_right_click)

    # ── Register panel ────────────────────────────────────────────
    def _build_register_panel(self, parent):
        frame = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER, highlightthickness=1)
        frame.grid(row=0, column=1, sticky="nsew")
        self._reg_frame = frame

        # Section header
        sec_hdr = tk.Frame(frame, bg=NAVY, height=46)
        sec_hdr.pack(fill="x"); sec_hdr.pack_propagate(False)
        tk.Label(sec_hdr, text="  📋  Attendance Register", font=(FONT_MAIN, 12, "bold"),
                 bg=NAVY, fg="#ffffff", padx=10).pack(side="left", fill="y")

        # View mode radios
        vm_frame = tk.Frame(sec_hdr, bg=NAVY)
        vm_frame.pack(side="left", padx=14, fill="y")
        tk.Label(vm_frame, text="View:", font=(FONT_MAIN, 8, "bold"),
                 bg=NAVY, fg="#93b4d4").pack(side="left", padx=(0, 6))
        for label, val in [("Last 30 days", "30days"), ("All data", "all")]:
            tk.Radiobutton(vm_frame, text=label, variable=self.reg_view_mode, value=val,
                           command=self._on_view_mode_change, bg=NAVY, fg="#ffffff",
                           selectcolor="#0f2847", activebackground=NAVY,
                           activeforeground="#bfdbfe", font=(FONT_MAIN, 8, "bold"),
                           cursor="hand2").pack(side="left", padx=3)

        make_btn(sec_hdr, "📤 Export", self._export_csv,
                 bg="#60a5fa", fg=NAVY, padx=10, pady=3
                 ).pack(side="right", padx=8, pady=6)

        # Filter bar
        fr = tk.Frame(frame, bg=SURFACE3, highlightbackground=BORDER, highlightthickness=0)
        fr.pack(fill="x")
        all_classes = get_classes(self.students, self.extra_classes)
        tk.Label(fr, text="  Class:", font=(FONT_MAIN, 10, "bold"),
                 bg=SURFACE3, fg=TEXT2).pack(side="left", padx=(14, 4), pady=8)
        self.reg_class_cb = ttk.Combobox(fr, textvariable=self.reg_class_var,
                                          values=all_classes, state="readonly", width=9)
        self.reg_class_cb.pack(side="left", pady=8)
        self.reg_class_cb.bind("<<ComboboxSelected>>", self._on_reg_class_change)
        tk.Label(fr, text="  Section:", font=(FONT_MAIN, 10, "bold"),
                 bg=SURFACE3, fg=TEXT2).pack(side="left", padx=(14, 4))
        self.reg_section_cb = ttk.Combobox(fr, textvariable=self.reg_section_var,
                                            values=[], state="disabled", width=7)
        self.reg_section_cb.pack(side="left", pady=8)
        self.reg_section_cb.bind("<<ComboboxSelected>>", self._on_reg_section_change)
        self.dir_lbl = tk.Label(fr, text="", font=(FONT_MAIN, 8, "bold"),
                                bg=SURFACE3, fg=NAVY2)
        self.dir_lbl.pack(side="left", padx=(14, 0))
        self._update_dir_label()
        tk.Label(fr, text="click cell → toggle P/A  |  click name → profile",
                 font=(FONT_MAIN, 8), bg=SURFACE3, fg=MUTED).pack(side="right", padx=10)

        self._reg_tree_frame = tk.Frame(frame, bg=SURFACE)
        self._reg_tree_frame.pack(fill="both", expand=True)
        self._build_reg_tree()

    # ── Search / filter helpers ───────────────────────────────────
    def _clear_search(self):
        self.search_var.set("")
        self._se.delete(0, "end")
        self._se.insert(0, self._search_placeholder)
        self._se.config(fg=MUTED)

    def _toggle_select_all(self):
        all_ids = list(self.stu_tree.get_children())
        if self.selected:
            for iid in list(self.selected):
                self.selected.discard(iid); self._update_stu_row(iid)
            self.selected.clear()
            self.sel_lbl.config(text="")
            self._sel_all_btn.config(text="☐ Select All", fg=TEXT2)
        else:
            for iid in all_ids:
                self.selected.add(iid); self._update_stu_row(iid)
            n = len(self.selected)
            self.sel_lbl.config(text=f"{n} selected" if n else "")
            self._sel_all_btn.config(text="☑ Select All", fg=NAVY)

    def _clear_selection(self):
        for iid in list(self.selected):
            self.selected.discard(iid); self._update_stu_row(iid)
        self.selected.clear()
        self.sel_lbl.config(text="")
        if hasattr(self, "_sel_all_btn"):
            self._sel_all_btn.config(text="☐ Select All", fg=TEXT2)

    def _on_list_cls_change(self):
        cls = self.filter_cls.get()
        secs = (sorted(set(s[4] for s in self.students) |
                       {sec for secs in self.extra_classes.values() for sec in secs})
                if cls == "All" else
                get_sections_for_class(self.students, cls, self.extra_classes))
        self.list_sec_cb.configure(values=["All"] + secs)
        self.filter_sec.set("All")
        self._refresh_list()

    def _schedule_refresh_list(self):
        if hasattr(self, "_refresh_id"):
            self.after_cancel(self._refresh_id)
        self._refresh_pending = True
        self._refresh_id = self.after(250, self._do_refresh_list)

    def _sfocus_in(self, e):
        if self._se.get() == self._search_placeholder:
            self._se.delete(0, "end"); self._se.config(fg=TEXT)

    def _sfocus_out(self, e):
        if not self._se.get():
            self._se.insert(0, self._search_placeholder); self._se.config(fg=MUTED)

    def _on_stu_click(self, event):
        col = self.stu_tree.identify_column(event.x)
        iid = self.stu_tree.identify_row(event.y)
        if not iid: return
        if col == "#1":
            if iid in self.selected: self.selected.discard(iid)
            else:                    self.selected.add(iid)
            self._update_stu_row(iid)
            n = len(self.selected)
            self.sel_lbl.config(text=f"{n} selected" if n else "")

    def _on_stu_dbl(self, event):
        iid = self.stu_tree.identify_row(event.y)
        if iid:
            StudentProfileWindow(self, iid)

    def _on_stu_right_click(self, event):
        iid = self.stu_tree.identify_row(event.y)
        if not iid:
            return
        student = next((s for s in self.students if s[0] == iid), None)
        if not student:
            return
        menu = tk.Menu(self, tearoff=0, bg=SURFACE, fg=TEXT,
                       font=(FONT_MAIN, 10), relief="flat",
                       activebackground=NAVY_LIGHT, activeforeground=NAVY)
        menu.add_command(label="👤  View Profile",
                         command=lambda: StudentProfileWindow(self, iid))
        menu.add_command(label="✏  Edit Student",
                         command=lambda: self._edit_student(iid))
        menu.add_separator()
        menu.add_command(label="🗑  Remove Student",
                         command=lambda: self._delete_one(iid, student[1]))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _update_stu_row(self, sid):
        if not self.stu_tree.exists(sid): return
        vals = list(self.stu_tree.item(sid, "values"))
        vals[0] = "☑" if sid in self.selected else "☐"
        # Keep colour tags, drop old sel, re-append sel at end so bg shows
        # but foreground from present/absent/atrisk still wins (tkinter last-tag-wins)
        tags = [t for t in self.stu_tree.item(sid, "tags") if t != "sel"]
        if sid in self.selected: tags.append("sel")
        self.stu_tree.item(sid, values=vals, tags=tags)

    def _refresh_list(self):
        self._do_refresh_list()

    def _do_refresh_list(self):
        self._refresh_pending = False
        self.stu_tree.delete(*self.stu_tree.get_children())
        q     = self.search_var.get().strip().lower()
        if q == self._search_placeholder.lower(): q = ""
        fcls  = self.filter_cls.get()
        fsec  = self.filter_sec.get()
        fstat = self.filter_stat.get()
        count = 0
        for s in self.students:
            sid, name, roll, cls, sec, gender = s
            if q and q not in name.lower() and q not in roll.lower() and q not in cls.lower(): continue
            if fcls != "All" and cls != fcls: continue
            if fsec != "All" and sec != fsec: continue
            ts = self.att.get(sid, {}).get(self.today_str)
            if fstat == "Present"  and ts != "P":      continue
            if fstat == "Absent"   and ts != "A":      continue
            if fstat == "Unmarked" and ts is not None: continue
            pct   = att_pct(sid, self.att)
            chk   = "☑" if sid in self.selected else "☐"
            today = "P" if ts == "P" else ("A" if ts == "A" else "–")
            tags  = []
            if ts == "P":   tags.append("present")
            elif ts == "A": tags.append("absent")
            if pct < 75:    tags.append("atrisk")
            if sid in self.selected: tags.append("sel")
            self.stu_tree.insert("", "end", iid=sid,
                values=(chk, name, roll, cls, sec, today, f"{pct}%"), tags=tags)
            count += 1
        self.stu_count_lbl.config(text=f"{count}/{len(self.students)}")

    # ── Register panel helpers ────────────────────────────────────
    def _update_dir_label(self):
        if self.reg_view_mode.get() == "30days":
            self.dir_lbl.config(text=f"Today ({date.today().strftime('%d/%m')}) ← newest")
        else:
            self.dir_lbl.config(text="All recorded dates (newest left)")

    def _on_view_mode_change(self):
        self._update_reg_days(); self._update_dir_label(); self._rebuild_reg_tree()

    def _rebuild_reg_tree(self):
        for w in self._reg_tree_frame.winfo_children(): w.destroy()
        self._build_reg_tree(); self._refresh_full_reg()

    def _build_reg_tree(self):
        today_iso = date.today().isoformat()
        cols = ["Student"] + list(self.full_days) + ["Att%"]
        tf = self._reg_tree_frame
        self.full_tree = ttk.Treeview(tf, columns=cols, show="headings", selectmode="none")
        vsb = ttk.Scrollbar(tf, orient="vertical",   command=self.full_tree.yview)
        hsb = ttk.Scrollbar(tf, orient="horizontal", command=self.full_tree.xview)
        self.full_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.full_tree.heading("Student", text="Student")
        self.full_tree.column("Student", width=178, anchor="w", stretch=False)
        self.full_tree.heading("Att%", text="Att%")
        self.full_tree.column("Att%", width=52, anchor="center", stretch=False)
        for iso_d in self.full_days:
            display = datetime.fromisoformat(iso_d).strftime("%d/%m")
            self.full_tree.heading(iso_d, text=f"▶{display}" if iso_d == today_iso else display)
            self.full_tree.column(iso_d, width=44, anchor="center", stretch=False)
        self.full_tree.tag_configure("P",    background=TAG_P_BG, foreground=EMERALD)
        self.full_tree.tag_configure("A",    background=TAG_A_BG, foreground=CORAL)
        self.full_tree.tag_configure("none", background=SURFACE,  foreground=MUTED)
        vsb.pack(side="right",  fill="y")
        hsb.pack(side="bottom", fill="x")
        self.full_tree.pack(fill="both", expand=True)
        self.full_tree.bind("<ButtonRelease-1>", self._on_reg_click)

    def _on_reg_class_change(self, event=None):
        cls  = self.reg_class_var.get()
        secs = get_sections_for_class(self.students, cls, self.extra_classes)
        self.reg_section_var.set("A" if "A" in secs else (secs[0] if secs else ""))
        self.reg_section_cb.configure(values=secs, state="readonly" if secs else "disabled")
        self._refresh_full_reg(); self._build_stat_cards()

    def _on_reg_section_change(self, event=None):
        self._refresh_full_reg(); self._build_stat_cards()

    def _sync_reg_dropdowns(self):
        all_classes  = get_classes(self.students, self.extra_classes)
        all_sections = sorted(
            set(s[4] for s in self.students) |
            {sec for secs in self.extra_classes.values() for sec in secs})
        self.reg_class_cb.configure(values=all_classes)
        cls = self.reg_class_var.get()
        if cls:
            secs = get_sections_for_class(self.students, cls, self.extra_classes)
            self.reg_section_cb.configure(values=secs if secs else [],
                                          state="readonly" if secs else "disabled")
        cur_cls = self.filter_cls.get()
        valid_cls_list = ["All"] + all_classes
        self.list_cls_cb.configure(values=valid_cls_list)
        if cur_cls not in valid_cls_list:
            self.filter_cls.set("All"); cur_cls = "All"
        valid_sec_list = (["All"] + all_sections if cur_cls == "All" else
                          ["All"] + get_sections_for_class(self.students, cur_cls, self.extra_classes))
        self.list_sec_cb.configure(values=valid_sec_list)
        if self.filter_sec.get() not in valid_sec_list:
            self.filter_sec.set("All")

    def _refresh_full_reg(self):
        if not hasattr(self, "full_tree"): return
        self.full_tree.delete(*self.full_tree.get_children())
        cls = self.reg_class_var.get(); sec = self.reg_section_var.get()
        if not cls or not sec: return
        today_iso = date.today().isoformat()
        for s in self.students:
            sid, name, roll, scls, ssec, gender = s
            if scls != cls or ssec != sec: continue
            pct  = att_pct(sid, self.att, self.full_days)
            vals = [f"{name}  (#{roll})"]
            today_status = self.att.get(sid, {}).get(today_iso, "")
            for d in self.full_days:
                v = self.att.get(sid, {}).get(d, "")
                vals.append(v if v else "–")
            vals.append(f"{pct}%")
            tag = "P" if today_status == "P" else ("A" if today_status == "A" else "none")
            self.full_tree.insert("", "end", iid=sid, values=vals, tags=(tag,))

    def _update_reg_row(self, sid):
        if not self.full_tree.exists(sid): return
        today_iso = date.today().isoformat()
        pct  = att_pct(sid, self.att, self.full_days)
        vals = list(self.full_tree.item(sid, "values"))
        for i, d in enumerate(self.full_days):
            v = self.att.get(sid, {}).get(d, "")
            vals[i + 1] = v if v else "–"
        vals[-1] = f"{pct}%"
        today_status = self.att.get(sid, {}).get(today_iso, "")
        tag = "P" if today_status == "P" else ("A" if today_status == "A" else "none")
        self.full_tree.item(sid, values=vals, tags=(tag,))

    def _on_reg_click(self, event):
        if self.full_tree.identify_region(event.x, event.y) != "cell": return
        col_idx = int(self.full_tree.identify_column(event.x).replace("#", "")) - 1
        iid     = self.full_tree.identify_row(event.y)
        if not iid: return
        if col_idx == 0: StudentProfileWindow(self, iid); return
        if col_idx >= len(self.full_days) + 1: return
        d   = self.full_days[col_idx - 1]
        cur = self.att.get(iid, {}).get(d)
        self.att.setdefault(iid, {})[d] = "P" if cur != "P" else "A"
        self._update_reg_row(iid)
        self._build_stat_cards()
        self.after_idle(lambda: flush_att(self.att))
        if d == self.today_str and self.stu_tree.exists(iid):
            ts    = self.att.get(iid, {}).get(self.today_str)
            today = "P" if ts == "P" else ("A" if ts == "A" else "–")
            pct   = att_pct(iid, self.att)
            vals  = list(self.stu_tree.item(iid, "values"))
            vals[5] = today; vals[6] = f"{pct}%"
            # Colour tags first so foreground is visible even if sel is present
            base_tags = [t for t in self.stu_tree.item(iid, "tags")
                         if t not in ("present", "absent")]
            colour_tags = []
            if ts == "P":   colour_tags.append("present")
            elif ts == "A": colour_tags.append("absent")
            # put colour first, then remaining (atrisk/sel)
            tags = colour_tags + [t for t in base_tags if t not in colour_tags]
            self.stu_tree.item(iid, values=vals, tags=tags)

    # ── Bulk operations ───────────────────────────────────────────
    def _bulk_mark(self, status):
        if not self.selected: return
        n = len(self.selected)
        for sid in self.selected:
            self.att.setdefault(sid, {})[self.today_str] = status
        self.after_idle(lambda: flush_att(self.att))
        for sid in list(self.selected):
            if self.stu_tree.exists(sid):
                vals    = list(self.stu_tree.item(sid, "values"))
                vals[5] = "P" if status == "P" else "A"
                vals[6] = f"{att_pct(sid, self.att)}%"
                # Rebuild tags: colour tags first, no "sel" (we clear selection after)
                tags = []
                tags.append("present" if status == "P" else "absent")
                if att_pct(sid, self.att) < 75: tags.append("atrisk")
                vals[0] = "☐"
                self.stu_tree.item(sid, values=vals, tags=tags)
            self._update_reg_row(sid)
        self.selected.clear()
        self.sel_lbl.config(text="")
        if hasattr(self, "_sel_all_btn"):
            self._sel_all_btn.config(text="☐ Select All", fg=TEXT2)
        self._build_stat_cards()
        self._toast(f"Marked {n} student(s) as {'Present' if status == 'P' else 'Absent'}")

    def _bulk_remove(self):
        if not self.selected: return
        n     = len(self.selected)
        names = [s[1] for s in self.students if s[0] in self.selected]
        prev  = "\n".join(f"  • {nm}" for nm in names[:6])
        if len(names) > 6: prev += f"\n  …and {len(names) - 6} more"
        if not messagebox.askyesno("Confirm Remove", f"Permanently remove {n} student(s)?\n\n{prev}"): return
        self.students = [s for s in self.students if s[0] not in self.selected]
        for sid in self.selected: self.att.pop(sid, None)
        save_students(self.students); flush_att(self.att)
        self.selected.clear(); self.sel_lbl.config(text="")
        self._toast(f"Removed {n} student(s) 🗑")
        self.refresh_all()

    # ── Add / Edit / Delete ───────────────────────────────────────
    def _clear_all_data(self):
        if not messagebox.askyesno("Clear All Data",
                "This will permanently delete ALL students and attendance records.\n\n"
                "The students.csv and attendance.csv files will be wiped.\n\n"
                "Are you absolutely sure?", icon="warning"): return
        self.students = []; self.att = {}; self.selected.clear()
        save_students(self.students); flush_att(self.att)
        self.reg_class_var.set(""); self.reg_section_var.set("")
        self.reg_section_cb.configure(values=[], state="disabled")
        self._toast("All data cleared 🗑")
        self.refresh_all()

    def _add_student(self):
        def on_save(_, name, roll, cls, section, gender):
            sid = next_id(self.students)
            self.students.append((sid, name, roll, cls, section, gender))
            self.att.setdefault(sid, {})
            save_students(self.students)
            if cls in self.extra_classes:
                self.extra_classes[cls].discard(section)
                if not self.extra_classes[cls]: del self.extra_classes[cls]
            self._post_student_change(cls, section)
            self._toast(f"Added  {name}")
        StudentDialog(self, on_save=on_save)

    def _edit_student(self, sid):
        student = next((s for s in self.students if s[0] == sid), None)
        if not student: return
        def on_save(_, name, roll, cls, section, gender):
            idx = next((i for i, s in enumerate(self.students) if s[0] == sid), None)
            if idx is None: return
            self.students[idx] = (sid, name, roll, cls, section, gender)
            save_students(self.students)
            self._post_student_change(cls, section)
            self._toast(f"Updated  {name}")
        StudentDialog(self, on_save=on_save, existing=student)

    def _post_student_change(self, cls, section):
        all_classes = get_classes(self.students, self.extra_classes)
        secs = get_sections_for_class(self.students, cls, self.extra_classes)
        self.filter_cls.set(cls); self.filter_sec.set(section)
        self.reg_class_var.set(cls); self.reg_section_var.set(section)
        self.list_cls_cb.configure(values=["All"] + all_classes)
        self.list_sec_cb.configure(values=["All"] + secs)
        self.reg_class_cb.configure(values=all_classes)
        self.reg_section_cb.configure(values=secs, state="readonly" if secs else "disabled")
        self._do_full_refresh_keeping_selection(cls, section)

    def _delete_one(self, sid, name):
        if not messagebox.askyesno("Confirm", f"Remove  {name}?\nCannot be undone."): return
        self.students = [s for s in self.students if s[0] != sid]
        self.att.pop(sid, None); self.selected.discard(sid)
        save_students(self.students); flush_att(self.att)
        self._toast(f"Removed  {name}  🗑")
        self.refresh_all()

    def _add_class_section(self): AddClassSectionDialog(self)

    def _on_class_section_created(self, cls, sec):
        self.extra_classes.setdefault(cls, set()).add(sec)
        all_classes = get_classes(self.students, self.extra_classes)
        secs = get_sections_for_class(self.students, cls, self.extra_classes)
        self.reg_class_var.set(cls); self.reg_section_var.set(sec)
        self.reg_class_cb.configure(values=all_classes)
        self.reg_section_cb.configure(values=secs, state="readonly")
        self.filter_cls.set(cls); self.filter_sec.set("All")
        self.list_cls_cb.configure(values=["All"] + all_classes)
        self.list_sec_cb.configure(values=["All"] + secs)
        self._toast(f"Class {cls} · Section {sec} ready.")
        if hasattr(self, "_stat_val_labels"): del self._stat_val_labels
        for w in self.stats_frame.winfo_children(): w.destroy()
        self._update_reg_days()
        self._build_stat_cards(); self._do_refresh_list(); self._refresh_full_reg()

    def _import_csv(self):  ImportCSVDialog(self)
    def _save_all(self):
        save_students(self.students); flush_att(self.att)
        self._toast("All changes saved 💾")

    def _export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv",
                                            filetypes=[("CSV", "*.csv")],
                                            title="Export Attendance Report")
        if not path: return
        self._write_export(path, self.students, self.full_days)
        self._toast(f"Exported → {os.path.basename(path)}")

    def _export_by_class_section(self):
        groups = {}
        for s in self.students: groups.setdefault((s[3], s[4]), []).append(s)
        if not groups: messagebox.showinfo("No Data", "No students to export."); return
        folder = filedialog.askdirectory(title="Select folder to save per-class CSVs")
        if not folder: return
        count = 0
        def _safe(x): return x.replace("/", "_").replace("\\", "_")
        for (cls, sec), stu_list in sorted(groups.items()):
            filepath = os.path.join(folder, f"Class_{_safe(cls)}_Section_{_safe(sec)}.csv")
            self._write_export(filepath, stu_list, self.full_days)
            count += 1
        self._toast(f"Exported {count} file(s) → {os.path.basename(folder)}")

    def _write_export(self, path, students, days):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID", "Name", "Roll", "Class", "Section", "Gender"] + days + ["Att%"])
            for s in students:
                sid, name, roll, cls, sec, gen = s
                row = [sid, name, roll, cls, sec, gen]
                for d in days: row.append(self.att.get(sid, {}).get(d, ""))
                row.append(f"{att_pct(sid, self.att, days)}%")
                w.writerow(row)

    # ── Refresh ───────────────────────────────────────────────────
    def _do_full_refresh_keeping_selection(self, cls, section):
        if hasattr(self, "_stat_val_labels"): del self._stat_val_labels
        for w in self.stats_frame.winfo_children(): w.destroy()
        self._update_reg_days()
        self.reg_class_var.set(cls); self.reg_section_var.set(section)
        self.filter_cls.set(cls);    self.filter_sec.set(section)
        self._build_stat_cards(); self._do_refresh_list(); self._refresh_full_reg()

    def refresh_all(self):
        if hasattr(self, "_stat_val_labels"): del self._stat_val_labels
        for w in self.stats_frame.winfo_children(): w.destroy()
        self._sync_reg_dropdowns(); self._update_reg_days()
        self._set_default_register()
        self._build_stat_cards(); self._do_refresh_list(); self._refresh_full_reg()

    # ── Toast notification ────────────────────────────────────────
    def _toast(self, msg):
        t = tk.Toplevel(self)
        t.overrideredirect(True); t.configure(bg="#ffffff")
        t.attributes("-topmost", True)
        tk.Frame(t, bg=NAVY, height=3).pack(fill="x")
        tk.Label(t, text=f"  {msg}  ", font=(FONT_MAIN, 10, "bold"),
                 bg=SURFACE, fg=TEXT, pady=10, padx=14).pack()
        self.update_idletasks()
        x = self.winfo_x() + self.winfo_width() - 360
        y = self.winfo_y() + self.winfo_height() - 90
        t.geometry(f"+{x}+{y}")
        t.after(2800, t.destroy)


# ══ ENTRY POINT ═══════════════════════════════════════════════════
if __name__ == "__main__":
    app = AttendIQ()
    app.mainloop()
