pipeline {
    agent {
        label 'forlab'  // Dùng built-in node với label "forlab"
    }
    
    environment {
        // Biến từ Jenkins Credentials/Parameters
        REGISTRY_URL = credentials('REGISTRY_URL')
        IMAGE_NAME = credentials('IMAGE_NAME')
        SONAR_PROJECT_KEY = credentials('SONAR_PROJECT_KEY')
        SONAR_ORG = credentials('SONAR_ORG')
        SONAR_TOKEN = credentials('SONAR_TOKEN')
        
        // Biến môi trường cho deploy
        STACK_NAME = credentials('STACK_NAME')
        DB_KEY = credentials('DB_KEY')
        DB_NAME = credentials('DB_NAME')
        REPLICAS = credentials('REPLICAS')
        
        // Biến build-time
        IMAGE_TAG = "${env.BRANCH_NAME}-${env.BUILD_ID}"
        IMAGE_REF = "${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    }
    
    parameters {
        choice(name: 'BRANCH', choices: ['main', 'develop'], description: 'Branch to build')
        booleanParam(name: 'RUN_SONAR', defaultValue: true, description: 'Run SonarQube analysis')
        booleanParam(name: 'RUN_TRIVY', defaultValue: true, description: 'Run Trivy security scan')
        choice(name: 'DEPLOY_ENV', choices: ['dev', 'staging', 'prod'], description: 'Deploy environment')
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    // Set branch từ parameter
                    env.BRANCH_NAME = params.BRANCH
                }
            }
        }
        
        stage('Lint & Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install flake8 black isort pylint detect-secrets
                    
                    # Lint Python
                    flake8 todolist/ --count --select=E9,F63,F7,F82 --show-source --statistics || true
                    
                    # Secret scanning
                    detect-secrets scan --all-files --force-use-all-plugins || true
                '''
            }
        }
        
        stage('SonarQube Analysis') {
            when {
                expression { params.RUN_SONAR == true }
            }
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
            when {
                expression { params.RUN_SONAR == true }
            }
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        
        stage('Build Docker Image') {
            steps {
                script {
                    docker.build("${IMAGE_REF}")
                }
            }
        }
        
        stage('Trivy Security Scan') {
            when {
                expression { params.RUN_TRIVY == true }
            }
            steps {
                sh """
                    trivy image --severity HIGH,CRITICAL \
                      --exit-code 1 \
                      --ignore-unfixed \
                      --format table \
                      ${IMAGE_REF}
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
                    // Set environment-specific variables
                    def deployConfig = [
                        'dev': [stack: 'todolist-dev', replicas: '1', db: 'todolist_dev'],
                        'staging': [stack: 'todolist-staging', replicas: '2', db: 'todolist_staging'],
                        'prod': [stack: 'todolist-prod', replicas: '2', db: 'todolist']
                    ]
                    
                    def config = deployConfig[params.DEPLOY_ENV]
                    
                    sh """
                        export STACK_NAME="${config.stack}"
                        export IMAGE_REF="${IMAGE_REF}"
                        export KEY="${DB_KEY}"
                        export DB_NAME="${config.db}"
                        export REPLICAS="${config.replicas}"
                        
                        docker stack deploy \\
                          --with-registry-auth \\
                          -c deploy/docker-compose.yml \\
                          \${STACK_NAME}
                        
                        # Verify deployment
                        sleep 10
                        docker stack services \${STACK_NAME}
                    """
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()  // Xóa workspace
            sh 'docker system prune -f'  // Cleanup Docker
        }
        success {
            echo "✅ Pipeline thành công!"
        }
        failure {
            echo "❌ Pipeline thất bại!"
        }
    }
}