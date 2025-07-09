from api.prompt.views import OUTPUT_MODELS, TOOLS
from api.prompt.models import Department, Task as TaskModel, Agent as AgentModel
from api.instagram.models import Account,UnwantedAccount
from django.utils import timezone
from django.db.models import Q
from api.dialogflow.helpers.notify_click_up import notify_click_up_tech_notifications, create_click_up_task
# from .tasks import qualify_and_reschedule
from django.core.mail import send_mail


from crewai import Task, Agent, Crew,Process,LLM
from django_tenants.utils import schema_context
from crewai.flow.flow import Flow, and_, listen, start
from api.instagram.utils import initialize_hikerapi_client
import json
import os
import ast
import requests
import asyncio
import inspect
import logging
from pydantic import BaseModel
from typing import List, Optional, Union



class PrequalifyingOutput(BaseModel):
   prequalified: Optional[bool] = None
   name: Optional[str] = None
   media_details: Optional[List[str]] = None 
   strengths: Optional[Union[str, List[str]]] = None
   biography: Optional[str] = None
   area: Optional[str] = None
   contact_details: Optional[Union[dict, str]] = None
   external_url: Optional[str] = None
   desired_provider: Optional[bool] = None
   desired_size: Optional[bool] = None
   desired_location: Optional[bool] = None
   desired_category: Optional[bool] = None
   desired_visibility: Optional[bool] = None
   desired_activity: Optional[bool] = None
   lead_score: Optional[Union[int,str]] = None





class PrequalifyingWorkflow(Flow):
   
   
   def __init__(self, agents, tasks, inputs):
      super().__init__()
      self.agents = agents
      self.tasks = tasks
      self.inputs = inputs
      self.headers = {"Content-Type": "application/json"}


   def clean_json_output(self, raw_output: str) -> dict:
      """
      Parses a raw JSON string and ensures 'content' is a list.
      If 'content' is a string, it converts it into a list.
      Handles nested JSON structures recursively.
      """
      try:
         # Extract JSON from raw output (if wrapped in additional text)
         start_index = raw_output.find("{")
         end_index = raw_output.rfind("}")
         if start_index == -1 or end_index == -1:
               raise ValueError("Invalid JSON structure in raw output")

         json_string = raw_output[start_index:end_index + 1]
         no_newlines = json_string.replace("\n", " ")

         data  = None
         try:
            data = json.loads(no_newlines)
         except json.decoder.JSONDecodeError as err:
            logging.warning("Error loading JSON")
            try:
               data = eval(no_newlines)
            except Exception as e:
               logging.warning(e, "Error evaluating JSON")
               try:
                  data = no_newlines
               except Exception as e:
                  logging.error(e, "Error converting JSON to string")
                  data = {}


         
         # Check if 'content' exists and is a string; convert to list if so
         if "content" in data:
               if isinstance(data["content"], str):
                  data["content"] = [data["content"]]  # Convert string to list
         return data

      except (json.JSONDecodeError, ValueError) as e:
         print(f"Error decoding or cleaning JSON: {e}")
         return {}
 

   
   def get_agents(self,filter_value):
      filtered_dict = [agent for agent in self.agents if any(v == filter_value for _, v in agent.items())]
      return [v for filtered_dict_ in filtered_dict for _, v in filtered_dict_.items() if isinstance(v, Agent)]


   def get_tasks(self, filter_value):
      filtered_tasks = [task for task in self.tasks if task.agent.goal == filter_value]
      return filtered_tasks
   
   @schema_context(os.getenv('SCHEMA_NAME'))
   def patch_account_request(self, output, username):
      username = self.inputs["outsourced_info"]["username"] if isinstance(self.inputs["outsourced_info"], dict) else ast.literal_eval(self.inputs["outsourced_info"])['username']
      
      get_id_account_data = {
         "username": username
      }
      response = requests.post(f"{os.getenv('API_URL')}/instagram/account/get-id/",data=get_id_account_data)
      # import pdb;pdb.set_trace()
      print(response.json())
      account_id = response.json()['id']
      prequalified_flag = False
      try:
         prequalified_flag = output['prequalified']['prequalified']
      except Exception as e:
         logging.warning(e)
         try:
            prequalified_flag = output['prequalified'] if isinstance(output['prequalified'],bool) else output['prequalified']['desired_category']
         except Exception as err:
            logging.warning(err)
            try:
               prequalified_flag = False
            except Exception as err:
               logging.error(err)
               prequalified_flag = False

      # import pdb;pdb.set_trace()
      # print(prequalified_flag)
      account_dict = {
         "igname": username,
         "is_manually_triggered":True,
         "relevant_information": output if output else {},
         "qualified": prequalified_flag,
      }

      # response = requests.patch(
      #    f"{os.getenv('API_URL')}/instagram/account/{account_id}/",
      #    headers=self.headers,
      #    data=json.dumps(account_dict)
      # )
      accounts = Account.objects.filter(igname=username)
      if accounts.exists():
         for account in accounts:
            account.relevant_information = output if output else {}
            account.qualified = prequalified_flag
            account.dormant_profile_created = True
            account.save()
      logging.warning(f"Account {username} updated with prequalified status: {prequalified_flag}")
      return response

   @start()
   def prequalifying_flag_assessor(self):
      agents = self.get_agents(inspect.currentframe().f_code.co_name)
      first_agent = next(iter(agents))
      tasks = self.get_tasks(first_agent.goal)
      desired_category = None
      desired_location = None
      desired_visibility = None
      desired_activity = None
      desired_provider = None
      desired_size = None

      for task in tasks: # we iterate through each task and handle them separately if needed
         crew = Crew(agents=agents, tasks=[task], verbose=True, memory=True)
         # outsourced_info_ = {"preqaulified":self.state.get("prequalified_result",{})}
         result = crew.kickoff(inputs=self.inputs)
         if result.json_dict:
            if result.json_dict.get("desired_location") is not None and isinstance(result.json_dict.get("desired_location"),bool):
               desired_location = result.json_dict.get("desired_location")
            
            if result.json_dict.get("desired_category") is not None and isinstance(result.json_dict.get("desired_category"),bool):
               desired_category = result.json_dict.get("desired_category")

            if result.json_dict.get("desired_visibility") is not None and isinstance(result.json_dict.get("desired_visibility"),bool):
               desired_visibility = result.json_dict.get("desired_visibility")
            
            if result.json_dict.get("desired_activity") is not None and isinstance(result.json_dict.get("desired_activity"),bool):
               desired_activity = result.json_dict.get("desired_activity")

            if result.json_dict.get("desired_provider") is not None and isinstance(result.json_dict.get("desired_provider"),bool):
               desired_provider = result.json_dict.get("desired_provider")

            if result.json_dict.get("desired_size") is not None and isinstance(result.json_dict.get("desired_size"),bool):
               desired_size = result.json_dict.get("desired_size")

      conditions = [desired_location, desired_category, desired_visibility, desired_activity, desired_provider, desired_size]
      print(conditions)
      true_count_of_conditions = sum(conditions)
      if true_count_of_conditions >= 3 and desired_location and desired_provider:
         self.state["prequalified_result"] = {
            "prequalified":True,
            "desired_location":desired_location, 
            "desired_category": desired_category, 
            "desired_visibility":desired_visibility, 
            "desired_activity": desired_activity, 
            "desired_provider": desired_provider, 
            "desired_size": desired_size
         }
      else:
         self.state["prequalified_result"] = {
            "prequalified":False,
            "desired_location":desired_location, 
            "desired_category": desired_category, 
            "desired_visibility":desired_visibility, 
            "desired_activity": desired_activity, 
            "desired_provider": desired_provider, 
            "desired_size": desired_size
         }
      # import pdb;pdb.set_trace()
         # crew_result = result.json_dict
      # self.state["prequalified_result"] = result.json_dict
      # outsourced_info_.update(result.json_dict)
      # print(crew_result)
      print(self.state)
      print(1)
      # biography = outsourced_info_['biography']
      # external_url = outsourced_info_['external_url']
      # city_name = outsourced_info_['city_name']
      # full_name = outsourced_info_['full_name']
      # public_email = outsourced_info_['public_email']
      # public_phone_number = outsourced_info_['public_phone_number'],
      # contact_phone_number = outsourced_info_['contact_phone_number']
      
      # if self.state["prequalified_result"]["prequalified"]:
      #    # print(self.state["output"])
      #    self.patch_account_request(
      #       {
      #          "prequalified":self.state["prequalified_result"]["prequalified"],
      #          "name":full_name if full_name else "",
      #          "full_name":full_name if full_name else "",
      #          "bio": biography if biography else "",
      #          "external_url": external_url if external_url else "",
      #          "strengths": result.json_dict.get("strengths",""),
      #          "area": result.json_dict.get("area") if result.json_dict.get("area") else city_name,
      #          "contact_details": {
      #             "public_email": public_email if public_email else "",
      #             "public_phone_number": public_phone_number if public_phone_number else "",
      #             "contact_phone_number": contact_phone_number if contact_phone_number else ""
      #          }

      #       }, self.inputs["outsourced_info"]["username"])
      

   # @listen(prequalifying_flag_assessor)
   # def lead_score_calculator(self):
   #    agents = self.get_agents(inspect.currentframe().f_code.co_name)
   #    first_agent = next(iter(agents))
   #    tasks = self.get_tasks(first_agent.goal)
   #    crew = Crew(agents=agents, tasks=tasks, verbose=True, memory=True)
   #    result = crew.kickoff(inputs=self.inputs)
   #    crew_result = result.json_dict
   #    self.state["score_result"] = crew_result
   #    print(2)

   

   @listen(and_(prequalifying_flag_assessor))
   def prequalifying_output_extractor(self):
        print("---- Logger ----")
        agents = self.get_agents(inspect.currentframe().f_code.co_name)
        first_agent = next(iter(agents))
        tasks = self.get_tasks(first_agent.goal)
        crew = Crew(agents=agents, tasks=tasks, verbose=True, memory=True)
        # outsourced_info_.update({"lead_score":self.state.get("score_result",{}), "preqaulified":self.state.get("prequalified_result",{})})
        # import pdb;pdb.set_trace()
        outsourced_info_ = None
        if isinstance(self.inputs['outsourced_info'], str):
            # If the input is a string, we need to parse it as a dictionary
            outsourced_info_ = ast.literal_eval(self.inputs['outsourced_info'])
        else:
            outsourced_info_ = self.inputs['outsourced_info']
        biography = outsourced_info_['biography']

        external_url = outsourced_info_['external_url']
        city_name = outsourced_info_['city_name']
        full_name = outsourced_info_['full_name']
        public_email = outsourced_info_['public_email']
        public_phone_number = outsourced_info_['public_phone_number'],
        contact_phone_number = outsourced_info_['contact_phone_number']
        outsourced_info_ = {"username":outsourced_info_['username'],"bio":outsourced_info_['biography']}
        # outsourced_info_.update({"preqaulified":self.state.get("prequalified_result",{})})
        # outsourced_info_ = {"preqaulified":self.state.get("prequalified_result",{})}
        result = crew.kickoff(inputs=self.inputs)
        # import pdb;pdb.set_trace()
        # crew_result = result.json_dict
        self.state["output"] = result.json_dict

      # import pdb;pdb.set_trace()
      # print(self.state["output"])
    #   if self.state["prequalified_result"]["prequalified"]:
         # print(self.state["output"])
        self.patch_account_request(
        {
            "prequalified":self.state["prequalified_result"]["prequalified"],
            "name":self.state["output"]["name"],
            "full_name":full_name if full_name else "",
            "bio": biography if biography else "",
            "external_url": external_url if external_url else "",
            "strengths": result.json_dict.get("strengths",""),
            "area": result.json_dict.get("area") if result.json_dict.get("area") else city_name,
            "contact_details": {
                "public_email": public_email if public_email else "",
                "public_phone_number": public_phone_number if public_phone_number else "",
                "contact_phone_number": contact_phone_number if contact_phone_number else ""
            }

        }, self.inputs["outsourced_info"]["username"] if isinstance(self.inputs["outsourced_info"], dict) else ast.literal_eval(self.inputs["outsourced_info"])['username'])


        # patch the output to the database
        print(3)


def prequalifying_automatically():
   department = "Qualifying Department"
   null = None
   false, true = False, True

   threshold = 26
   with schema_context(os.getenv("SCHEMA_NAME")):
      start_date = timezone.now().date() - timezone.timedelta(days=0)
      end_date = timezone.now().date() + timezone.timedelta(days=1)
      unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)
      start_datetime = timezone.make_aware(
         timezone.datetime.combine(start_date, timezone.datetime.min.time())
      )

      prequalified_accounts = Account.objects.filter(
         Q(qualified=True) & Q(created_at__gte=start_datetime) & Q(created_at__lte=end_date)
      ).exclude(
         status__name="sent_compliment"
      ).exclude(
         igname__in=unwanted_usernames
      ).filter(dormant_profile_created=True)

      while prequalified_accounts.count() < threshold:
               # return
         qualifying_payloads = []
         with schema_context(os.getenv("SCHEMA_NAME")):
               start_date = timezone.now().date() - timezone.timedelta(days=0)
               end_date = timezone.now().date() + timezone.timedelta(days=1)
               unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)
               start_datetime = timezone.make_aware(
                  timezone.datetime.combine(start_date, timezone.datetime.min.time())
               )

               accounts = Account.objects.filter(
                  Q(qualified=True) & Q(created_at__gte=start_datetime) & Q(created_at__lte=end_date)
               ).exclude(
                  status__name="sent_compliment"
               ).exclude(
                  igname__in=unwanted_usernames
               ).exclude(
                  dormant_profile_created=True
               )[:10]

               # accounts = accounts.filter(igname="_barberc").distinct('igname')
               print(f"Accounts to process: {accounts.count()}")
               # if accounts.count() < threshold:
                  # print(f"Not enough accounts to process. Only {accounts.count()} accounts found.")
               for account in accounts:
                  print(account.outsourced_set.all().latest('created_at').results if account.outsourced_set.exists() else {"username":account.igname})
               # import pdb;pdb.set_trace()
               for account in accounts:
                  cl = initialize_hikerapi_client()
                  check_user_exists = cl.user_by_username_v1(account.igname)
                  if 'exc_type' in check_user_exists.keys():
                     account_name = account.igname
                     account.delete()
                     continue
                   
                  if not account.outsourced_set.exists():
                     account.qualified = False
                     account.dormant_profile_created = True
                     account.save()
                     continue


                  qualifying_payload = {
                     "department":"Prequalifying",
                     "agent_name":"Qualifying Agent",
                     "agent_task":"QD_QualifyingA_CalculatePersonaInfluencerAuditQualifyingScoreT",
                     "converstations":"",
                     "Scraped":{
                        "message":"",
                        "sales_rep":"barbersince98",
                        "influencer_ig_name":"barbersince98",
                        "outsourced_info":account.outsourced_set.all().latest('created_at').results if account.outsourced_set.exists() else {"username":account.igname},
                        "relevant_information": account.relevant_information if account.relevant_information else {}
                     }
                  }
                  qualifying_payloads.append(qualifying_payload)



         agents = []
         tasks = []
         department_name = "Prequalifying"

         with schema_context(os.getenv("SCHEMA_NAME")):
            print(Department.objects.filter(name=department_name))
            department = Department.objects.filter(name=department_name).latest("created_at")
            
            agents_ = department.agents.all()
            tasks_ = department.tasks.all()
            # print(tasks_)
            for i, agent in enumerate(agents_):
               print(agent.llm)
               llm_val = None
               if agent.is_opensource:
                  llm_val = agent.llm
               else:
                  llm_val = LLM(model="gpt-3.5-turbo")
               agents.append({f"agent_{i}":Agent(
                                    role=agent.role.description + " " + agent.role.tone_of_voice if agent.role else "Qualifying department",
                                    goal=agent.goal,
                                    backstory=agent.prompt.last().text_data,
                                    allow_delegation=False,
                                    verbose=True,
                                    llm=llm_val
                              ),
                              f"workflow_step_{i}":agent.workflow
                           })
            for i,task in enumerate(tasks_):    
               llm_val = None
               if agent.is_opensource:
                  llm_val = task.agent.llm
               else:
                  llm_val = LLM(model="gpt-3.5-turbo")
               tasks.append(Task(
                              description=task.prompt.last().text_data if task.prompt.exists() else "perform agents task",
                              expected_output=task.expected_output,
                              tools=[TOOLS.get(tool.name) for tool in task.tools.all()],
                              agent=Agent(
                                    role=task.agent.role.description + " " + task.agent.role.tone_of_voice if task.agent.role else "Qualifying department",
                                    goal=task.agent.goal,
                                    backstory=task.agent.prompt.last().text_data,
                                    allow_delegation=False,
                                    verbose=True,
                                    llm=llm_val
                              ),
                              # output_json=OUTPUT_MODELS.get(task.output)
                              output_json=PrequalifyingOutput
                           ))
                           
            # print(tasks)
            # I need to get it to work continually with a threshold of x
            for i,payload in enumerate(qualifying_payloads):
            #  if i == 2:
                  # break 
               try:
                  flow = PrequalifyingWorkflow(agents = agents,tasks = tasks,inputs = payload.get(department.baton.start_key))
                  asyncio.run(flow.kickoff())
               except Exception as e:
                  print(f"Error processing payload {i}-for user {payload}: {e}")
                  continue
            
            try:

               if prequalified_accounts.count() >= 25:
                  message = f'Finished prequalifying accounts for today {timezone.now()}'
               else:
                  message = (
                        f'Finished prequalifying current batch but did not reach the threshold target of 25, therefore we are proceeding to the next batch.'
                        f'Only {prequalified_accounts.count()} accounts were processed as of {timezone.now()}'
                  )
               subject = 'Hello Team'
               from_email = 'lutherlunyamwi@gmail.com'
               recipient_list = ['lutherlunyamwi@gmail.com', 'tomek@boostedchat.com']
               # send_mail(subject, message, from_email, recipient_list)
               notify_click_up_tech_notifications(comment_text=message, notify_all=True)
            except Exception as error:
               print(error)
      
         from api.instagram.tasks import qualify_and_reschedule
         qualify_and_reschedule() # we reload accounts afresh
         prequalifying_automatically() # we call the function again to continue processing until we reach the threshold

