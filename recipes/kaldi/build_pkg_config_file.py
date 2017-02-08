#!/usr/bin/env python
# extract what we need from flag files and put them into pkg-config

import os.path
import shlex
import sys

def main(
        cxxflags_file, ldflags_file, ldlibs_file, pkg_config_dir,
        install_prefix, pkg_version):
    cxxflags = None
    with open(cxxflags_file) as f:
        cxxflags = shlex.split(f.read())
    idx = 0
    while idx < len(cxxflags):
        if cxxflags[idx][:2] in ('-W', '-I'):
            # throw away warnings and includes
            if len(cxxflags[idx]) == 2:
                # arg has a space after; delete it
                del cxxflags[idx]
            del cxxflags[idx]
        elif cxxflags[idx][:5] == '-arch':
            del cxxflags[idx]
            del cxxflags[idx]
        else:
            idx += 1
    ldflags = None
    with open(ldflags_file) as f:
        ldflags = shlex.split(f.read())
    ldlibs = None
    with open(ldlibs_file) as f:
        ldlibs = shlex.split(f.read())
    idx = 0
    while idx < len(ldlibs):
        if ldlibs[idx][:2] in ('-W', '-L'):
            # warnings and library paths
            if len(ldlibs[idx]) == 2:
                del ldlibs[idx]
            del ldlibs[idx]
        else:
            idx += 1
    preamble = """\
prefix={}
includedir=${{prefix}}/include
libdir=${{prefix}}/lib

""".format(install_prefix)
    postamble = """\
Cflags: -I${{includedir}} -I${{includedir}}/kaldi {}
Libs: -L${{libdir}} {}
""".format(' '.join(cxxflags), ' '.join(ldlibs + ldflags))
    # base library
    with open(os.path.join(pkg_config_dir, 'kaldi-base.pc'), 'w') as f:
        f.write(preamble)
        f.write('Name: kaldi-base\nDescription: kaldi i/o component\n')
        if pkg_version:
            f.write('Version: ')
            f.write(pkg_version)
            f.write('\n')
        f.write(postamble)
    # matrix and thread libraries (same deps)
    for name in 'kaldi-thread', 'kaldi-matrix':
        with open(os.path.join(pkg_config_dir, name + '.pc'), 'w') as f:
            f.write(preamble)
            f.write('Name: ')
            f.write(name)
            f.write('\nDescription: kaldi i/o component\n')
            if pkg_version:
                f.write('Version: ')
                f.write(pkg_version)
                f.write('\nRequires: kaldi-base >= ')
                f.write(pkg_version)
                f.write('\n')
            else:
                f.write('Requires: kaldi-base\n')
            f.write(postamble)
    with open(os.path.join(pkg_config_dir, 'kaldi-util.pc'), 'w') as f:
        f.write(preamble)
        f.write('Name: kaldi-util\nDescription: kaldi i/o component\n')
        if pkg_version:
            f.write(
                'Version: {0}\nRequires: kaldi-base >= {0}, kaldi-matrix >= '
                '{0}, kaldi-thread >= {0}\n'.format(pkg_version))
        else:
            f.write('Requires: kaldi-base kaldi-matrix kaldi-thread\n')
        f.write(postamble)
    with open(os.path.join(pkg_config_dir, 'kaldi-feat.pc'), 'w') as f:
        f.write(preamble)
        f.write('Name: kaldi-feat\nDescription: kaldi i/o component\n')
        if pkg_version:
            f.write(
                'Version: {0}\nRequires: kaldi-base >= {0}, kaldi-matrix >= '
                '{0}, kaldi-thread >= {0} kaldi-util >= {0}\n'
                ''.format(pkg_version))
        else:
            f.write(
                'Requires: kaldi-base kaldi-matrix kaldi-thread kaldi-util\n')
        f.write(postamble)
    return 0

if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
