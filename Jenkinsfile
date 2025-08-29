pipeline {

    agent any

    parameters {
        choice(
            name: 'MODE',
            choices: ['local', 'remote'],
            description: 'Modes of the echo-server client'
        )
        string(
            name: 'FILENAME',
            defaultValue: 'filename.txt',
            description: 'Name of the file to which the text from server response will be saved (default: "filename.txt")'
        )
        string(
            name: 'REMOTE_HOST',
            defaultValue: '',
            description: 'Host address of the remote machine where the file will be saved via SSH (required for remote mode)'
        )
    }

    environment {
        IMAGE_NAME = 'echoserver_client'
        IMAGE_TAG  = 'latest'
        REMOTE_CREDS = credentials('794bee4e-98ab-4efb-bf27-056564d60977')
    }

    stages {
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${IMAGE_NAME}:${IMAGE_TAG}")
                }
            }
        }

        stage('Run Container with given parameters') {
            steps {
                script {
                    if (params.MODE == 'local') {
                        sh """
                        docker run --rm -v \$(pwd):/app/output ${IMAGE_NAME}:${IMAGE_TAG} -m=${params.MODE} -f=${params.FILENAME}
                        ls -l ${params.FILENAME} || true
                        """
                    }
                    if (params.MODE == 'remote') {
                        sh """
                        docker run --rm -v .:/app/output ${IMAGE_NAME}:${IMAGE_TAG} \
                          -m=${params.MODE} \
                          -f=${params.FILENAME} \
                          --remote_host=${params.REMOTE_HOST} \
                          --remote_creds=$REMOTE_CREDS_USR:$REMOTE_CREDS_PSW
                        """
                    }
                }
            }
        }
    }
}