# System Setup

This repository provides a python script that will set up a development environment. To run it, open the Terminal application and paste this command:

```
curl -fSsL https://raw.githubusercontent.com/portlandcodeschool/initial-setup/master/system_setup.py | python
```

## Developing on this script

For compatibility with as many Macs as possible, this script is targeted at python 2.6 through 3.3. Python 2.6 doesn't have `with_statement` or `print_function` in `__future__`, so it makes some compromises:

* calls to `print` are invoked as if they were a function: `print("hello")`. In python 3 this will in fact call the print function. In 2 it is the print statement with some irrelevant parentheses.
* `open` must be used with `try: ...`/`finally: close()`.
* Some imports must be wrapped in `try`/`except ImportError` because module names have changed.
* `subprocess` doesn't have `check_output` in 2.6, so you have to use `Popen` if you care about the command's output.

There is a Vagrantfile that'll launch an OSX 10.10 (Yosemite) virtual machine. You'll need [Vagrant](https://www.vagrantup.com/); once you have it you can say `vagrant up`. Note that the `xcode-select --install` step requires a GUI to be available, so you'll have to sign into the machine through the GUI. The username and password are both "vagrant". Once you're logged in you can use either Terminal.app inside the VM or `vagrant ssh` from outside it.

OSX VMs can't have synced folders, so you have to scp or copy/paste the script to test changes. :(
