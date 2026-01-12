import customtkinter as ctk
from tkinter import StringVar, messagebox
from datetime import datetime

# -------------------------
# 模拟数据
# -------------------------
ALL_PROJECTS = [
    "risk-control-core",
    "risk-control-model",
    "payment-gateway",
    "user-center",
    "order-service",
    "account-service",
    "data-platform",
    "anti-fraud-engine",
    "report-service",
    "gateway-service",
]

REVIEWERS = [
    "张三", "李四", "王五", "赵六", "架构师-A", "负责人-B"
]


class BranchToolApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("Git 分支管理工具")
        self.geometry("1000x650")

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._init_layout()
        self._init_sidebar()
        self._init_content()

    # -------------------------
    # 布局
    # -------------------------
    def _init_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    # -------------------------
    # 左侧菜单
    # -------------------------
    def _init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=180, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        ctk.CTkLabel(
            self.sidebar, text="功能菜单",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        ctk.CTkButton(
            self.sidebar, text="创建分支",
            command=self.show_create_branch_page
        ).grid(row=1, column=0, padx=20, pady=10)

        ctk.CTkButton(
            self.sidebar, text="合并分支",
            command=self.show_merge_branch_page
        ).grid(row=2, column=0, padx=20, pady=10)

    # -------------------------
    # 内容区
    # -------------------------
    def _init_content(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        self.content_frame.grid_rowconfigure(0, weight=3)
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.page_frame = ctk.CTkFrame(self.content_frame)
        self.page_frame.grid(row=0, column=0, sticky="nsew")

        self._init_console()
        self.show_create_branch_page()

    # -------------------------
    # 控制台（含清除按钮）
    # -------------------------
    def _init_console(self):
        console_frame = ctk.CTkFrame(self.content_frame)
        console_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        header = ctk.CTkFrame(console_frame)
        header.pack(fill="x", padx=10, pady=(5, 0))

        ctk.CTkLabel(
            header, text="运行控制台",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        ctk.CTkButton(
            header, text="清除",
            width=60,
            command=self.clear_console
        ).pack(side="right")

        self.console = ctk.CTkTextbox(
            console_frame, height=120, state="disabled"
        )
        self.console.pack(fill="both", expand=True, padx=10, pady=5)

    # -------------------------
    # 日志方法
    # -------------------------
    def log(self, msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console.configure(state="normal")
        self.console.insert("end", f"[{timestamp}] {msg}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def clear_console(self):
        self.console.configure(state="normal")
        self.console.delete("1.0", "end")
        self.console.configure(state="disabled")
        self.log("控制台日志已清空")

    def clear_page(self):
        for w in self.page_frame.winfo_children():
            w.destroy()

    # =====================================================
    # 创建分支页面
    # =====================================================
    def show_create_branch_page(self):
        self.clear_page()
        self.log("切换到【创建分支】页面")

        frame = ctk.CTkFrame(self.page_frame)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            frame, text="创建分支",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        project_var = StringVar()
        search_var = StringVar()

        ctk.CTkEntry(
            frame, textvariable=search_var,
            placeholder_text="搜索项目"
        ).pack(fill="x")

        list_frame = ctk.CTkScrollableFrame(frame, height=120)
        list_frame.pack(fill="x", pady=10)

        radios = []

        def refresh():
            for r in radios:
                r.destroy()
            radios.clear()

            key = search_var.get().lower()
            for p in ALL_PROJECTS:
                if key in p.lower():
                    rb = ctk.CTkRadioButton(
                        list_frame, text=p,
                        variable=project_var, value=p
                    )
                    rb.pack(anchor="w", padx=10)
                    radios.append(rb)

        search_var.trace_add("write", lambda *_: refresh())
        refresh()

        branch_entry = ctk.CTkEntry(
            frame, placeholder_text="分支名（如 feature/login）"
        )
        branch_entry.pack(fill="x", pady=10)

        def confirm():
            if not project_var.get() or not branch_entry.get():
                messagebox.showerror("错误", "请填写完整信息")
                return

            self.log(f"开始创建分支：{project_var.get()} -> {branch_entry.get()}")
            self.log("分支创建成功（模拟）")
            messagebox.showinfo("成功", "分支创建成功")

        ctk.CTkButton(frame, text="确认创建", command=confirm).pack(anchor="e")

    # =====================================================
    # 合并分支页面
    # =====================================================
    def show_merge_branch_page(self):
        self.clear_page()
        self.log("切换到【合并分支】页面")

        frame = ctk.CTkFrame(self.page_frame)
        frame.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            frame, text="合并分支",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(anchor="w", pady=(0, 20))

        search_var = StringVar()
        ctk.CTkEntry(
            frame, textvariable=search_var,
            placeholder_text="搜索项目（可多选）"
        ).pack(fill="x")

        project_frame = ctk.CTkScrollableFrame(frame, height=120)
        project_frame.pack(fill="x", pady=10)

        project_vars = {}

        def refresh_projects():
            for w in project_frame.winfo_children():
                w.destroy()
            project_vars.clear()

            key = search_var.get().lower()
            for p in ALL_PROJECTS:
                if key in p.lower():
                    var = ctk.BooleanVar()
                    ctk.CTkCheckBox(project_frame, text=p, variable=var).pack(anchor="w", padx=10)
                    project_vars[p] = var

        search_var.trace_add("write", lambda *_: refresh_projects())
        refresh_projects()

        src_branch = ctk.CTkEntry(frame, placeholder_text="源分支")
        src_branch.pack(fill="x", pady=5)

        tgt_branch = ctk.CTkEntry(frame, placeholder_text="目标分支")
        tgt_branch.pack(fill="x", pady=5)

        ctk.CTkLabel(frame, text="代码审查人员").pack(anchor="w", pady=(10, 5))
        reviewer_frame = ctk.CTkFrame(frame)
        reviewer_frame.pack(fill="x")

        reviewer_vars = {}
        for r in REVIEWERS:
            var = ctk.BooleanVar()
            ctk.CTkCheckBox(reviewer_frame, text=r, variable=var).pack(side="left", padx=10)
            reviewer_vars[r] = var

        def confirm_merge():
            projects = [p for p, v in project_vars.items() if v.get()]
            if not projects or not src_branch.get() or not tgt_branch.get():
                messagebox.showerror("错误", "请填写完整信息")
                return

            self.log(f"提交合并请求：{projects}")
            self.log(f"{src_branch.get()} -> {tgt_branch.get()}")
            self.log("Merge Request 创建成功（模拟）")
            messagebox.showinfo("成功", "合并请求已提交")

        ctk.CTkButton(frame, text="确认合并", command=confirm_merge).pack(anchor="e", pady=10)


if __name__ == "__main__":
    app = BranchToolApp()
    app.mainloop()
