# gitkup
gitkup is a little python script to quickly backup all private repositories from a gitlab server
[api v4 - gitlab9.0+].

Need ssh key loaded on agent to work.

Work on gitlab.com by default, but on selfhosted/onpremises server too. [ssl needed]


### Python3 required.

Install requirements.txt for dependencies. [gitpython + requests]

Use requirements-dev.txt if you want contribute to [really appreaciate].


For a bit of info
```console
$ python gitkup.py --help
```

Example
```console
$ python gitkup.py
$ python gitkup.py --dest ./my_treasure
$ python gitkup.py --mail true
```


issue&&PR || GTFO

have fun!
