from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from django_celery_beat.models import PeriodicTask

from api.instagram.helpers.llm import query_gpt
from api.instagram.models import Account, StatusCheck, Thread
from api.instagram.tasks import follow_user


class GenerateResponse(object):
    def __init__(self, status: str, thread: Thread, lead_response: str) -> None:
        self.status = status
        self.instance = thread
        self.lead_response = lead_response

    def if_followup_task_delete(self):
        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

    def update_account_status(self, stage, new_status):
        statuscheck, _ = StatusCheck.objects.update_or_create(stage=stage, name=new_status)

        account = get_object_or_404(Account, id=self.instance.account.id)
        account.status = statuscheck
        account.save()

    def check_responded_to_first_compliment(self):
        self.if_followup_task_delete()
        prompt = query_gpt(
            f"""
            appropriately respond to the following dm within the triple backticks
            ```{self.lead_response}``` in a friendly tone add emoji where necessary
            """
        )

        enforced_shared_compliment = query_gpt(prompt=prompt)

        generated_response = enforced_shared_compliment.get("choices")[0].get("message").get("content")

        follow_user.delay(self.instance.account.igname)

        self.update_account_status(2, "preparing_to_send_first_question")

        return generated_response

    def check_sent_first_question(self):

        self.if_followup_task_delete()

        rephrase_defined_problem = query_gpt(
            f"""
            rephrase the problem stated in the followin dm within the triple backticks
            ```{self.lead_response}``` in a friendly tone add emoji that indicate
            you are in sympathy with them
            """
        )
        generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")

        self.update_account_status(2, "preparing_to_send_second_question")

        return generated_response

    def check_sent_second_question(self):
        last_seven_days = [date.today() - timedelta(days=day) for day in range(7)]
        if self.instance.account.outsourced:
            if self.instance.account.outsourced.updated_at.date() in last_seven_days:
                pass
        else:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                rephrase the importance stated in the following dm within the triple backticks
                ```{self.lead_response}``` in a friendly tone add emoji that indicate
                you are affirming what they are saying
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")

            self.update_account_status(2, "preparing_to_send_third_question")

            return generated_response

    def check_sent_third_question(self):
        booking_system = None
        last_seven_days = [date.today() - timedelta(days=day) for day in range(7)]
        if booking_system and self.instance.account.outsourced.updated_at.date() in last_seven_days:
            pass
        else:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")

            self.update_account_status(2, "preparing_to_send_first_needs_assessment_question")

            return generated_response

    def check_sent_first_needs_assessment_question(self):
        confirm_reject_problem = True
        if confirm_reject_problem:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "preparing_to_send_second_needs_assessment_question")
            return generated_response
        else:
            pass

    def check_sent_second_needs_assessment_question(self):

        confirm_reject_problem = True
        if confirm_reject_problem:

            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "preparing_to_send_third_needs_assessment_question")
            return generated_response
        else:
            pass

    def check_sent_third_needs_assessment_question(self):

        confirm_reject_problem = True
        if confirm_reject_problem:

            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "follow_up_after_presentation")
            return generated_response
        else:
            pass

    def check_sent_follow_up_presententation(self):
        check_email = True

        generated_response = None

        if check_email:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "ask_for_email_first_attempt")

        else:
            interested = query_gpt(
                f"""
                analyse to the following dm within the triple backticks
                ```{self.lead_response}``` to know whether they are interested in the
                product or not and return
                a boolean of 0 -if not interested, and 1 -if interested and 2 -if have any objections.
                """
            )
            if int(interested) == 1:
                pass

            elif int(interested) == 0:
                rephrase_defined_problem = query_gpt(
                    f"""
                    rephrase the following dm within the triple backticks
                    ```{self.lead_response}``` asking them why they are not interested.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
                self.update_account_status(3, "ask_uninterest")
            elif int(interested) == 2:
                rephrase_defined_problem = query_gpt(
                    f"""
                    rephrase objection within the triple backticks
                    ```{self.lead_response}``` in a way
                    to show that they’re understood
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
                self.update_account_status(3, "ask_objection")

        return generated_response
