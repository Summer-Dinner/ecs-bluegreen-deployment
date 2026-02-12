# ALB Listener Configuration

This project implements a validated Blue/Green strategy using a dual-listener architecture. This ensures that new code is not only "healthy" according to AWS, but also manually or programmatically verified before the final traffic swap.

1. **Production Listener (Port 80)**
    - **Purpose**: Serves live traffic to end-users.
    - **Routing**: Points to the Blue (Stable) Target Group.
    - **Cutover**: Only shifts to the Green Target Group after the Test Listener validation is complete.

2. **Test Listener (Port 8080)**
    - **Purpose**: Provides a "Preview" environment for the Green (New) Target Group.

    - **Routing**: Always points to the Target Group currently undergoing deployment.

    - **Usage**: Before the final shift, I can access http://ALB-DNS:8080 to verify the new version's UI and API responses (such as the ``/health`` failure test) without affecting users on Port 80.

### Targer Group Mapping
|Feature|Blue Target Group|Green Target Group
|:--|:--|:--
|**Identifier**|new-wk3-alb-target|wk4-green-target
**Protocol/Port**|HTTP : 80|HTTP : 80
**Target Type**|IP (Fargate)|IP (Fargate)
**Health Check Path**|/health|/health

---
### Resilience
**Validation-Driven Deployment**:  By utilizing a **Test Listener (Port 8080)**, I introduced a critical manual-gate/automated-check layer. During my failure test (injecting a 500 error on the ``/health`` endpoint), the Test Listener allowed me to identify the breakage immediately on the Green environment. Because the traffic swap had not yet occurred on the Production Listener (Port 80), the system's availability remained at 100% despite the 'faulty' code being deployed to the cluster.