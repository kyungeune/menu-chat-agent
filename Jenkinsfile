pipeline {
    agent any

    environment {
        IMAGE_NAME = "amdp-registry.skala-ai.com/skala26a-ai2/sk044-frontend:latest"
        REGISTRY_URL = "amdp-registry.skala-ai.com"
        NAMESPACE = "class-2"
        BUILDER_NAME = "sk044builder"
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

        stage('Image Build & Push') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'harbor-credentials',
                    usernameVariable: 'HARBOR_USER',
                    passwordVariable: 'HARBOR_PASS'
                )]) {
                    sh '''
                    echo "$HARBOR_PASS" | docker login $REGISTRY_URL -u "$HARBOR_USER" --password-stdin

                    docker buildx create --name $BUILDER_NAME --use || true
                    docker buildx use $BUILDER_NAME
                    docker buildx inspect --bootstrap

                    docker buildx build \
                      --platform linux/amd64 \
                      -t $IMAGE_NAME \
                      -f frontend/Dockerfile ./frontend \
                      --push
                    '''
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh '''
                kubectl apply -f k8s/devops-frontend.yaml
                kubectl rollout restart deployment devops-frontend -n $NAMESPACE
                kubectl rollout status deployment devops-frontend -n $NAMESPACE --timeout=120s
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