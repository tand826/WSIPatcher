from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog
import wsiprocess as wp


class Application(ttk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.set_window()
        self.set_types()
        self.set_default_params()
        self.labels = {}
        self.grid(column=0, row=0)
        self.create_widgets()
        self.selected_files

    def create_widgets(self):
        self.wsi_select = ttk.Button(
            self,
            text="Open File",
            command=self.select_wsis
        ).grid(column=0, row=0)

        self.selected_files_list = []
        self.selected_files = tk.Listbox(
            self,
            selectmode="single"
        )
        self.selected_files.bind(
            '<ButtonRelease-1>', self.show_thumb_when_selected)
        self.selected_files.grid(column=0, row=1, rowspan=11, sticky=tk.N+tk.S)

        self.add_combobox(
            "method", ["none", "classification", "detection", "segmentation"], col=1, row=0)
        self.add_dialog_box("where to save", self.select_one_directory, col=1, row=1)
        self.add_dialog_box("annotation file", self.select_one_file, col=1, row=2)
        self.add_dialog_box("inclusion file", self.select_one_file, col=1, row=3)
        self.add_param_box("patch width", col=1, row=4)
        self.add_param_box("patch height", col=1, row=5)
        self.add_param_box("overlap width", col=1, row=6)
        self.add_param_box("overlap height", col=1, row=7)
        self.add_param_box("ratio of foreground", col=1, row=8)
        self.add_param_box("ratio of annotation", col=1, row=9)
        self.add_combobox("magnification", ["40", "20", "10"], col=1, row=10)
        self.add_run_button(col=1, row=11)
        self.add_status_bar(col=0, row=12)

    def add_dialog_box(self, param_name, callback, col, row):
        self.labels[param_name] = ttk.Label(
            self,
            textvariable=self.params[param_name]
        )
        self.labels[param_name].grid(column=col+1, row=row)
        ttk.Button(
            self,
            text="{}".format(param_name),
            command=lambda: callback(param_name)
        ).grid(column=col, row=row)

    def select_wsis(self):
        files = filedialog.askopenfilenames(
            initialdir=Path.home(),
            filetypes=self.types
        )
        for file in files:
            if file not in self.selected_files_list:
                self.selected_files_list.append(file)
                self.selected_files.insert("end", Path(file).name)

        self.params["status"].set("Selected {} files".format(len(files)))

    def select_one_file(self, param_name):
        selected = filedialog.askopenfilename(
            initialdir=Path.home(),
        )
        self.params[param_name].set(selected)
        self.params["status"].set("Selected {}".format(selected))
        return selected

    def select_one_directory(self, param_name):
        selected = filedialog.askdirectory(
            initialdir=Path.home(),
        )
        self.params[param_name].set(selected)
        self.params["status"].set("Selected {}".format(selected))
        return selected

    def add_param_box(self, param_name, col, row):
        ttk.Label(
            self,
            text=param_name,
            justify=tk.RIGHT
        ).grid(column=col, row=row)
        ttk.Entry(
            self,
            textvariable=self.params[param_name]
        ).grid(column=col+1, row=row)

    def add_combobox(self, param_name, dropdowns, col, row):
        ttk.Label(
            self,
            text=param_name
        ).grid(column=col, row=row)
        box = ttk.Combobox(
            self,
            state='readonly',
            values=dropdowns,
        )
        box.current(0)
        box.grid(column=col+1, row=row)

    def add_status_bar(self, col, row):
        ttk.Label(
            self,
            textvariable=self.params["status"],
            anchor="w"
        ).grid(column=col, row=row, rowspan=3)

    def add_run_button(self, col, row):
        ttk.Button(
            self,
            text="Run",
            command=self.run_process
        ).grid(column=col, row=row, columnspan=2)

    def run_process(self):
        wsiidx = self.selected_files.curselection()[0]
        self.params["wsi"] = self.selected_files_list[wsiidx]
        slide = wp.slide(self.params["wsi"])
        if self.params["inclusion file"].get():
            inclusion = wp.inclusion(self.params["inclusion file"].get())
        else:
            inclusion = False
        if self.params["annotation file"].get():
            annotation = wp.annotation(self.params["annotation file"].get())
            annotation.make_masks(slide, inclusion, foreground=True)
            annotation.classes.remove("foreground")
            classes = annotation.classes
        else:
            annotation = False
            classes = None
        patcher = wp.patcher(
            slide,
            self.params["method"].get(),
            annotation=annotation,
            save_to=self.params["where to save"].get(),
            patch_width=self.params["patch width"].get(),
            patch_height=self.params["patch height"].get(),
            overlap_width=self.params["overlap width"].get(),
            overlap_height=self.params["overlap height"].get(),
            on_foreground=self.params["ratio of foreground"].get(),
            on_annotation=self.params["ratio of annotation"].get(),
            start_sample=False,
            finished_sample=False,
            extract_patches=True)
        patcher.get_patch_parallel(classes)

    def show_thumb_when_selected(self, event):
        return  # no operation for now
        #idx = self.selected_files.curselection()[0]
        #filepath = self.selected_files_list[idx]
        #slide = wp.slide(filepath)
        #thumbname = "{}.png".format(Path(filepath).stem)
        #slide.get_thumbnail(256).pngsave(thumbname)
        #image = ImageTk.PhotoImage(file=thumbname)
        #self.thumbnail_label = ttk.Label(
        #    self.master,
        #    image=image
        #)
        #self.thumbnail_label.pack(side="top")

    def set_window(self):
        self.master.geometry("515x327")
        self.master.title("WSI Patcher")
        self.master.configure(bg="white")
        # self.selected_files_scrollbar = tk.Scrollbar(self)
        # self.selected_files_scrollbar.pack(fill="y")

    def set_types(self):
        self.types = [
            ("Aperio", "*.svs"),
            ("Hamamatsu", "*.vms"),
            ("Hamamatsu", "*.vmu"),
            ("Hamamatsu", "*.ndpi"),
            ("Leica", "*.scn"),
            ("MIRAX", "*.mrxs"),
            ("Philips", "*.tiff"),
            ("Sakura", "*.svslide"),
            ("Trestle", "*.tif"),
            ("Ventana", "*.bif"),
            ("Ventana", "*.tif"),
            ("Generic tiled Tiff", "*.tif"),
            ("Generic tiled Tiff", "*.tiff")
        ]

    def set_default_params(self):
        self.params = {
            "wsi": tk.StringVar(value=""),
            "method": tk.StringVar(value="none"),
            "where to save": tk.StringVar(value=Path.home().resolve()),
            "annotation file": tk.StringVar(value=""),
            "inclusion file": tk.StringVar(value=""),
            "patch width": tk.IntVar(value=256),
            "patch height": tk.IntVar(value=256),
            "overlap width": tk.IntVar(value=1),
            "overlap height": tk.IntVar(value=1),
            "ratio of foreground": tk.DoubleVar(value=0.5),
            "ratio of annotation": tk.DoubleVar(value=0.5),
            "magnification": tk.IntVar(value=20),
            "status": tk.StringVar(value="")
        }

    def change_name(self, filename):
        title = f"WSI Patcher | {filename}"
        self.master.title(title)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
