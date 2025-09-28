@echo off
set PROJECT_ID=%1
set REGION=us-central1
set SERVICE_NAME=test-generator

if "%PROJECT_ID%"=="" (
    echo Error: Please provide PROJECT_ID as argument
    echo Usage: deploy.bat your-project-id
    exit /b 1
)

echo 🚀 Deploying Test Generator to Cloud Run...

REM Set the project
gcloud config set project %PROJECT_ID%

REM Build and deploy
echo 🔨 Building and deploying...
gcloud run deploy %SERVICE_NAME% --source . --region=%REGION% --platform=managed --allow-unauthenticated --memory=2Gi --cpu=2 --timeout=900 --max-instances=10 --set-env-vars="GOOGLE_CLOUD_PROJECT=%PROJECT_ID%,GOOGLE_CLOUD_REGION=%REGION%" --execution-environment=gen2

if %ERRORLEVEL% EQU 0 (
    echo ✅ Deployment complete!
    echo 🔧 Getting service URL...
    gcloud run services describe %SERVICE_NAME% --region=%REGION% --format="value(status.url)"
) else (
    echo ❌ Deployment failed!
)