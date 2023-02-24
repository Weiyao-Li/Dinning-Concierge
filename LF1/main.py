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
        return slots[slotName]['value']['resolvedValues']
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
                             'originatingRequestId': 'REQUESTID'
                             },
            'sessionId': intent_request['sessionId'],
            'messages': [message],
            'requestAttributes': intent_request['requestAttributes']
            if 'requestAttributes' in intent_request else None
            }


def build_validation_result(is_valid, violated_slot, message_content):

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def GetItemInDatabase(postal_code):
    """
    Perform database check for transcribed postal code. This is a no-op
    check that shows that postal_code can't be found in the database.
    """
    return None


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def delegateSlot(intent_request):
    return {
        "dialogAction": {
            "type": "Delegate",
            "slots": intent_request["currentIntent"]["slots"]
        }
    }

def validate_phone_number(phone_number):
    """
    Validate the format of the phone number.
    """
    pattern = re.compile(r'^\d{10}$')  # pattern for 10-digit phone number
    if not pattern.match(phone_number):
        return build_validation_result(False, 'Phonenumber', 'Please enter a valid phone number with 10 digits.')
    return build_validation_result(True, None, None)

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }
def validationProcess(Location, Cuisine, Date, Time, Numberofpeople, Phonenumber):
    # Location Validation
    if Location and Location.lower() not in ['new york city', 'manhattan', 'bronx', 'queens', 'nyc', 'new york']:
        return build_validation_result(False,
                                       'location',
                                       'Currently this is not an available location. Please enter location, like Manhattan')

    # Cuisine Validation:
    if Cuisine and Cuisine.lower() not in ['chinese', 'japanese', 'thai', 'american', 'french', 'italian', 'indian']:
        return build_validation_result(False, 'Cuisine', 'Sorry! The one you just entered is invalid! '
                                                         'Please choose from the following options: '
                                                         'chinese, japanese, thai, american, french, italian, indian')

    # Numberofpeople Validation

    if Numberofpeople:
        if int(Numberofpeople) not in range(1, 11):
            return build_validation_result(False,
                                           'Numberofpeople',
                                           'Number of people should be between 1 and 10')
    # Phonenumber Validation
    if Phonenumber:
        if not validate_phone_number(Phonenumber):
            return build_validation_result(False,
                                           'Phonenumber',
                                           'The phone number you entered is not valid. Please enter a valid phone number.')
    else:
        return build_validation_result(False,
                                       'Phonenumber',
                                       'Please provide a phone number.')


    # Date Validation
    if not Date:
        # 'Date' slot is empty, delegate to Lex to prompt the user for input.
        return delegateSlot()

    try:
        entered = datetime.strptime(Date, '%Y-%m-%d')
        cur_time = datetime.now()

        if entered.date() < cur_time.date():
            # Reservation date is in the past, elicit 'Date' slot and prompt the user for a valid date.
            return elicitSlotExecute('Date', build_validation_result(
                False, 'Date', "Oh. We can't make a reservation in the past. Could you please enter a valid date?"))

        if entered.date() == cur_time.date():
            if not Time:
                # 'Time' slot is empty, elicit 'Time' slot and prompt the user for a valid time.
                return elicitSlotExecute('Time', build_validation_result(
                    False, 'Time', "Please provide a valid time in the format HH:MM."))

            try:
                entered_time = datetime.strptime(Time, '%H:%M').time()
                if entered_time < cur_time.time():
                    # Reservation time is in the past, elicit 'Time' slot and prompt the user for a valid time.
                    return elicitSlotExecute('Time', build_validation_result(
                        False, 'Time',
                        "Oh. We can't make a reservation for a time in the past. Could you please enter a valid time?"))
            except ValueError:
                # User entered an invalid time format, elicit 'Time' slot and prompt the user for a valid time.
                return elicitSlotExecute('Time', build_validation_result(
                    False, 'Time',
                    "Sorry, I didn't understand that. Could you please enter a valid time in the format HH:MM?"))

        # Reservation date and time are valid, delegate to Lex to continue with the next step of the conversation.
        return delegateSlot()

    except ValueError:
        # User entered an invalid date format, elicit 'Date' slot and prompt the user for a valid date.
        return elicitSlotExecute('Date', build_validation_result(
            False, 'Date',
            "Sorry, I didn't understand that. Could you please enter a valid date in the format yyyy-mm-dd?"))

def DiningSuggestionsIntent(intent_request):
    state = intent_request['sessionState']
    slots = intent_request["intent"]["slots"]

    Location = get_slots(intent_request)["Location"]
    Cuisine = get_slots(intent_request)["Cuisine"]
    Date = get_slots(intent_request)["Date"]
    Time = get_slots(intent_request)["Time"]
    Numberofpeople = get_slots(intent_request)["Numberofpeople"]
    Phonenumber = get_slots(intent_request)["Phonenumber"]

    # type of event that triggered the function
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        print("Here we are in DialogCodeHook!")

        slots = get_slots(intent_request)

        resOfValidation = validationProcess(Location, Cuisine, Date, Time, Numberofpeople, Phonenumber)
        if not resOfValidation['isValid']:
            slots[resOfValidation['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'], intent_request['intent']['name'], slots, resOfValidation['violatedSlot'], resOfValidation['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

        return delegate(output_session_attributes, get_slots(intent_request))

    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Thanks. We will send you email shortly'})


# --- Intents ---

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    intent_name = intent_request['sessionState']['intent']['name']
    state = intent_request['sessionState']

    if intent_name == 'DiningSuggestionsIntent':
        return DiningSuggestionsIntent(intent_request)
    print("Error!", intent_name)


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
