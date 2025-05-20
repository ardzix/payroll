pipeline {
    agent { label 'escrow prod' }

    environment {
        DEPLOY = 'true'
        DOCKER_IMAGE = 'ardzix/payroll_system' // DockerHub repo
        DOCKER_REGISTRY_CREDENTIALS = 'ard-dockerhub' // Jenkins credentials ID for DockerHub PAT
        NAMESPACE = 'payroll_system' // Service name
        STACK_NAME = 'payroll_system' // Swarm stack name
        REPLICAS = '1' // Number of service replicas
        NETWORK_NAME = 'production' // Swarm overlay network
    }

    stages {
        stage('Clean Workspace') {
            steps {
                script {
                    sh '''
                        # Clean everything except Jenkinsfile
                        find . -mindepth 1 -maxdepth 1 ! -name 'Jenkinsfile' -exec rm -rf {} +
                        ls -la
                    '''
                }
            }
        }

        stage('Checkout Code') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'github-ardzix', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
                        sh '''
                            # Remove the Jenkinsfile temporarily
                            mv Jenkinsfile ../Jenkinsfile.tmp
                            
                            # Clean the workspace completely
                            rm -rf ./*
                            rm -rf ./.??*
                            
                            # Clone the repository with credentials
                            git clone https://${GIT_USER}:${GIT_TOKEN}@github.com/ardzix/payroll.git .
                            
                            # Restore the Jenkinsfile
                            mv ../Jenkinsfile.tmp Jenkinsfile
                            
                            ls -la
                        '''
                    }
                }
            }
        }

        stage('Inject Environment Variables') {
            steps {
                script {
                    withCredentials([
                        file(credentialsId: 'payroll-system-env', variable: 'ENV_FILE'),
                        string(credentialsId: 'ms-arnatech-storage-access', variable: 'AWS_ACCESS_KEY_ID'),
                        string(credentialsId: 'ms-arnatech-storage-secret', variable: 'AWS_SECRET_ACCESS_KEY')
                    ]) {
                        sh """
                            # Copy the .env file to the root
                            cp "${ENV_FILE}" ./.env.tmp
                            
                            # Update S3 credentials in the temporary file
                            sed -i "s|^AWS_ACCESS_KEY_ID=.*|AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}|" ./.env.tmp
                            sed -i "s|^AWS_SECRET_ACCESS_KEY=.*|AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}|" ./.env.tmp
                            
                            # Move the temporary file to the final location
                            mv ./.env.tmp ./.env
                            
                            # Verify the .env file was created
                            ls -la ./.env
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${DOCKER_IMAGE}:latest", "--file Dockerfile .")
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKER_REGISTRY_CREDENTIALS) {
                        docker.image("${DOCKER_IMAGE}:latest").push()
                    }
                }
            }
        }

        stage('Deploy to Swarm') {
            when {
                expression { return env.DEPLOY?.toBoolean() ?: false }
            }
            steps {
                withCredentials([
                    sshUserPrivateKey(credentialsId: 'stag-arnatech-sa-01', keyFileVariable: 'SSH_KEY_FILE'),
                    usernamePassword(credentialsId: 'ard-dockerhub', usernameVariable: 'DOCKERHUB_CREDENTIALS_USR', passwordVariable: 'DOCKERHUB_CREDENTIALS_PSW')
                ]) {
                    sh """
                        # First, create the directory on the server and copy the .env file
                        ssh -i "${SSH_KEY_FILE}" -o StrictHostKeyChecking=no root@172.105.124.43 "mkdir -p /root/payroll-system"
                        scp -i "${SSH_KEY_FILE}" -o StrictHostKeyChecking=no ./.env root@172.105.124.43:/root/payroll-system/.env

                        # Then deploy the service
                        ssh -i "${SSH_KEY_FILE}" -o StrictHostKeyChecking=no root@172.105.124.43 -p 22 "
                            # Ensure Docker Swarm is initialized
                            docker swarm init || true

                            # Ensure the overlay network exists
                            docker network create --driver overlay ${NETWORK_NAME} || true

                            # Deploy or update the service
                            docker service rm ${NAMESPACE} || true
                            docker service create --name ${NAMESPACE} \
                                --replicas ${REPLICAS} \
                                --network ${NETWORK_NAME} \
                                --env-file /root/payroll-system/.env \
                                ${DOCKER_IMAGE}:latest
                            "
                    """
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline finished!'
        }
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
} 