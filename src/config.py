# config.py
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

# Application version (set by meson during build)
VERSION = '@VERSION@'

# Directory and file names
RECOVERY_DATA_FOLDER = "Recovery Data"
WORKING_DIR_NAME = "working"
RECOVERED_FILES_DIR = "recovered_files"

# Log file names
DATARECOVERY_LOG = "datarecovery.log"
IMAGER_LOG = "imager_output.log"
PHOTOREC_LOG_PREFIX = "photorec_"
DUPLICATES_LOG = "duplicates.log"

# File extensions
IMAGE_FILE_EXTENSION = ".img"
MAP_FILE_EXTENSION = ".map"
LOG_FILE_EXTENSION = ".log"

# ddrescue settings
DDRESCUE_RETRY_PASSES = 3
DISK_SPACE_SAFETY_MARGIN_PERCENT = 0.10  # 10%

# Tool names (for dependency checking)
REQUIRED_TOOLS = ['ddrescue', 'photorec', 'rdfind', 'udisksctl']

# PhotoRec options
PHOTOREC_OPTIONS_BASE = "options"
PHOTOREC_OPTION_KEEP_CORRUPTED = "keep_corrupted_file"
PHOTOREC_OPTION_SEARCH = "search"

# PhotoRec file types organized by category
FILE_TYPES = {
    "Documents": [
        "csv", "doc", "docx", "fb2", "odt", "pages", "pdf", "rtf", "tex", 
        "txt", "wpd"
    ],
    "Spreadsheets": [
        "et", "fods", "ods", "slk", "sxc", "wk4", "wks", "xlr", "xls", "xlsx"
    ],
    "Presentations": [
        "odp", "ppt", "pptx", "sdd", "sxi"
    ],
    "Images": [
        "arw", "bmp", "bpg", "cr2", "cr3", "crw", "dcr", "dng", "gif", 
        "heic", "ico", "icns", "jng", "jpg", "mng", "nef", "orf", "pbm", 
        "pct", "pcx", "pef", "pgm", "png", "pnm", "ppm", "raw", "rw2", 
        "sr2", "svg", "tif", "webp", "x3f"
    ],
    "Audio": [
        "aif", "ape", "au", "caf", "flac", "gsm", "m4p", "mid", "mp3", 
        "ogg", "qcp", "ra", "ram", "shn", "wav", "wv"
    ],
    "Video": [
        "3g2", "3gp", "asf", "avi", "flv", "m2t", "m2ts", "mkv", "mov", 
        "mp4", "mpg", "ogm", "ogv", "rm", "TiVo", "tod", "ts", "webm", "wtv"
    ],
    "Archive": [
        "7z", "a", "ace", "apk", "arj", "bkf", "bz2", "cab", "dar", "deb", 
        "dump", "gz", "lzh", "lzo", "par2", "rar", "rpm", "tar", "tar.gz", 
        "wim", "xar", "xz", "zip"
    ],
    "Design &amp; CAD": [
        "3dm", "3ds", "ai", "blend", "c4d", "CATDrawing", "cdr", "dwg", 
        "dxf", "dgn", "emf", "eps", "ipt", "max", "psb", "psd", "skp", 
        "sldprt", "sld", "stl", "stp", "vsd", "vsdx", "wmf", "xcf"
    ],
    "Database": [
        "accdb", "db", "dbf", "edb", "fdb", "fp7", "fp12", "ibd", "ldf", 
        "mdb", "MYI", "pdb", "sqlite", "sql", "wdb"
    ],
    "Email &amp; Contacts": [
        "dbx", "eml", "emlx", "msg", "msf", "nk2", "ost", "pst", "vcf", 
        "vcard", "wab"
    ],
    "Finance &amp; Accounting": [
        "gnucash", "kmy", "mny", "qbb", "qbmb", "qbw", "qdf", "qdf-backup", 
        "steuer2014", "steuer2015", "tax"
    ],
    "Code &amp; Development": [
        "asm", "asp", "bat", "c", "class", "dex", "dll", "elf", "exe", 
        "f", "h", "html", "html.gz", "jar", "java", "jks", "json", "jsonlz4",
        "jsp", "php", "pl", "pm", "py", "pyc", "rb", "sh", "vb"
    ],
    "3D &amp; CAD Files": [
        "3dm", "3ds", "binvox", "blend", "c4d", "dgn", "dwg", "dxf", 
        "ipt", "max", "mb", "prt", "rvt", "skp", "sldprt", "sld", "stl", "stp"
    ],
    "Graphics &amp; Photography": [
        "abr", "acb", "ado", "aep", "afdesign", "asl", "cdr", "cdt", 
        "csh", "fla", "ora", "psb", "psd", "sketch", "xcf", "xd"
    ],
    "Audio Production": [
        "aep", "als", "flp", "logic", "ptb", "pts", "rns", "rpp", "ses", 
        "xrns"
    ],
    "Video Production": [
        "aep", "camrec", "fcp", "mlt", "prproj", "veg"
    ],
    "Publishing": [
        "ai", "cwk", "indd", "lyx", "odg", "pap", "pub", "qxd", "qxp", 
        "sda", "sdc", "sdw", "sla", "sxd", "sxw"
    ],
    "eBooks": [
        "epub", "fb2", "lit", "mobi", "pdb"
    ],
    "Disk Images": [
        "diskimage", "e01", "gho", "img", "iso", "sparseimage", "tib", 
        "v2i", "vdi", "vmdk"
    ],
    "Gaming": [
        "d2s", "gam", "gm6", "gm81", "gmd", "gmk", "nds", "nes", "save"
    ],
    "Music Production": [
        "cue", "gp2", "gp4", "gp5", "it", "logic", "ly", "mid", "mus", 
        "ptb", "xm"
    ],
    "Scientific &amp; Medical": [
        "bam", "dcm", "fcs", "fit", "fits", "hdf", "mat", "nd2", "RData"
    ],
    "Backup &amp; Recovery": [
        "bkf", "fbf", "fbk", "gho", "tib", "v2i", "vbm"
    ],
    "System &amp; Config": [
        "dat", "inf", "ini", "plist", "reg"
    ],
    "Encryption &amp; Security": [
        "axx", "eCryptfs", "gpg", "kdb", "kdbx", "luks", "pfx", "pgp", 
        "ppk", "priv", "rsa", "vault", "wallet"
    ],
    "Web &amp; Internet": [
        "css", "html", "http", "js", "url"
    ],
    "Others": [
        "1cd", "ab", "adr", "agn", "ahn", "all", "amb", "amd", "amr", "amt",
        "ani", "apa", "apple", "apr", "ari", "atd", "att", "axp", "bac", "bai",
        "bat", "bdm", "bgz", "bim", "bld", "bvr", "cam", "cda", "cdd", "cdl",
        "celtx", "che", "cls", "cm", "comicdoc", "compress", "cow", "cp_", "cpi",
        "cpr", "csi", "ctg", "dad", "dc", "ddf", "dim", "dmp", "dp", "dpx",
        "drw", "ds2", "dsa", "dsc", "dss", "ds_store", "dst", "dta", "dv", "dvi",
        "dvr", "ecr", "emb", "emka", "ers", "ess", "evt", "evtx", "exs", "fds",
        "fh1", "fh10", "fh5", "fm", "fob", "fos", "fp5", "freeway", "frm", "fs",
        "fst", "fwd", "gcs", "gct", "ghx", "gi", "gpx", "gsb", "hdr", "hds", "hm",
        "hr9", "ics", "idf", "idx", "iff", "imb", "imm", "ind", "ifo", "info",
        "itu", "jad", "jnb", "jp2", "key", "kmz", "kra", "ldif", "lnk", "lso",
        "lwo", "lxo", "mcd", "mcf", "mdf", "mdl", "mem", "mfa", "mfg", "mhbd",
        "mig", "mk5", "mlv", "mmap", "mp", "mpl", "mpo", "mrw", "msa", "mws",
        "mxf", "myo", "nef", "njx", "notebook", "nsf", "oci", "one", "p65", "paf",
        "pcap", "pcb", "pcp", "pds", "pf", "pli", "plt", "prc", "prd", "priv",
        "prt", "psf", "psmodel", "ps", "psp", "ptf", "ptx", "pvp", "pzf", "pzh",
        "qgs", "qkt", "qpw", "r3d", "raf", "rdc", "res", "rfp", "rlv", "sav",
        "schematic", "sgcta", "sh3d", "sib", "sit", "skd", "smil", "snag", "snt",
        "sp3", "spe", "spf", "spss", "sqm", "stu", "studio", "swc", "swf", "tcw",
        "tg", "ticket.bin", "torrent", "tph", "tpl", "ttd", "ttf", "tz", "vbm",
        "vdj", "veg", "vfb", "vib", "vmg", "wdp", "wee", "win", "wks", "wld",
        "wnk", "woff", "wpb", "wpl", "wps", "x3i", "x4a", "x4g", "x4p", "x4s",
        "xfi", "xmp", "xml", "xml.gz", "xoj", "xpi", "xpt", "xsv", "xv", "z2d",
        "zcode", "zpr"
    ]
}
