from pathlib import Path
import subprocess
import sys
import shutil

_script_dir = Path(__file__).resolve().parent
_vcpkg_dir = _script_dir / "vcpkg"
_vcpkg_exe = _vcpkg_dir / "vcpkg.exe"
_overlay_dir = _vcpkg_dir / "overlay_ports"

def _get_installed():
    return next((_vcpkg_dir / "installed").glob("*/include")).parent

_ports = {
    "libsigcpp": {
        "vcpkg.json": """\
{
  "name": "libsigcpp",
  "version": "2.12.1",
  "description": "Typesafe callback framework for C++",
  "homepage": "https://libsigcplusplus.github.io/libsigcplusplus/",
  "license": "LGPL-3.0-or-later",
  "dependencies": [
    {
      "name": "vcpkg-tool-meson",
      "host": true
    }
  ]
}
""",
        "portfile.cmake": """\
vcpkg_download_distfile(ARCHIVE
    URLS "https://download.gnome.org/sources/libsigc++/2.12/libsigc++-2.12.1.tar.xz"
    FILENAME "libsigc++-2.12.1.tar.xz"
    SHA512 5e5c920807952c732a9acb139f707fdf556786133c18bc8842130803f864ba1f260e1d4a51be0a9892c2228bcfdf129a9a2ce91e3d20077870431a53a87a9f2a
)

vcpkg_extract_source_archive(SOURCE_PATH ARCHIVE "${ARCHIVE}")

vcpkg_configure_meson(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -Dbuild-examples=false
        -Dbuild-documentation=false
)

vcpkg_install_meson()

vcpkg_copy_pdbs()

vcpkg_fixup_pkgconfig()

file(GLOB config_files "${CURRENT_PACKAGES_DIR}/lib/sigc++-2.0/include/*.h")
foreach(file IN LISTS config_files)
    get_filename_component(filename "${file}" NAME)
    file(RENAME "${file}" "${CURRENT_PACKAGES_DIR}/include/sigc++-2.0/${filename}")
endforeach()

file(REMOVE_RECURSE
    "${CURRENT_PACKAGES_DIR}/debug/lib/sigc++-2.0"
    "${CURRENT_PACKAGES_DIR}/lib/sigc++-2.0"
    "${CURRENT_PACKAGES_DIR}/debug/include"
)

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/COPYING")
""",
    },
    "glibmm": {
        "vcpkg.json": """\
{
  "name": "glibmm",
  "version": "2.66.8",
  "description": "This is glibmm, a C++ API for parts of glib that are useful for C++.",
  "homepage": "https://www.gtkmm.org.",
  "license": "LGPL-2.1-or-later",
  "supports": "!uwp & !xbox & !(windows & !mingw & static)",
  "dependencies": [
    "gettext",
    "glib",
    "libffi",
    "libiconv",
    "libsigcpp",
    "pcre",
    {
      "name": "vcpkg-tool-meson",
      "host": true
    },
    "zlib"
  ]
}
""",
        "portfile.cmake": """\
string(REGEX MATCH "^([0-9]*[.][0-9]*)" GLIBMM_MAJOR_MINOR "${VERSION}")
vcpkg_download_distfile(GLIBMM_ARCHIVE
    URLS "https://download.gnome.org/sources/glibmm/${GLIBMM_MAJOR_MINOR}/glibmm-${VERSION}.tar.xz"
    FILENAME "glibmm-${VERSION}.tar.xz"
    SHA512 4ebf203324d3ee95c47012915efb39d4dc59eb7a6f337e7b8c7c0b3589574b07967974363931b0d4159618f88178b04715b2c359c3dc3f67a7781bfac0d9f277
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE "${GLIBMM_ARCHIVE}"
)

vcpkg_configure_meson(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -Dbuild-examples=false
        -Dmsvc14x-parallel-installable=false
)

vcpkg_install_meson()
vcpkg_copy_pdbs()

file(REMOVE_RECURSE
    "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm-2.4/proc"
    "${CURRENT_PACKAGES_DIR}/lib/glibmm-2.4/proc"
)

vcpkg_fixup_pkgconfig()

file(INSTALL "${SOURCE_PATH}/COPYING" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME copyright)
file(INSTALL "${SOURCE_PATH}/README.md" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}" RENAME readme.txt)
file(INSTALL "${SOURCE_PATH}/README.win32.md" DESTINATION "${CURRENT_PACKAGES_DIR}/share/${PORT}")
""",
    },
    "cairomm": {
        "vcpkg.json": """\
{
  "name": "cairomm",
  "version": "1.14.5",
  "description": "A C++ wrapper for the cairo graphics library",
  "homepage": "https://www.cairographics.org",
  "license": "LGPL-2.0-only",
  "supports": "!xbox",
  "dependencies": [
    "cairo",
    "libsigcpp",
    {
      "name": "vcpkg-tool-meson",
      "host": true
    }
  ]
}
""",
        "portfile.cmake": """\
vcpkg_download_distfile(ARCHIVE
    URLS "https://cairographics.org/releases/cairomm-1.14.5.tar.xz"
    FILENAME "cairomm-1.14.5.tar.xz"
    SHA512 19e5f84f6167c1641b27545c3af4e780b6a072513322adc6296577e2d0ebcffe933afd15c32117a203394e9f5f28734820aaf1802dfdeb35ff2a657f140570b0
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE "${ARCHIVE}"
)

vcpkg_replace_string("${SOURCE_PATH}/meson.build" "dependency('sigc++-2.0', version: sigcxx_req)" "dependency('sigc++-2.0')")
vcpkg_replace_string("${SOURCE_PATH}/meson.build" "'sigc++-2.0', sigcxx_req" "'sigc++-2.0'")

vcpkg_configure_meson(
    SOURCE_PATH "${SOURCE_PATH}"
    DEPENDENCIES libsigcpp cairo
    OPTIONS
        -Dbuild-examples=false
        -Dmsvc14x-parallel-installable=false
        -Dbuild-tests=false
)

vcpkg_install_meson()
vcpkg_fixup_pkgconfig()
vcpkg_copy_pdbs()

file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include")

if(VCPKG_LIBRARY_LINKAGE STREQUAL "static")
    vcpkg_replace_string("${CURRENT_PACKAGES_DIR}/include/cairommconfig.h" "# define CAIROMM_DLL 1" "# undef CAIROMM_DLL\\n#define CAIROMM_STATIC_LIB 1")
endif()

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/COPYING")
""",
    },
    "pangomm": {
        "vcpkg.json": """\
{
  "name": "pangomm",
  "version": "2.42.2",
  "description": "pangomm is the official C++ interface for the Pango font layout library.",
  "homepage": "https://gitlab.gnome.org/GNOME/pangomm",
  "license": "LGPL-2.1-or-later",
  "supports": "!xbox",
  "dependencies": [
    "cairo",
    "cairomm",
    "fontconfig",
    "freetype",
    "gettext",
    "glib",
    {
      "name": "glib",
      "host": true
    },
    "glibmm",
    "harfbuzz",
    "pango",
    {
      "name": "vcpkg-tool-meson",
      "host": true
    }
  ]
}
""",
        "portfile.cmake": """\
vcpkg_download_distfile(ARCHIVE
    URLS "https://download.gnome.org/sources/pangomm/2.42/pangomm-2.42.2.tar.xz"
    FILENAME "pangomm-2.42.2.tar.xz"
    SHA512 5e4826d64c0178527b4df73e901d2fdf5661d41777e189f5e2d4b26577e42689efaccf5a28502246c6b3926571ccd5876cb23d33267b44ace7ee164322c14667
)

vcpkg_extract_source_archive(
    SOURCE_PATH
    ARCHIVE ${ARCHIVE}
)

vcpkg_replace_string("${SOURCE_PATH}/pango/src/attrlist.ccg" 
    "// -*- c++ -*-"
    "// -*- c++ -*-\\n#include <pango/pango-markup.h>")

vcpkg_configure_meson(
    SOURCE_PATH "${SOURCE_PATH}"
    OPTIONS
        -Dmsvc14x-parallel-installable=false
        -Dbuild-documentation=false
    ADDITIONAL_BINARIES
        glib-genmarshal='${CURRENT_HOST_INSTALLED_DIR}/tools/glib/glib-genmarshal'
        glib-mkenums='${CURRENT_HOST_INSTALLED_DIR}/tools/glib/glib-mkenums'
        glibmm_generate_extra_defs-2.4='${CURRENT_HOST_INSTALLED_DIR}/tools/glibmm/glibmm_generate_extra_defs-2.4'
)

file(GLOB_RECURSE attrlist_cc 
    "${SOURCE_PATH}/untracked/pango/pangomm/attrlist.cc")
foreach(file ${attrlist_cc})
    vcpkg_replace_string("${file}"
        "// Generated by gmmproc"
        "// Generated by gmmproc\\n#include <pango/pango-markup.h>")
endforeach()

vcpkg_install_meson()
vcpkg_fixup_pkgconfig()
vcpkg_copy_pdbs()

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/COPYING")
""",
    },
}

_aubio_pc_content = """\
prefix=${{pcfiledir}}/../..
includedir=${{prefix}}/{include_path}
libdir=${{prefix}}/lib

Name: aubio
Description: aubio library
Version: 0.4.9
Libs: "-L${{libdir}}" -laubio
Cflags: "-I${{includedir}}"
"""

def run(cmd, cwd=None):
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"  ERROR: command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def setup_vcpkg():
    if not _vcpkg_dir.exists():
        run(["git", "clone", "https://github.com/microsoft/vcpkg.git"])

    if not _vcpkg_exe.exists():
        run(["bootstrap-vcpkg.bat", "-disableMetrics"], cwd=_vcpkg_dir)

def create_ports():
    shutil.rmtree(_overlay_dir, ignore_errors=True)
    for name, files in _ports.items():
        pkg_dir = _overlay_dir / name
        pkg_dir.mkdir(parents=True)
        for fn, content in files.items():
            (pkg_dir / fn).write_text(content)

def install_deps(*packages):
    if not _vcpkg_exe.exists():
        setup_vcpkg()
    create_ports()
    run([str(_vcpkg_exe), f"--overlay-ports={_overlay_dir}", "install", *packages], cwd=_vcpkg_dir)

def add_aubio_pc(): # Assumes there may be a future where .pc files are made and installed for aubio.
    installed = _get_installed()
    for pc_dir, include_path in zip(
        [installed / "lib/pkgconfig", installed / "debug/lib/pkgconfig"],
        ["include", "../include"],
    ):
        aubio_pc = pc_dir / "aubio.pc"
        if not aubio_pc.exists():
            aubio_pc.parent.mkdir(parents=True, exist_ok=True)
            aubio_pc.write_text(_aubio_pc_content.format(include_path=include_path))

def fix_jack_pc():
    installed = _get_installed()
    for pc_dir in [installed / "lib/pkgconfig", installed / "debug/lib/pkgconfig"]:
        for pc in pc_dir.glob("jack*.pc"):
            text = pc.read_text()
            if "Version: 1.9.22" in text:
                continue
            if "Version: 1.9" in text:
                text = text.replace("Version: 1.9", "Version: 1.9.22", 1)
                pc.write_text(text)

def rename_vamp_hostsdk_lib():
    installed = _get_installed()
    for sub in ["lib", "debug/lib"]:
        src = installed / sub / "VampHostSDK.lib"
        dst = installed / sub / "vamp-hostsdk.lib"
        if src.exists() and not dst.exists():
            src.rename(dst)

def rename_vamp_pluginsdk_lib():
    installed = _get_installed()
    for sub in ["lib", "debug/lib"]:
        src = installed / sub / "VampPluginSDK.lib"
        dst = installed / sub / "vamp-sdk.lib"
        if src.exists() and not dst.exists():
            src.rename(dst)

def fix_vamp_pc():
    installed = _get_installed()
    pkgconfig_dirs = (
        installed / "lib/pkgconfig",
        installed / "debug/lib/pkgconfig",
    )
    for pc_dir in pkgconfig_dirs:
        pc = pc_dir / "vamp-hostsdk.pc"
        if pc.exists():
            text = pc.read_text()
            text = text.replace("-ldl", "")
            pc.write_text(text)

def rename_liblo_lib():
    installed = _get_installed()
    for sub_dir in [installed / "lib", installed / "debug/lib"]:
        src = sub_dir / "liblo.lib"
        dst = sub_dir / "lo.lib"
        if src.exists() and not dst.exists():
            src.rename(dst)

if __name__ == "__main__":
    install_deps(
        "boost-ptr-container", "glib", "libsndfile", "curl", "libarchive",
        "liblo", "taglib", "vamp-sdk", "libusb", "rubberband",
        "jack2", "pthreads", "fftw3[threads]", "aubio[core]", "libpng",
        "pango", "lv2", "libxml2", "cppunit", "libwebsockets",
        "portaudio[asio]", "libsamplerate", "serd", "sord", "sratom",
        "lilv", "boost-uuid", "boost-tokenizer", "boost-multiprecision",
        "boost-pool", "boost-algorithm", "boost-property-tree",
        "boost-multi-array", "getopt", "libjpeg-turbo",
        "readline", "libsigcpp", "glibmm", "cairomm", "pangomm",
    )

    add_aubio_pc()
    fix_jack_pc()
    rename_vamp_hostsdk_lib()
    rename_vamp_pluginsdk_lib()
    fix_vamp_pc()
    rename_liblo_lib()