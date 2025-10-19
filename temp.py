import gi
import sys
import os
from pathlib import Path

# Require GTK version 4.0 and Adwaita for icons
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Gio, GLib, Adw, Gdk

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
        hbox.set_margin_top(6)
        hbox.set_margin_bottom(6)
        hbox.set_margin_start(6)
        hbox.set_margin_end(6)
        hbox.append(icon)
        hbox.append(vbox)
        
        self.set_child(hbox)


class AppWindow(Gtk.ApplicationWindow):
    """
    The main application window, providing an application search interface.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_apps = []

        # Set up the window
        self.set_default_size(600, 400)
        self.set_title("Application Search")

        # Main vertical layout
        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(main_vbox)

        # --- Search Entry ---
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search for applications...")
        self.search_entry.connect("search-changed", self.on_search_changed)
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
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_vexpand(True)
        self.results_listbox = Gtk.ListBox()
        self.results_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.results_listbox.connect("row-activated", self.on_result_activated)

        # Add event controller to move focus back to search with Escape
        list_controller = Gtk.EventControllerKey.new()
        list_controller.connect("key-pressed", self.on_list_key_pressed)
        self.results_listbox.add_controller(list_controller)
        scrolled_window.set_child(self.results_listbox)
        
        main_vbox.append(scrolled_window)
        
        self.load_applications()

    def on_search_key_pressed(self, controller, keyval, keycode, state):
        """Handle key presses specifically in the search entry."""
        if keyval == Gdk.KEY_Down:
            # If there are results, move focus to the listbox
            if self.results_listbox.get_first_child():
                self.results_listbox.grab_focus()
                # Also select the first row to make navigation intuitive
                self.results_listbox.select_row(self.results_listbox.get_row_at_index(0))
                return True # We've handled this key press
        return False # Let other handlers process the event

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

    def filter_applications(self, query):
        """Filters applications and populates the listbox with results."""
        for app_info in self.all_apps:
            # Check against name, description, and keywords
            if (query in app_info.get_display_name().lower() or
                (app_info.get_description() and query in app_info.get_description().lower()) or
                (app_info.get_keywords() and any(query in k.lower() for k in app_info.get_keywords()))):
                
                result_widget = SearchResultRow(app_info)
                self.results_listbox.append(result_widget)


    def on_result_activated(self, listbox, row):
        """Handles clicks on a search result to launch the application."""
        app_info = row.app_info
        try:
            app_info.launch([], None)
            # Close the launcher window after an app is successfully launched
            self.get_application().quit()
        except GLib.Error as e:
            print(f"Error launching application: {e.message}")


class MyApplication(Gtk.Application):
    """
    The main GTK Application class.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="org.example.applauncher", **kwargs)
        self.window = None

    def do_activate(self):
        """Activates the application by creating and showing the main window."""
        if not self.window:
            self.window = AppWindow(application=self, title="App Launcher")
        self.window.present()

if __name__ == "__main__":
    # Initialize Adwaita for modern styling
    Adw.init()
    app = MyApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)

