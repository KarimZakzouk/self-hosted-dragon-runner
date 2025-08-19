# 🐉 Self-Hosted GitHub Actions Runner

> **Always-on EC2 GitHub Actions runner for reliable CI/CD workflows**

Transform your CI/CD pipeline with a dedicated, always-available self-hosted runner on AWS EC2. Perfect for projects requiring custom environments, specific software, consistent performance, or enhanced security controls.

## ✨ Features

- �️ **Always Available** - Dedicated EC2 instance ready for your workflows 24/7
- ⚡ **Instant Execution** - No startup delays, workflows run immediately
- 🔧 **Persistent Environment** - Keep tools, dependencies, and cache between runs
- � **Consistent Performance** - Predictable resources and execution times
- 🏗️ **Infrastructure as Code** - Terraform-managed, repeatable deployments
- 🔒 **Secure** - Isolated EC2 instance with proper security groups

## 🚀 How to Use

### Setup Your Always-On Runner

Perfect for consistent CI/CD workflows with zero startup time.

#### 📋 **Start Runner:**
1. **Navigate to Runner Settings**
   ```
   GitHub Repository → Settings → Actions → Runners
   ```

2. **Add New Runner**
   - Click **"New self-hosted runner"**
   - Select **Linux** as your OS
   - Copy the provided registration commands

3. **Configure on Your EC2 Instance**
   ```bash
   # SSH into your EC2 instance first
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Example commands from GitHub (yours will be different)
   mkdir actions-runner && cd actions-runner
   curl -o actions-runner-linux-x64-2.311.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
   tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz
   ./config.sh --url https://github.com/KarimZakzouk/self-hosted-dragon-runner --token YOUR_TOKEN
   
   # Install as a service for always-on operation
   sudo ./svc.sh install
   sudo ./svc.sh start
   ```

#### 🛑 **Stop Runner:**
1. **Stop the Service**
   ```bash
   # SSH into your EC2 instance
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Stop the runner service
   cd actions-runner
   sudo ./svc.sh stop
   ```

2. **Remove from GitHub**
   ```
   GitHub Repository → Settings → Actions → Runners
   ```
   - Click the **"..."** menu next to your runner
   - Select **"Remove"** to unregister

#### 🔄 **Run Your Workflow:**
1. **Trigger Manually**
   ```
   GitHub Repository → Actions → Select Workflow → "Run workflow"
   ```

2. **Or Push Code Changes**
   ```bash
   git add . && git commit -m "trigger workflow" && git push
   ```

> **💡 Pro Tip:** Since your runner is always on, workflows execute immediately with no cold start delays!
