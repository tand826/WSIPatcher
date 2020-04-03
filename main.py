from pathlib import Path
from PIL import ImageTk
import tkinter as tk
from tkinter import ttk, filedialog
import wsiprocess as wp


class Application(tk.Frame):

    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.set_window()
        self.set_types()
        self.set_default_params()
        self.pack()
        self.create_widgets()
        self.selected_files

    def create_widgets(self):
        self.wsi_select = ttk.Button(
            self,
            text="Open File",
            command=self.select_wsis
        )
        self.wsi_select.pack(side="top")

        self.selected_files_list = []
        self.selected_files = tk.Listbox(
            self,
            selectmode="single"
        )
        self.selected_files.bind(
            '<ButtonRelease-1>', self.show_thumb_when_selected)
        self.selected_files.pack(side="top")

        self.add_combobox(
            "method", ["none", "classification", "detection", "segmentation"])
        self.add_dialog_box("where to save", self.select_one_directory)
        self.add_dialog_box("annotation file", self.select_one_file)
        self.add_dialog_box("inclusion file", self.select_one_file)
        self.add_param_box("patch width")
        self.add_param_box("patch height")
        self.add_param_box("overlap width")
        self.add_param_box("overlap height")
        self.add_param_box("ratio of foreground")
        self.add_param_box("ratio of annotation")
        self.add_param_box("magnification")
        self.add_run_button()

    def add_dialog_box(self, param_name, callback):
        ttk.Button(
            self,
            text="Select {}".format(param_name),
            command=lambda: callback(param_name)
        ).pack(side="top")
        ttk.Label(
            self,
            text=self.params[param_name]
        ).pack()

    def select_wsis(self):
        files = filedialog.askopenfilenames(
            initialdir=Path.home(),
            filetypes=self.types
        )
        for file in files:
            if file not in self.selected_files_list:
                self.selected_files_list.append(file)
                self.selected_files.insert("end", Path(file).name)

    def select_one_file(self, param_name):
        selected = filedialog.askopenfilename(
            initialdir=Path.home(),
        )
        self.params[param_name].set(selected)
        return selected

    def select_one_directory(self, param_name):
        selected = filedialog.askdirectory(
            initialdir=Path.home(),
        )
        self.params[param_name].set(selected)
        return selected

    def add_param_box(self, param_name):
        ttk.Label(
            self,
            text=param_name
        ).pack()
        ttk.Entry(
            self,
            textvariable=self.params[param_name]
        ).pack()

    def add_combobox(self, param_name, dropdowns):
        box = ttk.Combobox(
            self,
            state='readonly',
            values=dropdowns,
        )
        box.current(0)
        box.pack()

    def add_run_button(self):
        ttk.Button(
            self,
            text="Run",
            command=self.run_process
        ).pack()

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
        idx = self.selected_files.curselection()[0]
        filepath = self.selected_files_list[idx]
        slide = wp.slide(filepath)
        thumbname = "{}.png".format(Path(filepath).stem)
        slide.get_thumbnail(256).pngsave(thumbname)
        image = ImageTk.PhotoImage(file=thumbname)
        self.thumbnail_label = ttk.Label(
            self.master,
            image=image
        )
        self.thumbnail_label.pack(side="top")

    def set_window(self):
        self.master.geometry("500x800")
        self.master.title("WSI Patcher")
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
            "magnification": tk.IntVar(value=20)
        }

    def change_name(self, filename):
        title = f"WSI Patcher | {filename}"
        self.master.title(title)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
