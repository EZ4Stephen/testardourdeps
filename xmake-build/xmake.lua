set_policy("package.sync_requires_to_deps", true)
add_requireconfs("**", {configs = {shared = true}, system = false})

if is_mode("debug") then
    add_requireconfs("**", {configs = {debug = true}})
end

if is_subhost("windows") then
    add_requires("pkgconf")
else
    add_requires("pkg-config")
end

-- Library deps
add_requires("libcurl")
add_requires("boost")
add_requires("libogg")
add_requires("libflac")
add_requires("libopus")
add_requires("libvorbis")
add_requires("libsndfile")
add_requires("zlib")
add_requires("bzip2")
add_requires("lz4")
add_requires("zstd")
add_requires("openssl3")
add_requires("libarchive")
add_requires("liblo")
add_requires("utfcpp")
add_requires("taglib")
add_requires("vamp-plugin-sdk")
add_requires("libusb")
add_requires("rubberband")
add_requires("jack2")
add_requires("fftw")
add_requires("aubio")
add_requires("libxml2")
add_requires("cppunit")
add_requires("libwebsockets")
add_requires("portaudio", {configs = {asio = true}})
add_requires("libsamplerate")
add_requires("lv2")
add_requires("serd")
add_requires("zix")
add_requires("sord")
add_requires("sratom")
add_requires("lilv")
add_requires("libjpeg-turbo")
add_requires("libffi")
add_requires("libintl")
add_requires("pcre2")
add_requires("glib <2.89.2")
add_requires("fribidi")
add_requires("freetype")
add_requires("harfbuzz", {configs = {glib = true}})
add_requires("expat")
add_requires("fontconfig")
add_requires("libpng")
add_requires("pixman")
add_requires("cairo")
add_requires("pango", {build = true})
add_requires("libsigcplusplus <3.0.0")
add_requires("glibmm <2.68.0")
add_requires("cairomm <1.16.0")
add_requires("pangomm <2.48.0")
if is_plat("windows") then
    add_requires("pthreads4w")
end

target("collect_deps")
    set_kind("phony")
    after_load(function()
        import("core.project.project")
        import("core.project.config")
        local dest = path.join(os.projectdir(), config.mode() or "release")
        local subdirs = {"include", "lib"}
        if is_plat("windows") then table.insert(subdirs, "bin") end
        for _, pkg in pairs(project.required_packages()) do
            local dir = pkg:installdir()
            if dir and os.isdir(dir) then
                for _, sub in ipairs(subdirs) do
                    local src = path.join(dir, sub)
                    if os.isdir(src) then
                        for _, fp in ipairs(os.files(path.join(src, "**"))) do
                            local tgt = path.join(dest, sub, path.relative(fp, src))
                            os.mkdir(path.directory(tgt))
                            os.cp(fp, tgt)
                        end
                    end
                end
            end
        end
    end)
