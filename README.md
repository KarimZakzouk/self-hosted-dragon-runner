# 🐉 Self-Hosted GitHub Actions Runner

Automated EC2 GitHub Actions runner management via Lambda functions.

## 🚀 How to Use

### Method 1: Simple Way (GitHub UI)

**Start Runner:**
1. Go to **GitHub → Settings → Actions → Runners**
2. Click **"New self-hosted runner"**
3. Follow GitHub's setup instructions on your server

**Stop Runner:**
1. Go to **GitHub → Settings → Actions → Runners**
2. Click the **"..."** next to your runner
3. Click **"Remove"**

**Re-run Job:**
1. Go to **GitHub → Actions**
2. Click on your workflow
3. Click **"Re-run jobs"** or **"Run workflow"**

### Method 2: Advanced Way (API - What I Built)

**Start Runner:**
```bash
curl -X POST https://0xwfoeelwa.execute-api.us-east-1.amazonaws.com/lambda/create
```
✅ Response: `{"message": "Runner created", "instanceId": "i-xxxxxxxxxxxxxxxxx"}`

**Stop Runner:**
```bash
curl -X POST https://0xwfoeelwa.execute-api.us-east-1.amazonaws.com/lambda/destroy
```
✅ Response: `{"message": "Runner destroyed", "instances": ["i-xxxxxxxxxxxxxxxxx"]}`

**Re-run Job:**
1. Go to **GitHub → Actions**
2. Click on your workflow  
3. Click **"Re-run jobs"** or **"Run workflow"**

**Why Advanced Way is Better:**
- ⚡ **Automated**: No manual server setup
- 💰 **Cost-effective**: Auto-destroys to save money
- 🔄 **On-demand**: Create/destroy as needed
- 🏗️ **Infrastructure as Code**: Repeatable setup

## ⚡ Example Workflow

The dragon workflow runs cowsay with a dragon:
```yaml
name: Cowsay Dragon
on: workflow_dispatch
jobs:
  dragon-job:
    runs-on: self-hosted
    steps:
      - name: Install cowsay
        run: sudo apt-get install cowsay -y
      - name: Dragon says hello
        run: export PATH=$PATH:/usr/games && cowsay -f dragon "Hello from self-hosted runner!"
```

## 🔧 Setup (One-time)

1. **Configure environment** in `terraform/lambda/.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   GITHUB_REPO=KarimZakzouk/self-hosted-dragon-runner
   AWS_REGION=us-east-1
   KEY_PAIR_NAME=MyKeyPair
   ```

2. **Deploy infrastructure**:
   ```bash
   cd terraform && terraform apply
   ```

## 💡 Tips

- Runner takes ~2-3 minutes to appear in GitHub
- Runners auto-expire after 60 minutes
- Always destroy when done to save costs
- Check GitHub Settings → Actions → Runners for status
