import boto3
import os
import json
import time
import requests

# Function to load .env file if it exists
def load_env_file(env_file_path=".env"):
    """Load environment variables from .env file if it exists"""
    if os.path.exists(env_file_path):
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:  # Don't override existing env vars
                        os.environ[key] = value

# Load .env file if present (for local development)
load_env_file()

# Load environment variables
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "KarimZakzouk/self-hosted-dragon-runner")
KEY_PAIR_NAME = os.environ.get("KEY_PAIR_NAME", "MyKeyPair")
INSTANCE_TYPE = os.environ.get("INSTANCE_TYPE", "t2.micro")
AMI_ID = os.environ.get("AMI_ID", "ami-020cba7c55df1f615")

# Constants
INSTANCE_TAG_KEY = "GitHubRunner"
INSTANCE_TAG_VALUE = "True"
TTL_TAG_KEY = "ExpireAt"
SECURITY_GROUP_NAME = "github-runner-sg"

# Validate required environment variables
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN environment variable is required")

ec2 = boto3.client("ec2", region_name=AWS_REGION)

def get_or_create_security_group():
    """Get or create the security group for GitHub runners"""
    try:
        # Try to find existing security group
        response = ec2.describe_security_groups(
            Filters=[
                {"Name": "group-name", "Values": [SECURITY_GROUP_NAME]}
            ]
        )
        if response["SecurityGroups"]:
            return response["SecurityGroups"][0]["GroupId"]
    except Exception:
        pass
    
    # Create new security group
    try:
        response = ec2.create_security_group(
            GroupName=SECURITY_GROUP_NAME,
            Description="Security group for GitHub Actions runners"
        )
        sg_id = response["GroupId"]
        
        # Add inbound rules
        ec2.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[
                {
                    "IpProtocol": "tcp",
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "SSH"}]
                },
                {
                    "IpProtocol": "tcp", 
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTP"}]
                },
                {
                    "IpProtocol": "tcp",
                    "FromPort": 443,
                    "ToPort": 443,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0", "Description": "HTTPS"}]
                }
            ]
        )
        return sg_id
    except Exception as e:
        print(f"Error creating security group: {e}")
        # Return default security group as fallback
        return None

def find_existing_instance():
    response = ec2.describe_instances(
        Filters=[
            {"Name": f"tag:{INSTANCE_TAG_KEY}", "Values": [INSTANCE_TAG_VALUE]},
            {"Name": "instance-state-name", "Values": ["pending", "running"]}
        ]
    )
    instances = []
    for res in response["Reservations"]:
        for inst in res["Instances"]:
            instances.append(inst)
    return instances

def get_github_runner_token():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/actions/runners/registration-token"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    r = requests.post(url, headers=headers)
    r.raise_for_status()
    return r.json()["token"]

def lambda_handler(event, context):
    # Debug: print the event to see its structure
    print(f"Event: {json.dumps(event)}")
    
    # Handle different API Gateway event formats
    path = event.get("resource", event.get("rawPath", event.get("path", "")))
    method = event.get("httpMethod", event.get("requestContext", {}).get("http", {}).get("method", ""))
    
    print(f"Path: {path}, Method: {method}")

    existing = find_existing_instance()

    if path.endswith("/create") and method == "POST":
        if existing:
            return {"statusCode": 400, "body": "Runner already exists."}

        fresh_token = get_github_runner_token()
        expire_at = str(int(time.time()) + 3600)  # 60 minutes
        
        # Get or create security group
        security_group_id = get_or_create_security_group()

        user_data = f"""#!/bin/bash
# Update system and install dependencies (Ubuntu)
apt-get update -y
apt-get install -y git curl tar sudo

# Create runner user and add to sudoers
useradd -m -s /bin/bash runner
echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Set up GitHub Actions runner
cd /home/runner
sudo -u runner bash << 'EOF'
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64-2.320.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.320.0/actions-runner-linux-x64-2.320.0.tar.gz
echo "93ac1b7ce743ee85b5d386f5c1787385ef07b3d7c728ff66ce0d3813d5f46900  actions-runner-linux-x64-2.320.0.tar.gz" | shasum -a 256 -c
tar xzf ./actions-runner-linux-x64-2.320.0.tar.gz
./config.sh --url https://github.com/{GITHUB_REPO} --token {fresh_token} --unattended --replace --name lambda-runner-$(date +%s)
EOF

# Install and start as service
cd /home/runner/actions-runner
./svc.sh install runner
./svc.sh start

# Log the status
./svc.sh status
"""

        run_instances_params = {
            "ImageId": AMI_ID,
            "InstanceType": INSTANCE_TYPE,
            "MinCount": 1,
            "MaxCount": 1,
            "KeyName": KEY_PAIR_NAME,
            "TagSpecifications": [
                {
                    "ResourceType": "instance",
                    "Tags": [
                        {"Key": INSTANCE_TAG_KEY, "Value": INSTANCE_TAG_VALUE},
                        {"Key": TTL_TAG_KEY, "Value": expire_at}
                    ]
                }
            ],
            "UserData": user_data
        }
        
        # Add security group if available
        if security_group_id:
            run_instances_params["SecurityGroupIds"] = [security_group_id]

        response = ec2.run_instances(**run_instances_params)
        instance_id = response["Instances"][0]["InstanceId"]
        
        # Wait for instance to be running (quick check)
        print(f"Waiting for instance {instance_id} to start...")
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id], WaiterConfig={'Delay': 5, 'MaxAttempts': 6})
        print("Instance is running!")
        
        return {"statusCode": 200, "body": json.dumps({"message": "Runner created", "instanceId": instance_id})}

    elif path.endswith("/destroy") and method == "POST":
        if not existing:
            return {"statusCode": 404, "body": "No runner exists."}
        ids = [inst["InstanceId"] for inst in existing]
        ec2.terminate_instances(InstanceIds=ids)
        return {"statusCode": 200, "body": json.dumps({"message": "Runner destroyed", "instances": ids})}

    else:
        return {"statusCode": 400, "body": "Invalid request"}
