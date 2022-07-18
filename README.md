[![Build Status](https://travis-ci.org/gionniboy/gitkup.svg?branch=master)](https://travis-ci.org/gionniboy/gitkup)

[![Maintainability](https://api.codeclimate.com/v1/badges/20e51cf47dda0b5dcaa3/maintainability)](https://codeclimate.com/github/gionniboy/gitkup/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/20e51cf47dda0b5dcaa3/test_coverage)](https://codeclimate.com/github/gionniboy/gitkup/test_coverage)

[![Updates](https://pyup.io/repos/github/gionniboy/gitkup/shield.svg)](https://pyup.io/repos/github/gionniboy/gitkup/)
[![Python 3](https://pyup.io/repos/github/gionniboy/gitkup/python-3-shield.svg)](https://pyup.io/repos/github/gionniboy/gitkup/)


# **gitkup**
gitkup is a little python script to quickly backup all private repositories from a gitlab server
[api v4 - gitlab9.0+].

Need ssh key loaded on agent to work.

Work on gitlab.com by default, but on selfhosted/onpremises server too. [ssl needed]

### **Python3 required**.

### To the Users
Install dependencies using Pipenv and copy config.ini to config.local.ini and customize as needed.

**REMEMBER!** Create token on gitlab to access read repositories info.
```console
$ pipenv --three install
```

For a bit of info
```console
$ pipenv run python gitkup.py --help
```

#### Example
```console
$ pipenv run python gitkup.py
$ pipenv run python gitkup.py --dest ./my_treasure
$ pipenv run python gitkup.py --mail true
```

## To Contributors
Install dev dipendencies to avoid useless issues.

```console
$ pipenv --three install -d
```

To launch tests
```console
$ pipenv run pytest -v
```
or use pipenv shortcut
```console
$ pipenv run tests
```


issue&&PR || GTFO

have fun!

### **License**
This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details
