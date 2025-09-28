@echo off
set PROJECT_ID=%1

if "%PROJECT_ID%"=="" (
    echo Error: Please provide PROJECT_ID as argument
    echo Usage: setup-gcp.bat your-project-id
    exit /b 1
)

echo 🔧 Setting up GCP project for Test Generator...

REM Set the project
gcloud config set project %PROJECT_ID%

echo 💳 Please ensure billing is enabled for project: %PROJECT_ID%

REM Enable required APIs
echo 📋 Enabling required APIs...
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable logging.googleapis.com

REM Create service account
echo 🔐 Creating service account...
gcloud iam service-accounts create test-generator-sa --display-name="Test Generator Service Account" --description="Service account for Test Generator application"

REM Grant permissions
echo 🔑 Granting permissions...
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:test-generator-sa@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/aiplatform.user"
gcloud projects add-iam-policy-binding %PROJECT_ID% --member="serviceAccount:test-generator-sa@%PROJECT_ID%.iam.gserviceaccount.com" --role="roles/logging.logWriter"

echo ✅ GCP setup complete!
echo 🔧 Next step: Run deploy.bat %PROJECT_ID%