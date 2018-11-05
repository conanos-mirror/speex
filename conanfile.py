from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from shutil import copyfile
import os

class SpeexConan(ConanFile):
    name = "speex"
    version = "1.2rc2"
    description = "A Free Codec For Free Speech"
    url = "https://github.com/conanos/speex"
    homepage = "https://www.speex.org/"
    license = "BSD_like"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = "shared=True"
    generators = "cmake"
    requires = "libogg/1.3.3@conanos/dev"
    source_subfolder = "source_subfolder"

    def source(self):
        tools.get("http://downloads.xiph.org/releases/speex/{name}-{version}.tar.gz".format(name=self.name, version=self.version))
        extracted_dir = "{name}-{version}".format(name=self.name, version=self.version)
        os.rename(extracted_dir, self.source_subfolder)

    def build(self):
        with tools.chdir(self.source_subfolder):
            autotools = AutoToolsBuildEnvironment(self)
            _args = ["--prefix=%s/builddir"%(os.getcwd()), "--disable-maintainer-mode", "--disable-silent-rules"]
            if self.options.shared:
                _args.extend(['--enable-shared=yes','--enable-static=no'])
            else:
                _args.extend(['--enable-shared=no','--enable-static=yes'])
            autotools.configure(args=_args, 
                                pkg_config_paths='%s/lib/pkgconfig'%(self.deps_cpp_info["libogg"].rootpath))
            autotools.make(args=["-j2"])
            autotools.install()

    def package(self):
        if tools.os_info.is_linux:
            with tools.chdir(self.source_subfolder):
                self.copy("*", src="%s/builddir"%(os.getcwd()))

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)

