from pathlib import Path
import urllib.request
import tarfile
import subprocess
import shutil
import os

URLS = [
    "https://download.gnome.org/sources/libsigc++/2.12/libsigc++-2.12.1.tar.xz",
    "https://download.gnome.org/sources/glibmm/2.62/glibmm-2.62.0.tar.xz",
    "https://cairographics.org/releases/cairomm-1.14.5.tar.xz",
    "https://download.gnome.org/sources/pangomm/2.42/pangomm-2.42.2.tar.xz",
]

DEPS_DIR = Path("Deps")
DEPS_DIR.mkdir(exist_ok=True)

VCPKG_ROOT = Path.cwd() / "vcpkg_installed" / "x64-windows"
VCPKG_TOOLS = Path("vcpkg_installed/x64-windows/tools/pkgconf")
PKGCONF_EXE = VCPKG_TOOLS / "pkgconf.exe"
PKG_CONFIG_EXE = VCPKG_TOOLS / "pkg-config.exe"
SIGCPP_DIR = DEPS_DIR / "libsigc++-2.12.1"
GLIBM_DIR = DEPS_DIR / "glibmm-2.62.0"
CAIROMM_DIR = DEPS_DIR / "cairomm-1.14.5"
PANGOMM_DIR = DEPS_DIR / "pangomm-2.42.2"
MSVC_DIR = GLIBM_DIR / "MSVC_NMake"

os.environ["PATH"] = str(VCPKG_TOOLS.absolute()) + os.pathsep + os.environ.get("PATH", "")

if PKGCONF_EXE.exists() and not PKG_CONFIG_EXE.exists():
    shutil.copy2(PKGCONF_EXE, PKG_CONFIG_EXE)

for url in URLS:
    archive = DEPS_DIR / Path(url).name
    urllib.request.urlretrieve(url, archive)
    tarfile.open(archive, "r:xz").extractall(DEPS_DIR)
    archive.unlink()

missing = [cmd for cmd in ("meson", "ninja") if not shutil.which(cmd)]
if missing:
    subprocess.run(["pip", "install", *missing], check=True)

vcvarsall = subprocess.run(
    r'where /r "C:\Program Files\Microsoft Visual Studio" vcvarsall.bat',
    shell=True, capture_output=True, text=True, check=True
).stdout.splitlines()[0]

def build_with_meson(name: str, src_dir: Path) -> None:
    for cfg in ("release", "debug"):
        build = f"build-{cfg}"
        prefix = VCPKG_ROOT / ("debug" if cfg == "debug" else "")
        pkg_config_path = prefix / "lib/pkgconfig"
        env = os.environ.copy()
        env["PKG_CONFIG_PATH"] = str(pkg_config_path)

        subprocess.run(
            f'meson setup {build} --prefix={prefix} -Dbuild-documentation=false -Dbuildtype={cfg}',
            cwd=src_dir, shell=True, check=True, env=env
        )
        subprocess.run(
            f'"{vcvarsall}" x64 && ninja -C {build} && ninja -C {build} install',
            cwd=src_dir, shell=True, check=True, env=env
        )

build_with_meson("sigc++", DEPS_DIR / "libsigc++-2.12.1")

def patch_file(
    filepath: Path,
    insertions: dict[int, str] | None = None,
    line_edits: dict[int, str] | None = None,
    deletions: set[int] | None = None,
) -> None:
    lines = filepath.read_text().splitlines()
    for line_num in sorted(deletions or (), reverse=True):
        del lines[line_num - 1]
    for line_num, new_text in sorted((line_edits or {}).items(), reverse=True):
        lines[line_num - 1] = new_text
    for idx, text in sorted((insertions or {}).items(), reverse=True):
        lines.insert(idx, text)
    filepath.write_text("\n".join(lines) + "\n")

def replace_in_file(filepath: Path, old: str, new: str) -> None:
    content = filepath.read_text()
    if old not in content:
        raise ValueError(f"replace_in_file: marker not found in {filepath}:\n  {old!r}")
    filepath.write_text(content.replace(old, new, 1))

shutil.copy(
    VCPKG_ROOT / "include/glib-2.0/msvc_recommended_pragmas.h",
    MSVC_DIR / "gendef"
)

FINDSTR_FIX = '\t@findstr /v "Avx2WmemEnabledWeakValue" $@ > $@.tmp && move /Y $@.tmp $@'

patch_file(MSVC_DIR / "config-msvc.mak", line_edits={
    45: "LIBSIGC_LIBNAME = sigc-$(LIBSIGC_MAJOR_VERSION).$(LIBSIGC_MINOR_VERSION)",
    50: "GLIBMM_LIBNAME = glibmm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)",
    55: "GIOMM_LIBNAME = giomm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)",
})

replace_in_file(MSVC_DIR / "config-msvc.mak",
    "!ifndef GLIB_COMPILE_SCHEMAS",
    """\
EXTRADEFS_LIBNAME = glibmm_generate_extra_defs-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)
EXTRADEFS_DLL     = $(CFG)\\$(PLAT)\\$(EXTRADEFS_LIBNAME).dll
EXTRADEFS_LIB     = $(CFG)\\$(PLAT)\\$(EXTRADEFS_LIBNAME).lib
EXTRADEFS_OUTDIR  = $(CFG)\\$(PLAT)\\extra_defs_gen
EXTRADEFS_CFLAGS  = /I..\\tools\\extra_defs_gen $(LIBGLIBMM_CFLAGS)

!ifndef GLIB_COMPILE_SCHEMAS""")

patch_file(MSVC_DIR / "generate-msvc.mak", deletions=[24, 25], insertions={18: FINDSTR_FIX, 21: FINDSTR_FIX})

replace_in_file(MSVC_DIR / "generate-msvc.mak",
    "$(CFG)\\$(PLAT)\\giomm-tests:",
    "$(CFG)\\$(PLAT)\\giomm-tests\t\\\n$(CFG)\\$(PLAT)\\extra_defs_gen:")

replace_in_file(MSVC_DIR / "generate-msvc.mak",
    "# Compile schema for giomm settings example",
    """\
# Generate .def file for glibmm_generate_extra_defs
$(EXTRADEFS_OUTDIR)\\glibmm_generate_extra_defs.def: $(GENDEF) $(EXTRADEFS_OUTDIR) $(EXTRADEFS_OUTDIR)\\generate_extra_defs.obj
\t$(CFG)\\$(PLAT)\\gendef.exe $@ $(EXTRADEFS_LIBNAME) $(EXTRADEFS_OUTDIR)\\*.obj

\t@findstr /v "Avx2WmemEnabledWeakValue" $@ > $@.tmp && move /Y $@.tmp $@

# Compile schema for giomm settings example""")

patch_file(MSVC_DIR / "build-rules-msvc.mak", deletions=[105])
patch_file(MSVC_DIR / "Makefile.vc", line_edits={36: "all: $(GIOMM_LIB) $(EXTRADEFS_DLL) all-build-info"})
replace_in_file(MSVC_DIR / "build-rules-msvc.mak",
    "clean:",
    """\
# Rules for building glibmm_generate_extra_defs and the defs generator tools
$(EXTRADEFS_OUTDIR)\\generate_extra_defs.obj: ..\\tools\\extra_defs_gen\\generate_extra_defs.cc
\t@if not exist $(EXTRADEFS_OUTDIR) $(MAKE) -f Makefile.vc CFG=$(CFG) $(EXTRADEFS_OUTDIR)
\t$(CXX) $(EXTRADEFS_CFLAGS) $(CFLAGS_NOGL) /DGLIBMM_GENERATE_EXTRA_DEFS_BUILD /Fo$(EXTRADEFS_OUTDIR)\\ /c ..\\tools\\extra_defs_gen\\generate_extra_defs.cc

$(EXTRADEFS_DLL): $(EXTRADEFS_OUTDIR)\\glibmm_generate_extra_defs.def $(EXTRADEFS_OUTDIR)\\generate_extra_defs.obj $(GLIBMM_LIB)
\tlink /DLL $(LDFLAGS_NOLTCG) $(GOBJECT_LIBS) $(LIBSIGC_LIB) /implib:$(EXTRADEFS_LIB) /def:$(EXTRADEFS_OUTDIR)\\glibmm_generate_extra_defs.def -out:$@ $(EXTRADEFS_OUTDIR)\\generate_extra_defs.obj

\t@-if exist $@.manifest mt /manifest $@.manifest /outputresource:$@;2

$(CFG)\\$(PLAT)\\generate_defs_glib.exe: ..\\tools\\extra_defs_gen\\generate_defs_glib.cc $(EXTRADEFS_LIB) $(GLIBMM_LIB)
\t@if not exist $(EXTRADEFS_OUTDIR) $(MAKE) -f Makefile.vc CFG=$(CFG) $(EXTRADEFS_OUTDIR)
\t$(CXX) $(EXTRADEFS_CFLAGS) $(CFLAGS_NOGL) /Fo$(EXTRADEFS_OUTDIR)\\ ..\\tools\\extra_defs_gen\\generate_defs_glib.cc /link $(LDFLAGS) $(GOBJECT_LIBS) $(LIBSIGC_LIB) $(EXTRADEFS_LIB) /out:$@

$(CFG)\\$(PLAT)\\generate_defs_gio.exe: ..\\tools\\extra_defs_gen\\generate_defs_gio.cc $(EXTRADEFS_LIB) $(GIOMM_LIB)
\t@if not exist $(EXTRADEFS_OUTDIR) $(MAKE) -f Makefile.vc CFG=$(CFG) $(EXTRADEFS_OUTDIR)
\t$(CXX) $(EXTRADEFS_CFLAGS) $(CFLAGS_NOGL) /Fo$(EXTRADEFS_OUTDIR)\\ ..\\tools\\extra_defs_gen\\generate_defs_gio.cc /link $(LDFLAGS) $(GIO_LIBS) $(LIBSIGC_LIB) $(EXTRADEFS_LIB) /out:$@

clean:""")
replace_in_file(MSVC_DIR / "build-rules-msvc.mak",
    "\t@-del /f /q vc$(PDBVER)0.pdb",
    """\
\t@-del /f /q vc$(PDBVER)0.pdb
\t@-if exist $(EXTRADEFS_OUTDIR) del /f /q $(EXTRADEFS_OUTDIR)\\*.obj
\t@-if exist $(EXTRADEFS_OUTDIR) rd $(EXTRADEFS_OUTDIR)""")

replace_in_file(MSVC_DIR / "install.mak",
    '\t@copy ".\\giomm\\giommconfig.h" "$(PREFIX)\\lib\\giomm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)\\include\\"',
    """\
\t@copy ".\\giomm\\giommconfig.h" "$(PREFIX)\\lib\\giomm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)\\include\\"
\t@if not exist "$(PREFIX)\\include\\glibmm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)\\glibmm_generate_extra_defs\\" mkdir "$(PREFIX)\\include\\glibmm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)\\glibmm_generate_extra_defs"
\t@copy /b $(CFG)\\$(PLAT)\\$(EXTRADEFS_LIBNAME).dll $(PREFIX)\\bin
\t@copy /b $(CFG)\\$(PLAT)\\$(EXTRADEFS_LIBNAME).lib $(PREFIX)\\lib
\t@copy ..\\tools\\extra_defs_gen\\generate_extra_defs.h "$(PREFIX)\\include\\glibmm-$(GLIBMM_MAJOR_VERSION).$(GLIBMM_MINOR_VERSION)\\glibmm_generate_extra_defs\\" """)

for cfg in ("release", "debug"):
    install_prefix = VCPKG_ROOT / ("debug" if cfg == "debug" else "")
    base_cmd = f'"{vcvarsall}" x64 && nmake /f Makefile.vc CFG={cfg}'
    subprocess.run(f'{base_cmd} PREFIX={VCPKG_ROOT}',         cwd=MSVC_DIR, shell=True, check=True)
    subprocess.run(f'{base_cmd} PREFIX={install_prefix} install', cwd=MSVC_DIR, shell=True, check=True)

def create_glibmm_pc_files() -> None:
    for cfg, inc_dir in (("debug", "../include"), ("", "include")):
        pc_dir = (VCPKG_ROOT / "debug" if cfg else VCPKG_ROOT) / "lib/pkgconfig"
        pc_dir.mkdir(parents=True, exist_ok=True)

        for name, desc, extra in (("glibmm", "GLib", ""), ("giomm", "GIO", " gio-2.0")):
            (pc_dir / f"{name}-2.4.pc").write_text(
                f'prefix=${{pcfiledir}}/../..\n'
                f'libdir=${{prefix}}/lib\n'
                f'includedir=${{prefix}}/{inc_dir}\n\n'
                f'Name: {name}\n'
                f'Description: C++ wrapper for {desc}\n'
                f'Version: 2.62.0\n'
                f'Requires: glib-2.0 gobject-2.0{extra} sigc++-2.0\n'
                f'Libs: -L${{libdir}} -l{name}-2.4\n'
                f'Cflags: -I${{includedir}}/{name}-2.4 -I${{libdir}}/{name}-2.4/include\n'
            )

        (pc_dir / "aubio.pc").write_text(
            f'prefix=${{pcfiledir}}/../..\n'
            f'includedir=${{prefix}}/{inc_dir}\n'
            f'libdir=${{prefix}}/lib\n\n'
            f'Name: aubio\n'
            f'Description: aubio library\n'
            f'Version: 0.4.9\n'
            f'Libs: "-L${{libdir}}" -laubio\n'
            f'Cflags: "-I${{includedir}}"\n'
        )

create_glibmm_pc_files()

build_with_meson("cairomm", DEPS_DIR / "cairomm-1.14.5")

replace_in_file(
    PANGOMM_DIR / "tools" / "extra_defs_gen" / "meson.build",
    "'glibmm_generate_extra_defs@0@-2.4'.format(msvc14x_toolset_ver)",
"'glibmm_generate_extra_defs-2.4',\n  dirs: [meson.source_root() / (get_option('buildtype') == 'debug' ? '../../vcpkg_installed/x64-windows/debug/lib' : '../../vcpkg_installed/x64-windows/lib')]",
)

replace_in_file(
    PANGOMM_DIR / "untracked" / "pango" / "pangomm" / "attrlist.cc",
    "#include <glibmm.h>",
    "#include <glibmm.h>\n#include <pango/pango-markup.h>",
)

build_with_meson("pangomm", DEPS_DIR / "pangomm-2.42.2")

for cfg in ("", "debug/"):
    jack_pc = VCPKG_ROOT / f"{cfg}lib/pkgconfig/jack.pc"
    if jack_pc.read_text().splitlines()[9] != "Version: 1.9.22":
        replace_in_file(jack_pc, jack_pc.read_text().splitlines()[9], "Version: 1.9.22")