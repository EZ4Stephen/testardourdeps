vcpkg_download_distfile(ARCHIVE
    URLS "https://download.gnome.org/sources/glibmm/2.62/glibmm-2.62.0.tar.xz"
    FILENAME "glibmm-2.62.0.tar.xz"
    SHA512 f26fca5724c17d915480556b6918ae6e4999c14a25e7623cda3d37a59d6965310fc2b2d8a8500a849f1d0f00fd2d326eeddc690207846d38a13ae695ad0805de
)
vcpkg_extract_source_archive(SOURCE_PATH ARCHIVE "${ARCHIVE}")

file(COPY "${CURRENT_PORT_DIR}/msvc_recommended_pragmas.h" DESTINATION "${SOURCE_PATH}/MSVC_NMake")

# Patch library names and paths
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/config-msvc.mak" "glibmm-vc\$(PDBVER)0\$(DEBUG_SUFFIX)-\$(GLIBMM_MAJOR_VERSION)_\$(GLIBMM_MINOR_VERSION)" "glibmm-2.4\$(DEBUG_SUFFIX)")
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/config-msvc.mak" "giomm-vc\$(PDBVER)0\$(DEBUG_SUFFIX)-\$(GLIBMM_MAJOR_VERSION)_\$(GLIBMM_MINOR_VERSION)" "giomm-2.4\$(DEBUG_SUFFIX)")
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/config-msvc.mak" "sigc-vc\$(PDBVER)0\$(DEBUG_SUFFIX)-\$(LIBSIGC_MAJOR_VERSION)_\$(LIBSIGC_MINOR_VERSION)" "sigc-2.0")
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/config-msvc.mak" "/I$(PREFIX)\\" "/I${CURRENT_INSTALLED_DIR}\\")
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/detectenv-msvc.mak" "/libpath:$(PREFIX)\\" "/libpath:${CURRENT_INSTALLED_DIR}\\")
file(APPEND "${SOURCE_PATH}/MSVC_NMake/config-msvc.mak" [[

EXTRA_DEFS_LIBNAME = glibmm_generate_extra_defs-2.4$(DEBUG_SUFFIX)
EXTRA_DEFS_DLL = $(CFG)\$(PLAT)\$(EXTRA_DEFS_LIBNAME).dll
EXTRA_DEFS_LIB = $(CFG)\$(PLAT)\$(EXTRA_DEFS_LIBNAME).lib
]])

# Fix gendef build and filter problematic symbol
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/build-rules-msvc.mak" 
    "$(CXX) $(GLIBMM_BASE_CFLAGS) $(CFLAGS) /Fo$(CFG)\\$(PLAT)\\gendef"
    "$(CXX) $(GLIBMM_BASE_CFLAGS) $(GLIBMM_EXTRA_INCLUDES) $(CFLAGS) /Fo$(CFG)\\$(PLAT)\\gendef")
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/gendef/gendef.cc"
    "strchr(s, '@') == 0) // this is a C export type"
    "strchr(s, '@') == 0 && strcmp(s + 1, \"Avx2WmemEnabledWeakValue\") != 0) // this is a C export type")

# Add glibmm_generate_extra_defs build rules
file(APPEND "${SOURCE_PATH}/MSVC_NMake/build-rules-msvc.mak" [[

$(CFG)\$(PLAT)\glibmm_generate_extra_defs:
	@if not exist $(CFG)\$(PLAT)\glibmm_generate_extra_defs mkdir $(CFG)\$(PLAT)\glibmm_generate_extra_defs

$(CFG)\$(PLAT)\glibmm_generate_extra_defs\glibmm_generate_extra_defs-2.4.def: $(CFG)\$(PLAT)\gendef.exe $(CFG)\$(PLAT)\glibmm_generate_extra_defs $(CFG)\$(PLAT)\generate_extra_defs.obj
	$(CFG)\$(PLAT)\gendef.exe $@ glibmm_generate_extra_defs-2.4 $(CFG)\$(PLAT)\generate_extra_defs.obj

$(EXTRA_DEFS_LIB): $(EXTRA_DEFS_DLL)

$(EXTRA_DEFS_DLL): $(CFG)\$(PLAT)\glibmm_generate_extra_defs\glibmm_generate_extra_defs-2.4.def $(CFG)\$(PLAT)\generate_extra_defs.obj
	link /DLL $(LDFLAGS_NOLTCG) $(GLIBMM_LIB) $(GOBJECT_LIBS) /implib:$(EXTRA_DEFS_LIB) /def:$(CFG)\$(PLAT)\glibmm_generate_extra_defs\glibmm_generate_extra_defs-2.4.def /out:$(EXTRA_DEFS_DLL) $(CFG)\$(PLAT)\generate_extra_defs.obj

$(CFG)\$(PLAT)\generate_extra_defs.obj: ..\tools\extra_defs_gen\generate_extra_defs.cc
	$(CXX) $(LIBGLIBMM_CFLAGS) $(CFLAGS_NOGL) /c /Fo$@ $**
]])
vcpkg_replace_string("${SOURCE_PATH}/MSVC_NMake/Makefile.vc" 
    "all: $(GIOMM_LIB) $(glibmm_ex) $(giomm_ex) all-build-info"
    "all: $(GIOMM_LIB) $(EXTRA_DEFS_LIB) $(glibmm_ex) $(giomm_ex) all-build-info")

# Replace install.mak (fix path quoting issues and add extra_defs)
file(WRITE "${SOURCE_PATH}/MSVC_NMake/install.mak" [[
install: all
	@if not exist "$(PREFIX)\bin" mkdir "$(PREFIX)\bin"
	@if not exist "$(PREFIX)\lib\glibmm-2.4\include" mkdir "$(PREFIX)\lib\glibmm-2.4\include"
	@if not exist "$(PREFIX)\include\glibmm-2.4\glibmm\private" mkdir "$(PREFIX)\include\glibmm-2.4\glibmm\private"
	@if not exist "$(PREFIX)\include\glibmm-2.4\glibmm_generate_extra_defs" mkdir "$(PREFIX)\include\glibmm-2.4\glibmm_generate_extra_defs"
	@if not exist "$(PREFIX)\lib\giomm-2.4\include" mkdir "$(PREFIX)\lib\giomm-2.4\include"
	@if not exist "$(PREFIX)\include\giomm-2.4\giomm\private" mkdir "$(PREFIX)\include\giomm-2.4\giomm\private"
	@copy /b $(CFG)\$(PLAT)\$(GLIBMM_LIBNAME).dll "$(PREFIX)\bin"
	@copy /b $(CFG)\$(PLAT)\$(GLIBMM_LIBNAME).pdb "$(PREFIX)\bin"
	@copy /b $(CFG)\$(PLAT)\$(GLIBMM_LIBNAME).lib "$(PREFIX)\lib"
	@copy /b $(CFG)\$(PLAT)\$(GIOMM_LIBNAME).dll "$(PREFIX)\bin"
	@copy /b $(CFG)\$(PLAT)\$(GIOMM_LIBNAME).pdb "$(PREFIX)\bin"
	@copy /b $(CFG)\$(PLAT)\$(GIOMM_LIBNAME).lib "$(PREFIX)\lib"
	@copy /b $(CFG)\$(PLAT)\$(EXTRA_DEFS_LIBNAME).dll "$(PREFIX)\bin"
	@copy /b $(CFG)\$(PLAT)\$(EXTRA_DEFS_LIBNAME).pdb "$(PREFIX)\bin"
	@copy /b $(CFG)\$(PLAT)\$(EXTRA_DEFS_LIBNAME).lib "$(PREFIX)\lib"
	@copy ..\glib\glibmm.h "$(PREFIX)\include\glibmm-2.4\"
	@copy ..\gio\giomm.h "$(PREFIX)\include\giomm-2.4\"
	@copy ..\tools\extra_defs_gen\generate_extra_defs.h "$(PREFIX)\include\glibmm-2.4\glibmm_generate_extra_defs\"
	@for %h in ($(glibmm_files_all_h)) do @copy ..\glib\glibmm\%h "$(PREFIX)\include\glibmm-2.4\glibmm\%h"
	@for %h in ($(glibmm_generated_private_headers)) do @copy ..\glib\glibmm\private\%h "$(PREFIX)\include\glibmm-2.4\glibmm\private\%h"
	@for %h in ($(glibmm_files_extra_ph_int)) do @copy ..\glib\glibmm\%h "$(PREFIX)\include\glibmm-2.4\glibmm\%h"
	@for %h in ($(giomm_generated_headers) $(giomm_files_extra_h)) do @copy ..\gio\giomm\%h "$(PREFIX)\include\giomm-2.4\giomm\%h"
	@for %h in ($(giomm_generated_private_headers)) do @copy ..\gio\giomm\private\%h "$(PREFIX)\include\giomm-2.4\giomm\private\%h"
	@copy .\glibmm\glibmmconfig.h "$(PREFIX)\lib\glibmm-2.4\include\"
	@copy .\giomm\giommconfig.h "$(PREFIX)\lib\giomm-2.4\include\"
]])

# Build
if(VCPKG_TARGET_ARCHITECTURE MATCHES "x86")
    set(PLAT Win32)
else()
    set(PLAT x64)
endif()
vcpkg_install_nmake(SOURCE_PATH "${SOURCE_PATH}" PROJECT_SUBPATH "MSVC_NMake" PROJECT_NAME Makefile.vc
    OPTIONS "PREFIX=${CURRENT_PACKAGES_DIR}" "PLAT=${PLAT}"
    OPTIONS_DEBUG "CFG=debug" OPTIONS_RELEASE "CFG=release")

# Organize debug files
file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/debug/bin" "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm-2.4/include" "${CURRENT_PACKAGES_DIR}/debug/lib/giomm-2.4/include")
foreach(lib glibmm giomm glibmm_generate_extra_defs)
    file(RENAME "${CURRENT_PACKAGES_DIR}/bin/${lib}-2.4-d.dll" "${CURRENT_PACKAGES_DIR}/debug/bin/${lib}-2.4-d.dll")
    file(RENAME "${CURRENT_PACKAGES_DIR}/bin/${lib}-2.4-d.pdb" "${CURRENT_PACKAGES_DIR}/debug/bin/${lib}-2.4-d.pdb")
    file(RENAME "${CURRENT_PACKAGES_DIR}/lib/${lib}-2.4-d.lib" "${CURRENT_PACKAGES_DIR}/debug/lib/${lib}-2.4-d.lib")
endforeach()
file(RENAME "${CURRENT_PACKAGES_DIR}/lib/glibmm-2.4/include/glibmmconfig.h" "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm-2.4/include/glibmmconfig.h")
file(RENAME "${CURRENT_PACKAGES_DIR}/lib/giomm-2.4/include/giommconfig.h" "${CURRENT_PACKAGES_DIR}/debug/lib/giomm-2.4/include/giommconfig.h")

# Copy config files to release lib as well (needed for meson build)
file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/lib/glibmm-2.4/include" "${CURRENT_PACKAGES_DIR}/lib/giomm-2.4/include")
file(COPY "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm-2.4/include/glibmmconfig.h"
     DESTINATION "${CURRENT_PACKAGES_DIR}/lib/glibmm-2.4/include/")
file(COPY "${CURRENT_PACKAGES_DIR}/debug/lib/giomm-2.4/include/giommconfig.h"
     DESTINATION "${CURRENT_PACKAGES_DIR}/lib/giomm-2.4/include/")

# Copy glibmm_generate_extra_defs to tools directory for meson ADDITIONAL_BINARIES
file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/tools/glibmm")
file(COPY "${CURRENT_PACKAGES_DIR}/bin/glibmm_generate_extra_defs-2.4.dll"
     DESTINATION "${CURRENT_PACKAGES_DIR}/tools/glibmm/")
file(COPY "${CURRENT_PACKAGES_DIR}/debug/bin/glibmm_generate_extra_defs-2.4-d.dll"
     DESTINATION "${CURRENT_PACKAGES_DIR}/tools/glibmm/")

# Copy debug lib without -d suffix for meson find_library compatibility
file(COPY "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm_generate_extra_defs-2.4-d.lib"
     DESTINATION "${CURRENT_PACKAGES_DIR}/debug/lib/")
file(RENAME "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm_generate_extra_defs-2.4-d.lib"
     "${CURRENT_PACKAGES_DIR}/debug/lib/glibmm_generate_extra_defs-2.4.lib")

# Generate pkgconfig files
file(MAKE_DIRECTORY "${CURRENT_PACKAGES_DIR}/lib/pkgconfig" "${CURRENT_PACKAGES_DIR}/debug/lib/pkgconfig")
foreach(lib glibmm giomm glibmm_generate_extra_defs)
    if(EXISTS "${CURRENT_PORT_DIR}/${lib}-2.4.pc.in")
        file(INSTALL "${CURRENT_PORT_DIR}/${lib}-2.4.pc.in" DESTINATION "${CURRENT_PACKAGES_DIR}/lib/pkgconfig" RENAME "${lib}-2.4.pc")
        file(READ "${CURRENT_PORT_DIR}/${lib}-2.4.pc.in" pc)
        string(REPLACE [[prefix=${pcfiledir}/../..]] [[prefix=${pcfiledir}/../../..]] pc "${pc}")
        string(REPLACE [[libdir=${exec_prefix}/lib]] [[libdir=${prefix}/lib]] pc "${pc}")
        string(REPLACE "-l${lib}-2.4" "-l${lib}-2.4-d" pc "${pc}")
        file(WRITE "${CURRENT_PACKAGES_DIR}/debug/lib/pkgconfig/${lib}-2.4.pc" "${pc}")
    endif()
endforeach()

vcpkg_copy_pdbs()
vcpkg_fixup_pkgconfig()
file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/share" "${CURRENT_PACKAGES_DIR}/lib/giomm-2.4/include" "${CURRENT_PACKAGES_DIR}/lib/glibmm-2.4/include")
vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/COPYING")
