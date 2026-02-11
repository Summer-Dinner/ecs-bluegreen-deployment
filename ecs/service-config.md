# ECS Service Configuration

The application is orchestrated as an Amazon ECS Service using the AWS Fargate (Serverless) launch type. This configuration ensures that the desired state of the application is maintained without manual server intervention.

1. Compute & Scaling
    - Launch Type: FARGATE .

    - Platform Version: LATEST (1.4.0).

    - Desired Tasks: 2 (Distributed across multiple Availability Zones for HA).

    - Auto-Scaling Policy: * Metric: Target Tracking on ``ECSServiceAverageCPUUtilization``.

        - Threshold: 70%.

2. Networking & Security
    - VPC Mode: awsvpc (Each task receives its own Elastic Network Interface and private IP).

    - Subnets: Private subnets across us-east-1a and us-east-1b.

    - Security Group Rules:

    - Inbound: Port 80  restricted to traffic originating only from the Application Load Balancer's Security Group.

    - Outbound: All traffic (0.0.0.0/0) to allow for image pulls from ECR and logging to CloudWatch.

3. Load Balancing & Health Checks
    - Load Balancer: Application Load Balancer (ALB).

    - Target Group Mapping:

        - Protocol: HTTP

        - Target Port: 5000 (Container Port).

        - Health Check Path: ``/health``

        - Health Check Thresholds: Healthy: 2, Unhealthy: 3, Interval: 30s.

    - Deregistration Delay: 60 seconds (Ensures active connections are drained before a task is terminated).

---

# ECS Native Blue/Green Service Config
### Native ECS Blue/Green Implementation:
Unlike traditional setups that require AWS CodeDeploy, this project utilizes the Native ECS Blue/Green Deployment Controller. By leveraging ALB Target Group Weights, the ECS service scheduler orchestrates an 'all-at-once' traffic shift from the Blue environment to the Green environment. This reduces operational overhead by eliminating the need for AppSpec files and external deployment groups, while still providing near-instant rollback capabilities through ALB listener rule manipulation

1. **Deployment Controller**
    - Type: ``ECS`` (Native).

    - Strategy: ``Blue/Green``.

    - Benefit: Simplifies the pipeline by removing the need for a separate CodeDeploy "Deployment Group." ECS manages the Target Group weight swap itself.

2. **Target Group Orchestration**
Instead of a manual swap, ECS uses Target Group Weights within the ALB Listener rule:

    - **Blue Target Group**: Initially has a weight of 100 (100% traffic).

    - **Green Target Group**: Initially has a weight of 0.

    - **The Switch**: When the service is updated with a new Task Definition, ECS spins up the "Green" tasks. Once healthy, ECS automatically updates the ALB Listener rule to flip the weights (Blue: ``0``, Green: ``100``).

3. **Rollback & Failover**

    - **Manual Rollback**: A rollback can be triggered manually in the ECS console/CLI if it is observed that the ``/health`` endpoint fails health test and it instantly flips the ALB weights back to the Blue group.

    - **Automatic Rollback**: I configured the Bake Time to 3 minutes. If CloudWatch alarms (like your 5XX alarm) trigger during this bake time, ECS will abort and flip back automatically.