Tokfetch Manager is an open source project that provides a command line
tool to fetch token balances to SQlite db.

![image](https://img.shields.io/travis/LikoIlya/tokfetch.svg)

# Tokfetch Manager
___________


Tokfetch Manager provides technical operations for balance monitoring:

-   Fetching balances of tokens
-   Printing out richlist table

The command line tool is locally installed via Docker and available for
Windows, OSX and Linux. The API is written in Python programming
language.

## Installation
### Requirements
Skills needed

- Command line usage experience
- Ethereum and smart contract experience 

Software or services needed:
- Ethereum node, for example a local Parity installation or Infura-node-as-a-service
- Docker

### Advanced users

The `tokfetch` command line application is provided as a Docker image to minimize the issues with painful native dependency set up for your operating system. To use `tokfetch` we will set up a command line alias, as Docker command itself is quite long.

Install [Docker](https://www.docker.com/products/docker-desktop) (Linux, OSX).

### OSX and Linux
Set up a shell alias for sto command that executes Dockerised binary:

```shell
alias tokfetch='docker run -p 2222:2222 -v `pwd`:`pwd` -w `pwd` ilyaliko/tokfetch:latest'
```

Then you can do:

```shell 
tokfetch --help
```

Docker will automatically pull an image from Docker registry for your local computer on the first run. We map port 2222 to the localhost.

[image]()

After installing see how to set up the software.

###Developers
Python 3.6+ required.

Create Python virtual environment.

Then within the activated venv do:

```shell
git clone "git+https://github.com/TokenMarketNet/sto.git"
python -m venv venv  # Python 3 needed
source venv/bin/activate
pip install -U pip  # Make sure you are at least pip 18.1 - older versions will fail
pip install -e ".[dev,test]"
```


##Usage

```shell

```

## Links


[Github Source code and issue
tracker](https://github.com/LikoIlya/tokfetch)

[Docker releases](https://hub.docker.com/r/ilyaliko/tokfetch/)

[Python releases](https://pypi.org/project/sto/)

