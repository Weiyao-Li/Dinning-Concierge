import math
from datetime import datetime, timedelta

import boto3
import json
import time
import os
import logging
import re

# maybe import math and re, To-do later

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# --- Helpers that build all of the responses ---



def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']


def get_session_attributes(intent_request):
    sessionState = intent_request['sessionState']
    if 'sessionAttributes' in sessionState:
        return sessionState['sessionAttributes']
    return {}


def elicitSlotExecute(event, slotToElicit, message):
    return {
        'sessionAttributes': event['sessionAttributes'],
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': event['currentIntent']['name'],
            'slots': event['currentIntent']['slots'],
            'slotToElicit': slotToElicit,
            'message': message
        }
    }


def get_slot(intent_request, slotName):
    slots = get_slots(intent_request)
    if slots is not None and slotName in slots and slots[slotName] is not None:
        logger.debug('resolvedValue={}'.format(slots[slotName]['value']['resolvedValues']))
        return slots[slotName]['value']['interpretedValue']
    else:
        return None


def elicit_slot(session_attributes, intent_request, slots, slot_to_elicit, slot_elicitation_style, message):
    return {'sessionState': {'dialogAction': {'type': 'ElicitSlot',
                                              'slotToElicit': slot_to_elicit,
                                              'slotElicitationStyle': slot_elicitation_style
                                              },
                             'intent': {'name': intent_request['sessionState']['intent']['name'],
                                        'slots': slots,
                                        'state': 'InProgress'
                                        },
                             'sessionAttributes': session_attributes,
                             'originatingRequestId': '70d49ca7-53de-4e1e-ac0a-70ecfc45b70a'
                             },
            'sessionId': intent_request['sessionId'],
            'messages': [message],
            'requestAttributes': intent_request['requestAttributes']
            if 'requestAttributes' in intent_request else None
            }


def build_validation_result(isvalid, violated_slot, slot_elicitation_style, message_content):
    return {'isValid': isvalid,
            'violatedSlot': violated_slot,
            'slotElicitationStyle': slot_elicitation_style,
            'message': {'contentType': 'PlainText',
            'content': message_content}
            }

def GetItemInDatabase(postal_code):
    """
    Perform database check for transcribed postal code. This is a no-op
    check that shows that postal_code can't be found in the database.
    """
    return None


def close(intent_request, session_attributes, fulfillment_state, message):
    intent_request['sessionState']['intent']['state'] = fulfillment_state
    return {
        'sessionState': {
            'sessionAttributes': session_attributes,
            'dialogAction': {
                'type': 'Close'
            },
            'intent': intent_request['sessionState']['intent'],
            'originatingRequestId': '2d3558dc-780b-422f-b9ec-7f6a1bd63f2e'
        },
        'messages': [ message ],
        'sessionId': intent_request['sessionId'],
        'requestAttributes': intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
    }



def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def delegate(intent_request, slots):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Delegate"
            },
            "intent": {
                "name": intent_request['sessionState']['intent']['name'],
                "slots": slots,
                "state": "ReadyForFulfillment"
            },
            'sessionId': intent_request['sessionId'],
            "requestAttributes": intent_request['requestAttributes'] if 'requestAttributes' in intent_request else None
        }}


def validationProcess(Location, Cuisine, Date, Time, Numberofpeople, Email):
    # Location Validation
    if Location:
        print("12312313131")
        if Location.lower() not in ['new york city', 'manhattan', 'bronx', 'queens', 'nyc', 'new york']:
            return build_validation_result(False,
                                       'Location',
                                       'SpellbyWord',
                                       'Currently this is not an available location. Please enter location, like Manhattan')
        else:
            print("4546456456464")
            return True
    # Cuisine Validation:
    if Cuisine:
        if Cuisine.lower() not in ['chinese', 'japanese', 'thai', 'american', 'french', 'italian', 'indian']:
            return build_validation_result(False, 'Cuisine', 'SpellbyWord', 'Sorry! The one you just entered is invalid! '
                                                         'Please choose from the following options: '
                                                         'chinese, japanese, thai, american, french, italian, indian')
        else:
            return True
    # Numberofpeople Validation

    if Numberofpeople:
        if int(Numberofpeople) not in range(1, 11):
            return build_validation_result(False,
                                           'Numberofpeople',
                                           'SpellbyWord',
                                            'Number of people should be between 1 and 10')
        else:
            return True

    # Date Validation
    if Date:
        print("Debug: date is:", Date)
        year, month, day = map(int, Date.split('-'))
        date_to_check = datetime.date(year, month, day)
        if date_to_check < datetime.date.today():
            return build_validation_result(False, 'date', 'SpellByWord', 'Please enter a valid Dining date')
        else:
            return True
    if Time:
        print("Debug: time is:", Time)
        if not Time:
            return build_validation_result(False, 'Time', 'SpellByWord', '')
        if Time:
            return True

def DiningSuggestionsIntent(intent_request):
    state = intent_request['sessionState']

    Location = get_slot(intent_request, "Location")
    Cuisine = get_slot(intent_request, "Cuisine")
    Date = get_slot(intent_request, "Date")
    Time = get_slot(intent_request, "Time")
    Numberofpeople = get_slot(intent_request, "Numberofpeople")
    Email = get_slot(intent_request, "Email")

    session_attributes = get_session_attributes(intent_request)

    # type of event that triggered the function
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        print("Here we are in DialogCodeHook!")

        slots = get_slots(intent_request)

        resOfValidation = validationProcess(Location, Cuisine, Date, Time, Numberofpeople, Email)
        if not resOfValidation:
            slots[resOfValidation['violatedSlot']] = None
            return elicit_slot(session_attributes, intent_request, slots,
                               resOfValidation['violatedSlot'], resOfValidation['slotElicitationStyle'], resOfValidation['message'])

    if not Location or not Date or not Time or not Numberofpeople or not Email or not Cuisine:
        return delegate(intent_request, get_slots(intent_request))
    else:
        send_message_to_SQS(
            Location,
            Cuisine,
            Date,
            Time,
            Numberofpeople,
            Email


        )

        return close(intent_request,
                     session_attributes,
                     'Fulfilled',
                     {'contentType': 'PlainText',
                      'content': 'Thanks. We will send you email shortly'})


# --- Intents ---

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    intent_name = intent_request['sessionState']['intent']['name']
    # state = intent_request['sessionState']

    if intent_name == 'DiningSuggestionsIntent':
        return DiningSuggestionsIntent(intent_request)
    print("Error!", intent_name)



def send_message_to_SQS(Location, Cuisine, Date, Time, Numberofpeople, Email):
    sqs = boto3.client('sqs')

    response = sqs.send_message(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/778348423801/RestaurantQueue",
        MessageAttributes={
            'Location': {
                'DataType': 'String',
                'StringValue': Location
            },
            'Cuisine': {
                'DataType': 'String',
                'StringValue': Cuisine
            },
            'Date': {
                'DataType': 'String',
                'StringValue': Date
            },
            'Time': {
                'DataType': 'String',
                'StringValue': Time
            },
            'Numberofpeople': {
                'DataType': 'Number',
                'StringValue': str(Numberofpeople)
            },
            'Email': {
                'DataType': 'String',
                'StringValue': Email
            }
        },

        MessageBody=('Information about user inputs of Dining Chatbot.'),
    )

# --- Main handler ---

def lambda_handler(event, context):
    """
    Route the incoming request based on the intent.

    The JSON body of the request is provided in the event slot.
    """

    # By default, treat the user request as coming from
    # Eastern Standard Time.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()

    logger.debug('event={}'.format(json.dumps(event)))
    response = dispatch(event)

    return response
