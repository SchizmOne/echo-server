# EchoServer
1. [Short description](#short-description)
2. [Running the instance of echo-server](#running-the-instance-of-echo-server)
3. [EchoServer client script](#echoserver-client-script)
4. [Building and using Docker image](#building-and-using-docker-image)
5. [Makefile](#makefile)
6. [Ansible Playbook](#ansible-playbook)
7. [Jenkins pipeline](#jenkins-pipeline)

## Short description

This project contains several key items:
1. `echoserver/`. This is the directory that contains the source code for **EchoServer**.
2. `client.py`. This is the client script that allows users to make requests to a running **EchoServer** instance.
3. `Dockerfile`. This is a text file for your **Docker** client. With it you can build the Docker image with installed project dependencies and run the container from this image as another way to use `client.py`.
4. `Makefile`. This is the text file for **make** program. Defines automation tasks such as building the Docker image or preparing a Python virtual environment for `client.py`.
5. `utils/deploy-server-to-remote-machine.yml`. This is an Ansible playbook. With it you can deploy the **echo-server** project to a remote Linux machine. The playbook creates
virtual environment on the remote machine and installs the **echoserver** library from the https://test.pypi.org/project/schizmone-echoserver/ into this environment.
6. `utils/Jenkinsfile.template`. This is a Jenkins pipeline template file. With it you can target this repository in your Jenkins to build and run the aforementioned Docker image with different parameters. This particular file has extension `.template` because it has some placeholder values, that you're supposed to update with your own.

## Running the instance of echo-server
You don't need any additional dependencies to start the instance of **EchoServer**. It only requires Python 3.10 or higher.

Simply type:

```sh
# Linux, macOS
python3 echoserver/

# Windows (with additional arguments, if you want)
python .\echoserver\ --bind="127.0.0.1" --port=15000
```
And you will have the running instance of **EchoServer** with default parameters:
```sh
2025-08-29 18:29:21,978 [INFO] __main__: Starting EchoServer on the address: "http://0.0.0.0:15000" ...
```

## EchoServer API endpoints

There are two API endpoints for the **EchoServer** and both are simple and easy to use:

### Get "hello" string
* **Request**: GET /hello
* **Response code**: 200 OK
* **Response body**: 'hello'
* **curl example**: `curl -XGET 'http://localhost:8080/hello'`

### Get randomized string
* **Request**: GET /random
* **Query parameters**:
    - length (int | str, default is '10'): Length of the expected randomized string
    - digits (boolean | str, default is 'true'): Allow digits in the expected randomized string
    - lowercase (boolean | str, default is 'true'): Allow lowercase ascii letters in the the expected randomized string
    - uppercase (boolean | str, default is 'false'): Allow uppercase ascii letters in the the expected randomized string
* **Response code**: 200 OK or 400 Bad Request if query params are invalid
* **Response body**: RANDOMIZED_STRING
* **curl example**: `curl -XGET 'http://localhost:8080/random?length=20&digits=false&uppercase=True'`

## EchoServer client script

### Installation
> [!NOTE]
> Installation of the correct [Python](https://www.python.org/downloads/) version goes outside of the scope of this particular guide.

```sh
# Linux, macOS
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
pip install -e .

# Windows
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -e .
```

### Usage

This script serves as the **EchoServer** client.

It allows the user to execute it in two modes:
1. `(local)` Makes a GET request to the **/hello** endpoint of the running instance
   of EchoServer and saves the phrase from server response to the local file
   by a given name. The file is overwritten each time because the response
   is always the same phrase.

   EXAMPLE:
   ```sh
   python3 client.py -m=local --filename='local_name.txt'
   ```

2. `(remote)` Makes a GET request to the **/random** endpoint (without any query params)
   of the running instance of EchoServer, then connects via SSH to a remote machine,
   and saves the randomly generated text from server response to the file by a given
   name. Each new phrase will be added to the file.

   EXAMPLE:
   ```sh
   python3 client.py -m=remote --server_address='http://127.0.0.1:8080'
   --remote_host='192.168.100.30' --filename='remote_name.txt'
   ```

If you want to use the **remote** mode, then you have to provide **remote host address**
in the arguments and write the **user credentials** for SSH access to this host to
the **environment variable called REMOTE_CREDS** (value format is "username:password").

The total list of arguments is:
  - `-h, --help`: show this help message and exit
  - `-m, --mode {local,remote}`: Modes of the echo-server client
  - `-s, --server_address SERVER_ADDRESS`: Address of the running instance of EchoServer. (default: http://localhost:8080)
  - `-f, --filename FILENAME`: Name of the file to which the text from server response will be saved (default: "filename.txt")
  - `--remote_host REMOTE_HOST`: Host address of the remote machine where the file will be saved via SSH (required for remote mode)


### Usage example:
Applying client:

```
(venv) PS C:\Users\User\Path-To-Project\echo-server> python .\client.py -m=remote --server_address='http://127.0.0.1:15000' --remote_host='192.168.100.30' --filename='example.txt'
Selected mode: remote
[19:11:03] Successfully received response from the endpoint /random                                                                        
           Generated phrase: "13vsfg32wc"
```

Results on the remote machine:
```sh
user@machine:~$ ls
example.txt
user@machine:~$ cat example.txt
13vsfg32wc
```

## Building and using Docker image

### Building image
Install Docker client [depending on your platform](https://docs.docker.com/engine/install/).

Then you can build the image with:
```sh
# If you want, you can just name it "echoserver" instead

docker build -t IMAGE_NAME:IMAGE_TAG .
```

### Running image

`local` example:
```
(venv) PS C:\Users\User\Path-To-Project\echo-server> docker run --rm -v .:/app/output echoserver client.py -m=local -f="local-example.txt"
Selected mode: local
[17:38:51] Server address was not provided, setting up              client.py:69
           server in daemon thread...
           EchoServer started locally at the address of             client.py:74
           "http://localhost:8080"
127.0.0.1 - - [29/Aug/2025 17:38:51] "GET /hello HTTP/1.1" 200 -
           Successfully received response from the                  client.py:94
           endpoint /hello
           Stopping EchoServer...                                   client.py:80
           EchoServer stopped successfully                          client.py:83
(venv) PS C:\Users\User\Path-To-Project\echo-server> cat .\local-example.txt
hello
```

> [!NOTE]
> Notice how we're mounting the volume in the example above. This is because we want to save the file after the Docker container will be removed. Here we mount the volume to the current directory to preserve files after the container is removed.

`remote` example:
```
(venv) PS C:\Users\User\Path-To-Project\echo-server> docker run --rm echoserver client.py -m=remote -f="remote-example.txt" --remote_host="192.168.100.30"
Selected mode: remote
[17:42:49] Server address was not provided, setting up              client.py:69
           server in daemon thread...
           EchoServer started locally at the address of             client.py:74
           "http://localhost:8080"
127.0.0.1 - - [29/Aug/2025 17:42:49] "GET /random HTTP/1.1" 200 -
           Successfully received response from the                  client.py:107
           endpoint /random
           Generated phrase: "qtatf2zj39"
[17:42:50] Stopping EchoServer...                                   client.py:80
           EchoServer stopped successfully                          client.py:83

(venv) PS C:\Users\User\Path-To-Project\echo-server> ssh username@192.168.100.30 "cat remote-example.txt"
username@192.168.100.30's password: 
qtatf2zj39
```

## Makefile

Install the [make](https://www.gnu.org/software/make/manual/make.html) program depending on your platform.

This particular **Makefile** provides two targets:
- `build_image`. If selected, this will build the aforementioned Docker image.
- `prepare_venv`. If selected, this will create the Python virtual environment for the **EchoServer** client script and will install all necessary dependencies there.

Simply type:
```sh
make TARGET_NAME
```

## Ansible Playbook

> [!NOTE]
> Ansible only works on Linux machines, so if you want to check this playbook on Windows, you should use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install). Check how to install the Ansible [here](https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html).


The `utils/deploy-server-to-remote-machine.yml` playbook serves as a quick way to deploy the **EchoServer** to the remote machine. It should work with machines that are using Debian-like OS (e.g. Ubuntu).

This is a very simplistic approach where the playbook will install the latest version of Python. Then it will create the virtual environment by a given name, into which it then will install the `echoserver` library via pip. After that a user of the remote machine should be able to start the instance of the
**EchoServer** with the following command:
```sh
/path/to/venv/bin/python3 -m echoserver
```

Notice that this playbook requires the privilege escalation, since it ensures the latest Python 3 is installed before creating the virtual environment.

So the playbook should be run like this:
```sh
# By default the virtual environment name is "ansible_venv", but you can change that. Keep in mind that this path is relative to the user's home directory.
ansible-playbook -v --extra-vars="venv_path=your/path/to/venv" -K utils/deploy-server-to-remote-machine.yml
```

Enter the user password when being asked and that's it.


## Jenkins pipeline

### Preparation

> [!NOTE]
> If you don't have the prepared Jenkins environment, you can prepare it from the [official installation guide](https://www.jenkins.io/doc/book/installing/).

To use the `utils/Jenkinsfile.template`, create at least one set of **Credentials** for your remote user.
After that provide your credentials ID here:

```groovy
    environment {
        IMAGE_NAME = 'echoserver'
        IMAGE_TAG  = 'latest'
        HELLO_STRING = 'hello'
        REMOTE_CREDS = credentials('YOUR_CREDENTIALS_ID')
    }
```

Then you should rename this file to `Jenkinsfile`, move it to the root directory of this project and you should be ready to create a new Jenkins pipeline job that will be based on this file in this repository.

### Parameters

This pipeline has only 3 parameters.
- `MODE`. Same as the *--mode* argument to the **client.py** script. Can be either **local** or **remote**. Required.
- `SERVER_ADDRESS`. Same as the *--server_address* argument to the **client.py** script. Required.
- `FILENAME`. Same as the *--filename* argument to the **client.py** script. Default is **filename.txt**.
- `REMOTE_HOST`. Same as the *--remote_host* argument to the **client.py** script. Required for remote mode.

### Stages

1. `Check Parameters`. Verifies that if `remote` mode is selected then `REMOTE_HOST` argument also should be provided.
2. `Build EchoServer image`. Creates the aforementioned Docker image with prepared **client.py** script.
3. `Run the client in EchoServer image`. Executes the Docker container based on the created image with the given `MODE` argument.
4. `Verify EchoServer client run results`. Checks the changes after the previous stage, validates that the files are present/created.
