from argparse import ArgumentParser
from models import Config

parser = ArgumentParser(
    prog="timebucks bot",
    usage="command [args]",
    description="cmd utility for timebucks automation",
)
parser.add_argument("-b", nargs="+", type=int, help="list of browsers to use")
parser.add_argument("-p", nargs="+", type=int, help="list of profiles to use")
parser.add_argument(
    "-ps", help="set the worker to passive, passive worker only submit previews"
)
parser.add_argument('-fs',help='file service url e.g http://localhost:5000')
parser.add_argument(
    "-s", nargs="+", type=int, help="list of saved profile sessions to use"
)
parser.add_argument("-wd", help="working directory for the bot")

args = parser.parse_args()

latest_config = None

try:
    latest_config = Config.select().order_by(Config.id.desc()).get()

except Config.DoesNotExist:
    latest_config = None
except Exception as e:
    print(f"Error fetching latest config: {e}")
    latest_config = None


# Create a tkinter configuration form to collect user input if not provided
try:
    from tkinter import Tk, Label, Entry, Button, filedialog, Checkbutton, IntVar

    class ConfigForm:
        def __init__(self, callback):
            self.callback = callback
            master = Tk()

            self.master = master
            self.master.title("Auto Configuration Form")

            # Create labels and entry fields for each argument
            self.browser_label = Label(master, text="Browsers (space-separated):")
            self.browser_label.pack()
            self.browser_entry = Entry(master)

            self.browser_entry.pack()

            self.profile_label = Label(master, text="Profiles (space-separated):")
            self.profile_label.pack()
            self.profile_entry = Entry(master)
            self.profile_entry.pack()

            self.session_label = Label(
                master, text="Saved Profile Sessions (space-separated):"
            )
            self.session_label.pack()
            self.session_entry = Entry(master)
            self.session_entry.pack()

            self.fs_label = Label(master, text='File Service Server')
            self.fs_component = Entry(master)
            self.fs_label.pack()
            self.fs_component.pack()

            self.passive_mode_var = IntVar()
            self.check_button = Checkbutton(master, text='passive mode',variable=self.passive_mode_var)
            self.check_button.pack()

            self.working_dir_label = Label(master, text="Working Directory:")
            self.working_dir_label.pack()
            self.working_dir_entry = Entry(master)

            self.working_dir_entry.pack()

            # set default values from the latest config
            if latest_config:
                if latest_config.browsers:
                    self.browser_entry.insert(
                        0, args.b or " ".join(map(str, latest_config.browsers.split()))
                    )
                if latest_config.profiles:
                    self.profile_entry.insert(
                        0, args.p or " ".join(map(str, latest_config.profiles.split()))
                    )
                if latest_config.sessions:
                    self.session_entry.insert(
                        0, args.s or " ".join(map(str, latest_config.sessions.split()))
                    )
                if latest_config.working_dir:
                    self.working_dir_entry.insert(0, latest_config.working_dir)

                if latest_config.file_service:
                    self.fs_component.insert(0,args.fs or latest_config.file_service)

            # Create a browse button for the working directory
            self.browse_button = Button(master, text="Browse", command=self.browse)
            self.browse_button.pack()

            # Create a submit button
            self.submit_button = Button(self.master, text="Submit", command=self.submit)
            self.submit_button.pack()

        def browse(self):
            # Open a file dialog to select the working directory
            directory = filedialog.askdirectory()
            if directory:
                self.working_dir_entry.delete(0, "end")  # Clear the entry field
                self.working_dir_entry.insert(0, directory)

        def submit(self):
            # Get the values from the entry fields
            browsers = (
                list(map(int, self.browser_entry.get().split()))
                if self.browser_entry.get()
                else None
            )
            profiles = (
                list(map(int, self.profile_entry.get().split()))
                if self.profile_entry.get()
                else None
            )
            sessions = (
                list(map(int, self.session_entry.get().split()))
                if self.session_entry.get()
                else None
            )
            working_dir = (
                self.working_dir_entry.get() if self.working_dir_entry.get() else None
            )
            file_service = (
                self.fs_component.get() if self.fs_component.get() else None
            )

            config = {
                "browsers": browsers,
                "profiles": profiles,
                "sessions": sessions,
                "working_dir": working_dir,
                "passive_mode":1 if self.passive_mode_var.get()==1 else None,
                "file_service":file_service
            }

            self.master.quit()
            self.master.destroy()

            # Call the callback function with the collected data
            self.callback(config)
            # Save the config to the database
            print(config)
            new_config = Config()
            new_config.browsers = (
                " ".join(map(str, config["browsers"])) if config["browsers"] else None
            )
            new_config.profiles = (
                " ".join(map(str, config["profiles"])) if config["profiles"] else None
            )
            new_config.sessions = (
                " ".join(map(str, config["sessions"])) if config["sessions"] else None
            )
            new_config.working_dir = (
                config["working_dir"] if config["working_dir"] else None
            )
            new_config.save()

    # Create an instance of the ConfigForm
    config_data = {}
    form = ConfigForm(lambda data: config_data.update(data))

    # Start the tkinter main loop
    form.master.mainloop()

    args.b = config_data.get("browsers", args.b)
    args.p = config_data.get("profiles", args.p)
    args.s = config_data.get("sessions", args.s)
    args.wd = config_data.get("working_dir", args.wd)
    args.ps = config_data.get("passive_mode",args.ps)
    args.fs = config_data.get('file_service',args.fs)


except ModuleNotFoundError:
    print(
        "tkinter module not found, using configurations provided by console command arguments"
    )
