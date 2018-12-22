# -*- coding: utf-8 -*-
import re
import time
#from slackclient import SlackClient

from commandBook import dice, food, yes, no, guide, food_list, set_loc, visualize, evaluation, slack_client
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None
# constants
RTM_READ_DELAY = 0.6 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "!"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"], event["user"]
    return None, None, None

def parse_direct_mention(message_text):
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel, user):
    # Default response is help text for the user
    default_response = "명령어 입력의 시작은 *{}* 로 해주세요.".format(EXAMPLE_COMMAND)
    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        if command == "!help":
            response = guide()
        if command == "!food_list":
            response = food_list()
        if command == "!dice":
            ran_num = dice()
            response = "Your role: {}".format(ran_num)
        if command == "!food":
            response = food(user, channel)
        if command == "!no":
            response = no(user, channel)
        if command == "!yes":
            try:
                response = yes(user)
            except:
                response = "지역을 바꿔주세요."
        if command.startswith("!location"):
            try:
                location = command.split(" ")[1]
                response = set_loc(user, location)
            except:
                response = "\"!location 신촌역\"과 같이 입력해주세요" 
        if command == "!visualize":
            response = visualize(user)
        if command == "!evaluation":
            evaluation(channel)
            response = "Evaluation 결과"
        if response == None:
            response = "유효하지 않은 명령어입니다. !help를 입력해 명령어를 알아보세요."

    # Sends the response back to the channel
    slack_client.api_call("chat.postMessage", channel=channel, text=response or default_response)


if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel, user = parse_bot_commands(slack_client.rtm_read())
            if command:
                start = time.time()
                command = command.lower()
                handle_command(command, channel, user)
                taken_time = round(time.time() - start,3)
                text_format = "Taken time: {} seconds".format(taken_time)
                slack_client.api_call("chat.postMessage", channel=channel, text=text_format)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")