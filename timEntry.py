import boto3
import json
import random

echo_app_id = "amzn1.ask.skill.8b319f25-ea6b-4972-9ed7-91b6af7af994"
#intents
gibberish = "Gibberish"
funny = "Funny"
rehydrate = "Rehydrate"

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


def say_funny():
    responses = ['Welcome to Gooming!',
                 'I will get to documenting that.',
                 'Tim is on coffee break.',
                 'Would you like some honey?',
                 'Tim has been added as the owner contact for all stacks'

    ]
    return random.choice(responses)


def rehydrate_stack():
    # TODO call rehydration functions
    return "Tim says I will now execute rehydrate on the stack"


def build_response(intent):
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

    alexa_speak = "Tim says I will now execute "
    if intent:
        if intent == gibberish:
            alexa_speak = "Tim has no idea what you just said."
        elif intent == funny:
            alexa_speak = say_funny()
        elif intent == rehydrate:
            alexa_speak = rehydrate_stack()
        else:
            alexa_speak += str(intent) + " for you."
    else:
        alexa_speak += "nothing for you."

    response['response']['outputSpeech']['text'] = alexa_speak

    response['response']['card']['content'] = alexa_speak

    return response


# Get the intent from the request
def parse_request_intent(request):
    response = {}
    intent = request['intent']
    intent_function = intent['name']
    slots = get_data('slots', intent)
    for slot in slots:
        slot_name = slots[slot]['name']
        slot_value = slots[slot]['value']
        print slot_name
        response[slot_name] = slot_value

    if response:
        return response

    return intent_function


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
    print "Request Intent"

    request_intent = parse_request_intent(request)
    print "Request Intent: " + request_intent

    response = build_response(request_intent)
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
