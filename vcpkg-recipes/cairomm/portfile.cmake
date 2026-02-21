
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
        -Dmsvc14x-parallel-installable=false    # Use separate DLL and LIB filenames for Visual Studio 2017 and 2019
        -Dbuild-tests=false
)

vcpkg_install_meson()
vcpkg_fixup_pkgconfig()
vcpkg_copy_pdbs()

file(REMOVE_RECURSE "${CURRENT_PACKAGES_DIR}/debug/include")

if(VCPKG_LIBRARY_LINKAGE STREQUAL "static")
    vcpkg_replace_string("${CURRENT_PACKAGES_DIR}/include/cairommconfig.h" "# define CAIROMM_DLL 1" "# undef CAIROMM_DLL\n# define CAIROMM_STATIC_LIB 1")
endif()

vcpkg_install_copyright(FILE_LIST "${SOURCE_PATH}/COPYING")