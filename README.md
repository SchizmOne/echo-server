# echo-server
Implementation of the test task for the position of Automated QA Engineer.

## Quick access
1. [Short description](#short-description)
2. [Running the instance of echo-server](#running-the-instance-of-echo-server)
3. [EchoServer client script](#echoserver-client-script)
4. [Building and using Docker image](#building-and-using-docker-image)
5. [Makefile](#makefile)
6. [Ansible Playbook](#ansible-playbook)
7. [Jenkins pipeline](#jenkins-pipeline)

## Short description

This project contains several key items:
1. `src`. This is a directory with the source code for **echo-server** and with other dependencies for client script.
2. `echoserver_client.py`. This is a script that will allow user to make requests to the endpoints of the running instance of **echo-server** and even launch such instance by itself if needed.
3. `Dockerfile`. This is a text file for your **Docker** client. With it you can build the docker image with installed dependencies from `src` directory and run the container from this image as another way to use `echoserver_client.py`.
4. `Makefile`. This is a text file for **make** program. With it you can either build an instance of the aforementined docker image or prepare the virtual environmemnt to run the `echoserver_client.py` in it.
5. `deploy-server-to-remote-machine.yml`. This is an Ansible playbook. With it you can deploy the **echo-server** project to the remote Linux machine. This deploy will simply clone this repository to the `/home/usr/` directory on that machine and prepare the virtual environment.
6. `Jenkinsfile.template`. This a Jenkins pipeline file. With it you can target this repository in your Jenkins to build and run the aforementioned docker image with different parameters. This particular file has file extension `.template` because it has some placeholder values, that you're supposed to update with your own.

## Running the instance of echo-server
You don't need any additional dependencies to start the instance of **echo-server**, excluding the installed Python with >=3.10 version.

Simply type:

```sh
# Linux, macOS
python3 src/main.py

# Windows (with additional arguments, if you want)
python .\src\main.py --host="127.0.0.1" --port=15000
```
And you will have the running instance of **echo-server** with default parameters:
```sh
2025-08-29 18:29:21,978 [INFO] __main__: Starting EchoServer on the address: "http://localhost:8080" ...
```

## EchoServer API endpoints

There are only two API endpoints for the **echo-server** and both are relatively simlple:

### Get "hello" string
* **Request**: GET /hello
* **Response code**: 200 OK
* **Response body**: 'hello'
* **curl**: `curl -XGET 'http:localhost:8080/hello'`

### Get randomized string
* **Request**: GET /random
* **Query parameters**:
    - length (int | str, default is '10'): Length of the expected randomized string
    - digits (boolean | str, default is 'true'): Allow digits in the the expected randomized string
    - lowercase (boolean | str, default is 'true'): Allow lowercase ascii letters in the the expected randomized string
    - uppercase (boolean | str, default is 'false'): Allow uppercase ascii letters in the the expected randomized string
* **Response code**: 200 OK or 400 Bad Request if query params are invalid
* **Response body**: <RANDOMIZED_STRING>
* **curl**: `curl -XGET 'http://localhost:8080/random?length=20&digits=false&uppercase=True'`

## EchoServer client script

### Installation
**NOTE**: Installation of the correct [Python](https://www.python.org/downloads/) version goes outside of the scope of this particular guide.
```sh
# Linux, macOS
python3 -m venv venv
source venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
pip install -e src/

# Windows
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -e .\src\
```

### Usage

Script that serves as the EchoServer client.

This script allows the user to use it in two modes:
1. `local` Makes a GET request to the **/hello** endpoint of the running instance of EchoServer
   and saves the phrase from server response to the local file by a given name to the 
   `output/` directory.
   File will be rewritten every time because it's always the same phrase.

   Example:
   ```sh
   python3 echoserver_client.py -m=local --server_address='http://127.0.0.1:8080'
   --filename='testname.txt'
   ```

2. `remote` Makes a GET request to the **/random** endpoint (without any query params) of the running
   instance of EchoServer, then connects via SSH to a remote machine, and saves the
   randomly generated text from server response to the file by a given name. Each new
   phrase will be added to the file.

   Example:
   ```sh
   python3 echoserver_client.py -m=remote --remote_host='192.168.100.30'
   --remote_creds='username:password' --filename='another_name.txt'
   ```

If you don't provide the address of the currently running instance of EchoServer then
this script will start this instance automatically at the address "http:///localhost:8080".
This can lead to problems if you have some locally running instances of other web services, so be careful.

Also, if you want to use the **remote mode**, then **you have to provide both remote host
address and the user credentials** for SSH access to this host.


### Usage example:
Apllying client:

```sh
(venv) PS C:\Users\User\Path-To-Project\echo-server> python .\echoserver_client.py -m=remote --server_address='http://127.0.0.1:15000' --remote_host='192.168.100.30' --remote_creds='remote_username:remote_password' --filename='example.txt'

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
Install Docker client [depending on your platform](https://docs.docker.com/engine/install/). That's the hardest part.

Next part is pretty easy:
```sh
# If you want, you can just name it "echoserver_client" instead

docker build -t IMAGE_NAME:IMAGE_TAG .
```

### Running image

`local` example:
```
(venv) PS C:\Users\User\Path-To-Project\echo-server> docker run --rm -v .:/app/output echoserver_client -m=local -f="local-example.txt"
Selected mode: local
[17:38:51] Server address was not provided, setting up   echoserver_client.py:69
           server in daemon thread...
           EchoServer started locally at the address of  echoserver_client.py:74
           "http://localhost:8080"
127.0.0.1 - - [29/Aug/2025 17:38:51] "GET /hello HTTP/1.1" 200 -
           Successfully received response from the       echoserver_client.py:94
           endpoint /hello
           Stopping EchoServer...                        echoserver_client.py:80
           EchoServer stopped successfully               echoserver_client.py:83
(venv) PS C:\Users\User\Path-To-Project\echo-server> cat .\local-example.txt
hello
```
**NOTE**:
Notice how we're mounting the volume in the example above. This is because we want to save the file after docker container will be removed. Here we're mount the volume to the
current directory.

`remote` example:
```
(venv) PS C:\Users\User\Path-To-Project\echo-server> docker run --rm echoserver_client -m=remote -f="remote-example.txt" --remote_host="192.168.100.30" --remote_creds="username:password"                 
Selected mode: remote
[17:42:49] Server address was not provided, setting up   echoserver_client.py:69
           server in daemon thread...
           EchoServer started locally at the address of  echoserver_client.py:74
           "http://localhost:8080"
127.0.0.1 - - [29/Aug/2025 17:42:49] "GET /random HTTP/1.1" 200 -
           Successfully received response from the      echoserver_client.py:107
           endpoint /random
           Generated phrase: "qtatf2zj39"
[17:42:50] Stopping EchoServer...                        echoserver_client.py:80
           EchoServer stopped successfully               echoserver_client.py:83

(venv) PS C:\Users\User\Path-To-Project\echo-server> ssh username@192.168.100.30 "cat remote-example.txt"
username@192.168.100.30's password: 
qtatf2zj39
```

## Makefile

Install the [make](https://www.gnu.org/software/make/manual/make.html) program depending on your platform.

This particular **Makefile** has only two targets:
- `build_image`. If selected, this will build the aforementioned docker image .
- `prepare_venv`. If selected, this will create the Python virtual environment for the **echo-server** client script and will install all of the neccessary dependencies there.

Simply type:
```sh
make TARGET_NAME
```

## Ansible Playbook

**NOTE**: Ansible only works on Linux machines, so if you want to check this playbook on Windows, you should use [WSL](https://learn.microsoft.com/en-us/windows/wsl/install). Check how to install the Ansible [here](https://docs.ansible.com/ansible/latest/installation_guide/installation_distros.html).


The `deploy-server-to-remote-machine.yml` playbook serves as a quick way to deploy echo-server project to the remote machine. It should work with machines that are using Debian-like OS (e.g. Ubuntu).

This is a very simplistic approach where the playbook will clone this repository on the remote machine in user home directory. Then it will create the virtual environment in which user should be able to run client or simply launch the echo-server.

Notice that this playbook requires the privilege escalation. This is because we want to make sure that the latest version of Python 3 is installed on the remore machine, before attempting to create virtual environment.

So the playbook should be run like this:
```sh
ansible-playbook -v -K deploy-server-to-remote-machine.yml
```

Enter the user password when being asked and that's it.


## Jenkins pipeline

### Preparation

**NOTE**: If you don't have the prepared Jenkins environment, you can prepare it from the [official installation guide](https://www.jenkins.io/doc/book/installing/).

To use this Jenkins file example you should create at least one set of **Credentials** for your remote user.
After that all you need to do after this is to take your credentails ID and write it here:

```groovy
    environment {
        IMAGE_NAME = 'echoserver_client'
        IMAGE_TAG  = 'latest'
        HELLO_STRING = 'hello'
        REMOTE_CREDS = credentials('YOUR_CREDENTIALS_ID')
    }
```

Then you should rename this file to `Jenkinsfile` and you should be ready to
add this file to your **Pipeline** job in Jenkins. Or rather, you can create new job that will based on this pipeline file.

### Parameters

This pipeline has only 3 parameters.
- `MODE`. Same as the *--mode* argument to the **echoserver_client.py** script. Can be either **local** or **remote**.
- `FILENAME`. Same as the *--filename* argument to the **echoserver_client.py** script. Default is **filename.txt**.
- `REMOTE_HOST`. Same as the *--remote_host* argument to the **echoserver_client.py** script. Required for remote mode.

### Stages

1. `Build EchoServer client image`. Creates the aforementioned Docker image with prepared **echoserver_client.py** script.
2. `Run EchoServer client`. Executes the docker container based on the created image with the given `MODE` argument.
3. `Verify EchoServer client run results`. Checks the changes after the previous stage, validates that the files are present/created.
