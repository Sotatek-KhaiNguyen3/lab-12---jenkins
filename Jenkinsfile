pipeline {
    agent {
        label 'forlab'
    }
    
    environment {
        // Biến từ Jenkins Credentials
        REGISTRY_URL = credentials('registry-url')
        IMAGE_NAME = credentials('image-name')
        SONAR_PROJECT_KEY = credentials('sonar-project-key')
        SONAR_ORG = credentials('sonar-org')
        SONAR_TOKEN = credentials('sonar-token')
        DB_KEY = credentials('db-key')
        
        // Biến build-time
        IMAGE_TAG = "${env.BRANCH_NAME}-${env.BUILD_ID}"
        IMAGE_REF = "${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    }
    
    parameters {
        choice(name: 'BRANCH', choices: ['main', 'develop'], description: 'Branch to build')
        choice(name: 'ENVIRONMENT', choices: ['dev', 'staging', 'prod'], description: 'Deploy environment')
        booleanParam(name: 'RUN_SONAR', defaultValue: true, description: 'Run SonarQube')
        booleanParam(name: 'RUN_TRIVY', defaultValue: true, description: 'Run Trivy scan')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.BRANCH_NAME = params.BRANCH
                }
            }
        }
        
        stage('Lint & Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install flake8 black detect-secrets
                    flake8 todolist/ --count --select=E9,F63,F7,F82 || true
                    detect-secrets scan --all-files --force-use-all-plugins || true
                '''
            }
        }
        
        stage('SonarQube') {
            when { expression { params.RUN_SONAR == true } }
            steps {
                withSonarQubeEnv('SonarCloud') {
                    sh """
                        sonar-scanner \
                          -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                          -Dsonar.organization=${SONAR_ORG} \
                          -Dsonar.sources=. \
                          -Dsonar.host.url=https://sonarcloud.io \
                          -Dsonar.login=${SONAR_TOKEN}
                    """
                }
            }
        }
        
        stage('Quality Gate') {
            when { expression { params.RUN_SONAR == true } }
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        
        stage('Build Docker') {
            steps {
                script {
                    docker.build("${IMAGE_REF}")
                }
            }
        }
        
        stage('Security Scan') {
            when { expression { params.RUN_TRIVY == true } }
            steps {
                sh """
                    trivy image --severity HIGH,CRITICAL \
                      --exit-code 1 \
                      --ignore-unfixed \
                      ${IMAGE_REF} || true
                """
            }
        }
        
        stage('Push to Registry') {
            steps {
                script {
                    docker.withRegistry("http://${REGISTRY_URL}") {
                        docker.image("${IMAGE_REF}").push()
                    }
                }
            }
        }
        
        stage('Deploy to Swarm') {
            steps {
                script {
                    // Environment config
                    def configs = [
                        'dev': [stack: 'todolist-dev', replicas: '1', db: 'todolist_dev'],
                        'staging': [stack: 'todolist-staging', replicas: '2', db: 'todolist_staging'],
                        'prod': [stack: 'todolist-prod', replicas: '2', db: 'todolist']
                    ]
                    
                    def cfg = configs[params.ENVIRONMENT]
                    
                    sh """
                        export STACK_NAME="${cfg.stack}"
                        export IMAGE_REF="${IMAGE_REF}"
                        export KEY="${DB_KEY}"
                        export DB_NAME="${cfg.db}"
                        export REPLICAS="${cfg.replicas}"
                        
                        docker stack deploy \\
                          --with-registry-auth \\
                          -c deploy/docker-compose.yml \\
                          \${STACK_NAME}
                        
                        echo "✅ Deployed to ${params.ENVIRONMENT}"
                        sleep 5
                        docker stack services \${STACK_NAME}
                    """
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
            sh 'docker system prune -f'
        }
        success {
            echo "✅ Pipeline thành công!"
        }
        failure {
            echo "❌ Pipeline thất bại!"
        }
    }
}