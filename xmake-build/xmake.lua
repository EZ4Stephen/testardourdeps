set_policy("package.sync_requires_to_deps", true)
if is_mode("debug") then
    add_requireconfs("**", {configs = {debug = true, shared = true}, system = false, build = true})
else
    add_requireconfs("**", {configs = {shared = true}, system = false, build = true})
end

add_requires("libcurl")
add_requires("boost")
add_requires("libsndfile")
add_requires("libarchive")
add_requires("liblo")
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
add_requires("lilv")
add_requires("libjpeg-turbo")
add_requires("lrdf")
add_requires("pangomm <2.48.0")
if is_plat("windows") then
    add_requires("pthreads4w")
end

target("collect_deps")
    set_kind("phony")
    after_load(function()
        import("core.project.config")
        import("core.cache.localcache")

        local dest = path.join(os.projectdir(), config.mode() or "release")
        local subdirs = {"include", "lib"}
        if is_plat("windows") then table.insert(subdirs, "bin") end

        local skip = {python = true, cmake = true, ninja = true, meson = true, gperf = true}
        local function pkgname(installdir)
            local parts = path.split(installdir)
            return parts[#parts - 2]
        end

        local refs = localcache.cache("references")
        local pkgs = refs:get("packages") or {}

        os.mkdir(dest)
        for _, installdir in ipairs(pkgs) do
            if not skip[pkgname(installdir)] then
                for _, sub in ipairs(subdirs) do
                    local src = path.join(installdir, sub)
                    if sub == "lib" then
                        for _, fp in ipairs(os.files(path.join(src, "**"))) do
                            local tgt = path.join(dest, sub, path.relative(fp, src))
                            os.mkdir(path.directory(tgt))
                            os.cp(fp, tgt)
                        end
                    elseif os.isdir(src) then
                        os.cp(src, dest)
                    end
                end
            end
        end
    end)
