import boto3
import sys

REGION = "us-east-1"
ENDPOINT_URL = "http://localhost:9229"

def setup_local_cognito():
    print(f"Connecting to Cognito at {ENDPOINT_URL}...")
    try:
        client = boto3.client(
            "cognito-idp", 
            region_name=REGION, 
            endpoint_url=ENDPOINT_URL,
            aws_access_key_id="local",
            aws_secret_access_key="local"
        )
    except Exception as e:
        print(f"❌ Failed to create boto3 client: {e}")
        sys.exit(1)

    # 1. Create User Pool
    print("Creating User Pool...")
    try:
        pool_response = client.create_user_pool(
            PoolName="local-user-pool",
            Schema=[
                {
                    "Name": "tenant_id",
                    "AttributeDataType": "String",
                    "Mutable": True,
                    "Required": False
                },
                {
                    "Name": "email",
                    "AttributeDataType": "String",
                    "Mutable": True,
                    "Required": True
                }
            ],
            AutoVerifiedAttributes=["email"]
        )
        user_pool_id = pool_response["UserPool"]["Id"]
        print(f"✅ User Pool created: {user_pool_id}")
    except Exception as e:
        print(f"❌ Failed to create user pool. Is the Docker container running? Error: {e}")
        sys.exit(1)

    # 2. Create User Pool Client
    print("Creating User Pool Client...")
    try:
        client_response = client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName="local-app-client",
            GenerateSecret=False,
            ExplicitAuthFlows=[
                "ALLOW_USER_PASSWORD_AUTH",
                "ALLOW_REFRESH_TOKEN_AUTH",
                "ALLOW_ADMIN_USER_PASSWORD_AUTH"
            ]
        )
        client_id = client_response["UserPoolClient"]["ClientId"]
        print(f"✅ App Client created: {client_id}")
    except Exception as e:
        print(f"❌ Failed to create app client: {e}")
        sys.exit(1)

    # 3. Create Groups
    print("Creating Groups...")
    groups = ["ADMIN", "EDITOR", "VIEWER"]
    for group in groups:
        try:
            client.create_group(
                UserPoolId=user_pool_id,
                GroupName=group,
                Description=f"Group for {group} role"
            )
            print(f"  - Group '{group}' created.")
        except client.exceptions.GroupExistsException:
             print(f"  - Group '{group}' already exists.")
        except Exception as e:
            print(f"  ❌ Failed to create group '{group}': {e}")

    # 4. Create Demo User
    print("Creating Demo User (admin@example.com)...")
    try:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username="admin@example.com",
            UserAttributes=[
                {"Name": "email", "Value": "admin@example.com"},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "custom:tenant_id", "Value": "tenant-123"}
            ],
            MessageAction="SUPPRESS" 
        )
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username="admin@example.com",
            Password="P@ssword123",
            Permanent=True
        )
        client.admin_add_user_to_group(
            UserPoolId=user_pool_id,
            Username="admin@example.com",
            GroupName="ADMIN"
        )
        print("✅ Demo user created: admin@example.com / P@ssword123 (Tenant: tenant-123)")
    except client.exceptions.UsernameExistsException:
        print("  - User 'admin@example.com' already exists.")
    except Exception as e:
        print(f"  ❌ Failed to create demo user: {e}")

    # 5. Output .env content
    print("\n" + "="*50)
    print("SETUP COMPLETE! Copy the following to your .env file:")
    print("="*50)
    print(f"USER_POOL_ID={user_pool_id}")
    print(f"APP_CLIENT_ID={client_id}")
    print(f"AWS_REGION={REGION}")
    print("ENVIRONMENT=local")
    print("="*50)
    print("Demo Credentials:")
    print("Username: admin@example.com")
    print("Password: P@ssword123")
    print("="*50)

if __name__ == "__main__":
    setup_local_cognito()
