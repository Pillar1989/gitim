#!/usr/bin/env python3
# -*- coding: utf8 -*-

from __future__ import print_function
from getpass import getpass
from argparse import ArgumentParser
from os import chdir, path, makedirs, pardir, environ
from subprocess import call, Popen,check_output
from functools import partial
from platform import python_version_tuple
import os
import generate_ci

from github import Github

if python_version_tuple()[0] == u'2':
    input = lambda prompt: raw_input(prompt.encode('utf8')).decode('utf8')

__author__ = u'"Mustafa Hasturk"'
__version__ = '2.1.0'

def endWith(s, *endstring):
    array = map(s.endswith, endstring)
    if True in array:
        return True
    else:
        return False


def fileEndWith(p, *endstring):
    all_file = []
    wants_files = []

    for r, d, f in os.walk(p):
        if r.find('.git') == -1:
            for item in f:
                all_file.append(os.path.join(r, item))
    for i in all_file:
        if endWith(i, '.cpp', '.h', '.ino'):
            wants_files.append(i)
    return wants_files



class Gitim():
    def __init__(self):
        print(u"""
         .--.         .--. __  __   ___
  .--./) |__|         |__||  |/  `.'   `.
 /.''\\  .--.     .|  .--.|   .-.  .-.   '
| |  | | |  |   .' |_ |  ||  |  |  |  |  |
 \`-' /  |  | .'     ||  ||  |  |  |  |  |
 /("'`   |  |'--.  .-'|  ||  |  |  |  |  |
 \ '---. |  |   |  |  |  ||  |  |  |  |  |
  /'""'.\|__|   |  |  |__||__|  |__|  |__|
 ||     ||      |  '.'
 \'. __//       |   /
 `'----        `---`

created by {__author__}
Version: {__version__}
""".format(__author__=__author__, __version__=__version__))

    def set_args(self):
        """ Create parser for command line arguments """
        parser = ArgumentParser(
                usage=u'python -m gitim \'\nUsername and password will be prompted.',
                description='Clone all your Github repositories.')
        parser.add_argument('-u', '--user', help='Your github username')
        parser.add_argument('-p', '--password', help=u'Github password')
        parser.add_argument('-t', '--token', help=u'Github OAuth token')
        parser.add_argument('-o', '--org', help=u'Organisation/team. User used by default.')
        parser.add_argument('-d', '--dest', help=u'Destination directory. Created if doesn\'t exist. [curr_dir]')
        parser.add_argument('--nopull', action='store_true', help=u'Don\'t pull if repository exists. [false]')
        parser.add_argument('--shallow', action='store_true', help=u'Perform shallow clone. [false]')
        parser.add_argument('--ssh', action='store_true', help=u'Use ssh+git urls for checkout. [false]')
        return parser

    def make_github_agent(self, args):
        """ Create github agent to auth """
        if args.token:
            g = Github(args.token)
        else:
            user = args.user
            password = args.password
            if not user:
                user = input(u'Username: ')
            if not password:
                password = getpass('Password: ')
            if not args.dest:
                args.dest = input(u'Destination: ')
            g = Github(user, password)
        return g

    def clone_main(self):
        """ Clone all repos """
        parser = self.set_args()
        args = parser.parse_args()
        g = self.make_github_agent(args)
        user = g.get_user().login
        # (BadCredentialsException, TwoFactorException, RateLimitExceededException)
        
        Arduino_lib_num = 0
        join = path.join
        if args.dest:
            if not path.exists(args.dest):
                makedirs(args.dest)
                print(u'mkdir -p "{}"'.format(args.dest))
            join = partial(path.join, args.dest)

        get_repos = g.get_organization(args.org).get_repos if args.org else g.get_user().get_repos
        for repo in get_repos():
            if not path.exists(join(args.org, repo.name)):
                print(join(args.org,repo.name))
                clone_url = repo.clone_url
                if args.ssh:
                    clone_url = repo.ssh_url
                if args.shallow:
                    print(u'Shallow cloning "{repo.full_name}"'.format(repo=repo))
                    call([u'git', u'clone', '--depth=1', clone_url, join(repo.full_name)])
                else:
                    print(u'Cloning "{repo.full_name}"'.format(repo=repo))
                    call([u'git', u'clone', clone_url, join(repo.full_name)])
            elif not args.nopull:
                print(u'Updating "{repo.name}"'.format(repo=repo))
                call([u'git', u'pull'], env=dict(environ, GIT_DIR=join(args.org, repo.name, '.git').encode('utf8')))
                repo_path = join(args.org, repo.name)
                if path.exists(join(repo_path, 'library.properties')):
                    Arduino_lib_num = Arduino_lib_num + 1
                    if not path.exists(join(repo_path, '.travis.yml')):
                        generate_ci.generate_yml(join(repo_path, '.travis.yml'),["arduino:avr:uno","Seeeduino:samd:seeed_XIAO_m0"], [])
                        call([u'git',u'--git-dir='+repo_path+'/.git',u'--work-tree='+repo_path, u'add',u'--all'])
                        call([u'git',u'--git-dir='+repo_path+'/.git',u'--work-tree='+repo_path, u'commit',u'-m',u'Seeed:Arduino: Add travis.yml'])
                        call([u'git',u'--git-dir='+repo_path+'/.git',u'--work-tree='+repo_path, u'push',u'-u','origin','master'])
                    else:
                        readme_lines=[]
                        do_git = True
                        ci_status = "[![Build Status](https://travis-ci.com/Seeed-Studio/"+repo.name+".svg?branch=master)](https://travis-ci.com/Seeed-Studio/"+repo.name+")\n"
                        if  path.exists(join(repo_path, 'README.md')):
                            f_readme=open(join(repo_path, 'README.md'),'r') 
                            for line in f_readme:
                                readme_lines.append(line)
                            f_readme.close()
                            if readme_lines[0].find("Build Status") == -1:
                                readme_lines[0] = readme_lines[0][:-1] + "  " + ci_status
                                f_readme=open(join(repo_path, 'README.md'),'w') 
                                f_readme.write("".join(readme_lines))
                                f_readme.close()
                            else:
                                do_git = False
                        else:
                            f_readme=open(join(repo_path, 'README.md'),'w') 
                            f_readme.write("# "+repo.name+"  "+ci_status)
                            f_readme.close()
                        if do_git == True:
                            call([u'git',u'--git-dir='+repo_path+'/.git',u'--work-tree='+repo_path, u'add',u'--all'])
                            call([u'git',u'--git-dir='+repo_path+'/.git',u'--work-tree='+repo_path, u'commit',u'-m',u'Seeed:Arduino: Add travis build status'])
                            call([u'git',u'--git-dir='+repo_path+'/.git',u'--work-tree='+repo_path, u'push',u'-u','origin','master'])                        
            else:
                print(u'Already cloned, skipping...\t"{repo.full_name}"'.format(repo=repo))
        print(u'FIN',Arduino_lib_num)


if __name__ == '__main__':
    gitim = Gitim()
    gitim.clone_main()
