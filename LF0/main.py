import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    print('event start')
    print(event)
    print('event end')
    #
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='chatbot',
        botAlias='chatbot_lex',
        userId='10',
        sessionAttributes={
            },
        requestAttributes={
        },
        inputText = event['messages'][0]['unstructured']['text']
    )
    print("Message from bot:" +response["message"])
    return {
        'statusCode': 200,
        'body': json.dumps(response["message"])
    }



# Our code:
import boto3
import json

# Define the client to interact with Lex
client = boto3.client('lexv2-runtime')


def lambda_handler(event, context):
    # msg_from_user = event['messages'][0]
    # change this to the message that user submits on
    # your website using the 'event' variable
    print(event)
    msg_from_user = event['messages'][0]
    print(f"Message from frontend: {msg_from_user}")
    # Initiate conversation with Lex
    botMessage = "Please try again."
    if msg_from_user is None or len(msg_from_user) < 1:
        return {
            'statusCode': 200,
            'body': json.dumps(botMessage)
        }

    response = client.recognize_text(
        botId='EXWSIWKKTS',  # MODIFY HERE
        botAliasId='9ZSB8GYNLD',  # MODIFY HERE
        localeId='en_US',
        sessionId='testuser',
        text=msg_from_user["unstructured"]["text"])

    msg_from_lex = response.get('messages', [])
    if msg_from_lex:
        print(f"Message from Chatbot: {msg_from_lex[0]['content']}")
        print(response)
        resp = {
            'statusCode': 200,
            'messages': [{"type": "unstructured",
                          "unstructured": {
                              "text": json.dumps(msg_from_lex[0]['content'])
                          }}]
        }
        # modify resp to send back the next question Lex would ask from the user

        # format resp in a way that is understood by the frontend
        return resp
