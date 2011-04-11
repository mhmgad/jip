#! /usr/bin/env jython
# Copyright (C) 2011 Sun Ning<classicning@gmail.com>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import shutil

from . import logger, JIP_VERSION, get_lib_path, get_virtual_home
from jip.maven import repos_manager, Pom, Artifact

## command dictionary {name: function}
commands = {}
def command(func):
    ## init default repos before running command
    def wrapper(*args, **kwargs):
        repos_manager.init_repos()
        func(*args, **kwargs)
    ## register in command dictionary        
    commands[func.__name__] = wrapper
    return wrapper

def _install(*artifacts):
    ## ready set contains artifact jip file names
    ready_set = os.listdir(get_lib_path())
    
    ## dependency_set and installed_set contain artifact objects
    dependency_set = set()
    installed_set = set()

    for a in artifacts:
        dependency_set.add(a)

    while len(dependency_set) > 0:
        artifact = dependency_set.pop()

        ## to prevent multiple version installed
        if any(map(lambda a: a.is_same_artifact(artifact), installed_set)):
            continue

        found = False
        for repos in repos_manager.repos:

            pom = repos.download_pom(artifact)

            ## find the artifact
            if pom is not None:
                if not artifact.to_jip_name() in ready_set:
                    repos.download_jar(artifact, get_lib_path())
                    installed_set.add(artifact)
                    ready_set.append(artifact.to_jip_name())
                found = True

                pom_obj = Pom(pom)
                more_dependencies = pom_obj.get_dependencies()
                for d in more_dependencies:
                    d.exclusions.extend(artifact.exclusions)
                    if not any(map(lambda e: e.is_same_artifact(d), artifact.exclusions)):
                        dependency_set.add(d)
                break
        
        if not found:
            logger.error("[Error] Artifact not found: %s", artifact)
            sys.exit(1)


@command
def install(artifact_identifier):
    """Install a package with maven coordinate "groupId:artifactId:version" """
    group, artifact, version = artifact_identifier.split(":")
    artifact_to_install = Artifact(group, artifact, version)

    _install(artifact_to_install)
    logger.info("[Finished] %s successfully installed" % artifact_identifier)

@command
def clean():
    """ Remove all downloaded packages """
    logger.info("[Deleting] remove java libs in %s" % get_lib_path())
    shutil.rmtree(get_lib_path())
    logger.info("[Finished] all downloaded files erased")

## another resolve task, allow jip to resovle dependencies from a pom file.
@command
def resolve(pomfile):
    """ Resolve and download dependencies in pom file """
    pomfile = open(pomfile, 'r')
    pomstring = pomfile.read()
    pom = Pom(pomstring)
    ## custom defined repositories
    repositories = pom.get_repositories()
    for repos in repositories:
        repos_manager.add_repos(*repos)

    dependencies = pom.get_dependencies()
    _install(*dependencies)
    logger.info("[Finished] all dependencies resolved")

@command
def update(artifact_id):
    """ Update a snapshot artifact, check for new version """
    group, artifact, version = artifact_id.split(":")
    artifact = Artifact(group, artifact, version)

    if artifact.is_snapshot():
        installed_file = os.path.join(get_lib_path(), artifact.to_jip_name())
        if os.path.exists(installed_file):
            lm = os.stat(installed_file)[stat.ST_MTIME]

            ## find the repository contains the new release
            selected_repos = None
            for repos in repos_manager.repos:
                ts = repos.last_modified(artifact)
                if ts is not None and ts > lm :
                    lm = ts
                    selected_repos = repos
            
            if selected_repos is not None:
                ## download new jar
                selected_repos.download_jar(artifact)

                ## try to update dependencies
                pomstring = selected_repos.download_pom(artifact)
                pom = Pom(pomstring)
                dependencies = pom.get_dependencies()
                _install(*dependencies)
            logger.info('[Finished] Artifact snapshot %s updated' % artifact_id)
        else:
            logger.error('[Error] Artifact not installed: %s' % artifact)
            sys.exit(1)
    else:
        logger.error('[Error] Can not update non-snapshot artifact')
        return

@command
def version():
    """ Display jip version """
    logger.info('[Version] jip %s, jython %s' % (JIP_VERSION, sys.version))

@command
def install_dependencies(artifact_id):
    """ Install dependencies for given artifact, without download itself """
    group, artifact, version = artifact_id.split(":")
    artifact = Artifact(group, artifact, version)

    found = False
    for repos in repos_manager.repos:
        pom_raw = repos.download_pom(artifact)
        ## find the artifact
        if pom_raw is not None:
            pom = Pom(pom_raw)
            found = True
            _install(*pom.get_dependencies())
            break

    if not found:
        logger.error('[Error] artifact %s not found in any repository' % artifact_id)
        sys.exit(1)
    else:
        logger.info('[Finished] finished resolve dependencies for %s ' % artifact_id)

