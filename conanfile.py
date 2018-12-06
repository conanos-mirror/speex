from conans import ConanFile, tools, AutoToolsBuildEnvironment, MSBuild
from conanos.build import config_scheme
from shutil import copyfile
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
            with tools.chdir(self._source_subfolder):
                autotools = AutoToolsBuildEnvironment(self)
                _args = ["--prefix=%s/builddir"%(os.getcwd()), "--disable-maintainer-mode", "--disable-silent-rules"]
                if self.options.shared:
                    _args.extend(['--enable-shared=yes','--enable-static=no'])
                else:
                    _args.extend(['--enable-shared=no','--enable-static=yes'])
                autotools.configure(args=_args, pkg_config_paths='%s/lib/pkgconfig'%(self.deps_cpp_info["libogg"].rootpath))
                autotools.make(args=["-j2"])
                autotools.install()

        if self.settings.os == 'Windows':
            with tools.chdir(os.path.join(self._source_subfolder,"win32", "VS2008")):
                msbuild = MSBuild(self)
                msbuild.build("libspeex.sln",upgrade_project=True,platforms={'x86': 'Win32', 'x86_64': 'x64'})

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self._source_subfolder):
                self.copy("*", src="%s/builddir"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

