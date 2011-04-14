#! /usr/bin/env jython
# Copyright (C) 2011 Sun Ning<classicning@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from . import logger
from jip.commands import resolve, command
from jip.commands import _install as jip_install
from jip.maven import Artifact, repos_manager

try:
    from setuptools import setup as _setup
    from setuptools.command.install import install as _install
except:    
    from distutils.core import setup as _setup
    from distutils.command.install import install as _install

dist_descriptor = 'pom.xml'
dependencies = []
repositories = []
use_pom = True

def requires_java(requires_info):
    global use_pom, dependencies, repositories
    use_pom = False
    if 'repositories' in requires_info:
        repositories = requires_info['repositories']
    if 'dependencies' in requires_info:
        dependencies = [Artifact(*d) for d in requires_info['dependencies']]

@command(register=False)
def requires_java_install():
    for repos in repositories:
        repos_manager.add_repos(repos[0], repos[1], 'remote')
    jip_install(*dependencies)
    logger.info("[Finished] all dependencies resolved")

class install(_install):

    def run(self):
        _install.run(self)
        print 'running jip_resolve'
        if use_pom:
            resolve(dist_descriptor)
        else:
            requires_java_install()

def setup(**kwargs):
    if 'requires_java' in kwargs:
        requires_java(kwargs.pop('requires_java'))
    if 'pom' in kwargs:
        dist_descriptor = kwargs.pop('pom')
    if 'cmdclass' not in kwargs:
        kwargs['cmdclass'] = {'install': install}
    _setup(**kwargs)
