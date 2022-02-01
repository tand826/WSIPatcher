from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog

from PIL import ImageTk
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
        self.selected_files.grid(
            column=0, row=1, rowspan=6, sticky=tk.NS, padx=3)

        self.add_combobox(
            "method",
            ["evaluation", "classification", "detection", "segmentation"],
            col=0, row=7)
        self.add_dialog_box(
            "where to save",
            self.select_one_directory, col=0, row=8)
        self.add_dialog_box(
            "annotation file",
            self.select_one_file, col=0, row=9)
        self.add_dialog_box(
            "rule file",
            self.select_one_file, col=0, row=10)
        self.add_param_box("patch width", col=0, row=11)
        self.add_param_box("patch height", col=0, row=12)
        self.add_param_box("overlap width", col=0, row=13)
        self.add_param_box("overlap height", col=0, row=14)
        self.add_param_box("ratio of foreground", col=0, row=15)
        self.add_param_box("ratio of annotation", col=0, row=16)
        self.add_combobox("magnification", ["40", "20", "10"], col=0, row=17)
        self.add_checkbox("convert to", "VOC", col=0, row=18)
        self.add_checkbox("convert to", "COCO", col=0, row=19)
        self.add_run_button(col=0, row=20)
        self.add_canvas(width=256, height=256, col=1, row=0)
        self.add_status_bar(col=0, row=21)

    def add_dialog_box(self, param_name, callback, col, row):
        self.labels[param_name] = ttk.Entry(
            self,
            textvariable=self.params[param_name]
        )
        self.labels[param_name].grid(
            column=col+1, row=row, sticky=tk.E+tk.W)

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
        ).grid(column=col+1, row=row, sticky=tk.E+tk.W)

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

    def add_checkbox(self, param_name, param, col, row):
        ttk.Label(
            self,
            text=param_name
        ).grid(column=col, row=row)
        ttk.Checkbutton(
            self,
            text=param,
            variable=self.params[f"{param_name} {param}"]
        ).grid(column=col+1, row=row)

    def add_status_bar(self, col, row):
        style = ttk.Style()
        style.configure("Statusbar.TEntry",
                        background="#ECECEC", bordercolor="#ECECEC")
        ttk.Entry(
            self,
            textvariable=self.params["status"],
            justify="left",
            style="Statusbar.TEntry"
        ).grid(column=col, row=row, columnspan=2, sticky=tk.E+tk.W)

    def add_canvas(self, width, height, col, row):
        self.thumb_canvas = tk.Canvas(
            self,
            width=width,
            height=height,
            bg="#ECECEC"
        )
        self.thumb_canvas.grid(column=col, row=row, padx=3, rowspan=7)

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
        if self.params["rule file"].get():
            rule = wp.rule(self.params["rule file"].get())
        else:
            rule = False
        if self.params["annotation file"].get():
            annotation = wp.annotation(self.params["annotation file"].get())
            annotation.make_masks(slide, rule, foreground=True)
            annotation.classes.remove("foreground")
            classes = annotation.classes
        else:
            annotation = wp.annotation("")
            annotation.make_masks(slide, foreground=True)
            classes = annotation.classes
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
            finished_sample=False)
        patcher.get_patch_parallel(classes)
        if self.params["convert to voc"].get() or self.params["convert to coco"].get():
            converter = wp.converter(
                self.params["where to save"].get() + "/" + slide.filestem,
                self.params["where to save"].get(),
                "8:1:1")
            if self.params["convert to voc"].get():
                converter.to_voc()
            if self.params["convert to coco"].get():
                converter.to_coco()

    def show_thumb_when_selected(self, event):
        idx = self.selected_files.curselection()[0]
        filepath = self.selected_files_list[idx]
        slide = wp.slide(filepath)
        slide.export_thumbnail(save_as=f"{slide.filestem}.jpg", size=256)
        self.thumb = ImageTk.PhotoImage(file="thumb.png")
        x = (256-self.thumb.width())/2
        y = (256-self.thumb.height())/2
        self.thumb_canvas.create_image(
            x, y, image=self.thumb, anchor=tk.NW
        )

    def set_window(self):
        self.master.geometry("456x645")
        self.master.title("WSI Patcher")
        self.master.configure(bg="#ECECEC")

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
            "method": tk.StringVar(value="evaluation"),
            "where to save": tk.StringVar(value=Path.home().resolve()),
            "annotation file": tk.StringVar(value=""),
            "rule file": tk.StringVar(value=""),
            "patch width": tk.IntVar(value=256),
            "patch height": tk.IntVar(value=256),
            "overlap width": tk.IntVar(value=1),
            "overlap height": tk.IntVar(value=1),
            "ratio of foreground": tk.DoubleVar(value=0.5),
            "ratio of annotation": tk.DoubleVar(value=0.5),
            "convert to VOC": tk.BooleanVar(),
            "convert to COCO": tk.BooleanVar(),
            "magnification": tk.IntVar(value=20),
            "status": tk.StringVar(value="")
        }

    def change_name(self, filename):
        title = f"WSI Patcher ver 0.2 | {filename} "
        self.master.title(title)


if __name__ == "__main__":
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()
