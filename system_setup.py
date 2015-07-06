#!/usr/bin/env python

import subprocess
import sys
import getpass
import os
import re
import urllib2
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

SUDO_PASS = None
HOMEDIR = os.environ['HOME']

def sudo_password():
    global SUDO_PASS
    if SUDO_PASS is None:
        SUDO_PASS = getpass.getpass("Please enter your system password: ")
    return SUDO_PASS

# return whether a command is found in `which`. Note that it returns a simple
# boolean, not the path to the command.
def which(command):
    check = subprocess.Popen(
        ['which', command],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    return check.wait() == 0

def install_xcode_tools():
    print("I am going to try to install a C compiler.")
    xcode_install = subprocess.Popen(
        ['xcode-select', '--install'],
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
    )
    return_code = xcode_install.wait()
    if return_code == 1:
        print("You already have a C compiler! Great!")
    else:
        print("You'll see several prompts. Please click Install and accept " +\
              "the EULA.")
        raw_input("Please press enter when the installation is finished.")

def install_homebrew():
    if which('brew'):
        print("You have homebrew!")
        return

    print("I am going to try to install Homebrew. This can take some time "
          "with no indication that things are still happening; please be "
          "patient...")
    try:
        response = urllib2.urlopen('https://raw.githubusercontent.com/' +
                                   'Homebrew/install/master/install')
    except urllib2.HTTPError as e:
        print("Oh no! There was an error fetching homebrew:")
        print(e.getcode() + ' ' + e.msg)
        sys.exit(1)

    print "Downloaded the install script; running..."
    subprocess.check_call(
        ['ruby', '-e', response.read()],
    )

def install_utils():
    print("I am going to install several command-line utilities.")
    return_code = subprocess.Popen(
        ['brew', 'install', 'git', 'node', 'tree', 'colordiff']
    ).wait()
    if return_code:
        print("Homebrew failed (see the error above); aborting.")
        sys.exit(return_code)

# locate is a handy utility for finding files, but by default it doesn't work
# on OSX. This launchdaemon makes it available (eventually).
def prepare_locate():
    print("I am going to set up the locate utility.")
    sudo_pass = sudo_password()
    sudo = subprocess.Popen(
        [
            'sudo',
            'launchctl',
            'load',
            '-w',
            '/System/Library/LaunchDaemons/com.apple.locate.plist'
        ],
        stdin=subprocess.PIPE,
    )
    sudo.stdin.write(sudo_pass)

def prepare_home_bin():
    home_bin = os.path.join(HOMEDIR, 'bin')
    if not os.path.isdir(home_bin):
        os.mkdir(home_bin)

# If there's already an editor installed, make sure it can be invoked from the
# command line. If there isn't one installed, install Atom.
def prepare_editor():
    prepare_home_bin()

    if which('subl'):
        return 'subl'

    if which('atom'):
        return 'atom'

    # make a subl link if Sublime exists
    for version in ['', ' 2', ' 3']:
        sublime_path = '/Applications/Sublime Text{0}.app'.format(version)
        if os.path.exists(sublime_path):
            os.symlink(
                os.path.join(sublime_path, 'Contents', 'SharedSupport', 'bin', 'subl'),
                os.path.join(HOMEDIR, 'bin', 'subl'),
            )
            subprocess.Popen(['ln', '-s', 'sublime_path', ])
            print("I have created a subl command for you.")
            return 'subl'

    # make an atom link if Atom exists
    if os.path.exists('/Applications/Atom.app'):
        os.symlink(
            '/Applications/Atom.app/Contents/Resources/app/atom.sh',
            os.path.join(HOMEDIR, 'bin', 'atom')
        )
    else:
        # brew install atom (which creates a symlink itself)
        subprocess.check_call(['brew', 'tap', 'Caskroom/cask'])
        subprocess.check_call(['brew', 'install', 'caskroom/cask/brew-cask'])
        subprocess.check_call(['brew', 'cask', 'install', 'atom'])
        return 'atom'


def configure_git():
    # .gitconfig is a standard INI file, which ConfigParser can handle. INI
    # files have "sections" and "options," where options live inside sections.
    config_path = os.path.join(HOMEDIR, '.gitconfig')
    config = ConfigParser.SafeConfigParser()
    config.read(config_path) # proceeds happily on no-such-file, which is fine

    for section in ['user', 'core', 'push', 'diff', 'color']:
        if not config.has_section(section):
            config.add_section(section)

    if not config.has_option('user', 'name'):
        name = raw_input('Please enter your name: ')
        config.set('user', 'name', name)
    if not config.has_option('user', 'email'):
        email = raw_input('Please enter your email address: ')
        config.set('user', 'email', email)

    for (section, option, value) in [
                # ~ is ok here; git interprets it after reading the config
                ('core', 'excludesfile', '~/.gitignore_global'),
                ('push', 'default', 'current'),
                ('diff', 'renames', 'true'),
                ('color', 'ui', 'true'),
            ]:
        if not config.has_option(section, option):
            config.set(section, option, value)

    fh = open(config_path, 'w')
    try:
        config.write(fh)
    finally:
        fh.close()

    fh = open(os.path.join(HOMEDIR, '.gitignore_global'), 'a')
    try:
        fh.write('\n.DS_Store\n')
    finally:
        fh.close()

def configure_bash(editor):
    bash_profile = os.path.join(HOMEDIR, '.bash_profile')
    if os.path.exists(bash_profile):
        fh = open(bash_profile, 'r')
        try:
            bash_config = fh.read()
        finally:
            fh.close()
    else:
        bash_config = ''

    if 'PS1=' not in bash_config:
        bash_config += '\n'
        bash_config += r'export PS1="\[$(tput bold)\]\[$(tput setaf 5)\]\u' +\
                       r'\[$(tput sgr0)\]:\[$(tput bold)\]\[$(tput setaf ' + \
                       r'2)\]\h\[$(tput sgr0)\]:\[$(tput bold)\]\[$(tput ' + \
                       r'setaf 4)\]\w\[$(tput sgr0)\]\n$ \[$(tput sgr0)\]"'

    for path in ['/usr/local/sbin', '/usr/local/bin', '$HOME/bin']:
        if not re.search(r'PATH=.*{0}'.format(path), bash_config):
            bash_config += '\nexport PATH={0}:$PATH'.format(path)

    for (variable, value) in [
                # use colored output in ls.
                ('CLICOLOR', '1'),
                # colors to use in ls. See http://ss64.com/bash/lsenv.html
                ('LSCOLORS', 'ExFxCxDxBxegedabagacad'),
                # Some programs will send long output to $PAGER rather than
                # printing directly to the terminal.
                ('PAGER', 'less'),
                # Program to invoke when editing files. Used by git, among
                # others.
                ('EDITOR', '"{0} --wait"'.format(editor)),
            ]:
        if variable not in bash_config:
            bash_config += '\nexport {0}={1}'.format(variable, value)

    if not bash_config.endswith('\n'):
        bash_config += '\n'

    fh = open(bash_profile, 'w')
    try:
        fh.write(bash_config)
    finally:
        fh.close()

if __name__ == '__main__':
    install_xcode_tools()
    install_homebrew()
    install_utils()
    prepare_locate()
    editor = prepare_editor()
    configure_git()
    configure_bash(editor)

