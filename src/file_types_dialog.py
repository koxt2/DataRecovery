# file_types_dialog.py
#
# Copyright 2025 koxt2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later

from gi.repository import Adw, Gtk

@Gtk.Template(resource_path='/datarecovery/gtk/file_types.ui')
class FileTypesDialog(Adw.Window):
    __gtype_name__ = 'FileTypesDialog'
    
    container_box = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    select_all_button = Gtk.Template.Child()
    unselect_all_button = Gtk.Template.Child()
    
    FILE_TYPES = {
        "Archive": [
            "7z", "a", "ace", "apk", "arj", "bkf", "bz2", "cab", "dar", "deb", 
            "dump", "ghx", "gz", "lzh", "lzo", "par2", "rar", "rpm", "stu", 
            "tar", "tar.gz", "vbm", "wim", "xar", "xz", "zip"
        ],
        "Multimedia": [
            "3ds", "3dm", "3g2", "3gp", "abr", "acb", "ado", "aep", "afdesign",
            "aif", "albm", "all", "als", "ani", "ape", "ari", "arw", "asf",
            "asl", "au", "avi", "axp", "binvox", "bdm", "bld", "blend", "bmp",
            "bpg", "bvr", "c4d", "caf", "cam", "camrec", "CATDrawing", "cda",
            "cdd", "cdl", "cdr", "cdt", "celtx", "che", "comicdoc", "cpi",
            "cpr", "cr2", "cr3", "crw", "csh", "ctg", "cue", "dad", "db",
            "dcm", "dcr", "djv", "dng", "dp", "dpx", "ds2", "dsc", "dss",
            "ds_store", "dta", "dv", "dvi", "dvr", "dwg", "emf", "epub",
            "ers", "exs", "fcp", "fh10", "fh5", "flac", "fla", "flp", "flv",
            "gi", "gif", "gp4", "gp5", "gpx", "gsm", "heic", "icc", "icns",
            "ico", "idf", "idx", "iff", "ind", "ifo", "indd", "info", "ipt",
            "iso", "it", "itu", "ora", "jng", "jpg", "kra", "logic", "m2t",
            "m2ts", "m3u", "m4p", "max", "mb", "mcf", "mfa", "mhbd", "mid",
            "mkv", "mlv", "mng", "mov", "mp", "mp3", "mp4", "mpg", "mpl",
            "mpo", "mrw", "mus", "mws", "nef", "oci", "ogg", "ogm", "ogv",
            "orf", "pbm", "pct", "pcx", "psb", "pef", "pgm", "png", "pnm",
            "ppm", "prproj", "psd", "psf", "psp", "ptb", "pts", "pvp", "qcp",
            "qkt", "qxd", "qxp", "r3d", "raf", "ram", "ra", "raw", "rdc",
            "rm", "rns", "rpp", "rw2", "rx2", "ses", "shn", "sib", "sit",
            "skd", "sketch", "smil", "spss", "sr2", "svg", "swc", "swf",
            "tg", "tif", "TiVo", "tod", "tpl", "ts", "vdj", "wav", "wdp",
            "webm", "webp", "wee", "wmf", "wnk", "wpb", "wpl", "wtv", "wv",
            "x3f", "x3i", "xcf", "xd", "xm", "xmp", "xrns", "xv", "zcode"
        ],
        "Office": [
            "accdb", "ai", "apr", "csv", "cwk", "doc", "docx", "et", "fb2",
            "fods", "fp7", "fp12", "gnucash", "kmy", "lyx", "mdb", "njx",
            "odg", "odp", "ods", "odt", "one", "pages", "pap", "ppt", "pptx",
            "pub", "qbb", "qbw", "qpw", "rtf", "sda", "sdc", "sdd", "sdw",
            "slk", "sav", "snt", "sxc", "sxd", "sxi", "sxw", "tex", "txt",
            "vsd", "vsdx", "wpd", "wps", "xlr", "xls", "xlsx", "wdb", "wk4",
            "wks"
        ],
        "Others": [
            "1cd", "ab", "adr", "agn", "ahn", "amb", "amd", "amr", "amt",
            "apa", "apple", "asm", "asp", "atd", "att", "axx", "bac", "bai",
            "bam", "bat", "bgz", "bim", "c", "chm", "class", "cls", "cm",
            "compress", "cow", "cp_", "csi", "d2s", "dat", "db", "dbf",
            "dbn", "dbx", "dc", "ddf", "dex", "dgn", "dif", "dim", "diskimage",
            "dll", "dmp", "drw", "dsa", "dst", "dxf", "e01", "ecr", "eCryptfs",
            "edb", "elf", "emb", "emka", "emlx", "eps", "ess", "evt", "evtx",
            "exe", "fbf", "fbk", "fcs", "fdb", "fds", "f", "fh1", "fit",
            "fits", "fm", "fob", "fos", "fp5", "freeway", "frm", "fst", "fs",
            "fwd", "gam", "gcs", "gct", "gho", "gm6", "gm81", "gmd", "gmk",
            "gp2", "gpg", "gsb", "h", "hdf", "hdr", "hds", "hm", "hr9",
            "html.gz", "html", "http", "ibd", "ics", "imb", "img", "imm",
            "inf", "ini", "jad", "jar", "jks", "jnb", "jp2", "json", "jsonlz4",
            "jsp", "kdb", "kdbx", "key", "kmz", "ldf", "ldif", "lit", "lnk",
            "lso", "luks", "lwo", "lxo", "ly", "mat", "mcd", "mdf", "mdl",
            "mem", "mfg", "mig", "mk5", "mmap", "mny", "mobi", "msa", "msf",
            "msg", "mxf", "MYI", "myo", "nd2", "nds", "nes", "nk2", "notebook",
            "nsf", "p65", "paf", "pcap", "pcb", "pcp", "pdb", "pdf", "pds",
            "pf", "pfx", "pgp", "php", "pli", "plist", "pl", "plt", "pm",
            "ppk", "prc", "prd", "priv", "prt", "psmodel", "ps", "pst", "ptf",
            "ptx", "pub", "pyc", "py", "pzf", "pzh", "qbb", "qbmb", "qbw",
            "qdf-backup", "qdf", "qgs", "rb", "RData", "reg", "res", "rfp",
            "rlv", "rsa", "rvt", "save", "schematic", "sgcta", "sh3d", "sh",
            "skp", "sla", "sldprt", "sld", "snag", "sp3", "sparseimage",
            "spe", "spf", "sqlite", "sql", "sqm", "steuer2014", "steuer2015",
            "stl", "stp", "studio", "tax", "tcw", "tib", "ticket.bin", "torrent",
            "tph", "ttd", "ttf", "tz", "url", "v2i", "vault", "vb", "vcf",
            "vdi", "veg", "vfb", "vib", "wallet", "vmdk", "vmg", "wab", "wim",
            "win", "wld", "woff", "x4a", "x4g", "x4p", "x4s", "xfi", "xml.gz",
            "xml", "xoj", "xpi", "xpt", "xsv", "z2d", "zpr"
        ]
    }
    
    def __init__(self, parent_window, **kwargs):
        super().__init__(**kwargs)
        self.set_transient_for(parent_window)
        self.category_boxes = {}
        self.file_type_rows = {}
        self.populate_file_types()
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.select_all_button.connect("clicked", self.on_select_all)
        self.unselect_all_button.connect("clicked", self.on_unselect_all)
        self.connect("close-request", self.on_close_request)
    
    def on_close_request(self, window):
        self.hide()
        return True
    
    def populate_file_types(self):
        for category, file_types in self.FILE_TYPES.items():
            category_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            category_box.set_margin_bottom(20)
            
            category_listbox = Gtk.ListBox()
            category_listbox.set_css_classes(["boxed-list"])
            category_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
            
            category_label = Adw.ActionRow()
            category_label.set_title(f"<b>{category}</b>")
            category_label.set_title_lines(1)
            category_listbox.append(category_label)
            
            self.file_type_rows[category] = []
            
            for file_type in file_types:
                switch_row = Adw.SwitchRow()
                switch_row.set_title(file_type)
                switch_row.set_active(True)
                category_listbox.append(switch_row)
                self.file_type_rows[category].append((switch_row, file_type))
            
            category_box.append(category_listbox)
            self.container_box.append(category_box)
            self.category_boxes[category] = category_box
    
    def on_search_changed(self, entry):
        search_text = entry.get_text().lower()
        
        if not search_text:
            # Show all categories and rows
            for category_box in self.category_boxes.values():
                category_box.set_visible(True)
            for category_rows in self.file_type_rows.values():
                for switch_row, file_type in category_rows:
                    switch_row.set_visible(True)
        else:
            # Filter based on search text
            for category, category_box in self.category_boxes.items():
                has_visible_items = False
                
                # Check each file type in this category
                for switch_row, file_type in self.file_type_rows[category]:
                    matches = search_text in file_type.lower()
                    switch_row.set_visible(matches)
                    if matches:
                        has_visible_items = True
                
                # Show/hide the entire category based on whether it has visible items
                category_box.set_visible(has_visible_items)
    
    def on_select_all(self, button):
        for category_rows in self.file_type_rows.values():
            for switch_row, file_type in category_rows:
                switch_row.set_active(True)
    
    def on_unselect_all(self, button):
        for category_rows in self.file_type_rows.values():
            for switch_row, file_type in category_rows:
                switch_row.set_active(False)
    
    def get_selected_file_types(self):
        selected = []
        for category_rows in self.file_type_rows.values():
            for switch_row, file_type in category_rows:
                if switch_row.get_active():
                    selected.append(file_type)
        return selected
    
    def get_photorec_fileopt_commands(self):
        selected = self.get_selected_file_types()
        
        total_count = sum(len(rows) for rows in self.file_type_rows.values())
        selected_count = len(selected)
        
        if selected_count == 0:
            return "fileopt,everything,disable"
        elif selected_count == total_count:
            return "fileopt,everything,enable"
        elif selected_count > total_count / 2: ########## This needs testing ##########
            # More than half selected - use exclude mode (disable unselected)
            all_file_types = []
            for category_rows in self.file_type_rows.values():
                for switch_row, file_type in category_rows:
                    all_file_types.append(file_type)
            
            # Disable the ones that are NOT selected
            unselected = [ft for ft in all_file_types if ft not in selected]
            parts = ["fileopt", "everything", "enable"]
            for file_type in unselected:
                parts.extend([file_type, "disable"])
            return ",".join(parts)
        else:
            # Less than half selected - use include mode (enable only selected)
            parts = ["fileopt", "everything", "disable"]
            for file_type in selected:
                parts.extend([file_type, "enable"])
            return ",".join(parts)
