import gi
import sys

# Require GTK version 4.0
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

# --- Required for Global Hotkeys ---
# This script now requires the 'pynput' library.
# Install it using: pip install pynput
try:
    from pynput import keyboard
except ImportError:
    print("Error: The 'pynput' library is required for global shortcuts.")
    print("Please install it using: pip install pynput")
    sys.exit(1)


# Main Application Window Class
class ShortcutWindow(Gtk.ApplicationWindow):
    """
    This class represents the main application window.
    It sets up the UI and a shortcut controller for window-specific actions (like 'Esc').
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # --- Window Configuration ---
        self.set_title("Finder")
        self.set_default_size(400, 50)
        self.set_resizable(False)
        # Making the window undecorated and modal.
        # This combination should be treated as a dialog/popup by the window manager.
        self.set_decorated(False)
        self.set_modal(True)

        # --- UI Elements ---
        entry = Gtk.Entry()
        self.set_child(entry)

        # --- Shortcut Setup ---
        self.setup_shortcuts()

    def setup_shortcuts(self):
        """
        Initializes a ShortcutController for shortcuts that should only
        work when this window is focused.
        """
        controller = Gtk.ShortcutController()

        # --- Shortcut to HIDE the window (Escape key) ---
        # This shortcut is window-specific, so it stays here. It will only
        # trigger when the window has focus, which is the desired behavior.
        trigger_hide = Gtk.ShortcutTrigger.parse_string("Escape")
        action_hide = Gtk.CallbackAction.new(self.on_hide_shortcut)
        shortcut_hide = Gtk.Shortcut.new(trigger_hide, action_hide)
        controller.add_shortcut(shortcut_hide)

        self.add_controller(controller)

    def on_hide_shortcut(self, widget, args):
        """Callback function executed when the hide shortcut is triggered."""
        print("Escape pressed (window focused): Hiding window.")
        self.get_child().set_text("")
        self.set_visible(False)
        return True

# Main Application Class
class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.win = None
        self.hotkey_listener = None

    def do_activate(self):
        """Called when the application is launched or activated."""
        if not self.win:
            self.win = ShortcutWindow(application=self)
        self.win.present()
        self.win.set_position(Gtk.WindowPosition.CENTER)

    def do_startup(self):
        """Called once when the application first starts."""
        Gtk.Application.do_startup(self)
        self.setup_global_hotkeys()

    def do_shutdown(self):
        """Called when the application is about to quit."""
        print("Shutting down. Stopping global hotkey listener.")
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        Gtk.Application.do_shutdown(self)

    def setup_global_hotkeys(self):
        """
        Sets up the pynput.GlobalHotKeys listener to capture key combinations
        anywhere in the OS.
        """
        print("Setting up global hotkey listener for Alt+Space...")
        hotkeys = {
            '<alt>+<space>': self.on_show_shortcut
        }
        self.hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
        self.hotkey_listener.start()

    def on_show_shortcut(self):
        """
        Callback for the global 'show' hotkey. This is called from a
        separate thread by the pynput listener.
        """
        print("Alt+Space pressed (global): Activating window.")
        # GUI operations must be done in the main GTK thread.
        # GLib.idle_add() schedules our function to be run safely in the main loop.
        GLib.idle_add(self.activate)


if __name__ == "__main__":
    app = MyApp(application_id="com.example.gtk.globalshortcuts")
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
