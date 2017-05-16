# Python Client

g8os-resourcepool is the Python client used to talk to [G8OS Resource Pool API](https://github.com/g8os/resourcepool)

## Install

```bash
pip install g8os-resourcepool
```

## How to use

```python
In [9]: from g8os import resourcepool

In [10]: c = resourcepool.Client('http://192.168.193.212:8080')

In [11]: c.api.nodes.ListNodes().json()
Out[11]:
[{'hostname': '', 'id': '2c600cbc2545', 'status': 'running'},
 {'hostname': '', 'id': '2c600ccd2ae9', 'status': 'running'},
 {'hostname': '', 'id': '0cc47a3b3d6a', 'status': 'running'},
 {'hostname': '', 'id': '2c600ccd2ad1', 'status': 'running'},
 {'hostname': '', 'id': '2c600cbc23bc', 'status': 'running'}]
```

## To update the client from the RAML file

```shell
go-raml client -l python --ramlfile raml/api.raml --dir pyclient/g8os/resourcepool
```