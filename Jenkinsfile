pipeline {
    agent any

    environment {
        ECOMMERCE_SERVER = 'ubuntu@98.95.123.28'
        REMOTE_DIR = '/home/ubuntu/capstone/ecommerce-app'

        IMAGE_NAME = 'ecommerce-app'
        CONTAINER_NAME = 'ecommerce-app'
        TAR_NAME = 'ecommerce-app.tar'

        DB_CONTAINER = 'ecommerce-mysql'
        DB_NAME = 'ecommercedb'
        DB_USER = 'ecomuser'
        DB_PASSWORD = 'ecompass'
        DB_ROOT_PASSWORD = 'root123'

        BANK_PUBLIC_BASE = 'http://54-211-30-30.nip.io'
        MERCHANT_ACCOUNT = 'pageturn-books'
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Check Files') {
            steps {
                sh '''
                echo "Current workspace files:"
                ls -la
                '''
            }
        }

        stage('Run Tests If Available') {
            steps {
                sh '''
                if [ -d tests ]; then
                    echo "Tests folder found. Running tests..."
                    pip3 install -r requirements.txt
                    pip3 install pytest
                    pytest
                else
                    echo "No tests folder found. Skipping tests."
                fi
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                echo "Building ecommerce Docker image..."
                docker build -t $IMAGE_NAME:latest .
                '''
            }
        }

        stage('Save Docker Image') {
            steps {
                sh '''
                echo "Saving Docker image as tar file..."
                docker save $IMAGE_NAME:latest -o $TAR_NAME
                ls -lh $TAR_NAME
                '''
            }
        }

        stage('Prepare Remote Folder') {
            steps {
                sh '''
                echo "Preparing ecommerce server folder..."
                ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "
                    mkdir -p $REMOTE_DIR
                "
                '''
            }
        }

        stage('Copy Image to Ecommerce Server') {
            steps {
                sh '''
                echo "Copying ecommerce Docker image to ecommerce server..."
                scp -o StrictHostKeyChecking=no $TAR_NAME $ECOMMERCE_SERVER:$REMOTE_DIR/
                '''
            }
        }

        stage('Deploy Ecommerce App') {
            steps {
                sh '''
                echo "Deploying ecommerce app on ecommerce server..."

                ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "
                    cd $REMOTE_DIR &&

                    echo 'Creating Docker network if not existing...' &&
                    docker network create ecommerce-net || true &&

                    echo 'Checking MySQL container...' &&
                    if ! docker ps -a --format '{{.Names}}' | grep -w $DB_CONTAINER; then
                        echo 'Starting new ecommerce MySQL container...' &&
                        docker run -d \
                            --name $DB_CONTAINER \
                            --network ecommerce-net \
                            -e MYSQL_ROOT_PASSWORD=$DB_ROOT_PASSWORD \
                            -e MYSQL_DATABASE=$DB_NAME \
                            -e MYSQL_USER=$DB_USER \
                            -e MYSQL_PASSWORD=$DB_PASSWORD \
                            -v ecommerce_mysql_data:/var/lib/mysql \
                            mysql:8.0
                    else
                        echo 'MySQL container already exists. Starting it if stopped...' &&
                        docker start $DB_CONTAINER || true
                    fi &&

                    echo 'Waiting for MySQL to initialize...' &&
                    sleep 25 &&

                    echo 'Loading ecommerce Docker image...' &&
                    docker load -i $TAR_NAME &&

                    echo 'Stopping old ecommerce container if existing...' &&
                    docker stop $CONTAINER_NAME || true &&
                    docker rm $CONTAINER_NAME || true &&

                    echo 'Starting new ecommerce app container...' &&
                    docker run -d \
                        --name $CONTAINER_NAME \
                        --network ecommerce-net \
                        -p 80:5000 \
                        -e DB_HOST=$DB_CONTAINER \
                        -e DB_NAME=$DB_NAME \
                        -e DB_USER=$DB_USER \
                        -e DB_PASSWORD=$DB_PASSWORD \
                        -e BANK_PUBLIC_BASE=$BANK_PUBLIC_BASE \
                        -e MERCHANT_ACCOUNT=$MERCHANT_ACCOUNT \
                        $IMAGE_NAME:latest &&

                    echo 'Current running containers:' &&
                    docker ps
                "
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                echo "Waiting before health check..."
                sleep 10

                echo "Checking container status on ecommerce server..."
                ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "docker ps -a"

                echo "Checking ecommerce app locally from ecommerce server..."
                ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "curl --connect-timeout 10 --max-time 20 -f http://localhost/health"

                echo "Checking ecommerce app publicly from Jenkins..."
                curl --connect-timeout 10 --max-time 20 -f http://98-95-123-28.nip.io/health
                '''
            }
        }
    }

    post {
        success {
            echo 'Ecommerce app deployed successfully.'
        }

        failure {
            echo 'Ecommerce app deployment failed. Showing remote logs...'

            sh '''
            ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "
                echo '--- Docker containers ---' &&
                docker ps -a &&
                echo '--- Ecommerce app logs ---' &&
                docker logs $CONTAINER_NAME || true &&
                echo '--- Ecommerce MySQL logs ---' &&
                docker logs $DB_CONTAINER --tail 50 || true
            "
            '''
        }
    }
}
