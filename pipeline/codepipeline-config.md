# CI/CD Pipeline Configuration
This project utilizes a fully automated AWS CodePipeline to orchestrate the transition of code from commit to a live, resilient production environment.

**Stage 1: Source (AWS CodeCommit)**
    - **Repository**: ``wk1-summer_sky``

    - **Branch**: ``main``

    - **Detection**: Triggered automatically via Amazon EventBridge on every ``git push``.

    - **Output**: Source artifact containing the latest application code and ``buildspec.yml``.

**Stage 2: Build (AWS CodeBuild)**
- **Environment**: ``aws/codebuild/amazonlinux2-x86_64-standard:5.0``

- **Privileged Mode**: Enabled (required for Docker daemon to build images).

- **Key Operations**:

    1. **Login**: Authenticates Docker to Amazon ECR.

    2. **Build**: Packages the Flask application into a Docker image.

    3. **Tagging**: Applies a :latest tag and a unique :COMMIT_ID tag for version tracking.

    4. **Push**: Uploads the image to the ECR repository.

**Artifact**: Generates an ``imagedefinitions.json`` file used by ECS to identify the new image URI.

**Stage 3: Deploy (Amazon ECS - Native Blue/Green)**

- **Action Provider**: ECS (Blue/Green)

- **Deployment Mechanism**:

    - **Target Group 1 (Blue)**: Port 80 (Current Production).

    - **Target Group 2 (Green)**: Port 80 (New Release).

    - **Test Listener**: Port 8080.

- **Workflow**:

1. The pipeline triggers a new **Task Definition** revision.

2. The ECS Service spins up the "Green" tasks.

3. **Validation**: The new code is accessible via the Test Listener (8080) for smoke testing.

4. **Traffic Swap**: Once health checks pass, the ALB shifts 100% of production traffic (Port 80) to the Green tasks.

5. **Termination**: The old Blue tasks are drained and stopped after a 3-minute "bake time."

---
## Resilience & Observability Integration

**Fail-Fast Methodology**: During the 'Deploy' stage, if the **CloudWatch Alarms** (CPU/Memory/ALB 5XX) trigger or the ECS **Deployment Circuit Breaker** detects a crash-loop (like the 500-error failure test), the pipeline automatically halts the traffic swap. This ensures that a faulty build never reaches the primary Port 80 audience."