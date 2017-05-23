import boto3
import json
import random

echo_app_id = "amzn1.ask.skill.8b319f25-ea6b-4972-9ed7-91b6af7af994"
# intents
gibberish = "Gibberish"
funny = "Funny"
rehydrate = "Rehydrate"
stackFinder = "StackFinder"

LAMBDA_CLIENT = boto3.client('lambda')

#StackMap
stackMap = {'1': 'dottify A', '2': 'dottify B', '3': 'dottify C'}

sample_response = {
    "version": "1.0",
    "response": {
        "outputSpeech": {
            "type": "PlainText",
            "text": "This is a test from Tim."
        },
        "card": {
            "content": "This is a test from Tim.",
            "title": "Test Response",
            "type": "Simple"
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Come again?"
            }
        },
        "shouldEndSession": True
    },
    "sessionAttributes": {}
}


def get_data(key, obj_json):
    if key in obj_json:
        return obj_json[key]
    return ''


# Get slots from intent
def parse_request_slots(request):
    response = {}
    intent = request['intent']
    slots = get_data('slots', intent)
    for slot in slots:
        slot_name = slots[slot]['name']
        slot_value = slots[slot]['value'] # Need check if value does not exist
        print slot_name + ": " + slot_value
        response[slot_name] = slot_value
    return response


# Get the intent from the request
def parse_request_intent(request):
    response = {}
    intent = request['intent']
    intent_function = intent['name']
    return intent_function


# Funny Intent
def say_funny():
    responses = ['Welcome to Gooming!',
                 'Tim will get to documenting that right away.',
                 'Tim is on coffee break.',
                 'Would you like some honey?',
                 'Tim has been added as the owner contact for all stacks',
                 'Who is Tim? Do you mean Bryan?',
                 'What happens in the circle stays in the circle.',
                 'Tim is out hunting down S 3 policy violators.',
                 'In Soviet Russia, stack rehydrates Tim',
                 'Tim will create a swim lane for that.',
                 'Tim has altered the deal. Pray that he does not alter it further.',
                 'Tim says Loki approves.',
                 'You are killing me smalls',
                 'There are no dumb questions, only dumb people',
                 'Very good, you have passed the test'
                 ]
    return random.choice(responses)


# Prompt user to name the stack to be rehydrated
def rehydrate_stack():
    return "Tim wants to know which stack you want to rehydrate. Say 1 2 or 3 for one of the following: 1, dottify a; 2, dottify b; 3, dottify c."


# Use given stack (from slot) to begin rehydration {stack: stackName}
def stack_finder(request):
    # TODO call rehydration functions
    slot_response = parse_request_slots(request)
    print json.dumps(slot_response)
    stack_key = slot_response['stack']
    stack = stackMap[stack_key]

    #Trim whitespace
    stack_trim = stack.replace(" ", "")
    if stack_trim == 'dottifyA':
        stack_trim = 'dottifyA-ASG-12BOTQS4Q92C7'

    # Rehydrate stack
    event_payload = {'stack': stack_trim}
    invokeResponse = LAMBDA_CLIENT.invoke(
        FunctionName='modify_launch_config',
        InvocationType='RequestResponse',
        LogType='Tail',
        Payload=json.dumps(event_payload)
    )

    return "Tim will now rehydrate the Stack " + stack


def build_response(request):
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Tim says this is a test response."
            },
            "card": {
                "content": "Tim says this is a test response.",
                "title": "Test Response",
                "type": "Simple"
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Come again?"
                }
            },
            "shouldEndSession": True
        },
        "sessionAttributes": {}
    }

    intent = parse_request_intent(request)
    print "Request Intent: " + intent
    alexa_speak = "Tim says I will now execute "
    if intent:
        if intent == gibberish:
            alexa_speak = "Tim has no idea what you just said."
        elif intent == funny:
            alexa_speak = say_funny()
        elif intent == rehydrate:
            alexa_speak = rehydrate_stack()
            response['response']['shouldEndSession'] = False
        elif intent == stackFinder:
            alexa_speak = stack_finder(request)
        else:
            alexa_speak += str(intent) + " for you."
    else:
        alexa_speak += "nothing for you."

    response['response']['outputSpeech']['text'] = alexa_speak

    response['response']['card']['content'] = alexa_speak

    return response


def on_launch(request):
    print "Request Launched"
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Tim says what can I help you with?"
            },
            "card": {
                "content": "Tim says what can I help you with?",
                "title": "Launch Response",
                "type": "Simple"
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Come again?"
                }
            },
            "shouldEndSession": False
        },
        "sessionAttributes": {}
    }


def on_intent(request):
    # request_intent = parse_request_intent(request)
    # print "Request Intent: " + request_intent

    response = build_response(request)
    print "Response:"
    print response
    return response


def on_session_ended(request):
    print "Request Session Ended"
    return {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": "Tim says Goodbye"
            },
            "card": {
                "content": "Tim says Goodbye",
                "title": "End Response",
                "type": "Simple"
            },
            "reprompt": {
                "outputSpeech": {
                    "type": "PlainText",
                    "text": "Come again?"
                }
            },
            "shouldEndSession": True
        },
        "sessionAttributes": {}
    }


def lambda_handler(event, context):
    # Read in Skill event
    print "Alexa has been called!"
    event_str = json.dumps(event)
    print event_str

    if event['session']['application']['applicationId'] != echo_app_id:
        raise ValueError("Invalid Application ID")

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'])

    print "Other type of Request..."
    return sample_response
