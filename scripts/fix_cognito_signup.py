#!/usr/bin/env python3
"""
Quick fix for Cognito User Pool to enable self-signup
"""
import boto3
import os

def fix_cognito_signup():
    """Enable self-signup for existing Cognito User Pool"""
    
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
    if not user_pool_id:
        print("❌ COGNITO_USER_POOL_ID not set")
        return
    
    print(f"🔧 Fixing Cognito User Pool: {user_pool_id}")
    
    cognito = boto3.client('cognito-idp')
    
    try:
        # Get current user pool configuration
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        user_pool = response['UserPool']
        
        print(f"📋 Current signup policy: {user_pool.get('Policies', {}).get('PasswordPolicy', {})}")
        
        # Update user pool to allow self-signup
        update_params = {
            'UserPoolId': user_pool_id,
            'Policies': {
                'PasswordPolicy': {
                    'MinimumLength': 8,
                    'RequireUppercase': True,
                    'RequireLowercase': True,
                    'RequireNumbers': True,
                    'RequireSymbols': False
                }
            },
            'AdminCreateUserConfig': {
                'AllowAdminCreateUserOnly': False,  # This enables self-signup
                'UnusedAccountValidityDays': 7
            }
        }
        
        cognito.update_user_pool(**update_params)
        print("✅ Self-signup enabled successfully!")
        
        # Verify the change
        response = cognito.describe_user_pool(UserPoolId=user_pool_id)
        admin_only = response['UserPool']['AdminCreateUserConfig']['AllowAdminCreateUserOnly']
        print(f"📋 Admin only signup: {admin_only} (should be False)")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n🔧 Manual fix via AWS Console:")
        print(f"1. Go to Cognito User Pool: {user_pool_id}")
        print("2. Go to 'Sign-up experience' tab")
        print("3. Edit 'Self-service sign-up'")
        print("4. Enable 'Self-registration'")
        print("5. Save changes")

if __name__ == "__main__":
    fix_cognito_signup()