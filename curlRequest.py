import boto3
import os

def lambda_handler(event, context):
    
    # Initiate a curl call
    os.system("curl -X POST --data-urlencode 'payload={\"channel\": \"#dotify\", \"username\": \"Tim-Bot\", \"text\": \"Refreshing DotifyA stack...\", \"icon_emoji\": \":thumbsup:\"}' https://hooks.slack.com/services/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")
    return {'message' : "Script execution completed. See Cloudwatch logs for complete output"}
