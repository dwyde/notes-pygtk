#!/usr/bin/env python
import pygtk
pygtk.require("2.0")
import gtk
import os
import xml.sax, xml.sax.saxutils

class MyNoteBook(gtk.Notebook):
    """A modified GtkNotebook that saves notes to a file."""
    
    def __init__(self, notes_file, parent_window=None):
        """Initialize the notebook.
        
        notes_file -- a file to store the notes
        parent_window -- parent window, for dialogs in awn (default None)
        
        """
        self.notes_file = notes_file
        self.parent_window = parent_window
        gtk.Notebook.__init__(self)
        self.set_property("tab-hborder", 6) # make tabs wider
        self.set_property("scrollable", True)
        self.read_notes()
        self.set_current_page(0)
        self.connect("page-reordered", self.tab_reordered)
        
    def add_tab(self, text=""):
        """Add a page to the notebook.
        
        Each page is a GtkTextview inside a GtkScrolledWindow
        
        """
        buffer = gtk.TextBuffer()
        buffer.set_text(text)
        buffer.set_modified(False)
        tview = gtk.TextView(buffer)
        tview.set_wrap_mode(gtk.WRAP_WORD)
        swindow = gtk.ScrolledWindow()
        swindow.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)
        swindow.add(tview)
        swindow.show_all()
        num = self.append_page(swindow)
        self.set_tab_reorderable(swindow, True)
        child = self.get_nth_page(num)
        self.set_tab_label_text(child, str(num + 1))
        self.set_current_page(num)
        return num
        
    def remove_tab(self):
        """Remove a page from the notebook."""
        removed = self.get_current_page()
        self.remove_page(removed)
        self.renumber_tabs_after(removed)
        # mark an existing buffer as modified
        self.get_buffer(0).set_modified(True)
    
    def add_clicked(self, add_button):
        """Handle signals for the add (+) button."""
        current = self.add_tab()
        self.get_buffer(current).set_modified(True)
    
    def remove_clicked(self, remove_button):
        """Handle signals for the remove (-) button.
        
        Confirm the deletion with a dialog.
        
        """
        if self.get_n_pages() > 1:
            dialog = gtk.MessageDialog(self.parent_window,
                     gtk.DIALOG_MODAL,
                     gtk.MESSAGE_QUESTION,
                     gtk.BUTTONS_NONE,
                     "Really delete this page?")
            dialog.add_buttons(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT,
                     gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
            dialog.connect("response", self.confirm_remove)
            dialog.show()
    
    def confirm_remove(self, dialog, response_id):
        """Delete the page if the user confirms."""
        if response_id == gtk.RESPONSE_ACCEPT:
            self.remove_tab()
        dialog.hide()
    
    def read_notes(self):
        """Read notes from a file.
        
        Use the NoteHandler class to parse the text.
        
        """
        if os.path.isfile(self.notes_file):
            file = open(self.notes_file, 'r')
            try:
                parser = xml.sax.make_parser()
                handler = NoteHandler(self)
                parser.setContentHandler(handler)
                parser.parse(file)
            finally:
                file.close()
        if self.get_n_pages() == 0:
            self.add_tab() # start out with a blank tab
    
    def save_notes(self):
        """Save notes to a file (in XML)."""
        modified = False
        for i in range(self.get_n_pages()):
            if self.get_buffer(i).get_modified():
                modified = True
        if not modified:
            return
        # If a buffer has been modified, save everything
        f = open(self.notes_file, "w")
        try:
            f.write('<?xml version="1.0"?>\n<notes>\n')
            for i in range(self.get_n_pages()):
                buffer = self.get_buffer(i)
                text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter())
                text = xml.sax.saxutils.escape(text)
                text = '<note id="' + str(i + 1) + '">' + text + "</note>\n"
                f.write(text)
                buffer.set_modified(False)
            f.write("</notes>")
        finally:
            f.close()
    
    def get_buffer(self, page_n):
        """Return the buffer associated with a given page in the notebook."""
        scrolled = self.get_nth_page(page_n)
        textview = scrolled.get_child()
        return textview.get_buffer()
        
    def renumber_tabs_after(self, changed):
        """Renumber the tab labels if a page is reordered."""
        for i in range(changed, self.get_n_pages()):
            child = self.get_nth_page(i)
            self.set_tab_label_text(child, str(i + 1))
    
    def tab_reordered(self, notebook, child, page_num):
        """Renumber all tabs and record that a buffer was modified"""
        self.renumber_tabs_after(0) 
        self.get_buffer(0).set_modified(True)

class NoteHandler(xml.sax.handler.ContentHandler):
    """Read the XML save file into a GtkNotebook."""
    
    def __init__(self, notebook):
        """Initialize the class with a notebook to write into."""
        self.notebook = notebook
        self.text_list = []
        
    def startElement(self, name, attrs):
        """Start a new list of text after finding <note> tags."""
        if name == "note":
            self.text_list = []
            
    def endElement(self, name):
        """Add text to a new page in the notebook on </note> tags."""
        if name == "note":
            note_text = ''.join(self.text_list)
            self.notebook.add_tab(note_text)
            
    def characters(self, chars):
        """Store the text between opening and closing tags."""
        self.text_list.append(chars)

class NB_Window:
    """Test the MyNoteBook class."""
    def __init__(self, note_file):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_size_request(300, 350)
        self.nb = MyNoteBook(note_file, window)
        window.connect("destroy", self.window_destroyed, self.nb)
        self.create_toolbar()
        vbox = gtk.VBox()
        vbox.pack_start(self.toolbar, False)
        vbox.pack_start(self.nb)
        window.add(vbox)
        window.show_all()
        self.nb.get_nth_page(0).get_child().grab_focus()
        gtk.main()
    
    def create_toolbar(self):
        """Make a toolbar with buttons to add and remove tabs."""
        self.toolbar = gtk.Toolbar()
        separator = gtk.SeparatorToolItem()
        separator.set_draw(False)
        separator.set_expand(True)
        self.toolbar.insert(separator, -1)
        add_button = gtk.ToolButton(gtk.STOCK_ADD) 
        remove_button = gtk.ToolButton(gtk.STOCK_REMOVE)
        self.toolbar.insert(add_button, -1)
        self.toolbar.insert(remove_button, -1)
        add_button.connect("clicked", self.nb.add_clicked)
        remove_button.connect("clicked", self.nb.remove_clicked)
    
    def window_destroyed(self, window, notebook):
        """Save notes and exit when the window is closed."""
        notebook.save_notes()
        gtk.main_quit()

if __name__ == '__main__':
    NB_Window("notes.xml")
