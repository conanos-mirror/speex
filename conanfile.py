from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild
from conanos.build import config_scheme
import shutil
import os

class SpeexConan(ConanFile):
    name = "speex"
    version = "1.2.0"
    description = "A Free Codec For Free Speech"
    url = "https://github.com/conanos/speex"
    homepage = "https://www.speex.org/"
    license = "BSD_like"
    patch = "sln-subproject-and-sourcefile-not-existing.patch"
    exports = ["COPYING", patch]
    generators = "gcc","visual_studio"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "shared": [True, False],
        'fPIC': [True, False]
    }
    default_options = { 'shared': True, 'fPIC': True }
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"
    
    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx

        config_scheme(self)

    def requirements(self):
        self.requires.add("libogg/1.3.3@conanos/stable")

    def source(self):
        url_ = "https://ftp.osuosl.org/pub/xiph/releases/speex/speex-{version}.tar.gz".format(version=self.version)
        tools.get(url_)
        if self.settings.os == 'Windows':
            tools.patch(patch_file=self.patch)
        extracted_dir = "%s-%s"%(self.name, self.version)
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        if self.settings.os == 'Linux':
            prefix = os.path.join(self.build_folder, self._source_subfolder, "install")
            with tools.chdir(self._source_subfolder):
                autotools = AutoToolsBuildEnvironment(self)
                _args = ["--prefix=%s"%(prefix), "--disable-maintainer-mode", "--disable-silent-rules"]
                if self.options.shared:
                    _args.extend(['--enable-shared=yes','--enable-static=no'])
                else:
                    _args.extend(['--enable-shared=no','--enable-static=yes'])
                autotools.configure(args=_args, pkg_config_paths='%s/lib/pkgconfig'%(self.deps_cpp_info["libogg"].rootpath))
                autotools.make()
                autotools.install()

        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"win32", "VS2008")):
                msbuild = MSBuild(self)
                build_type = str(self.settings.build_type) + ("_Dynamic" if self.options.shared else "")
                msbuild.build("libspeex.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'}, build_type=build_type)

    def package(self):
        if self.settings.os == 'Linux':
            self.copy("*", dst=self.package_folder, src=os.path.join(self.build_folder,self._source_subfolder, "install"))

        if self.settings.os == 'Windows':
            build_type = str(self.settings.build_type) + ("_Dynamic" if self.options.shared else "")
            self.copy("*.h", dst=os.path.join(self.package_folder,"include","speex"), src=os.path.join(self.build_folder,self._source_subfolder,"include","speex"),keep_path=False)
            self.copy("*.exe", dst=os.path.join(self.package_folder,"bin"), src=os.path.join(self.build_folder,self._source_subfolder,"bin"),keep_path=False)
            self.copy("*.exe", dst=os.path.join(self.package_folder,"bin"), src=os.path.join(self.build_folder,self._source_subfolder,"win32", "VS2008",str(self.settings.build_type)))
            self.copy("*.lib", dst=os.path.join(self.package_folder,"lib"), src=os.path.join(self.build_folder,self._source_subfolder,"win32", "VS2008",build_type))
            self.copy("*.dll", dst=os.path.join(self.package_folder,"bin"), src=os.path.join(self.build_folder,self._source_subfolder,"win32", "VS2008",build_type))

            shutil.copyfile(os.path.join(self.build_folder,self._source_subfolder,"include","speex","speex_config_types.h.in"),
                            os.path.join(self.package_folder,"include","speex", "speex_config_types.h"))
            replacements = {
                "@INCLUDE_STDINT@"    :    "#include <stdint.h>",
                "@SIZE16@"            :    "int16_t",
                "@USIZE16@"           :    "uint16_t",
                "@SIZE32@"            :    "int32_t",
                "@USIZE32@"           :    "uint32_t",
            }
            for s, r in replacements.items():
                tools.replace_in_file(os.path.join(self.package_folder,"include","speex", "speex_config_types.h"),s,r)
            tools.mkdir(os.path.join(self.package_folder,"lib","pkgconfig"))
            shutil.copyfile(os.path.join(self.build_folder,self._source_subfolder,"speex.pc.in"),
                            os.path.join(self.package_folder,"lib","pkgconfig", "speex.pc"))
            replacements_pc = {
                "@prefix@"      : self.package_folder,
                "@exec_prefix@" : "${prefix}/bin",
                "@libdir@"      : "${prefix}/lib",
                "@includedir@"  : "${prefix}/include",
                "@SPEEX_VERSION@" : self.version,
                "@LIBM@"        : "-lm"
            }
            for s, r in replacements_pc.items():
                tools.replace_in_file(os.path.join(self.package_folder,"lib","pkgconfig", "speex.pc"),s,r)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

