pipeline {
    agent any

    environment {
        IMAGE_NAME = "amdp-registry.skala-ai.com/skala26a-ai2/sk044-frontend:latest"
        REGISTRY_URL = "amdp-registry.skala-ai.com"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Code Build') {
            steps {
                sh '''
                echo "Code build stage"
                ls -al
                ls -al frontend
                '''
            }
        }

        stage('Image Build') {
            steps {
                sh '''
                docker build -t $IMAGE_NAME -f frontend/Dockerfile ./frontend
                '''
            }
        }

        stage('Push Image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'harbor-credentials',
                    usernameVariable: 'HARBOR_USER',
                    passwordVariable: 'HARBOR_PASS'
                )]) {
                    sh '''
                    echo "$HARBOR_PASS" | docker login $REGISTRY_URL -u "$HARBOR_USER" --password-stdin
                    docker push $IMAGE_NAME
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                kubectl apply -f k8s/devops-frontend.yaml
                kubectl rollout restart deployment devops-frontend
                kubectl rollout status deployment devops-frontend
                '''
            }
        }
    }

    post {
        success {
            echo 'CI/CD pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed.'
        }
    }
}
