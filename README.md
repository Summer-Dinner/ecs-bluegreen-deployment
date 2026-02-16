# ECS Observability & Resilience Framework
## Deployment Strategy: Blue/Green
This project utilizes Native ECS Blue/Green Deployment. Unlike standard rolling updates, this strategy provisions a complete "Green" environment alongside the existing "Blue" environment. This allows for total environment isolation and near-instant cutover or rollback without affecting the steady state of the application.

---

### Traffic Control Mechanism
Traffic is managed via an Application Load Balancer (ALB) using a dual-listener configuration:

- **Production Listener (Port 80)**: Routes live traffic to the "Blue" Target Group.

- **Test Listener (Port 8080)**: Routes traffic to the "Green" Target Group for pre-deployment validation.

- **Shift Logic**: The ECS deployment controller manipulates Target Group weights. Only after the Green tasks pass health checks is the weight shifted 100% from Blue to Green.

---

### Failure Introduced in Green
To test system resilience, a **Logic Fault** was injected into the Green version of the application. I modified the ``/health`` endpoint in the Flask application code to return an ``HTTP 500 Internal Server Error`` instead of the standard ``200 OK``. This was designed to simulate a critical application-level failure that passed the container build phase but failed during the runtime "Bake Time."

---

### Rollback Decision
The ECS deployment controller prevented the green task set from becoming steady due to failing health checks. The production listener remained on the blue target group, ensuring no production traffic reached the unhealthy green tasks.

In native ECS blue/green deployments, traffic remains routed to the existing (blue) environment until the green task set passes health checks and is marked steady.

If the green tasks fail to stabilize, the deployment does not shift traffic, and the service continues serving from blue. ECS itself does not automatically revert traffic; instead, it *prevents the traffic shift*, effectively isolating the failure.

This behavior ensures that unhealthy green deployments do not impact live users, but the control to shift or revert remains with the operator or the deployment pipeline.

---

### How ECS Native Blue/Green Works Internally

- Two target groups are preconfigured: one for blue (production) and one for green (validation). 
- A single ALB listener can be reused with weighted rules if available, but most implementations use separate test listeners. 
- ECS deployment controller handles task set creation and registration to target groups.
- Traffic switches only after health checks pass; there is no built-in, gradual weighted shift with native ECS (unlike CodeDeploy). 

---

### Target Group Health Transition
The lifecycle of the Green targets during the failure followed a "Fail-Fast" pattern. Unlike the Blue targets, which remained Healthy, the Green targets moved through these states:

1. **Initial** (``unused``): Task is provisioned but not yet registered.

2. **Validation** (``initial``): Task is registered to the Green Target Group; health checks begin.

3. **Failure** (``unhealthy``): The application returns a 500 response. The ALB marks the target as unhealthy after 3 consecutive failures.

4. **Deregistration** (``draining``): The ECS Deployment Circuit Breaker identifies the failure and begins task termination.

**Analyst Insight**: Because I set the ``HealthCheckGracePeriodSeconds`` to 60s, the system allowed the application enough time to boot, ensuring that the Unhealthy signal was a genuine application error and not a premature network timeout.

---

### Cloudwatch Alarms

![UnhealtyHostCount](/app/images/Green-Target-UnhealthyHostCount.jpeg)
**Description**: Monitors the target that is failing health checks in the Green Target Group.
**Threshold**: If UnhealthyHostCount >= 1 for 1 minute during the deployment phase, an automatic rollback is triggered. This prevents traffic from shifting to a failing container.

![Alarm state change](/app/images/Alarm-state-change.png)
**Description**: This metric captures the moment a CloudWatch Alarm transitions from ``OK`` to ``ALARM`` state during a deployment
**Automated Rollback**: This alarm is configured as a "trigger" within the ECS Deployment Group. If this state change occurs during the traffic-shifting phase, ECS immediately halts the deployment and redirects 100% of traffic back to the "Blue" (original) environment.

**Visibility**: Ensures that the engineering team has real-time visibility into deployment health without needing to manually refresh the AWS Console.

![Production Stable](/app/images/Production-RequestCount.jpeg)
**Description**: Monitors the RequestCount on the Production Listener (Port 80) of the Application Load Balancer.
**Analysis**: We look for significant drops or spikes in traffic immediately following a shift. A steady request count indicates that the Blue/Green swap was transparent to the end-users and the new version is handling the load as expected.

---

### Blast Radius Analysis
- **Scope**: The failure was strictly isolated to the Green Target Group.

- **User Impact**: Zero. Live users hitting the ALB on Port 80 continued to be served by the stable Blue environment.

- **Infrastructure Impact**: Minimal. Only the additional Fargate tasks provisioned for the Green environment consumed resources before being decommissioned.

---

### Lessons Learned
1. **Test Listeners are Critical**: Relying solely on Port 80 for Blue/Green is risky. The 8080 listener allowed for verification without public exposure.

2. **Health Check Sensitivity**: Setting the HealthCheckGracePeriodSeconds correctly is vital to ensure the app has enough time to start before the circuit breaker kills the task.

3. **Observability beats Monitoring**: Simply knowing the task was "Down" wasn't enough; having centralized awslogs allowed me to see why the 500 error was occurring immediately.

4. **Deployment validation**: Observability signals (metrics + alarms) confirm safe deployment behavior.

---

## Outcome 
Safe Blue/Green deployment validated; controlled failure in Green prevented traffic exposure to production users. This demonstrates production-grade deployment and observability practices.
