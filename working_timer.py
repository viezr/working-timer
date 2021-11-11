#!/usr/bin/env python3
'''
Projects working timer
'''
import time
from datetime import date
from os import path
import pickle
import tkinter as tk
from threading import Thread
from config import Config


class Timer(tk.Tk):
    '''
    App GUI class.
    '''
    def __init__(self):
        '''
        Main app init.
        '''
        self.wtitle = "Working timer"
        tk.Tk.__init__(self, className = self.wtitle)
        self.title(self.wtitle)

        self.main_bg = "#222"
        self.main_font = "roboto, 10"
        self.label_col = {"bg": "#222", "fg": "#b38600"}
        self.colors = {
            "green": {"bg": "#28a745", "fg": "#eee", "hover": "#1e7b34"},
            "yellow": {"bg": "#ffc107", "fg": "#222", "hover": "#b38600"},
            "grey": {"bg": "#6c757d", "fg": "#eee", "hover": "#474d52"},
            "red": {"bg": "#f8d7da", "fg": "#721c24", "hover": "#f5c6cb"},
            "but_hl": "#474d52"
        }
        self.configure(background = self.main_bg)

        self.projects = load_projects()
        self.cur_project = tk.StringVar() # current project
        self.choice_project = tk.StringVar() # choosen project from config frame
        self.new_project = tk.StringVar() # new project from config frame
        self.cur_date = date.today()
        self.stop_timer = False # trigger for running timer loop
        self.timer_thread = None
        self.config_hidden = True # Config frame state
        self.details_hidden = True # Details frame state
        self.del_confirmed = False # trigger for del buttons for double press

        # if default project from config filse exists in base,
        # set it to cur_project esle set first found project
        self.cur_project.set(self.get_default_project())
        # if current project has time in base for today,
        # insert time into timer_seconds else insert 0
        self.timer_seconds = self.get_cur_project_time()

        # Widgets
        project_label_text = "No project"
        if not self.cur_project.get().lower() == "none":
            project_label_text = self.cur_project.get()
        self.project_label = tk.Label(self, text = project_label_text,
            width = 18, padx = 0, pady = 0, bg = self.label_col["bg"],
            fg = self.label_col["fg"], font = self.main_font)
        self.project_label.grid(row = 0, column = 0)

        self.timer_button = tk.Button(self, text = "Start",
            command = self.run_timer, width = 6, padx = 0, pady = 0,
            font = self.main_font, state = "disabled")
        if self.cur_project.get():
            self.timer_button.configure(state = "active")
        self.timer_button.grid(row = 0, column = 1)
        self.set_btn_color(self.timer_button, "green")

        self.timer_label = tk.Label(self,
            text = format_time(self.timer_seconds), width = 10, padx = 0,
            pady = 0, bg = self.label_col["bg"], fg = self.label_col["fg"],
            font = self.main_font)
        self.timer_label.grid(row = 0, column = 2)

        self.config_button = tk.Button(self, text = "Cfg",
            command = self.config_frame, width = 4, padx = 0, pady = 0,
            font = self.main_font)
        self.config_button.grid(row = 0, column = 3)
        self.set_btn_color(self.config_button, "grey")

        self.quit_button = tk.Button(self, text = "Quit",
            command = self.quit_app, width = 6, padx = 0, pady = 0,
            font = self.main_font)
        self.quit_button.grid(row = 0, column = 4)
        self.set_btn_color(self.quit_button, "grey")

    def get_default_project(self) -> str:
        '''
        Return default project from config file
        if it's in the database.
        '''
        default = Config.DEFAULT_PROJECT
        if default in self.projects:
            return default
        elif self.projects:
            first = next(iter(self.projects))
            return first

    def get_cur_project_time(self) -> int:
        '''
        Return time for current project
        if it has today time in the database.
        '''
        prj = self.cur_project.get()
        if self.projects:
            for day, val in self.projects[prj].items():
                if day == self.cur_date:
                    return val
        return 0

    def set_btn_color(self, button, color) -> None:
        '''
        Button color setter.
        '''
        button.configure(
            bg = self.colors[color]["bg"],
            fg = self.colors[color]["fg"],
            activebackground = self.colors[color]["hover"],
            activeforeground = self.colors[color]["fg"],
            highlightbackground = self.colors["but_hl"]
        )

    def update_details(self) -> None:
        '''
        Update list of data in details frame
        '''
        if self.details_hidden:
            return
        prj = self.cur_project.get()
        self.listbox.delete(0, tk.END)
        # Fill listbox with project data
        for day, sec in self.projects[prj].items():
           self.listbox.insert("end", f"Day: {day} Sec: {sec} " +
                f"Time: {format_time(sec)}")
        # Set listbox to last position
        lines = len(self.projects[prj])
        self.listbox.yview_scroll(lines, 'units')

        if "time_label" in self.__dict__:
            time = sum([sec for day, sec in self.projects[prj].items()]) / 3600
            self.time_label.configure(
                text = "Project hours: {:.2f}".format(time))

    def details_frame(self) -> None:
        '''
        Show the frame with details about the project.
        '''
        def del_date() -> None:
            '''
            Delete selected date.
            '''
            self.clear_del_confirmed()
            sel = self.listbox.curselection()
            if sel:
                sel_date = self.listbox.get(sel[0]).split()[1]
                rem_date = date.fromisoformat(sel_date)
                self.projects[prj].pop(rem_date)
                # Update current seconds if removed today data
                self.timer_seconds = self.get_cur_project_time()
                self.timer_label.configure(
                    text = format_time(self.timer_seconds))
                self.update_details()

        self.clear_del_confirmed()
        if not self.details_hidden:
            self.det_frame.destroy()
            self.details_hidden = True
            self.set_btn_color(self.details_button, "yellow")
            return

        self.details_hidden = False
        self.set_btn_color(self.details_button, "green")
        self.det_frame = tk.Frame(self)
        self.det_frame.configure(background = self.main_bg)
        self.det_frame.grid(row = 2, column = 0, columnspan = 5)

        # Widgets
        self.listbox = tk.Listbox(self.det_frame, width = 36, height = 10)
        self.listbox.grid(row = 0, column = 0)
        yscroll = tk.Scrollbar(self.det_frame, command = self.listbox.yview,
            orient = tk.VERTICAL)
        yscroll.grid(row = 0, column = 1, sticky = "NS")
        self.listbox.configure(yscrollcommand = yscroll.set)
        # Fill listbox with project data
        self.update_details()

        prj = self.cur_project.get()
        time = sum([sec for day, sec in self.projects[prj].items()]) / 3600
        self.time_label = tk.Label(self.det_frame,
            text = "Project hours: {:.2f}".format(time), width = 24,
            padx = 0, pady = 0, bg = self.label_col["bg"],
            fg = self.label_col["fg"], font = self.main_font)
        self.time_label.grid(row = 1, column = 0, columnspan = 2, padx = 4, pady = 8)

        del_button = tk.Button(self.det_frame, text = "Delete selected",
            command = del_date, width = 16, padx = 0, pady = 0,
            font = self.main_font)
        del_button.grid(row = 2, column = 0, columnspan = 2, padx = 4, pady = 10)
        self.set_btn_color(del_button, "grey")

    def update_config_projects(self) -> None:
        '''
        Update project in config frame
        '''
        if self.config_hidden:
            return
        if self.prj_frame:
            self.prj_frame.destroy()

        self.prj_frame = tk.Frame(self.cfg_frame)
        self.prj_frame.grid(row = 1, column = 0)
        self.prj_frame.configure(background = self.main_bg)
        self.radio_buttons = {}
        self.del_buttons = {}
        self.prj_frame.grid_columnconfigure(1, minsize = 20)


        # Widgets
        default = self.cur_project.get() # to swith radio to current project
        for idx, key in enumerate(self.projects):
            radio = tk.Radiobutton(self.prj_frame, text = key,
                variable = self.choice_project,
                command = self.cfg_switch_project,
                value = key, borderwidth = 0, relief = "flat",
                padx = 0, pady = 0, highlightthickness = 0,
                bg = self.main_bg, fg = self.label_col["fg"],
                highlightbackground = self.colors["but_hl"],
                activebackground = self.colors["yellow"]["hover"],
                activeforeground = self.colors["yellow"]["fg"],
                font = self.main_font)
            radio.grid(row = idx, column = 0, sticky = "W")
            self.radio_buttons[key] = radio
            if key == default:
                radio.invoke() # swith radio to current project

            del_button = tk.Button(self.prj_frame, text = "Del",
                command = self.cfg_del_project(key), width = 4,
                    padx = 0, pady = 0, font = self.main_font)
            del_button.grid(row = idx, column = 2, sticky = "E")
            self.set_btn_color(del_button, "grey")
            self.del_buttons[key] = del_button

    def config_frame(self) -> None:
        '''
        Show config frame.
        '''
        if not self.config_hidden:
            self.cfg_frame.destroy()
            self.clear_del_confirmed()
            self.config_hidden = True
            self.set_btn_color(self.config_button, "grey")
            if not self.details_hidden:
                self.details_hidden = True
            return
        self.config_hidden = False
        self.prj_frame = None
        self.set_btn_color(self.config_button, "green")

        self.cfg_frame = tk.Frame(self)
        self.cfg_frame.configure(background = self.main_bg)
        self.cfg_frame.grid(row = 1, column = 0, columnspan = 5)

        # Projects frame
        self.update_config_projects()

        # Widgets
        config_label = tk.Label(self.cfg_frame, text = "Projects", width = 10,
            padx = 0, pady = 0, bg = self.label_col["bg"], fg = "#fff",
            font = "roboto, 12")
        config_label.grid(row = 0, column = 0, pady = 4)

        new_entry = tk.Entry(self.cfg_frame, textvariable = self.new_project,
            bg = self.label_col["fg"], fg = self.label_col["bg"], width = 26,
            font = self.main_font)
        self.new_project.set("New project")
        new_entry.grid(row = 2, column = 0, pady = 8,
            sticky = "W")

        add_button = tk.Button(self.cfg_frame, text = "Add",
            command = self.cfg_add_project, width = 4, padx = 0, pady = 0,
            font = self.main_font)
        add_button.grid(row = 2, column = 0, sticky = "E")
        self.set_btn_color(add_button, "yellow")

        self.details_button = tk.Button(self.cfg_frame, text = "Details",
            command = self.details_frame, width = 8, padx = 0, pady = 0,
            font = self.main_font)
        self.details_button.grid(row = 3, column = 0,
            pady = 14, sticky = "NW")
        self.set_btn_color(self.details_button, "yellow")

        export_button = tk.Button(self.cfg_frame, text = "Export",
            command = self.export_projects, width = 8, padx = 0, pady = 0,
            font = self.main_font)
        export_button.grid(row = 3, column = 0,
            pady = 14, sticky = "NE")
        self.set_btn_color(export_button, "yellow")

    def clear_del_confirmed(self) -> None:
        '''
        Clear state of delete confirmation and reset buttons color
        '''
        if self.del_confirmed:
            self.del_confirmed = False
            for bkey, button in self.del_buttons.items():
                self.set_btn_color(button, "grey")
                button.configure(state = "active")

    def switch_project(self, project: str) -> None:
        '''
        Switch current project. Called from config frame functions
        '''
        # Save time for current project
        cur_prj = self.cur_project.get()
        sec = self.timer_seconds
        if not cur_prj.lower() == "none" and sec > 0:
            self.projects[cur_prj][self.cur_date] = sec
        save_projects(self.projects)
        # Set timer's settings for another project
        self.cur_project.set(project)
        self.project_label.configure(text = project)
        self.timer_seconds = self.get_cur_project_time()
        self.timer_label.configure(text = format_time(self.timer_seconds))
        self.clear_del_confirmed()
        self.update_details()

    def cfg_switch_project(self) -> None:
        '''
        Switch current project in config frame
        '''
        project = self.choice_project.get()
        if project == self.cur_project.get():
            return
        self.switch_project(project)

    def cfg_add_project(self) -> None:
        '''
        Add new project from config frame.
        Switch current project to new.
        '''
        new_prj = self.new_project.get()
        self.projects[new_prj] = {}
        # Set timer's settings for new project
        self.switch_project(new_prj)
        self.update_config_projects()

    def cfg_del_project(self, project: str):
        '''
        Return function with particular project
        for each delete button command.
        '''
        def wrapper() -> None:
            '''
            Delete project from config frame.
            Switch current project to first found in database.
            '''
            if self.del_confirmed:
                self.projects.pop(project)
                # Set timer's settings for other project
                self.switch_project(next(iter(self.projects)))
                self.update_config_projects()
            else:
                for bkey, button in self.del_buttons.items():
                    if bkey == project:
                        self.set_btn_color(button, "red")
                    else:
                        button.configure(state = "disabled")
                self.del_confirmed = True
        return wrapper

    def run_timer(self) -> None:
        '''
        Start threads to run or stop the timer.
        '''
        self.clear_del_confirmed()
        if self.timer_thread:
            Thread(target = stop_timer_thread, args = (self,)).start()
            return
        self.timer_thread = Thread(target = run_timer_thread, args = (self,))
        self.timer_thread.start()

    def export_projects(self) -> None:
        '''
        Export all projects to a text file with simple format:
        "project name",date,seconds.
        '''
        self.clear_del_confirmed()
        with open(Config.EXPORT_FILE, "w") as f:
            data = ""
            for key in app.projects:
                for item in self.projects[key].items():
                    date_, sec = item
                    data += f"{key},{date_},{sec}\n"
            f.write(data)

    def quit_app(self) -> None:
        '''
        Quit the app and save the database.
        If timer is running, start daemon thread to stop the timer.
        Thread daemon option set for forcing it to shutdown
        then the app is closing.
        '''
        cur_prj = self.cur_project.get()
        sec = self.timer_seconds
        if not cur_prj.lower() == "none" and sec > 0:
            self.projects[cur_prj][self.cur_date] = sec
        save_projects(self.projects)
        # Stop timer thread and close app.
        if self.timer_thread:
            Thread(target = stop_timer_thread, args = (self, True), daemon = True).start()
        else:
            self.destroy()

def run_timer_thread(app) -> None:
    '''
    Start timer as thread.
    '''
    app.stop_timer = False
    app.timer_button.configure(text = "Pause"),
    app.set_btn_color(app.timer_button, "yellow")

    while not app.stop_timer:
        app.timer_label.configure(text = format_time(app.timer_seconds))
        time.sleep(1)
        app.timer_seconds += 1
    app.stop_timer = False
    app.timer_thread = None
    app.timer_button.configure(text = "Start")
    app.set_btn_color(app.timer_button, "green")

def stop_timer_thread(app, quit = False) -> None:
    '''
    Thread for stopping the timer, and quit the app
    if called from quit_app function.
    '''
    app.stop_timer = True
    app.timer_thread.join(2)
    if quit:
        app.destroy()

def format_time(seconds: int) -> str:
    '''
    Return seconds as string in H:M:S format.
    '''
    if seconds == 0:
        return "--:--:--"
    time_inst = time.gmtime(seconds)
    time_out = time.strftime("%H:%M:%S", time_inst)
    return time_out

def load_projects() -> dict:
    '''
    Load projects from pickle file and return them.
    '''
    if not path.exists(Config.DB_FILE):
        return {}
    with open(Config.DB_FILE, "rb") as f:
        data = pickle.load(f)
    return data

def save_projects(projects: str) -> None:
    '''
    Save projects to pickle file.
    '''
    with open(Config.DB_FILE, "wb") as f:
        pickle.dump(projects, f, pickle.HIGHEST_PROTOCOL)


app = Timer()
app.mainloop()
