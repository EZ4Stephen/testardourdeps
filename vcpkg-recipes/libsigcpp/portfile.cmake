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
