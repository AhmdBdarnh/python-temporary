import boto3
import json

# Initialize the SQS client
sqs = boto3.client('sqs', region_name='us-west-2', endpoint_url='http://localhost:9324')

# URL of the SQS queue
SQS_QUEUE_URL = "http://localhost:9324/queue/youtube_trend_100"

all_messages = []  # List to store all messages

while True:
    # Receive messages from the queue (up to 10 at a time)
    response = sqs.receive_message(
        QueueUrl=SQS_QUEUE_URL,
        MaxNumberOfMessages=10,  # SQS max limit per request
        WaitTimeSeconds=5  # Optional: Long polling for messages
    )

    messages = response.get('Messages', [])

    if not messages:
        print("No more messages in the queue.")
        break

    for message in messages:
        body = message['Body']
        try:
            # Attempt to decode the JSON message
            decoded_message = json.loads(body)
            all_messages.append(decoded_message)  # Store each message
            
            # Delete the message from the queue after processing
            sqs.delete_message(
                QueueUrl=SQS_QUEUE_URL,
                ReceiptHandle=message['ReceiptHandle']
            )
        except json.JSONDecodeError as e:
            print(f"Failed to decode message ID {message['MessageId']}: {e}")
            print(f"Message content: {body}")

# Optionally, write all messages to a file
with open('all_sqs_messages.json', 'w', encoding='utf-8') as json_file:
    json.dump(all_messages, json_file, indent=4, ensure_ascii=False)

print(f"Retrieved {len(all_messages)} messages.")
