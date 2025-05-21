import re
import os
import json
import logging
import requests
from api.dialogflow.helpers.notify_click_up import create_click_up_task, notify_click_up_tech_notifications
from api.instagram.helpers.llm import query_gpt
from urllib.parse import urlparse
from django_tenants.utils import schema_context
from api.dialogflow.helpers.conversations import get_conversation_so_far
from django.core.mail import send_mail
from api.instagram.models import OutSourced

from lunyamwi import get_agent, setup_agent


def get_status_number(val, pattern=r"\d+"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return int(list_of_values[0])

def extract_text(json_string):
    # Regular expression to find the "text" field
    match = re.search(r'"text":"(.*?)"', json_string)
    if match:
        return match.group(1).replace('\\"', '"')  # Replace escaped quotes if needed
    return None

def get_if_confirmed_problem(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


def get_if_asked_first_question(val, pattern=r"`([^`]+)`"):
    list_of_values = re.findall(pattern=pattern, string=val)
    return str(list_of_values[0])


@schema_context(os.getenv("SCHEMA_NAME"))
def save_gpt_response(result, payload):
    print("===========now============")
    print(result.get("confirmed_problems"))
    print(payload.get("prompt_index"))
    if isinstance(result.get("confirmed_problems"), list):
        payload.update({
            "confirmed_problems": result.get("confirmed_problems")
        })
    else:
        payload.update({
            "confirmed_problems": [result.get("confirmed_problems")]
        })
    url = os.getenv("SCRIPTING_URL") + '/save-response/'
    headers = {'Content-Type': 'application/json'}  # Adjust based on your payload type

    response = requests.post(url, json=payload, headers=headers)

    print(response.request.body)
    return response.status_code


def clean_text(text):
    """
    Cleans up the input text by removing unwanted characters and formatting issues,
    including escape characters.
    
    Args:
        raw_text (str): The raw text to clean.
        
    Returns:
        str: The cleaned text.
    """
    # Remove escape characters
    text = text.replace("\\", "")

    # Remove non-ASCII characters
    text = re.sub(r'[^\x00-\x7F]+', '', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

@schema_context(os.getenv("SCHEMA_NAME"))
def get_gpt_response(account, message, thread_id=None):
   
    outsourced = None
    try:
        outsourced_object = OutSourced.objects.filter(account__igname=account.igname).first()
        outsourced = json.dumps(outsourced_object.results)
    except Exception as error:
        print(error)

    conversations = None
    if message:
        conversations = get_conversation_so_far(account.thread_set.latest('created_at').thread_id)
    # active_stage = None
    # if account.status_param:
    #     active_stage = account.status_param

    get_agent_payload = {
        "message":message,
        "text":message,
        "conversations":conversations if conversations else "",
        "active_stage": account.status_param if account.status_param else ""
    }
    print(get_agent_payload)
    agent_json_response= get_agent(payload=get_agent_payload)
    print(agent_json_response)
    # print(agent_json_response)
    # confirmed_problems = [
    #     "Need for new clients or increased clientele and market visibility",
    #     "Missed opportunities in diversifying revenue streams",
    #     "Inefficient payment processing",
    #     "Missed opportunity to promote your high-potential IG account by posting regularly with social media post creator tools",
    #     "Missed opportunity to enable bookings from platforms (Google, Instagram, Facebook, Booksy which is the biggest beauty marketplace, their Website) where clients discover and book beauty services",
    #     "Not assigning the right priority to engaging the returning, loyal clients",
    #     "Missed opportunity to reengage clients and fill up slower days with time-sensitive promotions",
    #     "Lack of ability to invite back to the chair the clients who stopped booking to build long-term success on returning clients",
    #     "Reviews are not visible across Google, Facebook, IG, and Booksy which is the major beauty marketplace",
    #     "Unclear and high client acquisition costs with Google Ads, Instagram Ads, and others that don't show total marketing cost per new client",
    #     "Missed opportunity to convert current and future IG followers to clients in the chair",
    #     "Need for new clients or increased clientele and market visibility ",
    #     "No-shows and cancellations ruining the bottom line",
    # ]
    
    agent_name = agent_json_response.get("agent_name")
    agent_task = agent_json_response.get("agent_task")
    # if not message:
    #     agent_name = "Engagement Persona Influencer Audit Rapport Building Agent"
    #     agent_task = "ED_PersonaInfluencerAuditRapportBuildlingA_BuildMessageT"

    

    # if account.question_asked and not account.confirmed_problems or account.confirmed_problems == "test" and not account.solution_presented:
    #     agent_name = "Engagement Persona Influencer Audit Needs Assessment Agent"
    #     agent_task = "ED_PersonaInfluencerAuditNeedsAssessmentA_BuildMessageT"
    # elif account.question_asked and account.confirmed_problems and account.confirmed_problems != "test" and not account.solution_presented:
    #     agent_name = "Engagement Persona Influencer Audit Solution Presentation Agent"
    #     agent_task = "ED_PersonaInfluencerAuditSolutionPresentationA_BuildMessageT"
    # elif account.question_asked and account.confirmed_problems and account.confirmed_problems != "test" and account.solution_presented:
    #     agent_name = "Engagement Persona Influencer Audit Closing the Sale Agent"
    #     agent_task = "ED_PersonaInfluencerAuditClosingTheDealA_BuildMessageT"
                        

    
    print("agent_name:",agent_name,"agent_task:",agent_task)

  
    # import pdb;pdb.set_trace()
    relevant_information = str(account.relevant_information) if account.relevant_information else ""
    payload = {
        "department":"Engagement Department",
        "version": account.engagement_version,
        "agent_name": agent_name,
        "agent_task": agent_task,
        "text":message if message else "",
        "Assigned":{
            "message":message if message else "",
            "text":message if message else "",
            "sales_rep":account.salesrep_set.first().ig_username,
            "influencer_ig_name":account.salesrep_set.last().ig_username,
            "outsourced_info":outsourced_object.results,
            "conversation_history": conversations if conversations else "",
            "relevant_information":account.confirmed_problems + relevant_information if account.confirmed_problems else ""
        }
    }
    
    print("*******************************************payload")
    print(payload)
    print("********************************************message")
    print(message)
    # import pdb;pdb.set_trace()
    response = setup_agent(payload=payload)
    print("**********************************************JSON")
    # response = query_gpt(prompt=payload)
    print(response)
    result = response.get('result')
    # Find the index of the opening quote after "text":
    try:
        prepended_result = None
        try:
            prepended_result = result
        except Exception as err:
            print("Trying json repair method 2: ",err)
            try:
                prepended_result_  = result.replace('```json\n','').replace('```','').replace("\n","")
                to_be_replaced = prepended_result_[prepended_result_.find("conversation_history")-4:len(prepended_result_)-1]
                prepended_result = json.loads(prepended_result_.replace(to_be_replaced,""))
            except Exception as err:
                print("Both trials have failed to repair the json: ",err)
                message = f"Both trials have failed to repair the json: {err} "
                notify_click_up_tech_notifications(comment_text=message,notify_all=True)
        try:

            active_stage_res = prepended_result['active_stage']
            print('active_stage:********************',active_stage_res,'****************')
            account.status_param = active_stage_res
            account.save()
        except Exception as err:
            print("Active stage issue *****: ",err)

        try:
            question_asked_res = prepended_result['question_asked']
            account.question_asked = bool(int(question_asked_res))
            account.save()
        except Exception as err:
            print("Question not asked: ",err)
        
        try:
            confirmed_problems_res = prepended_result['confirmed_problems']
            account.confirmed_problems = confirmed_problems_res
            account.save()
        except Exception as err:
            print("Problems not confirmed: ",err)
            create_click_up_task("Problems not confirmed: ",err, notify_all=False)
        try:
            solution_presented_res = prepended_result['solution_presented']
            account.solution_presented = bool(int(solution_presented_res))
            account.save()
        except Exception as err:
            print("Solution not presented: ",err) 
            create_click_up_task("Solution not presented: ",err, notify_all=False)
        try:
            human_takeover = prepended_result['human_takeover']
            print("human_takeover: ",human_takeover)
            if bool(int(human_takeover)):
                account.assigned_to = "Human"
                account.save()
                try:
                    subject = 'Hello Team'
                    message = f'Hello please address the account {account.igname} it has been handed over to you'
                    from_email = 'lutherlunyamwi@gmail.com'
                    recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                    send_mail(subject, message, from_email, recipient_list)
                    notify_click_up_tech_notifications(comment_text=message,notify_all=True)
                except Exception as error:
                    print(error)
                    task_name = "Error seding error notification"
                    task_desc = error
                    create_click_up_task(task_name,task_desc, notify_all=False)
            else:
                print(f"Human takeover not set well {human_takeover}")
                task_name = f"Human takeover not set  properly"
                task_desc = f"Wrong humann take onver variable. The variable returne is {human_takeover}"
                create_click_up_task(task_name,task_desc, notify_all=False)
        except Exception as err:
            print("Human takeover not set: ",err)   
            create_click_up_task("Human takeover not set", err, notify_all=False)
        # index = result.find('"question_asked":')
        # if index != -1:
        #     # Extract the value of 'solution_presented'
        #     question_asked = result[index + 19:].split(',')[0].strip()
        #     # Find the first digit in the text
        #     match = re.search(r'\d', question_asked)

        #     # If a digit is found
        #     if match:
        #         # Extract the digit
        #         first_digit = match.group(0)
        #         if int(first_digit) == 1:
        #             print(f"The first digit found in the text is: {first_digit}")
        #             # agent_name = "Engagement Persona Influencer Audit Closing the Sale Agent"
        #             # agent_task = "ED_PersonaInfluencerAuditClosingTheDealA_BuildMessageT"
                    
        #             account.question_asked = True
        #             account.save()
        #     else:
        #         print("No digit found in the text.")

        # try:
        #     confirmed_problems_str = result.split('"confirmed_problems": [')[1].split(']')[0]
        # except Exception as error:
        #     try:
        #         confirmed_problems_str = result.split('"confirmed_problems":')[1].split(']')[0]
        #     except Exception as error:
        #         print (error)            
        # confirmed_problems = [problem.strip('"') for problem in confirmed_problems_str.split(',')]

        # # Iterate over the confirmed problems
        # for problem in confirmed_problems:
        #     # Check if the problem exists in the text
        #     if problem.lower() in result.lower():
        #         print(f"Confirmed problem found: {problem}")
        #         # agent_name = "Engagement Persona Influencer Audit Solution Presentation Agent"
        #         # agent_task = "ED_PersonaInfluencerAuditSolutionPresentationA_BuildMessageT"
                
        #         account.confirmed_problems = problem.lower().strip().replace("\"","")
        #         account.save()
        #         index = result.find('"solution_presented":')
        #         if index != -1:
        #             # Extract the value of 'solution_presented'
        #             solution_presented = result[index + 19:].split(',')[0].strip()
        #             # Find the first digit in the text
        #             match = re.search(r'\d', solution_presented)

        #             # If a digit is found
        #             if match:
        #                 # Extract the digit
        #                 first_digit = match.group(0)
        #                 if int(first_digit) == 1:
        #                     print(f"The first digit found in the text is: {first_digit}")
        #                     # agent_name = "Engagement Persona Influencer Audit Closing the Sale Agent"
        #                     # agent_task = "ED_PersonaInfluencerAuditClosingTheDealA_BuildMessageT"
                            
        #                     account.solution_presented = True
        #                     account.save()
        #             else:
        #                 print("No digit found in the text.")
        #             #print(f"The value of 'solution_presented' is: {solution_presented}")
        #         else:
        #             print("'solution_presented' not found in the text.")
        #     else:
        #         print(f"No match found for: {problem}")
    except Exception as err:
        print("Improper json: ",err)

    print(result)

    # start_index = result.find('"text": "') + len('"text": "')
    
    # # Find the index of the closing quote before the end of the text
    # end_index = result.rfind('"', start_index)
    
    # # Extract the text
    # extracted_text = result[start_index:end_index]
    
    # print(result)
    # import pdb;pdb.set_trace()
    extracted_text = None
    try:  
        extracted_text = result.get('text').replace("\n", "")
    except Exception as err:
        try:
            extracted_text = extract_text(result)
        except Exception as err:
            print("Error in extracting text: ",err) 
            try:
                extracted_text = result.split('"text": "')[1].split('",')[0]
            except Exception as err:
                print("Error in extracting text: ",err)
                try:
                    extracted_text = "Just a minute"
                    notify_click_up_tech_notifications(comment_text="Error in extracting text, sending just a minute",notify_all=True)
                    create_click_up_task("Error in extracting text", err, notify_all=False)
                except Exception as err:
                    print("Error in extracting text: ",err)
                    notify_click_up_tech_notifications(comment_text="Error in extracting text",notify_all=True)
                    create_click_up_task("Error in extracting text", err, notify_all=False)
    # extracted_text = extracted_text.replace('\n\n', ' ').replace('\n', ' ')
    print(extracted_text)


    return clean_text(extracted_text)
