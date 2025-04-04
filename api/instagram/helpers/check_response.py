import json
import logging
import re
import uuid
from datetime import timedelta

from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from data.helpers.random_data import get_follow_up_messages
from api.dialogflow.helpers.conversations import get_client_conversation_so_far
from api.instagram.models import Message, Thread

from .llm import query_gpt


class CheckResponse(object):
    def __init__(self, status: str, thread: Thread) -> None:
        self.status = status
        self.daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*",
            hour="*",
            day_of_week="*/1",
            day_of_month="*",
            month_of_year="*",
        )
        self.monthly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*",
            hour="*",
            day_of_week="*",
            day_of_month="*/1",
            month_of_year="*",
        )
        self.instance = thread

    def if_followup_task_delete(self):
        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

    def follow_up_task_simple(self, message, time=1, task=None):
        message_object = Message()
        message_object.sent_by = "Robot"
        message_object.thread = self.instance
        message_object.content = message
        message_object.sent_on = timezone.now()
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*",
            hour="*",
            day_of_week=f"*/{time}",
            day_of_month="*",
            month_of_year="*",
        )
        try:
            PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.instance.account.igname}-{task}",
                crontab=schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[message], [self.instance.thread_id]]),
                start_time=timezone.now() + timedelta(days=time),
            )
            message_object.save()
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            task.args = json.dumps([[message], [self.instance.thread_id]])
            task.save()
            message_object.save()
            print(error)

    def follow_up_task(self, message, flip_to_monthly_schedule=True):
        message_object = Message()
        message_object.sent_by = "Robot"
        message_object.thread = self.instance
        message_object.content = message
        message_object.sent_on = timezone.now()
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.instance.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[message], [self.instance.thread_id]]),
                start_time=timezone.now() + timedelta(days=1),
            )
            message_object.save()
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            task.args = json.dumps([[message], [self.instance.thread_id]])
            task.save()
            message_object.save()
            logging.warning(str(error))

        if flip_to_monthly_schedule:
            if timezone.now() >= task.start_time + timedelta(weeks=4):
                followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
                followup_task.args = json.dumps([[message], [self.instance.thread_id]])
                followup_task.crontab = self.monthly_schedule
                followup_task.save()
                message_object.save()

    def follow_up_if_sent_first_compliment(self):
        prompt = f"""
            mention in your instagram-like message that you're sure that they remember their positive reviews but you think that reviews like the one from [get reviewer name from the reviewerNameAndDate from the list of reviews in the data within the triple backticks] that [get reviewer text from the review_text from the list of reviews in the data within the triple backticks and rephrase the review] result in plenty of referrals from their clients.
            here is an example that can guide you;
            example:  I had my browser still open on your profile and Iove what your clients are saying [get reviewServiceName in the reviews list within the data in the triple backticks and then summarize what they said in the review_text in the reviews list within the data in the triple backticks]
            complete this example with an encouraging remark that will keep them moving on.
            ```{[o_data.results['reviews'] for o_data in self.instance.account.outsourced_set.all()]}```
            Do not sound formal, be casual and friendly.
            Do not send greetings.
            Do not sign off.

            Mission Goal:
            The ultimate goal for this conversation is to get the barber to respond. How will you know if a barber has responded. This is how you shall
            detect if the barber has responded. I am going to attach historical data in double backticks below and if the conversation is one way
            that is to mean that you are the only one who is talking and there is no response from the barber you will notice by
            the fact that there will be no historical data within the triple backticks
            then please engage the barber until they get to respond (that is there is historical data exists within the double backticks),
            compliment them with the data given within the
            triple backticks as much as possible till you get them to respond. Do not use more than 20 words. Be simple and encouraging.
            Here is the historical data:
            ``
            {get_client_conversation_so_far(self.instance.thread_id)}
            ``
            if mission is accomplished then return the word
            ACCOMPLISHED in triple backticks and
            if the mission is not accomplished then return the word
            UNACCOMPLISHED in triple backticks as well.

            """
        enforced_shared_compliment = query_gpt(prompt=prompt)
        compliment = enforced_shared_compliment.get("choices")[0].get("message").get("content")
        accomplished_status = re.findall(r"```(.*?)```", compliment)
        if len(accomplished_status) > 0 and accomplished_status[0] == "ACCOMPLISHED":
            self.if_followup_task_delete()
        if len(accomplished_status) > 0 and accomplished_status[0] == "UNACCOMPLISHED":
            self.follow_up_task(message=compliment, flip_to_monthly_schedule=True)

    def follow_up_after_presentation(self):
        if self.instance.account.dormant_profile_created:
            # booksy_status, _ = StatusCheck.objects.get_or_create(stage=2, name="Trial")

            # account = get_object_or_404(Account, id=self.instance.account.id)
            # account.status = booksy_status
            # account.save()

            random_compliment = f""""
                What's up {self.instance.account.igname} let us make the most of your free trial account?
                you can manage it all with https://dl.booksy.com/WSlwk9kUhCb
                (login: {self.instance.account.igname} password: {str(uuid.uuid4())}) to
                [solution to combination of problems]
                DM: let me know what you think and I’ll guide you for a month to grow it like crazy:)
                """
            self.follow_up_task_simple(message=random_compliment, task="after_presentation")

    def follow_up_if_sent_email_first_attempt(self):
        combination_of_problems = []
        random_compliment = f"""
            I actually think Booksy will help you big time {combination_of_problems}
            Let me know your email address and I’ll help you with the setup;)
            """
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.instance.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [self.instance.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(
                name=f"FollowupTask-{self.instance.account.igname}-sent_email_first_attempt"
            )
            task.args = json.dumps([[random_compliment], [self.instance.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(days=1):
            second_attempt = """
                When you see your profile on Booksy you won’t believe that you
                used to [combination of problems].
                What’s your valid email address?
                """
            followup_task = PeriodicTask.objects.get(
                name=f"FollowupTask-{self.instance.account.igname}-sent_email_second_attempt"
            )
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[second_attempt], [self.instance.thread_id]])
            followup_task.save()

            # status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_email_second_attempt")
            # account = get_object_or_404(Account, id=self.instance.account.id)
            # account.status = status_after_response
            # account.save()

        if timezone.now() >= task.start_time + timedelta(days=2):
            third_attempt = """
                I can see you’re pretty busy and wanted to create profile on Booksy for you to
                elevate your business,
                I’ll just need your email address:)
                """
            followup_task = PeriodicTask.objects.get(
                name=f"FollowupTask-{self.instance.account.igname}-sent_email_last_attempt"
            )
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[third_attempt], [self.instance.thread_id]])
            followup_task.save()

            # status_after_response, _ = StatusCheck.objects.get_or_create(stage=3, name="sent_email_last_attempt")
            # account = get_object_or_404(Account, id=self.instance.account.id)
            # account.status = status_after_response
            # account.save()

    def follow_up_if_sent_uninterest(self):
        rephrase_defined_problem = query_gpt(
            """
            ask for the more detailed reason why they are not interested in Booksy as a solution
            """
        )
        random_compliment = rephrase_defined_problem.get("choices")[0].get("message").get("content")
        self.follow_up_task(message=random_compliment)

    def follow_up_profile_review(self):
        random_compliment = f""""
            Did you have a chance to review your profile?\n
            I was wondering if I can be of any help. Please let me know\n
            how did it go?
            """
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.instance.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [self.instance.thread_id]]),
                start_time=timezone.now() + timedelta(days=1),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            task.args = json.dumps([[random_compliment], [self.instance.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(days=1):
            second_attempt = f"""
                What's up {self.instance.account.igname}! I wanted to\n
                make sure you got into the account all okay yesterday? How
                do you like the app?
                """
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[second_attempt], [self.instance.thread_id]])
            followup_task.save()

            # status_after_response, _ = StatusCheck.objects.get_or_create(
            #     stage=2, name="sent_profile_review_second_attempt"
            # )
            # account = get_object_or_404(Account, id=self.instance.account.id)
            # account.status = status_after_response
            # account.save()

        if timezone.now() >= task.start_time + timedelta(days=2):
            second_attempt = f"""
                Hey {self.instance.account.igname} what's up? Just double\n
                checking with you if everything is ok and how is the app working\n
                for you so far
                """
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[second_attempt], [self.instance.thread_id]])
            followup_task.save()

            # status_after_response, _ = StatusCheck.objects.get_or_create(
            #     stage=2, name="sent_profile_review_third_attempt"
            # )
            # account = get_object_or_404(Account, id=self.instance.account.id)
            # account.status = status_after_response
            # account.save()

    def follow_up_calendar_availability(self):
        calendar_availability = "full"
        migration_available = False
        if calendar_availability == "empty":
            message = f""""
                I will work closely with you for a month to help you\n
                [solution to combination of problems]. Before we unlock advanced features\n
                like promoting you to new clients we have to focus on clients you already\n
                have to book with you.
                """

            self.follow_up_task_simple(message, task="calendar_availability")

        if calendar_availability == "full":
            if migration_available:
                message = f""""
                    I'll work closely with you for a month to ensure\n
                    smooth transition & [solution to combination of problems]🗓️\n
                    Are you able to make a switch today?🚀 \n
                    Do you need help to transfer your biz from [competitor]?
                    """

                self.follow_up_task_simple(message, task="calendar_availability")
            else:
                message = f""""
                    I'll work closely with you for a month to \n
                    ensure smooth transition & [solution to combination of problems]🗓️\n
                    Are you able to make a switch today?
                    """

                self.follow_up_task_simple(message, task="calendar_availability")

    def follow_up_ready_switch(self):
        message = f""""
            Alright, let's do this! 🔥🔥🔥\n
            Time is money so I'd recommend we focus on \n
            inviting your existing clients to book with you first. \n
            It'll enable marketing automation, new clients acquisition, \n
            no-show protection, mobile payments, and more.
            """

        self.follow_up_task_simple(message, task="ready_switch")

    def follow_up_highest_impact_actions(self):
        message = f""""
            Highest impact actions for today:\n
            ☑️ Import & Invite Clients\n
            ☑️ IG book button\n
            ☑️ Booksy link in IG bio + bio inviting to book you\n
            ☑️ share flyer with followers
            """

        self.follow_up_task_simple(message, task="high_impact_action")

    def follow_up_get_clients(self):
        message = f""""
            📞 Got your client details handy on your phone? \n
            Add them to Booksy like 1-2-3:\n
            1. Head to Clients and click '+' https://dl.booksy.com/4ch9X4Vyprb\n
            2. Choose Import & Invite.\n
            3. Select your peeps and hit Add clients.Easy, right? 👍
            """

        self.follow_up_task_simple(message, task="get_clients")

    def follow_up_instagram(self):
        message = f""""
            📸 Making booking a breeze on Instagram:
            1. Ensure your IG is synced with the same email as your Booksy (or ask our Support to change it).\n
            2. Set up an IG business account (Here's a handy guide: fb.com/help/instagram/502981923235522) \n
            3. Then, in IG: Edit profile 👉🏻 Action buttons  👉🏻 Book Now 👉🏻 Booksy 👉🏻 Select Country & sign in to Booksy 👉🏻 Continue
            Psst! Add [subdomain] and “book me via IG below 👇” to your IG bio for that extra oomph! 🌟
            """

        self.follow_up_task_simple(message, task="instagram")

    def follow_up_share_flyer(self):
        random_compliment = f"""
            share with followers your flyer or customize it first with your \n
            logo/ background in the app (⚡ ⟶ Social Post Creator)I'll \n
            happily repost something like:\n
            Book your next appointment with me on Booksy.\n
            Link in bio. #booksy #onlinebooking @[sales repss ig handle]\n
            Succeeding in the first days will set you up for a long term success💯 \n
            Let me know how it goes!💪🏻
        """
        self.follow_up_task_simple(random_compliment, task="share_flyer")

    def follow_up_greeting_day(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        for i in range(0, 18):
            followup_message = get_follow_up_messages(salesrep=salesrep, day=f"day_{i}")
            self.follow_up_task_simple(followup_message, 1, task=f"day_greeting_{i}")

    def follow_up_after_4_weeks(self):
        message = f"""
            Hey! I just wanted to check and see how things were going with Booksy?\n
            Are you satisfied with the onboarding process?\n
            Is there anything we could improve? \n
            Your feedback is very important to us and much appreciated!
        """
        self.follow_up_task_simple(message, 28, task="after_4_weeks")

    def follow_up_after_4_weeks_2_days(self):
        message = f"""
            Who are your closest [category] friends? \n
            I'm always on the lookout for talent - anyone I should follow?
        """
        self.follow_up_task_simple(message, 30, task="after_4_weeks_2_days")

    def follow_up_after_referral_positive(self):
        message = f"""
            I've had a closer look at [recommended lead name] and I'm amazed! \n
            I'd love to spend a month taking [recommended lead IG handle]'s business to another level.\n
            Can you introduce me? Your referral will naturally be rewarded;)
        """
        self.follow_up_task_simple(message, task="referral_positive")

    def follow_up_after_referral_negative(self):
        message = f"""
            Awesome, thanks a lot! do you know more people I should follow?\n
            it usually takes me at least 5 attempts to find a person like you:)\n
            Maybe someone who still spends time manually booking their appointments\n
            and could save a few hours a week? 🤔
        """
        self.follow_up_task_simple(message, task="referral_negative")

    def follow_up_if_account_not_blocked(self):
        message = f"""
            [name], Clients booked into your calendar for [days with CBs this week]\n
            days & [days with CBs next week] days next week.\n
            You've collected [number of 5-star reviews] reviews so far.\n
            Would it make sense to send another message blast or digital \n
            flyer today to keep those bookings coming in? 🤔
        """
        self.follow_up_task_simple(message)

    def follow_up_if_deferred(self, defferred_time=1):
        prompt = f"""
        Scenario Context:
        You are a sales representative for Booksy, a leading appointment booking system and beauty marketplace. Your goal is to re-engage with a US-based barber via Instagram DMs. You aim to proceed with the sales conversation, understanding the stage you're at and following up effectively. Your approach needs to be considerate of the barber's time and needs, and you should continue the conversation by referencing the main point of the previous messages.

        Snippet of Past Conversations:



        Instructions:
        Based on the context of the past messages make sure to provide ONLY the direct message to be sent to the respondent via Instagram DM based on the previous conversation, without any additional context or quotation marks:

        If early in the sales process (before sharing the solution):
        Engage in small talk, reference an earlier point from the conversation, and lead into sharing more about Booksy.
        If somewhere in the middle of the sales process (post presenting the solution but no commitment yet):
        Reference the main point from the previous message, and ask for feedback or thoughts.
        If further along the sales process (after answering questions or concerns):
        Ask directly if they're still interested or have found an alternative.
        """
        deffered_followup_text = query_gpt(prompt=prompt)

        text = deffered_followup_text.get("choices")[0].get("message").get("content")

        self.follow_up_task_simple(message=text, time=defferred_time, task="deferred")
