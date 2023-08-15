import datetime
import os
import threading

import wx
import openai


def add_newlines(string, line_length):
    words = string.split()
    lines = []
    current_line = ""

    for word in words:
        if len(current_line) + len(word) <= line_length:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return '\n'.join(lines)

def is_valid_filename(filename):
    try:
        # Check if the filename is valid for the current platform
        # This checks for invalid characters and reserved names
        os.path.basename(filename)

        return True
    except OSError:
        return False

class PanelsSwitcher(wx.BoxSizer):
    """
    A sizer for switching between panels in a parent window.
    """

    def __init__(self, parent, panels):
        """
        Constructor for PanelsSwitcher.

        :param parent: Parent window.
        :type parent: wx.Window
        :param panels: List of panels to switch between.
        :type panels: list of wx.Window
        """
        # Initialize the base class
        wx.BoxSizer.__init__(self)

        # Attach this sizer to the parent window
        parent.SetSizer(self)

        # Save the parent window
        self.parent = parent

        # Save the list of panels
        self.panels = panels

        # Add all the panels into this sizer
        for panel in self.panels:
            self.Add(panel, 1, wx.EXPAND)

        # Show the first panel and hide the rest of the panels
        self.Show(panels[0])

    def add_panel(self, panel):
        """
        Adds a new panel to the list of panels.

        :param panel: Panel to add.
        :type panel: wx.Window
        """
        self.panels.append(panel)
        self.Add(panel, 1, wx.EXPAND)

    def Show(self, panel):
        """
        Shows the given panel and hides the rest of the panels.

        :param panel: Panel to show.
        :type panel: wx.Window
        """
        # For each panel in the list of panels
        for p in self.panels:
            # Show the given panel
            if p == panel:
                p.Show()
            else:
                # and hide the rest of the panels
                p.Hide()

        # Rearrange the window
        self.parent.Layout()


class HomePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.selected_file = None

        self.error_label = wx.StaticText(self, label="")
        self.error_label.SetForegroundColour((255, 0, 0))

        self.title_label = wx.StaticText(self, label="Choose title:")
        self.title_entry = wx.TextCtrl(self)
        
        self.file_button = wx.Button(self, label="Select Audio File")
        self.file_display = wx.StaticText(self, label="")

        self.transcribe_button = wx.Button(self, label="Transcribe")

        self.settings_button = wx.Button(self, label="Settings")

        self.sizer.Add(self.settings_button, 0, wx.ALIGN_LEFT)
        self.sizer.AddSpacer(30)
        
        self.title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.title_sizer.Add(self.title_label, 0, wx.ALIGN_CENTER_VERTICAL)
        self.title_sizer.AddSpacer(5)
        self.title_sizer.Add(self.title_entry, 0, wx.ALL)
        self.sizer.Add(self.title_sizer, 0, wx.ALIGN_CENTER)
        self.sizer.AddSpacer(10)

        self.file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.file_sizer.Add(self.file_button, 0, wx.ALIGN_CENTER)
        self.file_sizer.AddSpacer(5)
        self.file_sizer.Add(self.file_display, 0, wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(self.file_sizer, 0, wx.ALIGN_CENTER)

        self.sizer.AddSpacer(20)
        self.sizer.Add(self.transcribe_button, 0, wx.ALIGN_CENTER)
        self.sizer.AddSpacer(60)
        self.sizer.Add(self.error_label, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.SetSizer(self.sizer)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.select_audio_file, self.file_button)
        self.Bind(wx.EVT_BUTTON, self.transcribe, self.transcribe_button)
        self.Bind(wx.EVT_BUTTON, self.show_settings, self.settings_button)


    def notify_error(self, msg):
        self.error_label.SetForegroundColour((255, 0, 0))
        self.error_label.SetLabel(msg)
        self.Layout()

    def clear_error(self):
        self.error_label.SetLabel("")
        self.Layout()

    def select_audio_file(self, event):
        self.clear_error()
        dlg = wx.FileDialog(self, "Select Audio File", wildcard="Audio Files (*.mp3;*.wav)|*.mp3;*.wav", style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            self.selected_file = dlg.GetPath()
            self.file_display.SetLabel(dlg.GetFilename())
            self.Layout()
        dlg.Destroy()

    def save_transcript(self, text):
        if is_valid_filename(self.title_entry.GetValue()) and self.title_entry.GetValue() != '':
            title = self.title_entry.GetValue()
        else:
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime("%Y_%m_%d_%H_%M_%S")
            title = 'transcript_' + formatted_datetime

        with open(f"{title}.txt", 'w') as file:
            file.write(text)

        self.error_label.SetForegroundColour((30, 117, 22))
        self.error_label.SetLabel(f"Saved transcript to '{os.getcwd()}\\{title}.txt'")
        self.Layout()


    def send_audio(self):
        with open(self.selected_file, "rb") as audio_file:
            try:
                response = openai.Audio.transcribe("whisper-1", audio_file)
            except openai.OpenAIError as e:
                self.notify_error('OPENAI error: ' + add_newlines(str(e), 50))
                self.save_transcript('test')
            else:
                self.save_transcript(response.data['text'])

    def transcribe(self, event):
        self.clear_error()
        if self.selected_file:
            if os.getenv('OPENAI_API_KEY'):
                threading.Thread(target=self.send_audio).start()
            else:
                self.notify_error("No API key provided.")
        else:
            self.notify_error("No audio file selected.")

    def show_settings(self, event):
        self.clear_error()
        self.parent.sizer.Show(self.parent.settings_panel)


class SettingsPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.return_home_button = wx.Button(self, label="Home")
        
        self.api_key_label = wx.StaticText(self, label="API Key:")
        self.api_key_entry = wx.TextCtrl(self, size=(340, 20))
        self.save_settings_button = wx.Button(self, label="Save")

        self.sizer.Add(self.return_home_button, 0, wx.ALIGN_LEFT)
        self.sizer.AddSpacer(40)
        self.sizer.Add(self.api_key_label, 0, wx.ALIGN_CENTER)
        self.sizer.Add(self.api_key_entry, 0, wx.ALIGN_CENTER)
        self.sizer.AddSpacer(10)
        self.sizer.Add(self.save_settings_button, 0, wx.ALIGN_CENTER)

        self.SetSizer(self.sizer)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.return_to_home, self.return_home_button)
        self.Bind(wx.EVT_BUTTON, self.save_api_key, self.save_settings_button)

    def save_api_key(self, event):
        os.environ['OPENAI_API_KEY'] = self.api_key_entry.GetValue()
        openai.api_key = self.api_key_entry.GetValue()
        self.return_to_home(event)

    def return_to_home(self, event):
        self.parent.sizer.Show(self.parent.home_panel)

class TranscriptionApp(wx.Frame):
    def __init__(self, parent, title):
        super(TranscriptionApp, self).__init__(parent, title=title, size=(500, 300))

        self.home_panel = HomePanel(self)
        self.settings_panel = SettingsPanel(self)

        self.sizer = PanelsSwitcher(self, [self.home_panel, self.settings_panel])
        self.SetSizer(self.sizer)

        self.sizer.Show(self.home_panel)

if __name__ == "__main__":
    app = wx.App()
    frame = TranscriptionApp(None, "Audio Transcription App")
    frame.Show()
    app.MainLoop()
