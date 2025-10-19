import gi
import sys

# Require GTK version 4.0
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk

# --- Required for Global Hotkeys ---
# This script now requires the 'pynput' library.
# Install it using: pip install pynput
try:
    from pynput import keyboard
except ImportError:
    print("Error: The 'pynput' library is required for global shortcuts.")
    print("Please install it using: pip install pynput")
    sys.exit(1)

class SearchResultRow(Gtk.ListBoxRow):
    """
    A custom widget for displaying a single application search result.
    It contains the application's icon and its name.
    """
    def __init__(self, app_info):
        super().__init__()
        self.app_info = app_info

        # Get the application's icon
        gicon = app_info.get_icon()
        if not gicon:
            gicon = Gio.ThemedIcon.new("application-x-executable") # Fallback icon
        icon = Gtk.Image.new_from_gicon(gicon)
        icon.set_icon_size(Gtk.IconSize.LARGE)
        icon.set_margin_end(10)

        # Create labels for name and description
        name_label = Gtk.Label.new(app_info.get_display_name())
        name_label.set_halign(Gtk.Align.START)
        
        description_label = Gtk.Label()
        description_label.set_halign(Gtk.Align.START)
        description_label.set_css_classes(["dim-label"]) # Make text less prominent
        description_label.set_label(app_info.get_description() or "") # Use description if available

        # Arrange labels vertically
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.append(name_label)
        vbox.append(description_label)

        # Main box for the row
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.set_margin_top(20)
        hbox.set_margin_bottom(20)
        hbox.set_margin_start(20)
        hbox.set_margin_end(20)
        hbox.append(icon)
        hbox.append(vbox)
        
        self.set_child(hbox)


# Main Application Window Class
class SearchBar(Gtk.ApplicationWindow):
    """
    This class represents the main application window.
    It sets up the UI and a shortcut controller for window-specific actions (like 'Esc').
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_apps = []
        # --- Window Configuration ---
        self.set_title("Finder")
        self.set_default_size(800, 0)
        self.set_resizable(True)

        # Making the window undecorated and modal.
        # This combination should be treated as a dialog/popup by the window manager.
        self.set_decorated(False)
        self.set_modal(True)

        # Main vertical layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(main_vbox)

        # --- Search Entry ---
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search for applications...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.search_entry.connect("activate", self.on_search_activate)
        self.search_entry.set_margin_start(10)
        self.search_entry.set_margin_end(10)
        self.search_entry.set_margin_top(10)
        self.search_entry.set_margin_bottom(5)

        # Add event controller to move focus to results with Down arrow
        search_controller = Gtk.EventControllerKey.new()
        search_controller.connect("key-pressed", self.on_search_key_pressed)
        self.search_entry.add_controller(search_controller)
        main_vbox.append(self.search_entry)

        # --- Results Area ---
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_visible(False) # Hide initially
        self.results_listbox = Gtk.ListBox()
        self.results_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results_listbox.connect("row-activated", self.on_result_activated)

        # Add event controller to move focus back to search with Escape
        list_controller = Gtk.EventControllerKey.new()
        list_controller.connect("key-pressed", self.on_list_key_pressed)
        self.results_listbox.add_controller(list_controller)
        self.scrolled_window.set_child(self.results_listbox)
        
        main_vbox.append(self.scrolled_window)
        
        self.load_applications()

        self.setup_shortcuts()

    def on_search_activate(self, entry):
        """Called when Enter is pressed in the search entry."""
        selected_row = self.results_listbox.get_selected_row()
        if selected_row:
            self.on_result_activated(self.results_listbox, selected_row)

    def on_search_key_pressed(self, controller, keyval, keycode, state):
        """Handle key presses specifically in the search entry."""
        if keyval not in (Gdk.KEY_Down, Gdk.KEY_Up):
            return False

        num_rows = len(list(self.results_listbox))
        if num_rows == 0:
            return False

        selected_row = self.results_listbox.get_selected_row()

        if keyval == Gdk.KEY_Down:
            if selected_row is None:
                current_index = -1
            else:
                current_index = selected_row.get_index()

            if current_index < num_rows - 1:
                next_row = self.results_listbox.get_row_at_index(current_index + 1)
                self.results_listbox.select_row(next_row)
            return True

        elif keyval == Gdk.KEY_Up:
            if selected_row is not None:
                current_index = selected_row.get_index()
                if current_index > 0:
                    prev_row = self.results_listbox.get_row_at_index(current_index - 1)
                    self.results_listbox.select_row(prev_row)
            return True

        return False

    def on_list_key_pressed(self, controller, keyval, keycode, state):
        """Handle key presses specifically in the results list."""
        # Pressing Escape in the list moves focus back to the search bar
        if keyval == Gdk.KEY_Escape:
            self.search_entry.grab_focus()
            return True # We've handled this key press
        return False

    def load_applications(self):
        """Loads all findable applications on the system."""
        self.all_apps = Gio.DesktopAppInfo.get_all()


    def on_search_changed(self, search_entry):
        """Called when text in the search entry changes."""
        search_query = search_entry.get_text().strip().lower()

        # Clear previous results
        while child := self.results_listbox.get_row_at_index(0):
            self.results_listbox.remove(child)

        if len(search_query) > 0:
            self.filter_applications(search_query)

        # --- Resize window based on number of results ---
        num_results = len(list(self.results_listbox))
        if num_results > 0:
            self.scrolled_window.set_visible(True)
            # Calculate new height: approx. 60px per row + search bar height
            new_height = (num_results * 85) + 50
            self.set_default_size(800, new_height)
        else:
            self.scrolled_window.set_visible(False)
            # Reset to a minimal height when there are no results
            self.set_default_size(800, 0)

    def filter_applications(self, query):
        """Filters applications and populates the listbox with results."""
        for app_info in self.all_apps:
            # Check against name, description, and keywords
            if (query in app_info.get_display_name().lower() or
                (app_info.get_description() and query in app_info.get_description().lower())):
                
                result_widget = SearchResultRow(app_info)
                self.results_listbox.append(result_widget)


    def on_result_activated(self, listbox, row):
        """Handles clicks on a search result to launch the application."""
        app_info = row.app_info
        try:
            app_info.launch([], None)
            # Hide the launcher window after an app is successfully launched
            self.set_visible(False)
        except GLib.Error as e:
            print(f"Error launching application: {e.message}")

    def on_hide_shortcut(self, widget, args):
        """Callback function executed when the hide shortcut is triggered."""
        self.set_visible(False)
        return GLib.SOURCE_REMOVE

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

# Main Application Class
class MyApp(Gtk.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.win = None
        self.hotkey_listener = None

    def do_activate(self):
        """Called when the application is launched or activated."""
        if not self.win:
            self.win = SearchBar(application=self)
        self.win.present()
        self.win.search_entry.grab_focus()

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
        print("Setting up global hotkey listener...")
        hotkeys = {
            '<alt>+<space>': self.on_show_shortcut,
            '<esc>': self.on_hide_shortcut
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

    def on_hide_shortcut(self):
        """
        Callback for the global 'hide' hotkey. This is called from a
        separate thread by the pynput listener.
        """
        print("Escape pressed (global): Hiding window.")
        # GUI operations must be done in the main GTK thread.
        # GLib.idle_add() schedules our function to be run safely in the main loop.
        GLib.idle_add(self.win.on_hide_shortcut, None, None)


if __name__ == "__main__":
    app = MyApp(application_id="com.example.gtk.globalshortcuts")
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
