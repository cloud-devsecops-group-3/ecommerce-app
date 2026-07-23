pipeline {
    agent any

    environment {
        ECOMMERCE_SERVER = 'ubuntu@98.95.123.28'
        REMOTE_DIR = '/home/ubuntu/capstone/ecommerce-app'

        IMAGE_NAME = 'ecommerce-app'
        CONTAINER_NAME = 'ecommerce-app'
        TAR_NAME = 'ecommerce-app.tar'

        APP_PORT = '5000'

        DB_CONTAINER = 'ecommerce-mysql'
        DB_NAME = 'ecommercedb'
        DB_USER = 'ecomuser'
        DB_PASSWORD = 'ecompass'
        DB_ROOT_PASSWORD = 'root123'

        BANK_PUBLIC_BASE = 'http://54.211.30.30:5001'
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
                sh 'ls -la'
            }
        }

        stage('Run Tests If Available') {
            steps {
                sh '''
                if [ -d tests ]; then
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
                sh 'docker build -t $IMAGE_NAME:latest .'
            }
        }

        stage('Save Docker Image') {
            steps {
                sh 'docker save $IMAGE_NAME:latest -o $TAR_NAME'
            }
        }

        stage('Prepare Remote Folder') {
            steps {
                sh '''
                ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "
                    mkdir -p $REMOTE_DIR
                "
                '''
            }
        }

        stage('Copy Image to Ecommerce Server') {
            steps {
                sh 'scp -o StrictHostKeyChecking=no $TAR_NAME $ECOMMERCE_SERVER:$REMOTE_DIR/'
            }
        }

        stage('Deploy Ecommerce App') {
            steps {
                sh '''
                ssh -o StrictHostKeyChecking=no $ECOMMERCE_SERVER "
                    cd $REMOTE_DIR &&

                    docker network create ecommerce-net || true &&

                    docker ps -a --format '{{.Names}}' | grep -w $DB_CONTAINER ||
                    docker run -d \
                        --name $DB_CONTAINER \
                        --network ecommerce-net \
                        -e MYSQL_ROOT_PASSWORD=$DB_ROOT_PASSWORD \
                        -e MYSQL_DATABASE=$DB_NAME \
                        -e MYSQL_USER=$DB_USER \
                        -e MYSQL_PASSWORD=$DB_PASSWORD \
                        -v ecommerce_mysql_data:/var/lib/mysql \
                        mysql:8.0 &&

                    echo 'Waiting for MySQL to initialize...' &&
                    sleep 25 &&

                    docker load -i $TAR_NAME &&

                    docker stop $CONTAINER_NAME || true &&
                    docker rm $CONTAINER_NAME || true &&

                    docker run -d \
                        --name $CONTAINER_NAME \
                        --network ecommerce-net \
                        -p $APP_PORT:$APP_PORT \
                        -e DB_HOST=$DB_CONTAINER \
                        -e DB_NAME=$DB_NAME \
                        -e DB_USER=$DB_USER \
                        -e DB_PASSWORD=$DB_PASSWORD \
                        -e BANK_PUBLIC_BASE=$BANK_PUBLIC_BASE \
                        -e MERCHANT_ACCOUNT=$MERCHANT_ACCOUNT \
                        $IMAGE_NAME:latest
                "
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                sleep 5
                curl -f http://98.95.123.28:5000/health
                '''
            }
        }
    }

    post {
        success {
            echo 'Ecommerce app deployed successfully.'
        }

        failure {
            echo 'Ecommerce app deployment failed. Check Jenkins console output.'
        }
    }
}
