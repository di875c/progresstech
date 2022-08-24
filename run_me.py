import tkinter as tk
import tkinter.messagebox as mb
import tkinter.filedialog as fd
import cbeam_create, os

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.filename = None
        self.message_entry = tk.Entry(textvariable='new file index')
        self.message_entry.pack(padx=60, pady=10)
        self.pshell_check = tk.IntVar()
        self.thick_including = tk.Checkbutton(text='Take into account PSHELL thickness?', variable=self.pshell_check)
        self.thick_including.pack(padx=60, pady=10)
        self.btn_file = tk.Button(self, text="Choose file",
                             command=self.choose_file)
        self.btn_file.pack(padx=60, pady=10)
        self.btn_start = tk.Button(self, text='Start', command=self.start)
        self.btn_start.pack(padx=60, pady=10)

    def choose_file(self):
        filetypes = (("bulk файл", "*.dat *.bdf *.blk"),
                     ("Текстовый файл", "*.txt"),
                     ("Любой", "*"))
        filename = fd.askopenfilename(title="Choose fule", initialdir="/",
                                      filetypes=filetypes)
        if filename: self.filename = filename

    def start(self):
        if self.message_entry.get() and self.filename:
            index = self.filename.find('.')
            new_file_name = self.filename[:index] + self.message_entry.get() + self.filename[index:]
            print(self.filename, new_file_name, self.pshell_check.get())
            cbeam_create.nc_generate(self.filename, new_file_name, self.pshell_check.get())
        else: mb.showwarning('Warning', 'Не выбран файл или не указан индекс нового файла')


if __name__ == "__main__":
    app = App()
    app.mainloop()