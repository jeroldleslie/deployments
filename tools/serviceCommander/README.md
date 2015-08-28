#Service Commander#

```
pop@appleTarts:serviceCommander $ ./serviceCommander.py --help
Usage: serviceCommander.py [OPTIONS]

Options:
  --debug / --no-debug       Turn debugging on
  --logfile TEXT             Log file to write to
  -e, --services TEXT        Services to impact input as a comma separated
                             list
  -l, --subset TEXT          Further limit selected hosts with an additional
                             pattern
  -i, --inventory-file TEXT  Ansible inventory file to use
  -m, --max-retries INTEGER  Max retries for running the playbook
  -r, --restart              restart services
  -s, --start                start services
  -t, --stop                 stop services
  -f, --force-stop           kill services
  -f, --clean                clean services
  --ansible-root-dir TEXT    Root directory for Ansible
  --help                     Show this message and exit.
```