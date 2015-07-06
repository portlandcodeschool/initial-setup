#!/usr/bin/env python

import subprocess
import sys
import getpass
import os
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

    print("I am going to try to install Homebrew.")
    ruby = subprocess.Popen(
        ['ruby'],
        stdin = subprocess.PIPE,
    )
    curl = subprocess.Popen(
        [
            'curl',
            '-fsSL',
            'https://raw.githubusercontent.com/Homebrew/install/master/install'
        ],
        stdout = ruby.stdin,
    )
    return_code = ruby.wait()
    if return_code:
        print("Installation of Homebrew failed (see the error above); aborting.")
        sys.exit(return_code)

def install_utils():
    print("I am going to install several command-line utilities.")
    return_code = subprocess.Popen(
        ['brew', 'install', 'git', 'node', 'tree', 'colordiff']
    ).wait()
    if return_code:
        print("Homebrew failed (see the error above); aborting.")
        sys.exit(return_code)

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

def prepare_editor():
    prepare_home_bin()

    if which('subl') or which('atom'):
        return

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
            return

    # make an atom link if Atom exists
    if os.path.exists('/Applications/Atom.app'):
        os.symlink(
            '/Applications/Atom.app/Contents/Resources/app/atom.sh',
            os.path.join(HOMEDIR, 'bin', 'atom')
        )
    else:
        # TODO: check return codes
        subprocess.Popen(['brew', 'tap', 'Caskroom/cask']).wait()
        subprocess.Popen(['brew', 'install', 'caskroom/cask/brew-cask']).wait()
        subprocess.Popen(['brew', 'cask', 'install', 'atom']).wait()


def configure_git():
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


# bashrc:
### export PS1="\[$(tput bold)\]\[$(tput setaf 5)\]\u\[$(tput sgr0)\]:\[$(tput bold)\]\[$(tput setaf 2)\]\h\[$(tput sgr0)\]:\[$(tput bold)\]\[$(tput setaf 4)\]\w\[$(tput sgr0)\]\n$ \[$(tput sgr0)\]"
### export PATH="$HOME/bin:/usr/local/bin:/usr/local/sbin:$PATH"
### export CLICOLOR=1
### export LSCOLORS=ExFxCxDxBxegedabagacad
### export PAGER="less"
### export EDITOR=...
##### need to figure out editor from before

if __name__ == '__main__':
    install_xcode_tools()
    install_homebrew()
    install_utils()
    prepare_locate()
    prepare_editor()
    configure_git()

